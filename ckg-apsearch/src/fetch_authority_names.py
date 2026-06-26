"""
Fetch preferred names for the residue of authority URIs not yet in crosswalk.json,
to prepare them for OpenRefine reconciliation.

Strategy:
  GND residue  → lobid.org JSON API (direct, works reliably)
  VIAF residue → lobid.org sameAs.id search (VIAF API has been retired/broken).
                 If lobid finds a GND entity for the VIAF URI AND that GND URI is
                 already in the crosswalk, we write the VIAF→QID mapping directly
                 to viaf_via_gnd_resolved.json (skipping OpenRefine for those).
  GeoNames     → hard-coded (4 Detmold entries only)

Outputs (all under ../data/openrefine/):
  names_for_reconciliation.csv      — authority_uri, name, entity_type, scheme
  authority_name_cache.json         — disk cache (append-safe, restart-safe)
  viaf_via_gnd_resolved.json        — {viaf_uri: qid} resolved via VIAF→GND→QID chain
  fetch_404s.txt                    — URIs where no name could be found

CWD must be src/ (standard for this pipeline).
"""

import csv
import json
import time
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# Paths (relative to src/)
# ---------------------------------------------------------------------------
DATA = Path("../data")
EXTRACTED = DATA / "extracted"
MAPPINGS = DATA / "mappings"
OUT_DIR = DATA / "openrefine"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CROSSWALK_PATH = MAPPINGS / "crosswalk.json"
CACHE_PATH = OUT_DIR / "authority_name_cache.json"
CSV_PATH = OUT_DIR / "names_for_reconciliation.csv"
VIA_GND_PATH = OUT_DIR / "viaf_via_gnd_resolved.json"
NOT_FOUND_PATH = OUT_DIR / "fetch_404s.txt"

UA = "LinkedMusic-datalake/1.0 (liam.pond@mail.mcgill.ca)"

# GeoNames residue — only 4 Detmold places. Names taken from GeoNames Linked Data
# (https://sws.geonames.org/<id>/about.rdf), re-verified 2026-06-17. The IDs are
# the Detmold source's ground truth; the earlier names (Aarau/Mannheim/Hamm) were
# mis-entered and did NOT match their IDs (2657896=Zürich, 2871039=Minden,
# 2910831=Hannover) — corrected below.
GEONAMES_HARDCODED = {
    "http://sws.geonames.org/2657896": ("Zürich", "Place"),
    "http://sws.geonames.org/2871039": ("Minden", "Place"),
    "http://sws.geonames.org/2910831": ("Hannover", "Place"),
    "http://sws.geonames.org/3247449": ("Aachen", "Place"),
}

GND_TYPE_MAP = {
    "Person": "Person",
    "DifferentiatedPerson": "Person",
    "UndifferentiatedPerson": "Person",
    "NameOfThePerson": "Person",
    "LiteraryOrLegendaryCharacter": "Person",
    "Family": "Person",
    "CorporateBody": "Organization",
    "ConferenceOrEvent": "Organization",
    "PlaceOrGeographicName": "Place",
    "SubjectHeading": "Collection",
    "Work": "Collection",
    "Periodical": "Collection",
    "Series": "Collection",
    "Collection": "Collection",
    "Manuscript": "Collection",
    "MusicManuscript": "Collection",
    "Newspaper": "Collection",
}


def load_json(path: Path) -> dict:
    if path.exists():
        with path.open() as f:
            return json.load(f)
    return {}


def save_json(path: Path, obj: dict) -> None:
    with path.open("w") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Build residue set: {authority_uri -> (entity_type, scheme)}
# ---------------------------------------------------------------------------

def build_residue(crosswalk: dict) -> dict[str, tuple[str, str]]:
    resolved = set(crosswalk.keys())

    # Build uri → entity_type from entities files
    uri_to_type: dict[str, str] = {}
    for feed in ("musiconn", "detmold"):
        ent_path = EXTRACTED / f"{feed}.entities.json"
        if not ent_path.exists():
            continue
        data = load_json(ent_path)
        for info in data.get("entities", {}).values():
            uri = info.get("a")
            t = info.get("t")
            if uri and t and uri not in uri_to_type:
                uri_to_type[uri] = t

    residue: dict[str, tuple[str, str]] = {}
    for feed in ("musiconn", "detmold"):
        auth_path = EXTRACTED / f"{feed}.authorities.json"
        if not auth_path.exists():
            continue
        auth = load_json(auth_path)
        for scheme, id_to_uri in auth.items():
            for uri in id_to_uri.values():
                if uri in resolved or uri in residue:
                    continue
                etype = uri_to_type.get(uri, "Person")
                residue[uri] = (etype, scheme)

    return residue


# ---------------------------------------------------------------------------
# GND fetch via lobid.org
# ---------------------------------------------------------------------------

def map_gnd_type(gnd_types: list) -> str:
    for t in gnd_types:
        short = t.split("#")[-1].split("/")[-1]
        if short in GND_TYPE_MAP:
            return GND_TYPE_MAP[short]
    return "Person"


def fetch_gnd(gnd_id: str, session: requests.Session, cache: dict) -> tuple[str, str] | None:
    """Returns (name, entity_type) or None on 404/parse error."""
    uri = f"https://d-nb.info/gnd/{gnd_id}"
    if uri in cache:
        entry = cache[uri]
        return (entry["name"], entry["type"]) if entry else None

    url = f"https://lobid.org/gnd/{gnd_id}.json"
    try:
        r = session.get(url, headers={"Accept": "application/json", "User-Agent": UA}, timeout=20)
    except requests.RequestException as exc:
        print(f"  GND request error {gnd_id}: {exc}")
        return None

    if r.status_code == 404:
        cache[uri] = None
        return None

    if r.status_code != 200:
        print(f"  GND {gnd_id} → HTTP {r.status_code}")
        return None

    try:
        data = r.json()
    except Exception:
        return None

    name = data.get("preferredName", "")
    if not name:
        variants = data.get("variantName", [])
        name = variants[0] if variants else ""

    etype = map_gnd_type(data.get("type", []))
    cache[uri] = {"name": name, "type": etype}
    return (name, etype)


# ---------------------------------------------------------------------------
# VIAF → GND cross-reference via lobid sameAs
# (VIAF JSON API was retired; lobid indexes VIAF URIs as sameAs on GND records)
# ---------------------------------------------------------------------------

def fetch_viaf_via_lobid(
    viaf_uri: str,
    session: requests.Session,
    cache: dict,
    crosswalk: dict,
) -> tuple[str | None, str | None, str | None]:
    """
    Returns (name, entity_type, gnd_uri_or_None).
    name and entity_type are None if nothing found.
    gnd_uri is set when a GND record was found that sameAs-links this VIAF URI.
    """
    cache_key = f"viaf_via_lobid:{viaf_uri}"
    if cache_key in cache:
        entry = cache[cache_key]
        return (entry.get("name"), entry.get("type"), entry.get("gnd_uri")) if entry else (None, None, None)

    url = "https://lobid.org/gnd/search"
    params = {"q": f'sameAs.id:"{viaf_uri}"', "format": "json", "size": 1}
    try:
        r = session.get(url, params=params, headers={"User-Agent": UA}, timeout=20)
    except requests.RequestException as exc:
        print(f"  lobid VIAF search error {viaf_uri}: {exc}")
        return (None, None, None)

    if r.status_code != 200:
        print(f"  lobid sameAs search → HTTP {r.status_code} for {viaf_uri}")
        cache[cache_key] = None
        return (None, None, None)

    try:
        data = r.json()
    except Exception:
        cache[cache_key] = None
        return (None, None, None)

    if data.get("totalItems", 0) == 0:
        cache[cache_key] = None
        return (None, None, None)

    hit = data["member"][0]
    name = hit.get("preferredName", "")
    gnd_id = hit.get("gndIdentifier", "")
    gnd_uri = f"https://d-nb.info/gnd/{gnd_id}" if gnd_id else None
    etype = map_gnd_type(hit.get("type", []))

    result = {"name": name, "type": etype, "gnd_uri": gnd_uri}
    cache[cache_key] = result
    return (name, etype, gnd_uri)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    crosswalk = load_json(CROSSWALK_PATH)
    cache: dict = load_json(CACHE_PATH)
    via_gnd: dict = load_json(VIA_GND_PATH)  # accumulate across runs

    print("Building residue list...")
    residue = build_residue(crosswalk)

    gnd_res = [(u, t) for u, (t, s) in residue.items() if s == "gnd"]
    viaf_res = [(u, t) for u, (t, s) in residue.items() if s == "viaf"]
    geo_res = [(u, t) for u, (t, s) in residue.items() if s == "geonames"]
    print(f"  GND: {len(gnd_res)}, VIAF: {len(viaf_res)}, GeoNames: {len(geo_res)}")

    session = requests.Session()
    rows: list[dict] = []
    not_found: list[str] = []

    # --- GeoNames (hard-coded) ---
    for uri, (etype, _) in residue.items():
        if "geonames" not in uri:
            continue
        if uri in GEONAMES_HARDCODED:
            name, _ = GEONAMES_HARDCODED[uri]
            rows.append({"authority_uri": uri, "name": name, "entity_type": etype, "scheme": "geonames"})
        else:
            print(f"  WARNING: unknown GeoNames URI {uri} — add to GEONAMES_HARDCODED")
            not_found.append(uri)
    print(f"GeoNames: {len(geo_res)} hard-coded.")

    # --- GND ---
    print(f"Fetching GND names ({len(gnd_res)} entries)...")
    already_cached = sum(1 for u, _ in gnd_res if u in cache)
    print(f"  {already_cached} already in cache, {len(gnd_res) - already_cached} to fetch")

    for i, (uri, etype) in enumerate(gnd_res):
        gnd_id = uri.rstrip("/").rsplit("/", 1)[-1]
        was_cached = uri in cache
        result = fetch_gnd(gnd_id, session, cache)
        if result:
            name, api_type = result
            # Prefer entity-index type for Collection (GND may call it "Work")
            final_type = api_type if etype not in ("Collection",) else etype
            rows.append({"authority_uri": uri, "name": name, "entity_type": final_type, "scheme": "gnd"})
        else:
            not_found.append(uri)

        if (i + 1) % 200 == 0:
            print(f"  GND: {i+1}/{len(gnd_res)} ({len(not_found)} misses so far)")
            save_json(CACHE_PATH, cache)

        if not was_cached:
            time.sleep(0.6)  # ~1.5 req/s; lobid handles this fine

    save_json(CACHE_PATH, cache)
    print(f"GND done. {sum(1 for r in rows if r['scheme']=='gnd')} names, {len(not_found)} misses.")

    # --- VIAF (via lobid sameAs cross-reference) ---
    print(f"Fetching VIAF names via lobid sameAs ({len(viaf_res)} entries)...")
    viaf_cached = sum(1 for u, _ in viaf_res if f"viaf_via_lobid:{u}" in cache)
    print(f"  {viaf_cached} already in cache, {len(viaf_res) - viaf_cached} to fetch")

    viaf_direct = 0  # resolved via VIAF→GND→crosswalk chain
    viaf_named = 0   # name found, needs OpenRefine
    viaf_missed = 0  # no lobid match

    for i, (uri, etype) in enumerate(viaf_res):
        cache_key = f"viaf_via_lobid:{uri}"
        was_cached = cache_key in cache
        name, api_type, gnd_uri = fetch_viaf_via_lobid(uri, session, cache, crosswalk)

        if name:
            # Check if this GND URI is already in crosswalk → direct resolution
            if gnd_uri and gnd_uri in crosswalk:
                qid = crosswalk[gnd_uri]
                via_gnd[uri] = qid
                viaf_direct += 1
                # Don't add to OpenRefine CSV — already resolved
            else:
                # Name found, no existing QID → add to OpenRefine CSV
                final_type = api_type if api_type else etype
                rows.append({"authority_uri": uri, "name": name, "entity_type": final_type, "scheme": "viaf"})
                viaf_named += 1
        else:
            not_found.append(uri)
            viaf_missed += 1

        if (i + 1) % 200 == 0:
            print(f"  VIAF: {i+1}/{len(viaf_res)} (direct={viaf_direct}, named={viaf_named}, miss={viaf_missed})")
            save_json(CACHE_PATH, cache)
            save_json(VIA_GND_PATH, via_gnd)

        if not was_cached:
            time.sleep(0.5)  # polite rate for lobid

    save_json(CACHE_PATH, cache)
    save_json(VIA_GND_PATH, via_gnd)
    print(f"VIAF done. Direct resolved: {viaf_direct}, named for OpenRefine: {viaf_named}, missed: {viaf_missed}")

    # --- Write CSV ---
    with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["authority_uri", "name", "entity_type", "scheme"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nWrote {len(rows)} rows to {CSV_PATH}")

    # --- Write 404/miss log ---
    with NOT_FOUND_PATH.open("w") as f:
        for uri in not_found:
            f.write(uri + "\n")

    print(f"Logged {len(not_found)} misses to {NOT_FOUND_PATH}")
    if via_gnd:
        print(f"Wrote {len(via_gnd)} VIAF→GND→QID direct resolutions to {VIA_GND_PATH}")
        print("  → These can be merged directly into crosswalk.json (run merge_openrefine.py with --viaf-gnd flag)")

    print()
    print("=== Summary ===")
    print(f"GND residue:             {len(gnd_res)}")
    print(f"VIAF residue:            {len(viaf_res)}")
    print(f"  Direct resolved:       {viaf_direct}")
    print(f"  Named for OpenRefine:  {viaf_named}")
    print(f"  No match found:        {viaf_missed}")
    print(f"GeoNames (hard-coded):   {len(geo_res)}")
    print(f"Total OpenRefine rows:   {len(rows)}")
    print(f"Total misses/404s:       {len(not_found)}")


if __name__ == "__main__":
    main()
