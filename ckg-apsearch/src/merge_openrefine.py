"""
Merge OpenRefine reconciliation results into crosswalk.json.

Reads ../openrefine/export/names_reconciled.csv (columns: authority_uri, qid)
and adds/updates each entry in ../data/mappings/crosswalk.json.

QIDs must be plain Q-numbers (no wd: prefix).  This script adds the wd: prefix
when storing in the crosswalk, same as build_crosswalk.py.

Usage (from src/):
    poetry run python merge_openrefine.py [--dry-run]

Flags:
    --dry-run   Print what would be added without writing crosswalk.json.
"""

import csv
import json
import sys
from pathlib import Path

CROSSWALK_PATH = Path("../data/mappings/crosswalk.json")
EXPORT_CSV = Path("../openrefine/export/names_reconciled.csv")


def load_json(path: Path) -> dict:
    with path.open() as f:
        return json.load(f)


def main(dry_run: bool = False) -> None:
    if not EXPORT_CSV.exists():
        print(f"ERROR: {EXPORT_CSV} not found. Export from OpenRefine first.")
        sys.exit(1)

    with EXPORT_CSV.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    print(f"Loaded {len(rows)} rows from {EXPORT_CSV}")

    crosswalk = load_json(CROSSWALK_PATH)
    before = len(crosswalk)
    added = 0
    updated = 0
    skipped = 0

    for row in rows:
        uri = row.get("authority_uri", "").strip()
        qid_raw = row.get("qid", "").strip()

        if not uri or not qid_raw:
            skipped += 1
            continue

        # Accept plain Q-numbers or wd:-prefixed; normalise to plain (crosswalk standard)
        qid = qid_raw.removeprefix("wd:")
        if not qid.startswith("Q"):
            print(f"  WARN: unexpected QID format '{qid_raw}' for {uri}, skipping")
            skipped += 1
            continue

        if uri in crosswalk:
            if crosswalk[uri] != qid:
                print(f"  UPDATE: {uri} {crosswalk[uri]} → {qid}")
                if not dry_run:
                    crosswalk[uri] = qid
                updated += 1
        else:
            if dry_run:
                print(f"  ADD: {uri} → {qid}")
            crosswalk[uri] = qid if not dry_run else crosswalk.get(uri)
            added += 1

    print(f"Crosswalk before: {before}")
    print(f"  New entries:     {added}")
    print(f"  Updated entries: {updated}")
    print(f"  Skipped (empty): {skipped}")
    print(f"Crosswalk after:  {before + added if not dry_run else before} (dry-run={dry_run})")

    if not dry_run:
        with CROSSWALK_PATH.open("w") as f:
            json.dump(crosswalk, f, ensure_ascii=False, indent=2)
        print(f"Saved {CROSSWALK_PATH}")
    else:
        print("DRY RUN — crosswalk.json not written.")


if __name__ == "__main__":
    main(dry_run="--dry-run" in sys.argv)
