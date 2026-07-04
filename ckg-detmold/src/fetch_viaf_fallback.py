"""
Fetch names for VIAF residue that lobid couldn't resolve, using MusicBrainz URL lookup.

MusicBrainz maintains a database of VIAF→artist/label/place links and has a clean API.
Hit rate on our residue: ~13% (the well-known musicians and ensembles).

Note: VIAF's own backend (cluster-record API) is currently returning 502 origin_bad_gateway
(confirmed 2026-06-17). Playwright scraping was attempted but cannot work when the backend
is down. Re-run this script later if VIAF's backend is restored.

Outputs: appends to names_for_reconciliation.csv, updates authority_name_cache.json
         and fetch_404s.txt (removes recovered entries).

CWD must be src/
"""

import csv
import json
import time
from pathlib import Path

import requests

DATA = Path("../data")
CSV_PATH = DATA / "openrefine/names_for_reconciliation.csv"
CACHE_PATH = DATA / "openrefine/authority_name_cache.json"
NOT_FOUND_PATH = DATA / "openrefine/fetch_404s.txt"

UA = "LinkedMusic-datalake/1.0 (liam.pond@mail.mcgill.ca)"
MB_DELAY = 1.1  # MusicBrainz rate limit: 1 req/s

MB_INC = "artist-rels+label-rels+place-rels+work-rels"


def load_json(path: Path) -> dict:
    if path.exists():
        with path.open() as f:
            return json.load(f)
    return {}


def save_json(path: Path, obj: dict) -> None:
    with path.open("w") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def load_entity_types() -> dict[str, str]:
    uri_to_type: dict[str, str] = {}
    for feed in ("musiconn", "detmold"):
        path = DATA / f"extracted/{feed}.entities.json"
        if not path.exists():
            continue
        with path.open() as f:
            data = json.load(f)
        for info in data.get("entities", {}).values():
            uri = info.get("a")
            t = info.get("t")
            if uri and t and uri not in uri_to_type:
                uri_to_type[uri] = t
    return uri_to_type


def mb_lookup(viaf_uri: str, session: requests.Session) -> tuple[str, str] | None:
    """Returns (name, mb_entity_type) or None."""
    r = session.get(
        "https://musicbrainz.org/ws/2/url",
        params={"resource": viaf_uri, "inc": MB_INC, "fmt": "json"},
        headers={"User-Agent": UA},
        timeout=20,
    )
    if r.status_code == 404:
        return None
    if r.status_code != 200:
        print(f"  MB HTTP {r.status_code} for {viaf_uri}")
        return None
    rels = r.json().get("relations", [])
    if not rels:
        return None
    rel = rels[0]
    tt = rel.get("target-type", "")
    entity = rel.get(tt, {})
    name = entity.get("name") or entity.get("title") or ""
    return (name, tt) if name else None


def main() -> None:
    cache = load_json(CACHE_PATH)
    uri_to_type = load_entity_types()

    with NOT_FOUND_PATH.open() as f:
        all_misses = [l.strip() for l in f if l.strip()]
    viaf_nulls = [u for u in all_misses if "viaf" in u]
    non_viaf_misses = [u for u in all_misses if "viaf" not in u]

    print(f"VIAF nulls to try: {len(viaf_nulls)}")

    session = requests.Session()
    recovered_rows: list[dict] = []
    still_missing: list[str] = []

    for i, uri in enumerate(viaf_nulls):
        cache_key = f"mb_lookup:{uri}"
        if cache_key in cache:
            entry = cache[cache_key]
            if entry:
                etype = uri_to_type.get(uri, entry.get("type", "Person"))
                recovered_rows.append({
                    "authority_uri": uri,
                    "name": entry["name"],
                    "entity_type": etype,
                    "scheme": "viaf",
                })
            else:
                still_missing.append(uri)
            continue

        result = mb_lookup(uri, session)
        if result:
            name, mb_type = result
            etype = uri_to_type.get(uri, "Person")
            cache[cache_key] = {"name": name, "type": mb_type}
            recovered_rows.append({
                "authority_uri": uri,
                "name": name,
                "entity_type": etype,
                "scheme": "viaf",
            })
        else:
            cache[cache_key] = None
            still_missing.append(uri)

        if (i + 1) % 50 == 0:
            save_json(CACHE_PATH, cache)
            print(f"  {i+1}/{len(viaf_nulls)}: found={len(recovered_rows)}, miss={len(still_missing)}")

        time.sleep(MB_DELAY)

    save_json(CACHE_PATH, cache)

    # Append newly found rows to CSV
    if recovered_rows:
        with CSV_PATH.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["authority_uri", "name", "entity_type", "scheme"])
            writer.writerows(recovered_rows)

    # Update 404 log: remove recovered, keep everything else
    recovered_uris = {r["authority_uri"] for r in recovered_rows}
    remaining_misses = non_viaf_misses + still_missing
    with NOT_FOUND_PATH.open("w") as f:
        f.write("\n".join(remaining_misses) + "\n")

    # Final CSV count
    with CSV_PATH.open() as f:
        total_rows = sum(1 for _ in csv.DictReader(f))

    print(f"\n=== Summary ===")
    print(f"MB recovered:        {len(recovered_rows)}")
    print(f"Still missing:       {len(still_missing)} (VIAF backend broken 2026-06-17; retry later)")
    print(f"CSV total:           {total_rows} rows")
    print(f"404 log remaining:   {len(remaining_misses)}")


if __name__ == "__main__":
    main()
