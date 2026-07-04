"""
Exact authority-ID -> QID lookup against Wikidata, unioned with vetted
OpenRefine name matches.

This is a *retry* of build_crosswalk.py's ID->QID step (which already produced
the 14,842-entry crosswalk) run only on the residue it failed to resolve, plus a
fold-in of the OpenRefine name matches. Two complementary sources:

  * ID lookup (here): asks Wikidata "which item carries this exact external-ID
    statement?" via CirrusSearch ``haswbstatement``. No name-based false
    positives. Finds the ~1% of residue with a Wikidata item build_crosswalk
    missed (mostly items created since it ran).
        GND -> P227 | VIAF -> P214 | GeoNames -> P1566
  * OpenRefine fold-in: the vetted name matches in the export. Catches Wikidata
    items that exist but never recorded their authority ID (e.g. Zürich Q72) -
    the one set ID lookup structurally cannot find. ID lookup wins on conflict.

Output : ../openrefine/export/names_reconciled.csv   (authority_uri, qid)
Cache  : ../data/openrefine/id_lookup_cache.json      ("<P>=<id>" -> "Q.." | "")
         (resumable: cached lookups are skipped on re-run)

CWD must be src/.  Usage:
    poetry run python wikidata_id_lookup.py --test   # 5-ID sanity check, no writes
    poetry run python wikidata_id_lookup.py          # full run + OpenRefine fold-in
"""

import csv
import json
import re
import sys
import time
from pathlib import Path

import requests

DATA = Path("../data")
CSV_PATH = DATA / "openrefine/names_for_reconciliation.csv"
CACHE_PATH = DATA / "openrefine/id_lookup_cache.json"
CROSSWALK_PATH = DATA / "mappings/crosswalk.json"
EXPORT_DIR = Path("../openrefine/export")
OUT_PATH = EXPORT_DIR / "names_reconciled.csv"
# The OpenRefine "Matched entity's ID" export. 2nd column holds the QID for
# matched cells and the name text for unmatched cells (we keep only real QIDs).
OPENREFINE_EXPORT = EXPORT_DIR / "names-for-reconciliation-csv.csv"

API = "https://www.wikidata.org/w/api.php"
UA = "LinkedMusic-datalake/1.0 (liam.pond@mail.mcgill.ca)"
SCHEME_PROP = {"gnd": "P227", "viaf": "P214", "geonames": "P1566"}
DELAY = 0.15  # polite gap between successful calls; CirrusSearch is rate-limited
QID_RE = re.compile(r"^Q\d+$")


class TransientError(Exception):
    """A throttle / 5xx / non-JSON response that should be retried, not cached."""


def load_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_cache() -> dict[str, str]:
    if CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    return {}


def save_cache(cache: dict[str, str]) -> None:
    CACHE_PATH.write_text(
        json.dumps(cache, ensure_ascii=False, indent=0), encoding="utf-8"
    )


def extract_id(uri: str, scheme: str) -> str | None:
    if scheme == "gnd" and "d-nb.info/gnd/" in uri:
        return uri.split("/gnd/")[-1]
    if scheme == "viaf" and "viaf.org/viaf/" in uri:
        return uri.rstrip("/").split("/")[-1]
    if scheme == "geonames" and "geonames.org/" in uri:
        return uri.rstrip("/").split("/")[-1]
    return None


def query_statement(session: requests.Session, prop: str, id_val: str) -> str:
    """Return the QID whose `prop` == `id_val`, or "" if Wikidata has none.

    Raises TransientError after exhausting backoffs so the caller can skip and
    retry later instead of caching a throttle as a false "no hit".
    """
    params = {
        "action": "query",
        "list": "search",
        "srsearch": f"haswbstatement:{prop}={id_val}",
        "srlimit": 2,
        "srprop": "",
        "format": "json",
        "formatversion": 2,
        "maxlag": 5,
    }
    backoff = [2, 5, 10, 20, 40]
    for attempt in range(len(backoff) + 1):
        try:
            r = session.get(API, params=params, timeout=30)
            if r.status_code == 429 or r.status_code >= 500:
                raise TransientError(f"HTTP {r.status_code}")
            data = r.json()  # JSONDecodeError (a ValueError) if throttled w/ HTML
            if "error" in data and data["error"].get("code") == "maxlag":
                raise TransientError("maxlag")
            hits = data.get("query", {}).get("search", [])
            return hits[0]["title"] if hits else ""
        except (requests.exceptions.RequestException, ValueError, TransientError) as e:
            if attempt == len(backoff):
                raise TransientError(f"{prop}={id_val}: {e}") from e
            time.sleep(backoff[attempt])
    return ""


def lookup(session, prop, id_val, cache) -> str | None:
    """Return QID/"" (and cache it), or None if it should be retried next run."""
    key = f"{prop}={id_val}"
    if key in cache:
        return cache[key]
    try:
        qid = query_statement(session, prop, id_val)
    except TransientError as e:
        print(f"    SKIP (transient, will retry next run): {e}")
        return None
    cache[key] = qid
    time.sleep(DELAY)
    return qid


def fold_openrefine(uri_to_qid: dict[str, str]) -> int:
    """Union vetted OpenRefine matches in (ID lookup keeps priority). Returns count."""
    if not OPENREFINE_EXPORT.exists():
        print(f"\nNo OpenRefine export at {OPENREFINE_EXPORT} - skipping fold-in.")
        return 0
    added = 0
    with OPENREFINE_EXPORT.open(newline="", encoding="utf-8") as f:
        rdr = csv.reader(f)
        next(rdr, None)  # header
        for row in rdr:
            if len(row) < 2:
                continue
            uri, val = row[0].strip(), row[1].strip()
            if uri and QID_RE.match(val) and uri not in uri_to_qid:
                uri_to_qid[uri] = val
                added += 1
    return added


def run_test(session: requests.Session) -> None:
    """Sanity-check the method before committing to a full run."""
    cases = [
        ("P227", "11850553X", "Q1339"),    # J.S. Bach
        ("P227", "2007744-0", "Q707283"),  # Berliner Philharmoniker
        ("P1566", "2657896", "Q72"),       # Zürich (a GeoNames row from the data)
    ]
    crosswalk = json.loads(CROSSWALK_PATH.read_text(encoding="utf-8"))
    picks = {"gnd": 0, "viaf": 0}
    for uri, qid in crosswalk.items():
        if "d-nb.info/gnd/" in uri and picks["gnd"] < 2:
            cases.append(("P227", extract_id(uri, "gnd"), qid)); picks["gnd"] += 1
        elif "viaf.org/viaf/" in uri and picks["viaf"] < 1:
            cases.append(("P214", extract_id(uri, "viaf"), qid)); picks["viaf"] += 1
        if picks["gnd"] >= 2 and picks["viaf"] >= 1:
            break

    print("=== SANITY TEST (no files written) ===")
    ok = 0
    for prop, id_val, expected in cases:
        got = query_statement(session, prop, id_val)
        verdict = "OK" if got == expected else ("MATCH(diff)" if got else "NO HIT")
        ok += got == expected
        print(f"  {prop}={id_val:<24} expected {expected:<11} got {got or '-':<11} [{verdict}]")
        time.sleep(DELAY)
    print(f"\n{ok}/{len(cases)} exact-as-expected.")


def run_full(session: requests.Session) -> None:
    rows = load_csv(CSV_PATH)
    cache = load_cache()
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    et_by_uri = {r["authority_uri"]: r["entity_type"] for r in rows}
    work: dict[tuple[str, str], list[str]] = {}
    for row in rows:
        prop = SCHEME_PROP.get(row["scheme"])
        id_val = extract_id(row["authority_uri"], row["scheme"])
        if prop and id_val:
            work.setdefault((prop, id_val), []).append(row["authority_uri"])

    total = len(work)
    print(f"Loaded {len(rows)} rows -> {total} unique (property, id) lookups "
          f"({len(cache)} already cached)")

    uri_to_qid: dict[str, str] = {}
    hits = skipped = 0
    for i, ((prop, id_val), uris) in enumerate(work.items(), 1):
        qid = lookup(session, prop, id_val, cache)
        if qid is None:
            skipped += 1
        elif qid:
            hits += 1
            for uri in uris:
                uri_to_qid[uri] = qid
        if i % 200 == 0:
            save_cache(cache)
            print(f"  {i}/{total}  id-hits={hits}  skipped={skipped}")
    save_cache(cache)

    id_hits = len(uri_to_qid)
    or_added = fold_openrefine(uri_to_qid)

    with OUT_PATH.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["authority_uri", "qid"])
        for uri, qid in sorted(uri_to_qid.items()):
            w.writerow([uri, qid])

    by_et = {}
    for uri in uri_to_qid:
        et = et_by_uri.get(uri, "?")
        by_et[et] = by_et.get(et, 0) + 1

    pct = 100 * len(uri_to_qid) // len(rows) if rows else 0
    print("\n=== DONE ===")
    print(f"ID-lookup hits        : {id_hits}")
    print(f"OpenRefine folded in  : {or_added} (ID lookup had priority)")
    print(f"Total resolved        : {len(uri_to_qid)} / {len(rows)} ({pct}%)")
    print(f"  by entity_type      : {by_et}")
    if skipped:
        print(f"Transient skips       : {skipped} (re-run to retry these)")
    print(f"Output                : {OUT_PATH}")
    print("Next: poetry run python merge_openrefine.py --dry-run")


def main() -> None:
    session = requests.Session()
    session.headers.update({"User-Agent": UA})
    if "--test" in sys.argv:
        run_test(session)
    else:
        run_full(session)


if __name__ == "__main__":
    main()
