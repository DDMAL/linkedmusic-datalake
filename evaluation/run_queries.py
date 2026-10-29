"""Run the independent LinkedMusic SELECT/ASK pilot, offline or read-only online."""

import argparse
import hashlib
import importlib.metadata
import json
import re
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

import requests
from rdflib import Dataset
from rdflib.plugins.sparql.parser import parseQuery
from rdflib.plugins.sparql.parserutils import CompValue

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
TOKEN = re.compile(r"\{\{([a-z_]+)\}\}")
PREFIXES = """\
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX cto: <https://nfdi4culture.de/ontology/>
PREFIX ckg: <https://linkedmusic.ca/terms/ckg/>
PREFIX mbterm: <https://linkedmusic.ca/terms/musicbrainz/>
PREFIX mbrel: <https://linkedmusic.ca/terms/musicbrainz/relationship/>
"""


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def iri(value):
    if not re.fullmatch(r"(?:https?://|urn:)[^\s<>\"{}|^`\\]+", value):
        raise ValueError(f"Invalid absolute IRI: {value!r}")
    return f"<{value}>"


def walk(value):
    yield value
    if isinstance(value, (dict, CompValue)):
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, (list, tuple)) or hasattr(value, "asList"):
        for child in value:
            yield from walk(child)


def validate_query(query):
    parsed = parseQuery(query)
    if parsed[1].name not in {"SelectQuery", "AskQuery"}:
        raise ValueError("Only SELECT and ASK are supported")
    if any(
        isinstance(node, CompValue) and node.name == "ServiceGraphPattern"
        for node in walk(parsed)
    ):
        raise ValueError("SERVICE is excluded; archive external evidence separately")
    return parsed[1].name


def render(case, graphs):
    template = (HERE / case["query"]).read_text()
    values = {**graphs, **case.get("parameters", {})}

    def substitute(match):
        key = match.group(1)
        if values.get(key) is None:
            raise ValueError(f"Unconfigured query parameter: {key}")
        return iri(values[key])

    query = PREFIXES + TOKEN.sub(substitute, template)
    validate_query(query)
    return query


def parse_result(body, query_kind):
    result = json.loads(body)
    if not isinstance(result, dict):
        raise ValueError("SPARQL result must be an object")
    if query_kind == "AskQuery":
        if type(result.get("boolean")) is not bool:
            raise ValueError("ASK response lacks a boolean")
    else:
        if not isinstance(result.get("head"), dict) or not isinstance(
            result.get("results"), dict
        ):
            raise ValueError("SELECT response lacks head/results objects")
        variables = result["head"].get("vars")
        rows = result["results"].get("bindings")
        if not isinstance(variables, list) or not isinstance(rows, list):
            raise ValueError("SELECT response lacks vars/bindings")
        if any(not isinstance(name, str) for name in variables):
            raise ValueError("Invalid variable names")
        for row in rows:
            if not isinstance(row, dict) or any(key not in variables for key in row):
                raise ValueError("Invalid binding variables")
            for term in row.values():
                if (
                    not isinstance(term, dict)
                    or term.get("type")
                    not in {"uri", "literal", "typed-literal", "bnode"}
                    or not isinstance(term.get("value"), str)
                ):
                    raise ValueError("Invalid RDF term in binding")
    return result


def comparable(result):
    """Compare complete bindings as a multiset; preserve term types and duplicates."""
    if "boolean" in result:
        return result["boolean"]
    return Counter(
        json.dumps(row, sort_keys=True) for row in result["results"]["bindings"]
    )


def execute_remote(query, endpoint, timeout, session=requests):
    query_kind = validate_query(query)
    started = time.monotonic()
    report = {"status": "endpoint_error", "headers": {}, "http_status": None}
    body = b""
    try:
        response = session.get(
            endpoint,
            params={
                "query": query,
                "format": "application/sparql-results+json",
                "timeout": timeout * 1000,
            },
            headers={
                "Accept": "application/sparql-results+json",
                "User-Agent": "LinkedMusic-independent-evaluation/1.0",
            },
            timeout=(5, timeout + 5),
        )
        body = response.content
        # Retain diagnostic headers, without archiving cookies.
        headers = {
            key.lower(): value
            for key, value in response.headers.items()
            if key.lower().startswith(("x-sparql", "x-sql"))
            or key.lower() in {"date", "server", "content-type", "retry-after"}
        }
        report.update(http_status=response.status_code, headers=headers)
        partial = response.status_code == 206 or any(
            key.startswith(("x-sparql-anytime", "x-sql")) for key in headers
        )
        report["partial_signals"] = partial
        if not 200 <= response.status_code < 300:
            report["error"] = f"HTTP {response.status_code}"
        else:
            try:
                report["result"] = parse_result(body, query_kind)
                report["status"] = "partial" if partial else "ok"
            except (ValueError, TypeError, KeyError) as exc:
                report["status"] = "partial" if partial else "invalid_response"
                report["error"] = str(exc)
    except requests.Timeout as exc:
        report.update(status="timeout", error=str(exc))
    except requests.RequestException as exc:
        report["error"] = str(exc)
    report["elapsed_seconds"] = round(time.monotonic() - started, 6)
    return report, body


def provenance(manifests, extra_paths=()):
    paths = {
        HERE / "run_queries.py",
        HERE / "cases.json",
        HERE / "manifests.json",
        ROOT / "pyproject.toml",
        ROOT / "poetry.lock",
        *HERE.glob("queries/*.rq"),
        *extra_paths,
    }
    for manifest in manifests["datasets"]:
        paths.update(ROOT / path for path in manifest["conversion"]["files"])
    hashes = {}
    for path in sorted(paths):
        label = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
        hashes[label] = sha256(path.read_bytes()) if path.is_file() else None
    git = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True
    )
    status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True
    )
    return {
        "git_head": git.stdout.strip() or None,
        "git_status": status.stdout.splitlines(),
        "file_sha256": hashes,
        "python": sys.version,
        "packages": {
            name: importlib.metadata.version(name) for name in ("rdflib", "requests")
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--fixture", action="store_true")
    mode.add_argument("--endpoint")
    parser.add_argument("--case", action="append", help="Repeat to select case IDs")
    parser.add_argument("--graph", action="append", default=[], metavar="KEY=IRI")
    parser.add_argument("--timeout", type=int, default=10, help="Server seconds, 1–60")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if not 1 <= args.timeout <= 60:
        parser.error("--timeout must be 1–60 seconds")
    if args.endpoint and urlsplit(args.endpoint).scheme not in {"http", "https"}:
        parser.error("--endpoint must be HTTP(S)")
    manifests = json.loads((HERE / "manifests.json").read_text())
    cases = json.loads((HERE / "cases.json").read_text())["cases"]
    ids = {case["id"] for case in cases}
    if args.case and set(args.case) - ids:
        parser.error(f"Unknown case IDs: {sorted(set(args.case) - ids)}")
    if args.case:
        cases = [case for case in cases if case["id"] in args.case]
    graphs = {item["key"]: item["graph_iri"] for item in manifests["datasets"]}
    graphs["musicbrainz_schema"] = None
    if args.fixture:
        graphs["musicbrainz_schema"] = "urn:linkedmusic:evaluation:schema"
    for override in args.graph:
        key, sep, value = override.partition("=")
        if not sep or key not in graphs:
            parser.error(f"Unknown/malformed graph override: {override}")
        try:
            iri(value)
        except ValueError as exc:
            parser.error(str(exc))
        graphs[key] = value
    if args.fixture and args.graph:
        parser.error("The fixture uses fixed graphs; overrides are for endpoints")
    # A fresh directory prevents accidentally replacing a previous measurement.
    args.output_dir.mkdir(parents=True, exist_ok=False)
    fixture_path = HERE / "fixtures/pilot.trig"
    expected_path = HERE / "fixtures/expected.json"
    dataset = None
    expected = {}
    if args.fixture:
        dataset = Dataset(default_union=False)
        dataset.parse(fixture_path, format="trig")
        expected = json.loads(expected_path.read_text())
    report = {
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "synthetic_fixture" if args.fixture else "live_graph_probe",
        "endpoint": args.endpoint,
        "graphs": graphs,
        "server_timeout_seconds": args.timeout,
        "scope": "Bounded query checks; no population accuracy or source recall estimate.",
        "provenance": provenance(
            manifests, (fixture_path, expected_path) if args.fixture else ()
        ),
        "cases": [],
    }
    failed = False
    for case in cases:
        row = {
            "id": case["id"],
            "question": case["question"],
            "answer_scope": case["answer_scope"],
            "started_at_utc": datetime.now(timezone.utc).isoformat(),
            "validation": "not_evaluated",
        }
        try:
            query = render(case, graphs)
        except ValueError as exc:
            row.update(status="configuration_error", error=str(exc))
        else:
            query_file = args.output_dir / f"{case['id']}.rq"
            query_file.write_text(query)
            row.update(query_file=query_file.name, query_sha256=sha256(query.encode()))
            if dataset is not None:
                started = time.monotonic()
                try:
                    body = dataset.query(query).serialize(format="json")
                    result = parse_result(body, validate_query(query))
                    row.update(
                        status="ok",
                        elapsed_seconds=round(time.monotonic() - started, 6),
                        result=result,
                    )
                except Exception as exc:
                    body = b""
                    row.update(status="query_error", error=str(exc))
            else:
                execution, body = execute_remote(query, args.endpoint, args.timeout)
                row.update(execution)
            raw_file = args.output_dir / f"{case['id']}.response"
            raw_file.write_bytes(body)
            row.update(response_file=raw_file.name, response_sha256=sha256(body))
            if "result" in row:
                result = row["result"]
                row["row_count"] = (
                    len(result["results"]["bindings"]) if "results" in result else None
                )
                row["at_row_limit"] = row["row_count"] == case.get("row_limit", 25)
                if args.fixture and row["status"] == "ok":
                    row["validation"] = (
                        "fixture_pass"
                        if comparable(result) == comparable(expected[case["id"]])
                        else "fixture_fail"
                    )
                elif row["status"] == "ok":
                    row["validation"] = "requires_independent_source_review"
        failed |= row["status"] != "ok" or row["validation"] == "fixture_fail"
        report["cases"].append(row)
        # Checkpoint after every case, including failures.
        write_json(args.output_dir / "report.json", report)
        print(case["id"], row["status"], row["validation"], flush=True)
    report["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    write_json(args.output_dir / "report.json", report)
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
