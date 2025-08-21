"""
Minimal HTTP SPARQL executor for Virtuoso with basic safety guardrails.

- Allows only read-only queries (SELECT, ASK) by default.
- Adds a DEFINE sql:timeout guard (Virtuoso-specific) and enforces client-side timeout.
- Enforces a max LIMIT; if missing, appends one; if present and higher, caps it.
- Saves responses to a target directory for easy inspection.

Note: This module avoids network calls in tests; use it directly in scripts/CLI.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

import requests


READ_ONLY_KINDS = ("select", "ask")
DISALLOWED_KEYWORDS = (
    # SPARQL Update & dangerous operations
    r"\binsert\b",
    r"\bdelete\b",
    r"\bload\b",
    r"\bclear\b",
    r"\bdrop\b",
    r"\bcreate\b",
    r"\balter\b",
    r"\bcopy\b",
    r"\bmove\b",
    r"\badd\b",
    # Virtuoso-specific loader / procedures
    r"rdf_loader_run",
    r"ld_dir",
)


@dataclass
class ExecutionResult:
    status_code: int
    duration_ms: int
    output_path: Path
    content_type: str


def _strip_sparql_prefix(q: str) -> str:
    # Users sometimes paste queries starting with the keyword SPARQL (for isql). Strip it.
    return re.sub(r"^\s*SPARQL\s+", "", q, flags=re.IGNORECASE)


def _kind_of_query(q: str) -> Optional[str]:
    m = re.match(r"^\s*([a-zA-Z]+)", q)
    return m.group(1).lower() if m else None


def _has_disallowed(q: str) -> Optional[str]:
    for pat in DISALLOWED_KEYWORDS:
        if re.search(pat, q, flags=re.IGNORECASE):
            return pat
    return None


def _enforce_limit(q: str, max_limit: int = 1000) -> str:
    # If ASK, no LIMIT semantics; leave unchanged
    kind = _kind_of_query(q)
    if kind == "ask":
        return q
    # Normalize whitespace for detection; but preserve original case/spacing via substitution
    limit_match = re.search(r"limit\s+(\d+)", q, flags=re.IGNORECASE)
    if limit_match:
        current = int(limit_match.group(1))
        if current > max_limit:
            q = re.sub(r"limit\s+\d+", f"LIMIT {max_limit}", q, flags=re.IGNORECASE)
        return q
    # Append a LIMIT at the end (before trailing semicolon if present)
    if q.strip().endswith(";"):
        q = q.rstrip().rstrip(";")
    return q.rstrip() + f"\nLIMIT {max_limit}"


def _inject_timeout_define(q: str, timeout_ms: int = 10000) -> str:
    # Virtuoso honors DEFINE sql:timeout in milliseconds (may be disabled on public endpoints)
    return f"DEFINE sql:timeout {timeout_ms}\n" + q


def prepare_query(
    raw_query: str,
    max_limit: int = 1000,
    allow_construct: bool = False,
    use_define: bool = False,
) -> str:
    """Prepare a SPARQL query for safe execution.

    - Strip optional 'SPARQL' prefix.
    - Require kind in READ_ONLY_KINDS (unless allow_construct=True to extend later).
    - Reject if disallowed keywords present.
    - Enforce LIMIT cap (for SELECT only).
    - Inject DEFINE sql:timeout guard.
    """
    q = _strip_sparql_prefix(raw_query or "")
    kind = _kind_of_query(q or "")
    if not kind:
        raise ValueError("Cannot determine query kind (SELECT/ASK)")

    if kind not in READ_ONLY_KINDS:
        if not (allow_construct and kind in ("construct", "describe")):
            raise ValueError(f"Only read-only queries allowed (got: {kind})")

    bad = _has_disallowed(q)
    if bad:
        raise ValueError(f"Query contains disallowed token: {bad}")

    q = _enforce_limit(q, max_limit=max_limit)
    if use_define:
        q = _inject_timeout_define(q)
    return q


def _resolve_format_and_headers(fmt: str) -> Tuple[str, dict]:
    fmt_l = fmt.lower()
    if fmt_l == "json":
        return "application/sparql-results+json", {"Accept": "application/sparql-results+json"}
    if fmt_l == "xml":
        return "application/sparql-results+xml", {"Accept": "application/sparql-results+xml"}
    if fmt_l == "csv":
        return "text/csv", {"Accept": "text/csv"}
    if fmt_l in ("tsv", "tsv11"):
        return "text/tab-separated-values", {"Accept": "text/tab-separated-values"}
    # Default to JSON
    return "application/sparql-results+json", {"Accept": "application/sparql-results+json"}


def run_http_sparql(
    endpoint_url: str,
    raw_query: str,
    out_dir: Path,
    fmt: str = "json",
    timeout_sec: int = 15,
    max_limit: int = 1000,
    allow_construct: bool = False,
) -> ExecutionResult:
    """Execute SPARQL over HTTP and save output to out_dir.

    Returns execution metadata including output path.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    # First try without DEFINE directive; some public endpoints reject it
    prepped = prepare_query(
        raw_query,
        max_limit=max_limit,
        allow_construct=allow_construct,
        use_define=False,
    )
    mime, headers = _resolve_format_and_headers(fmt)

    data = {"query": prepped}
    start = time.perf_counter()
    resp = requests.post(endpoint_url, data=data, headers=headers, timeout=timeout_sec)
    duration_ms = int((time.perf_counter() - start) * 1000)

    if resp.status_code == 400 and b"DEFINE" in resp.content:
        # Retry without DEFINE already; as a fallback, try GET semantics without DEFINE (rarely needed)
        start = time.perf_counter()
        resp = requests.get(endpoint_url, params={"query": prepped}, headers=headers, timeout=timeout_sec)
        duration_ms = int((time.perf_counter() - start) * 1000)

    resp.raise_for_status()

    # Build filename
    ts = time.strftime("%Y%m%d_%H%M%S")
    content_type_header = resp.headers.get("Content-Type", mime).split(";")[0].strip().lower()
    ext = {
        "application/sparql-results+json": ".json",
        "application/sparql-results+xml": ".xml",
        "text/csv": ".csv",
        "text/tab-separated-values": ".tsv",
    }.get(content_type_header, ".out")

    fname = f"sparql_{ts}{ext}"
    out_path = out_dir / fname
    out_path.write_bytes(resp.content)

    return ExecutionResult(
        status_code=resp.status_code,
        duration_ms=duration_ms,
        output_path=out_path,
        content_type=content_type_header,
    )
