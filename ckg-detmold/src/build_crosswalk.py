#!/usr/bin/env python3
"""
build_crosswalk.py - Stage C of the CKG -> LinkedMusic ingestion (doc/INGESTION-PLAN.md).

Resolve a feed's deduped authority IDs to Wikidata QIDs so the converter can
emit the ``wdt:P2888`` pivot. For musiconn/Detmold this is a fully deterministic
two-map crosswalk (GND ``P227`` + VIAF ``P214``); no OpenRefine is needed.

Method: batch the IDs into SPARQL ``VALUES`` queries against the Wikidata Query
Service via ``shared/wikidata_utils`` (rate-limited 20 req/s)::

    SELECT ?id ?qid WHERE { VALUES ?id { "118508288" ... } ?qid wdt:P227 ?id . }   # GND
    SELECT ?id ?qid WHERE { VALUES ?id { "10033017"  ... } ?qid wdt:P214 ?id . }   # VIAF

It also resolves the feed's record-type classifiers (AAT codes -> QID via
``P1014``) into ``record_types.json``.

Inputs : ../data/extracted/<feed>.authorities.json   (Stage B)
         ../data/extracted/<feed>.entities.json       (for the classifier set)
Outputs: ../data/mappings/crosswalk.json     {authority_URI -> QID}  (merged, shared)
         ../data/mappings/record_types.json  {classifier_URI -> QID} (merged, shared)

The coverage % is the real reconciliation rate - it is printed, not hidden.

Run from ``src/``::

    python build_crosswalk.py musiconn
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from collections import Counter
from pathlib import Path

import aiohttp

# shared/ is not an installed package (see CLAUDE.md); add it to the path.
_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "shared"))
from wikidata_utils import WikidataAPIClient  # noqa: E402

# authority scheme -> Wikidata property holding that external id
# (GeoNames P1566 added for Detmold, whose places are all sws.geonames.org.)
SCHEME_PROP = {"gnd": "P227", "viaf": "P214", "geonames": "P1566"}
AAT_PROP = "P1014"
AAT_HOST = "vocab.getty.edu/aat/"

BATCH = 150  # ids per SPARQL VALUES query (kept small: the client GETs the
# query in the URL, and larger VALUES lists overflow WDQS's header limit -> 431)
CONCURRENCY = 3  # in-flight queries (the client also rate-limits to 20/s)
RETRIES = 4  # an empty batch is treated as a transient error (429/timeout) and retried
QID_RE = re.compile(r"(Q\d+)$")


def _quote(value: str) -> str:
    """SPARQL-quote a literal id."""
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _qid(uri: str) -> str | None:
    m = QID_RE.search(uri)
    return m.group(1) if m else None


async def _resolve_ids(
    client: WikidataAPIClient,
    prop: str,
    ids: list[str],
    sem: asyncio.Semaphore,
    desc: str,
) -> tuple[dict[str, str], int]:
    """Resolve {bare_id -> QID} for one property; return (map, conflict_count)."""
    batches = [ids[i : i + BATCH] for i in range(0, len(ids), BATCH)]

    async def run_batch(batch: list[str]) -> list[dict]:
        values = " ".join(_quote(x) for x in batch)
        query = f"SELECT ?id ?qid WHERE {{ VALUES ?id {{ {values} }} ?qid wdt:{prop} ?id . }}"
        # The client returns [] on HTTP error (e.g. 429/431/timeout) as well as on
        # a genuinely empty result. With 150 ids at a ~60% hit rate an all-empty
        # batch is statistically an error, so retry empties with linear backoff.
        for attempt in range(RETRIES):
            async with sem:
                rows = await client.sparql(query, timeout=90)
            if rows:
                return rows
            await asyncio.sleep(2 * (attempt + 1))
        return []

    print(f"  {desc}: {len(ids):,} ids in {len(batches)} batches...", flush=True)
    results = await asyncio.gather(*(run_batch(b) for b in batches))

    mapping: dict[str, str] = {}
    conflicts = 0
    for rows in results:
        for row in rows:
            id_ = row.get("id")
            qid = _qid(row.get("qid", ""))
            if not id_ or not qid:
                continue
            if id_ in mapping and mapping[id_] != qid:
                conflicts += 1  # >1 Wikidata item shares this id; keep first
                continue
            mapping.setdefault(id_, qid)
    return mapping, conflicts


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


async def build(feed: str, extracted: Path, mappings: Path) -> None:
    authorities = _load_json(extracted / f"{feed}.authorities.json")
    index = _load_json(extracted / f"{feed}.entities.json")

    mappings.mkdir(parents=True, exist_ok=True)
    crosswalk_path = mappings / "crosswalk.json"
    record_types_path = mappings / "record_types.json"
    crosswalk = _load_json(crosswalk_path)  # merge: re-runnable, shared across feeds
    record_types = _load_json(record_types_path)

    async with aiohttp.ClientSession() as session:
        client = WikidataAPIClient(session)
        sem = asyncio.Semaphore(CONCURRENCY)

        coverage: dict[str, tuple[int, int]] = {}
        for scheme, prop in SCHEME_PROP.items():
            id_to_uri: dict[str, str] = authorities.get(scheme, {})
            if not id_to_uri:
                continue
            resolved, conflicts = await _resolve_ids(
                client, prop, list(id_to_uri), sem, f"{scheme.upper()} (wdt:{prop})"
            )
            for bare_id, qid in resolved.items():
                crosswalk[id_to_uri[bare_id]] = qid
            coverage[scheme] = (len(resolved), len(id_to_uri))
            if conflicts:
                print(f"      {scheme}: {conflicts} ids matched >1 QID (kept first)")

        # Record-type classifiers: resolve the AAT codes present in this feed.
        classifiers = sorted(set(index.get("record_classifier", {}).values()))
        aat_codes = {
            uri.rsplit("/", 1)[-1]: uri for uri in classifiers if AAT_HOST in uri
        }
        non_aat = [uri for uri in classifiers if AAT_HOST not in uri]
        if aat_codes:
            resolved, _ = await _resolve_ids(
                client, AAT_PROP, list(aat_codes), sem, f"AAT (wdt:{AAT_PROP})"
            )
            for code, qid in resolved.items():
                record_types[aat_codes[code]] = qid
        if non_aat:
            print(f"  note: {len(non_aat)} non-AAT classifier(s) need hand-mapping: {non_aat}")

    crosswalk_path.write_text(
        json.dumps(crosswalk, ensure_ascii=False, indent=0), encoding="utf-8"
    )
    record_types_path.write_text(
        json.dumps(record_types, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # --- Coverage report (the real reconciliation rate) ---
    print(f"\n[{feed}] crosswalk coverage")
    tot_res = tot_all = 0
    for scheme, (res, all_) in coverage.items():
        tot_res += res
        tot_all += all_
        pct = 100 * res / all_ if all_ else 0
        print(f"  {scheme.upper():<5}: {res:,} / {all_:,}  ({pct:.1f}%)")
    if tot_all:
        print(f"  TOTAL: {tot_res:,} / {tot_all:,}  ({100 * tot_res / tot_all:.1f}%)")
    print(f"  crosswalk size (all feeds): {len(crosswalk):,}  -> {crosswalk_path}")
    print(f"  record types:")
    for uri, qid in record_types.items():
        print(f"      {uri}  ->  wd:{qid}")


def main() -> None:
    parser = argparse.ArgumentParser(description="CKG Stage C: authority-ID -> QID crosswalk.")
    parser.add_argument("feed", help="feed name (e.g. musiconn)")
    parser.add_argument("--extracted", default="../data/extracted", help="Stage B output dir")
    parser.add_argument("--mappings", default="../data/mappings", help="crosswalk cache dir")
    args = parser.parse_args()
    asyncio.run(build(args.feed, Path(args.extracted), Path(args.mappings)))


if __name__ == "__main__":
    main()
