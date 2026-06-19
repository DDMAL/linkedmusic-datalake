"""
Direct Wikidata SPARQL lookup for authority IDs.

Bypasses OpenRefine for entity types where we have authority IDs.
Queries Wikidata for:
  P227  (GND ID)          → covers GND authority URIs
  P214  (VIAF cluster ID) → covers VIAF authority URIs
  P1566 (GeoNames ID)     → covers GeoNames authority URIs

Output: ckg/openrefine/export/names_reconciled_sparql.csv
  Columns: authority_uri, qid

Optionally merges an OpenRefine person export (persons_openrefine.csv) to fill
gaps where Wikidata has the entity but doesn't have the authority ID recorded.
SPARQL results take priority over OpenRefine results on conflicts.

CWD must be ckg/src/
"""

import csv
import json
import time
from pathlib import Path

import requests

DATA = Path("../data")
CSV_PATH = DATA / "openrefine/names_for_reconciliation.csv"
EXPORT_DIR = Path("../openrefine/export")
SPARQL_OUT = EXPORT_DIR / "names_reconciled_sparql.csv"
OPENREFINE_PERSONS = EXPORT_DIR / "persons_openrefine.csv"
FINAL_OUT = EXPORT_DIR / "names_reconciled.csv"

SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
UA = "LinkedMusic-datalake/1.0 (liam.pond@mail.mcgill.ca)"
BATCH_SIZE = 400  # conservative — large VALUES clauses can timeout
DELAY = 1.5       # Wikidata rate limit: be polite


def load_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def extract_id(uri: str, scheme: str) -> str | None:
    if scheme == "gnd" and "d-nb.info/gnd/" in uri:
        return uri.split("/gnd/")[-1]
    if scheme == "viaf" and "viaf.org/viaf/" in uri:
        return uri.rstrip("/").split("/")[-1]
    if scheme == "geonames" and "geonames.org/" in uri:
        return uri.rstrip("/").split("/")[-1]
    return None


def sparql_query(pid: str, ids: list[str]) -> dict[str, str]:
    """Returns {id_value: QID} for the given property and ID batch."""
    values = " ".join(f'"{v}"' for v in ids)
    query = f"""
SELECT ?item ?id WHERE {{
  VALUES ?id {{ {values} }}
  ?item wdt:{pid} ?id .
}}
"""
    r = requests.get(
        SPARQL_ENDPOINT,
        params={"query": query, "format": "json"},
        headers={"User-Agent": UA, "Accept": "application/sparql-results+json"},
        timeout=60,
    )
    r.raise_for_status()
    results = {}
    for binding in r.json()["results"]["bindings"]:
        item_uri = binding["item"]["value"]
        qid = item_uri.split("/")[-1]
        id_val = binding["id"]["value"]
        # If multiple items share an ID (rare), keep first
        if id_val not in results:
            results[id_val] = qid
    return results


def lookup_all(rows: list[dict]) -> dict[str, str]:
    """Returns {authority_uri: QID} for all rows via SPARQL."""
    # Group by scheme → property
    scheme_to_prop = {"gnd": "P227", "viaf": "P214", "geonames": "P1566"}
    by_scheme: dict[str, list[dict]] = {}
    for row in rows:
        s = row["scheme"]
        by_scheme.setdefault(s, []).append(row)

    uri_to_qid: dict[str, str] = {}

    for scheme, prop in scheme_to_prop.items():
        scheme_rows = by_scheme.get(scheme, [])
        if not scheme_rows:
            continue

        # Build id → uri mapping
        id_to_uri: dict[str, str] = {}
        for row in scheme_rows:
            id_val = extract_id(row["authority_uri"], scheme)
            if id_val and id_val not in id_to_uri:
                id_to_uri[id_val] = row["authority_uri"]

        ids = list(id_to_uri.keys())
        total = len(ids)
        found = 0
        print(f"\n{scheme.upper()} ({prop}): {total} IDs to query")

        for i in range(0, total, BATCH_SIZE):
            batch = ids[i : i + BATCH_SIZE]
            attempt = 0
            while attempt < 3:
                try:
                    results = sparql_query(prop, batch)
                    for id_val, qid in results.items():
                        uri = id_to_uri.get(id_val)
                        if uri:
                            uri_to_qid[uri] = qid
                            found += 1
                    break
                except Exception as e:
                    attempt += 1
                    print(f"  batch {i}–{i+len(batch)}: error ({e}), retry {attempt}/3")
                    time.sleep(5)

            end = min(i + BATCH_SIZE, total)
            print(f"  {end}/{total}: found so far = {found}")
            time.sleep(DELAY)

        print(f"{scheme.upper()} done: {found}/{total} matched")

    return uri_to_qid


def merge_openrefine_persons(
    uri_to_qid: dict[str, str], path: Path
) -> tuple[dict[str, str], int]:
    """Merge OpenRefine person export into uri_to_qid. SPARQL results win."""
    if not path.exists():
        print(f"\nNo OpenRefine person export found at {path} — skipping merge.")
        return uri_to_qid, 0

    rows = load_csv(path)
    added = 0
    for row in rows:
        uri = row.get("authority_uri", "").strip()
        qid_raw = row.get("qid", "").strip()
        if not uri or not qid_raw:
            continue
        qid = qid_raw.removeprefix("wd:")
        if not qid.startswith("Q"):
            continue
        if uri not in uri_to_qid:  # SPARQL already has it → skip
            uri_to_qid[uri] = qid
            added += 1

    print(f"\nOpenRefine persons merged: {added} additional matches added")
    return uri_to_qid, added


def main() -> None:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    rows = load_csv(CSV_PATH)
    print(f"Loaded {len(rows)} rows from {CSV_PATH}")

    uri_to_qid = lookup_all(rows)

    sparql_found = len(uri_to_qid)
    print(f"\n=== SPARQL total: {sparql_found} matched ===")

    # Write intermediate SPARQL-only output
    with SPARQL_OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["authority_uri", "qid"])
        for uri, qid in uri_to_qid.items():
            writer.writerow([uri, qid])
    print(f"Wrote {sparql_found} rows to {SPARQL_OUT}")

    # Merge OpenRefine person results
    uri_to_qid, or_added = merge_openrefine_persons(uri_to_qid, OPENREFINE_PERSONS)

    total = len(uri_to_qid)
    with FINAL_OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["authority_uri", "qid"])
        for uri, qid in sorted(uri_to_qid.items()):
            writer.writerow([uri, qid])

    print(f"\n=== Final summary ===")
    print(f"SPARQL matched:          {sparql_found}")
    print(f"OpenRefine persons added: {or_added}")
    print(f"Total in crosswalk:      {total} / {len(rows)} ({100*total//len(rows)}%)")
    print(f"Unmatched (no QID):      {len(rows) - total}")
    print(f"Output: {FINAL_OUT}")
    print(f"\nNext: poetry run python merge_openrefine.py")
    print(f"      (it reads {FINAL_OUT.name} — rename if needed)")


if __name__ == "__main__":
    main()
