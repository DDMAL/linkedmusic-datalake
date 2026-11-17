"""Classify RISM item IRIs from a saved response or an explicit bounded endpoint query."""

import argparse
import hashlib
import importlib.metadata
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import sys
from urllib.parse import urlsplit

from convert_to_rdf import WD, WDT, WIKIDATA_PATTERN

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "evaluation"))
from run_queries import execute_remote, parse_result

GRAPH = "https://linkedmusic.ca/graphs/rism/"


def sample_query(limit, noncanonical=False, predicate="P2888"):
    condition = (
        'FILTER(isIRI(?o) && !REGEX(STR(?o), "^http://www[.]wikidata[.]org/entity/Q[1-9][0-9]*$"))'
        if noncanonical
        else ""
    )
    return f"""SELECT ?s ?p ?o WHERE {{
  GRAPH <{GRAPH}> {{
    VALUES ?p {{ <{WDT[predicate]}> }}
    ?s ?p ?o .
    {condition}
  }}
}} LIMIT {limit}"""


def classify(result):
    if set(result["head"]["vars"]) != {"s", "p", "o"}:
        raise ValueError("Expected s, p and o projection variables")
    variants = Counter()
    changed = other = 0
    rows = result["results"]["bindings"]
    for row in rows:
        if not {"s", "p", "o"} <= row.keys():
            raise ValueError("Every binding must include s, p and o")
        term = row["o"]
        value = term["value"]
        match = WIKIDATA_PATTERN.fullmatch(value)
        if term["type"] != "uri" or not match:
            other += 1
            continue
        parts = urlsplit(value)
        variants[f"{parts.scheme}://{parts.netloc}/{parts.path.split('/')[1]}/"] += 1
        changed += value != str(WD[match.group(1)])
    return {
        "rows": len(rows),
        "would_normalize": changed,
        "other_terms": other,
        "variants": dict(variants),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "--response", type=Path, help="Archived SPARQL JSON response; no network access"
    )
    source.add_argument("--endpoint", help="Explicitly authorized SPARQL endpoint")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--noncanonical", action="store_true")
    parser.add_argument(
        "--predicate", choices=("P2888", "P86", "P136"), default="P2888"
    )
    args = parser.parse_args(argv)
    if not 1 <= args.limit <= 1000:
        parser.error("--limit must be between 1 and 1000")
    try:
        args.output_dir.mkdir(parents=True, exist_ok=False)
    except OSError as error:
        parser.error(str(error))
    report = {
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "saved_response" if args.response else "endpoint",
        "endpoint": args.endpoint,
        "graph": None if args.response else GRAPH,
        "input_path": str(args.response) if args.response else None,
        "status": "configuration_error",
        "request_attempted": False,
        "python": sys.version,
        "packages": {
            name: importlib.metadata.version(name)
            for name in ("requests", "urllib3", "rdflib", "pyparsing", "jsonschema")
        },
        "scope": (
            "Classification of supplied bindings only. A saved response does not "
            "prove its graph, query, deployment or completeness. Endpoint results "
            "are an unordered convenience sample, not a prevalence estimate or "
            "full count. Identifier normalization does not validate identity."
        ),
        "code_sha256": {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (
                Path(__file__).resolve(),
                ROOT / "rism/src/convert_to_rdf.py",
                ROOT / "evaluation/run_queries.py",
                ROOT / "poetry.lock",
            )
        },
    }
    body = b""
    try:
        if args.response:
            body = args.response.read_bytes()
            report["status"] = "invalid_response"
            result = parse_result(body, "SelectQuery")
            report["status"] = "ok"
        else:
            query = sample_query(args.limit, args.noncanonical, args.predicate)
            query_bytes = query.encode("utf-8")
            (args.output_dir / "query.rq").write_bytes(query_bytes)
            report["query_sha256"] = hashlib.sha256(query_bytes).hexdigest()
            execution, body = execute_remote(query, args.endpoint, 15)
            result = execution.pop("result", None)
            report.update(execution)
        if result is not None:
            report.update(classify(result))
            report["row_cap_reached"] = (
                "not_established" if args.response else report["rows"] >= args.limit
            )
    except (OSError, ValueError, TypeError, KeyError) as error:
        report.update(
            status=(
                "configuration_error"
                if isinstance(error, OSError)
                else "invalid_response"
            ),
            error=str(error),
        )
    (args.output_dir / "response.json").write_bytes(body)
    report["response_sha256"] = hashlib.sha256(body).hexdigest()
    (args.output_dir / "report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(report["status"])
    return 0 if report["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
