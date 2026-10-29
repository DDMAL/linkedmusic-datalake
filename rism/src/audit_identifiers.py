"""Read-only, bounded RISM item-IRI audit. Saves query and raw response locally."""

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

import requests

from convert_to_rdf import WD, WDT, WIKIDATA_PATTERN


def sample_query(limit, noncanonical=False, predicate="P2888"):
    # Graph IRI is deliberately fixed: the trailing slash is significant.
    condition = (
        'FILTER(isIRI(?o) && !STRSTARTS(STR(?o), "http://www.wikidata.org/entity/"))'
        if noncanonical
        else ""
    )
    return f"""
SELECT ?s ?p ?o FROM <https://linkedmusic.ca/graphs/rism/> WHERE {{
  VALUES ?p {{ <{WDT[predicate]}> }}
  ?s ?p ?o .
  {condition}
}} LIMIT {limit}
""".strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--noncanonical", action="store_true")
    parser.add_argument(
        "--predicate", choices=("P2888", "P86", "P136"), default="P2888"
    )
    parser.add_argument("--endpoint", default="https://virtuoso.simssa.ca/sparql")
    args = parser.parse_args()
    if not 1 <= args.limit <= 1000:
        parser.error("--limit must be between 1 and 1000")
    query = sample_query(args.limit, args.noncanonical, args.predicate)
    response = requests.get(
        args.endpoint,
        params={
            "query": query,
            "format": "application/sparql-results+json",
            "timeout": 15000,
        },
        headers={"User-Agent": "LinkedMusic-RISM-identifier-audit/1.0"},
        timeout=30,
    )
    response.raise_for_status()
    result = response.json()
    rows = result["results"]["bindings"]
    variants = Counter()
    changed = 0
    other = 0
    for row in rows:
        value = row["o"]["value"]
        match = WIKIDATA_PATTERN.fullmatch(value)
        if row["o"]["type"] != "uri" or not match:
            other += 1
            continue
        parts = urlsplit(value)
        variants[f"{parts.scheme}://{parts.netloc}/{parts.path.split('/')[1]}/"] += 1
        changed += value != str(WD[match.group(1)])
    report = {
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "endpoint": args.endpoint,
        "graph": "https://linkedmusic.ca/graphs/rism/",
        "query": query,
        "response_headers": {
            k: v
            for k, v in response.headers.items()
            if k.lower().startswith("x-sparql") or k.lower() in ("server", "date")
        },
        "response_sha256": hashlib.sha256(response.content).hexdigest(),
        "rows": len(rows),
        "would_normalize": changed,
        "other_terms": other,
        "possibly_partial": any(
            k.lower().startswith(("x-sparql-anytime", "x-sql"))
            for k in response.headers
        ),
        "variants": dict(variants),
        "scope": (
            f"Unordered {args.predicate} convenience sample; not a prevalence "
            "estimate or full count. A timed-out/partial response cannot establish absence."
        ),
        "response": result,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("rows", "would_normalize", "variants")}))


if __name__ == "__main__":
    main()
