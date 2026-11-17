"""Run the independent LinkedMusic SELECT/ASK pilot, offline or read-only online."""

import argparse
import hashlib
import importlib.metadata
import json
import math
import re
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

import requests
import rdflib
from rdflib import Dataset, URIRef
from rdflib.plugins.sparql.parser import parseQuery
from rdflib.plugins.sparql.parserutils import CompValue
from pyparsing import ParseBaseException
from urllib3.exceptions import HTTPError, ReadTimeoutError

import manifest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
TOKEN = re.compile(r"\{\{([a-z_]+)\}\}")
AUXILIARY_DATASETS = {"musicbrainz_schema": "musicbrainz"}
FIXTURE_GRAPHS = {
    "wjazzd": "https://linkedmusic.ca/graphs/wjazzd/",
    "musicbrainz": "https://linkedmusic.ca/graphs/musicbrainz/",
    "rism": "https://linkedmusic.ca/graphs/rism/",
    "musiconn": "https://linkedmusic.ca/graphs/ckg-musiconn/",
    "detmold": "https://linkedmusic.ca/graphs/ckg-detmold/",
    "apsearch": "https://linkedmusic.ca/graphs/ckg-apsearch/",
    "musicbrainz_schema": "urn:linkedmusic:evaluation:schema",
}
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
    pending = path.with_name(path.name + ".tmp")
    pending.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    pending.replace(path)


def parse_graph(graph, path, format_name):
    """Preserve RDF lexical terms; do not canonicalize source literal spellings."""
    previous = rdflib.NORMALIZE_LITERALS
    try:
        rdflib.NORMALIZE_LITERALS = False
        graph.parse(
            path, format=format_name, publicID="urn:linkedmusic:no-external-base:"
        )
    finally:
        rdflib.NORMALIZE_LITERALS = previous


def iri(value):
    if not isinstance(value, str) or not manifest.absolute_iri(value):
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
    try:
        parsed = parseQuery(query)
    except ParseBaseException as exc:
        raise ValueError(f"Invalid SPARQL: {exc}") from exc
    if parsed[1].name not in {"SelectQuery", "AskQuery"}:
        raise ValueError("Only SELECT and ASK are supported")
    if any(
        isinstance(node, CompValue) and node.name == "ServiceGraphPattern"
        for node in walk(parsed)
    ):
        raise ValueError("SERVICE is excluded; archive external evidence separately")
    if any(
        isinstance(node, CompValue) and node.name == "DatasetClause"
        for node in walk(parsed)
    ):
        raise ValueError("FROM is excluded; select named graphs explicitly")
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
    def unique_keys(pairs):
        value = {}
        for key, entry in pairs:
            if key in value:
                raise ValueError(f"Duplicate result key: {key}")
            value[key] = entry
        return value

    def finite_number(value):
        number = float(value)
        if not math.isfinite(number):
            raise ValueError("Nonfinite JSON number")
        return number

    result = json.loads(
        body,
        object_pairs_hook=unique_keys,
        parse_constant=finite_number,
        parse_float=finite_number,
    )
    if not isinstance(result, dict):
        raise ValueError("SPARQL result must be an object")
    if query_kind == "AskQuery":
        if type(result.get("boolean")) is not bool or "results" in result:
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
        if any(not isinstance(name, str) or not name for name in variables):
            raise ValueError("Invalid variable names")
        if len(set(variables)) != len(variables) or "boolean" in result:
            raise ValueError("Ambiguous SELECT result")
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
                if term["type"] in {"uri", "bnode"}:
                    if set(term) != {"type", "value"}:
                        raise ValueError("Non-literal binding has literal metadata")
                    if term["type"] == "uri":
                        iri(term["value"])
                else:
                    if set(term) - {"type", "value", "datatype", "xml:lang"}:
                        raise ValueError("Unknown literal metadata")
                    if "datatype" in term:
                        iri(term["datatype"])
                    if "xml:lang" in term and (
                        not isinstance(term["xml:lang"], str)
                        or not re.fullmatch(
                            r"[A-Za-z]+(?:-[A-Za-z0-9]+)*", term["xml:lang"]
                        )
                        or "datatype" in term
                    ):
                        raise ValueError("Invalid literal language metadata")
                    if term["type"] == "typed-literal" and "datatype" not in term:
                        raise ValueError("Typed literal lacks datatype")
    return result


def comparable(result):
    """Compare complete bindings as a multiset; preserve term types and duplicates."""
    if "boolean" in result:
        return result["boolean"]

    # RDF 1.1 simple literals have xsd:string type; legacy typed-literal and
    # literal+datatype are equivalent encodings. Do not normalize lexical values.
    def term_key(term):
        kind = term["type"]
        if kind in {"literal", "typed-literal"}:
            language = term.get("xml:lang", "").lower()
            datatype = term.get("datatype", "http://www.w3.org/2001/XMLSchema#string")
            return ("literal", term["value"], language, None if language else datatype)
        return (kind, term["value"])

    rows = Counter(
        tuple(sorted((key, term_key(term)) for key, term in row.items()))
        for row in result["results"]["bindings"]
    )
    return tuple(sorted(result.get("head", {}).get("vars", []))), rows


def execute_remote(query, endpoint, timeout, session=requests):
    query_kind = validate_query(query)
    started = time.monotonic()
    report = {
        "status": "endpoint_error",
        "headers": {},
        "http_status": None,
        "request_attempted": True,
        "partial_signals": False,
    }
    body = bytearray()
    response = None
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
            allow_redirects=False,
            stream=True,
        )
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
        # read1 returns available bytes without filling a fixed-size chunk first.
        # Preserve earlier decoded bytes if a later read times out or disconnects.
        while chunk := response.raw.read1(65536, decode_content=True):
            body.extend(chunk)
        if not 200 <= response.status_code < 300:
            report["error"] = f"HTTP {response.status_code}"
        else:
            try:
                report["result"] = parse_result(body, query_kind)
                report["status"] = "partial" if partial else "ok"
            except (ValueError, TypeError, KeyError) as exc:
                report["status"] = "partial" if partial else "invalid_response"
                report["error"] = str(exc)
    except (requests.RequestException, HTTPError) as exc:
        pending, seen = [exc], set()
        timed_out = False
        while pending:
            error = pending.pop()
            if not isinstance(error, BaseException) or id(error) in seen:
                continue
            seen.add(id(error))
            timed_out |= isinstance(error, (requests.Timeout, ReadTimeoutError))
            pending.extend((error.__cause__, error.__context__, *error.args))
        report.update(
            status="timeout" if timed_out else "endpoint_error", error=str(exc)
        )
    finally:
        if response is not None:
            response.close()
    report["elapsed_seconds"] = round(time.monotonic() - started, 6)
    return report, bytes(body)


def provenance(document, extra_paths=()):
    paths = {
        HERE / name
        for name in (
            "run_queries.py",
            "manifest.py",
            "manifest_schema.json",
            "cases.json",
            "protocol.md",
        )
    } | {
        ROOT / "pyproject.toml",
        ROOT / "poetry.lock",
        *HERE.glob("queries/*.rq"),
        *extra_paths,
    }
    hashes = {}
    for path in sorted(paths):
        label = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
        hashes[label] = sha256(path.read_bytes())
    references = {}
    for entry in document["datasets"]:
        for reference in entry["code_references"]:
            name = reference["path"]
            path = (ROOT / name).resolve()
            available = path.is_relative_to(ROOT) and path.is_file()
            references[name] = {
                "sha256": sha256(path.read_bytes()) if available else None,
                "status": "available" if available else "unavailable",
            }
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
        "current_reference_files": references,
        "reference_scope": "Current reference bytes only; not attributed to artifact conversion.",
        "python": sys.version,
        "packages": {
            name: importlib.metadata.version(name)
            for name in ("rdflib", "requests", "urllib3", "jsonschema", "pyparsing")
        },
        "rdf_store": "rdflib Memory; default_union=False",
    }


def artifact_bindings(values, allowed):
    """Primary KEY=ID never changes dataset; declared auxiliaries use DATASET/ID."""
    bindings = {}
    for value in values:
        key, sep, target = value.partition("=")
        if not sep or key not in allowed or not target or key in bindings:
            raise ValueError(
                f"Unknown, duplicate or malformed artifact binding: {value}"
            )
        if key in AUXILIARY_DATASETS:
            dataset, sep, identifier = target.partition("/")
            if not sep or dataset != AUXILIARY_DATASETS[key]:
                raise ValueError(
                    f"Auxiliary {key} requires {AUXILIARY_DATASETS[key]}/ID"
                )
        else:
            dataset, identifier = key, target
        if not identifier or "/" in identifier:
            raise ValueError(f"Malformed artifact binding: {value}")
        bindings[key] = (dataset, identifier)
    return bindings


def prepare_artifact(document, binding, population, root, dataset):
    dataset_key, identifier = binding
    artifact = manifest.select_artifact(document, dataset_key, population, identifier)
    graph = artifact["graph"]["iri"]
    if graph["status"] != "known":
        raise ValueError("Selected artifact requires a known graph IRI")
    iri(graph["value"])
    selection = {
        "dataset": dataset_key,
        "artifact_id": identifier,
        "population": population,
        "graph_iri": graph["value"],
        "file_sha256": artifact["file"]["sha256"],
        "file_verified": False,
    }
    if dataset is not None:
        manifest.verify_file(artifact, root)
        path = (root / artifact["file"]["path"]["value"]).resolve()
        format_name = {".ttl": "turtle", ".nt": "nt"}.get(path.suffix.lower())
        if format_name is None:
            raise ValueError("Local mode requires a single-graph .ttl or .nt artifact")
        # Never infer a graph from the filename or use the endpoint's default union.
        target = dataset.graph(URIRef(graph["value"]))
        parse_graph(target, path, format_name)
        # Catch edits during loading, before permitting any query over this graph.
        manifest.verify_file(artifact, root)
        selection["file_verified"] = True
    return selection


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--fixture", action="store_true")
    mode.add_argument(
        "--local", action="store_true", help="Load selected Turtle/N-Triples files"
    )
    mode.add_argument("--endpoint")
    parser.add_argument("--manifest", type=Path, default=HERE / "manifests.json")
    parser.add_argument("--population", choices=("stored", "deployed", "candidate"))
    parser.add_argument(
        "--artifact", action="append", default=[], metavar="KEY=[DATASET/]ID"
    )
    parser.add_argument(
        "--root", type=Path, default=ROOT, help="Root for manifest file paths"
    )
    parser.add_argument("--case", action="append", help="Repeat to select case IDs")
    parser.add_argument(
        "--timeout", type=int, default=10, help="Remote server seconds, 1–60"
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    if not 1 <= args.timeout <= 60:
        parser.error("--timeout must be 1–60 seconds")
    if args.fixture and (args.population or args.artifact):
        parser.error("Fixture mode cannot select measured populations/artifacts")
    if args.endpoint:
        if urlsplit(args.endpoint).scheme not in {
            "http",
            "https",
        } or not manifest.absolute_iri(args.endpoint):
            parser.error(
                "--endpoint must be an absolute HTTP(S) IRI without credentials"
            )
        if args.population != "deployed":
            parser.error("Endpoint runs require --population deployed")
    if args.local and args.population not in {"stored", "candidate"}:
        parser.error("Local runs require --population stored or candidate")
    cases = json.loads((HERE / "cases.json").read_text())["cases"]
    ids = {case["id"] for case in cases}
    if args.case and set(args.case) - ids:
        parser.error(f"Unknown case IDs: {sorted(set(args.case) - ids)}")
    if args.case:
        cases = [case for case in cases if case["id"] in args.case]
    required = {key for case in cases for key in case["datasets"]}
    try:
        bindings = artifact_bindings(args.artifact, required)
        args.output_dir.mkdir(parents=True, exist_ok=False)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    fixture_path = HERE / "fixtures/pilot.trig"
    expected_path = HERE / "fixtures/expected.json"
    report = {
        "report_version": "1.0",
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "mode": (
            "synthetic_fixture"
            if args.fixture
            else ("local_artifacts" if args.local else "live_graph_probe")
        ),
        "population": args.population,
        "endpoint": args.endpoint,
        "graphs": {},
        "artifacts": {},
        "artifact_errors": {},
        "server_timeout_seconds": args.timeout if args.endpoint else None,
        "scope": "Bounded query checks; no population accuracy or source recall estimate. Live observations do not verify an earlier deployment snapshot.",
        "cases": [],
    }
    report_path = args.output_dir / "report.json"
    write_json(report_path, report)
    try:
        # Preserve the exact versioned input; every consumer goes through the adapter.
        raw_manifest = args.manifest.read_bytes()
        (args.output_dir / "manifest.input.json").write_bytes(raw_manifest)
        report["manifest_input_sha256"] = sha256(raw_manifest)
        document = manifest.load(args.output_dir / "manifest.input.json")
        original = json.loads(raw_manifest)
        report["manifest_input_schema_version"] = original.get("schema_version", "1.0")
        report["manifest_schema_version"] = document["schema_version"]
        report["protocol_version"] = document["protocol_version"]
        write_json(args.output_dir / "manifest.normalized.json", document)
        report["manifest_normalized_sha256"] = sha256(
            (args.output_dir / "manifest.normalized.json").read_bytes()
        )
        report["provenance"] = provenance(
            document, (fixture_path, expected_path) if args.fixture else ()
        )
        expected = json.loads(expected_path.read_text()) if args.fixture else {}
        dataset = Dataset(default_union=False) if args.fixture or args.local else None
        if args.fixture:
            parse_graph(dataset, fixture_path, "trig")
            report["graphs"] = dict(FIXTURE_GRAPHS)
        else:
            seen_graphs = set()
            for key in sorted(required):
                try:
                    if key not in bindings:
                        raise ValueError(f"No explicit --artifact binding for {key}")
                    # Preflight graph collisions before any load, including failed loads.
                    artifact = manifest.select_artifact(
                        document, bindings[key][0], args.population, bindings[key][1]
                    )
                    graph = artifact["graph"]["iri"]["value"]
                    if graph in seen_graphs:
                        raise ValueError("Each binding must use a distinct named graph")
                    seen_graphs.add(graph)
                    selected = prepare_artifact(
                        document,
                        bindings[key],
                        args.population,
                        args.root.resolve(),
                        dataset,
                    )
                    report["artifacts"][key] = selected
                    report["graphs"][key] = selected["graph_iri"]
                except Exception as exc:
                    report["artifact_errors"][key] = str(exc)
    except Exception as exc:
        report.update(
            status="configuration_error",
            error=str(exc),
            finished_at_utc=datetime.now(timezone.utc).isoformat(),
        )
        write_json(report_path, report)
        print(str(exc), file=sys.stderr)
        return 1
    failed = False
    for case in cases:
        row = {
            "id": case["id"],
            "question": case["question"],
            "answer_scope": case["answer_scope"],
            "question_support": case["question_support"],
            "model_requirement": case.get("model_requirement"),
            "started_at_utc": datetime.now(timezone.utc).isoformat(),
            "validation": "not_evaluated",
            "request_attempted": False,
            "artifacts": {
                key: report["artifacts"][key]
                for key in case["datasets"]
                if key in report["artifacts"]
            },
        }
        try:
            errors = {
                key: report["artifact_errors"][key]
                for key in case["datasets"]
                if key in report["artifact_errors"]
            }
            if errors:
                raise ValueError(json.dumps(errors, sort_keys=True))
            query = render(case, report["graphs"])
        except (OSError, ValueError) as exc:
            row.update(status="configuration_error", error=str(exc))
        else:
            query_file = args.output_dir / f"{case['id']}.rq"
            query_bytes = query.encode("utf-8")
            query_file.write_bytes(query_bytes)
            row.update(query_file=query_file.name, query_sha256=sha256(query_bytes))
            if dataset is not None:
                started = time.monotonic()
                body = b""
                try:
                    body = dataset.query(query).serialize(format="json")
                    result = parse_result(body, validate_query(query))
                    row.update(
                        status="ok",
                        elapsed_seconds=round(time.monotonic() - started, 6),
                        result=result,
                    )
                except Exception as exc:
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
                row["at_row_limit"] = (
                    row["row_count"] is not None
                    and row["row_count"] >= case["row_limit"]
                )
                row["completeness"] = (
                    "partial"
                    if row["status"] == "partial"
                    else (
                        "row_cap_reached" if row["at_row_limit"] else "not_established"
                    )
                )
                if args.fixture and row["status"] == "ok":
                    row["validation"] = (
                        "fixture_pass"
                        if comparable(result) == comparable(expected[case["id"]])
                        else "fixture_fail"
                    )
                elif row["status"] == "ok":
                    row["validation"] = (
                        "unsupported_question"
                        if case["question_support"] == "unsupported"
                        else "requires_independent_source_review"
                    )
        failed |= row["status"] != "ok" or row["validation"] == "fixture_fail"
        report["cases"].append(row)
        write_json(report_path, report)
        print(case["id"], row["status"], row["validation"], flush=True)
    report.update(
        status="failed" if failed else "completed",
        finished_at_utc=datetime.now(timezone.utc).isoformat(),
    )
    write_json(report_path, report)
    if dataset is not None:
        dataset.close()
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
