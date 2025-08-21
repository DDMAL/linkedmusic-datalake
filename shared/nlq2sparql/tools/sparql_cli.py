"""
Simple CLI to run read-only SPARQL over HTTP against Virtuoso and save results.

Usage examples:
  poetry run python -m code.nlq2sparql.tools.sparql_cli \
    --endpoint https://virtuoso.staging.simssa.ca/sparql \
    --query "SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 1" \
    --format json

  poetry run python -m code.nlq2sparql.tools.sparql_cli \
    --file path/to/query.sparql \
    --format csv
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

from .sparql_http import run_http_sparql


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run read-only SPARQL over HTTP and save results")
    parser.add_argument(
        "--endpoint",
        default="https://virtuoso.staging.simssa.ca/sparql",
        help="SPARQL endpoint URL (default: staging Virtuoso)",
    )
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--query", help="Inline SPARQL query string")
    src.add_argument("--file", type=Path, help="Path to SPARQL query file")
    parser.add_argument(
        "--format",
        choices=["json", "xml", "csv", "tsv"],
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "results",
        help="Directory to save results (default: shared/nlq2sparql/results)",
    )
    parser.add_argument("--timeout", type=int, default=15, help="HTTP timeout in seconds (default: 15)")
    parser.add_argument("--limit", type=int, default=1000, help="Max LIMIT enforced for SELECT (default: 1000)")
    parser.add_argument(
        "--allow-construct",
        action="store_true",
        help="Allow CONSTRUCT/DESCRIBE (still read-only). Disabled by default.",
    )

    args = parser.parse_args(argv)

    if args.file:
        query_text = args.file.read_text(encoding="utf-8")
    else:
        query_text = args.query

    res = run_http_sparql(
        endpoint_url=args.endpoint,
        raw_query=query_text,
        out_dir=args.out_dir,
        fmt=args.format,
        timeout_sec=args.timeout,
        max_limit=args.limit,
        allow_construct=args.allow_construct,
    )

    print(f"Saved {res.content_type} to {res.output_path} in {res.duration_ms} ms (HTTP {res.status_code})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
