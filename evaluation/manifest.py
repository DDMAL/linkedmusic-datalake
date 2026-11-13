"""Validate, normalize and select explicitly identified population artifacts."""

import argparse
from copy import deepcopy
from datetime import date, datetime
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import sys
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator, FormatChecker

SCHEMA_PATH = Path(__file__).with_name("manifest_schema.json")
ROOT = Path(__file__).resolve().parents[1]
FORMATS = FormatChecker()


class ManifestError(ValueError):
    """Invalid inventory, ambiguous selection or unavailable selected bytes."""


@FORMATS.checks("repository-path")
def repository_path(value):
    if not isinstance(value, str):
        return True  # JSON Schema's type rule owns non-string rejection.
    return bool(value) and not (
        value.startswith(("/", "~"))
        or "\\" in value
        or ":" in value
        or any(ord(c) < 32 for c in value)
        or any(part in ("", ".", "..") for part in value.split("/"))
    )


@FORMATS.checks("absolute-iri")
def absolute_iri(value):
    if not isinstance(value, str):
        return True
    if not re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", value):
        return False
    if re.search(r"[\s<>\"{}|\\^`\x00-\x20\x7f]", value) or re.search(
        r"%(?![0-9a-fA-F]{2})", value
    ):
        return False
    try:
        parts = urlsplit(value)
        if parts.scheme.lower() in ("http", "https"):
            return bool(parts.hostname) and parts.username is None and parts.port != 0
        return bool(value.split(":", 1)[1])
    except ValueError:
        return False


@FORMATS.checks("evidence-location")
def evidence_location(value):
    if not isinstance(value, str):
        return True
    return repository_path(value) or (
        value.startswith(("https://", "http://")) and absolute_iri(value)
    )


@FORMATS.checks("archive-iri")
def archive_iri(value):
    if not isinstance(value, str):
        return True
    return absolute_iri(value) and urlsplit(value).scheme.lower() != "file"


@FORMATS.checks("utc-timestamp")
def utc_timestamp(value):
    if not isinstance(value, str):
        return True
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z", value):
        return False
    try:
        datetime.fromisoformat(value)
        return True
    except ValueError:
        return False


@FORMATS.checks("calendar-date")
def calendar_date(value):
    if not isinstance(value, str):
        return True
    try:
        return date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def validator(definition=None):
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    if definition is not None:
        schema = {"$ref": f"#/$defs/{definition}", "$defs": schema["$defs"]}
    return Draft202012Validator(schema, format_checker=FORMATS)


def _version(document):
    if not isinstance(document, dict):
        raise ManifestError("Manifest must be an object")
    version = document.get("schema_version", "1.0")
    if version not in ("1.0", "2.0"):
        raise ManifestError(f"Unsupported schema_version: {version!r}")
    return version


def _unique(records, field, label):
    values = [record[field] for record in records]
    if len(set(values)) != len(values):
        raise ManifestError(f"Duplicate {label}")


def validate(document):
    """Validate without reading artifact bytes or using the network."""
    version = _version(document)
    try:
        # API callers must obey the same finite JSON number contract as files.
        json.dumps(document, allow_nan=False)
    except (TypeError, ValueError) as error:
        raise ManifestError(f"Manifest must contain JSON values: {error}") from error
    errors = sorted(
        validator("v1" if version == "1.0" else "v2").iter_errors(document),
        key=lambda error: str(list(error.absolute_path)),
    )
    if errors:
        error = errors[0]
        where = "/".join(str(part) for part in error.absolute_path) or "/"
        raise ManifestError(f"{where}: {error.message}")
    _unique(document["datasets"], "key", "dataset key")
    if version == "1.0":
        return document
    for dataset in document["datasets"]:
        _unique(dataset["source_snapshots"], "id", "source snapshot ID")
        _unique(dataset["artifacts"], "id", "artifact ID")
        sources = {source["id"] for source in dataset["source_snapshots"]}
        artifacts = {artifact["id"]: artifact for artifact in dataset["artifacts"]}
        for artifact in artifacts.values():
            _unique(artifact["measurements"], "id", "measurement ID")
            if not set(artifact["source_snapshot_ids"]) <= sources:
                raise ManifestError("Artifact refers to an unknown source snapshot")
            if artifact["converter"]["dirty"] is True:
                files = artifact["converter"]["files"]
                if not files or any(f["sha256"]["status"] != "known" for f in files):
                    raise ManifestError("Dirty converter requires exact file hashes")
            for relation in artifact["relations"]:
                if relation["kind"] == "loaded_from":
                    target = artifacts.get(relation["artifact_id"])
                    if (
                        artifact["population"] != "deployed"
                        or target is None
                        or target["population"] != "stored"
                        or relation["source_snapshot_ids"]
                        or relation["converter_run_id"]["status"] != "not_applicable"
                    ):
                        raise ManifestError("loaded_from must link deployed to stored")
                elif (
                    artifact["population"] != "candidate"
                    or relation["artifact_id"] is not None
                    or not relation["source_snapshot_ids"]
                    or not set(relation["source_snapshot_ids"]) <= sources
                    or not set(relation["source_snapshot_ids"])
                    <= set(artifact["source_snapshot_ids"])
                    or relation["converter_run_id"]["status"] != "known"
                ):
                    raise ManifestError("generated_from requires sources and a run ID")
            for measurement in artifact["measurements"]:
                kind = measurement["method"]["kind"]
                if kind == "remote_query" and artifact["population"] != "deployed":
                    raise ManifestError("Remote graph counts belong to deployed RDF")
                if kind == "file_parse" and artifact["population"] == "deployed":
                    raise ManifestError("File counts belong to stored/candidate RDF")
    return document


def known(value):
    return {"status": "known", "value": value, "reason": None}


def unknown(reason, status="unknown"):
    return {"status": status, "value": None, "reason": reason}


def _legacy_value(value, reason):
    return unknown(reason) if value is None else known(value)


def normalize(document):
    """Return v2 without changing input or assigning legacy counts to populations."""
    validate(document)
    if _version(document) == "2.0":
        return deepcopy(document)
    result = {
        "schema_version": "2.0",
        "protocol_version": "1.0",
        "scope": document["scope"],
        "datasets": [],
        "legacy": {
            key: deepcopy(value) for key, value in document.items() if key != "datasets"
        },
    }
    reason = "Legacy inventory does not establish artifact or deployment provenance."
    for item in document["datasets"]:
        source = item["source"]
        result["datasets"].append(
            {
                "key": item["key"],
                "name": item["name"],
                "expected_graph": {
                    "iri": known(item["graph_iri"]),
                    "evidence": known(item["graph_iri_evidence"]),
                },
                "artifact_inventory": {"status": "unknown", "reason": reason},
                "source_snapshots": [
                    {
                        "id": "legacy-source",
                        "description": source["description"],
                        "snapshot_id": _legacy_value(
                            source["snapshot_id"], "Snapshot ID was not recorded."
                        ),
                        "snapshot_date": _legacy_value(
                            source["snapshot_date"], "Snapshot date was not recorded."
                        ),
                        "retrieved_at": _legacy_value(
                            source["retrieved_at_utc"],
                            "Retrieval time was not recorded.",
                        ),
                        "source_record_ids": [],
                        "file": {
                            "path": unknown("No source file path was recorded."),
                            "sha256": _legacy_value(
                                source["sha256"], "No source checksum was recorded."
                            ),
                        },
                        "storage": {
                            "location": unknown("No durable storage URI was recorded."),
                            "availability": {"status": "unknown", "reason": reason},
                        },
                        "availability": {"status": "unknown", "reason": reason},
                        "reconciliation_intermediates": [],
                        "licence": {
                            field: deepcopy(item["licence"][field])
                            for field in (
                                "references",
                                "verified_for_snapshot",
                                "notes",
                            )
                        },
                    }
                ],
                "code_references": [
                    {
                        "path": path,
                        "kind": "code_or_configuration",
                        "availability": {
                            "status": "unknown",
                            "reason": "Legacy reference; existence is not a required runtime input or proof of conversion.",
                        },
                        "sha256": unknown("No exact legacy file hash was recorded."),
                    }
                    for path in item["conversion"]["files"]
                ],
                "artifacts": [],
                "legacy": deepcopy(item),
            }
        )
    validate(result)
    return result


def _read_json(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ManifestError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result

    def invalid_constant(value):
        raise ManifestError(f"Non-JSON numeric constant: {value}")

    def finite_float(value):
        number = float(value)
        if not math.isfinite(number):
            raise ManifestError("JSON number exceeds the finite numeric range")
        return number

    return json.loads(
        Path(path).read_text(encoding="utf-8"),
        object_pairs_hook=pairs,
        parse_constant=invalid_constant,
        parse_float=finite_float,
    )


def load(path):
    """Read v1/v2 and return a validated v2 model, without writing migration."""
    return normalize(_read_json(path))


def select_artifact(document, dataset_key, population, artifact_id=None):
    """Never guess a population or choose arbitrarily between snapshots."""
    document = normalize(document)
    if population not in ("stored", "deployed", "candidate"):
        raise ManifestError("Select stored, deployed or candidate explicitly")
    dataset = next((d for d in document["datasets"] if d["key"] == dataset_key), None)
    if dataset is None:
        raise ManifestError(f"Unknown dataset: {dataset_key}")
    matches = [
        a
        for a in dataset["artifacts"]
        if a["population"] == population
        and (artifact_id is None or a["id"] == artifact_id)
    ]
    if len(matches) != 1:
        raise ManifestError("Selection must identify exactly one artifact")
    artifact = matches[0]
    if artifact["availability"]["status"] != "available":
        raise ManifestError("Selected artifact is not recorded as available")
    return artifact


def verify_file(artifact, repository_root=ROOT):
    """Verify selected local RDF bytes; never fetch or probe a deployed graph."""
    if artifact["population"] == "deployed":
        raise ManifestError("Deployed graphs require separate observation evidence")
    file = artifact["file"]
    if file["path"]["status"] != "known" or file["sha256"]["status"] != "known":
        raise ManifestError("Selected local artifact requires a path and SHA-256")
    name = file["path"]["value"]
    if not repository_path(name):
        raise ManifestError("Artifact path must be repository-relative")
    root = Path(repository_root).resolve()
    path = (root / PurePosixPath(name)).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ManifestError("Selected artifact is missing or outside the repository")
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    if digest != file["sha256"]["value"]:
        raise ManifestError("Selected artifact SHA-256 does not match")
    return digest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("validate", "migrate", "select"):
        child = sub.add_parser(command)
        child.add_argument("manifest", type=Path)
        if command == "migrate":
            child.add_argument("--output", type=Path, required=True)
        elif command == "select":
            child.add_argument("--dataset", required=True)
            child.add_argument(
                "--population",
                required=True,
                choices=("stored", "deployed", "candidate"),
            )
            child.add_argument("--artifact")
            child.add_argument("--verify-file", action="store_true")
            child.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    try:
        document = load(args.manifest)
        if args.command == "validate":
            print(
                f"Valid manifest: {len(document['datasets'])} datasets; normalized schema 2.0"
            )
        elif args.command == "migrate":
            # Exclusive creation preserves both input and any existing output.
            with args.output.open("x", encoding="utf-8") as stream:
                stream.write(
                    json.dumps(document, indent=2, ensure_ascii=False, allow_nan=False)
                    + "\n"
                )
            print(f"Wrote {args.output}")
        else:
            artifact = select_artifact(
                document, args.dataset, args.population, args.artifact
            )
            if args.verify_file:
                verify_file(artifact, args.root)
            print(json.dumps(artifact, indent=2, ensure_ascii=False, allow_nan=False))
    except (OSError, ValueError) as error:
        print(f"Manifest check failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
