"""Compare representative converter outputs across two installed environments.

Run from any directory with --old-python, --new-python and a fresh --output-dir.
The workers reuse tracked synthetic fixtures and retain their inputs and outputs.
"""

import importlib
import importlib.metadata
import importlib.util
import hashlib
import json
import sys
import tempfile
from pathlib import Path

from rdflib import Graph

import argparse
import difflib
import os
import subprocess
from collections import Counter
from rdflib.compare import isomorphic

ROOT = Path(__file__).resolve().parents[1]
ROUTES = (
    "rism",
    "musicbrainz-role-schema",
    "musicbrainz-auxiliary",
    "ckg-apsearch",
    "ckg-detmold",
    "ckg-musiconn",
    "shared-dtl",
    "shared-jukebox",
    "shared-simssa",
    "diamm-identifiers",
    "diamm-years",
    "diamm-provenance",
)


def run_fixture(W, OUT, ROUTE):
    OUT.mkdir(parents=True)
    (OUT / "scratch").mkdir()
    original_temporary = tempfile.TemporaryDirectory

    class RetainedTemporary(original_temporary):
        def __init__(self, *args, **kwargs):
            kwargs["dir"] = str(OUT / "scratch")
            super().__init__(*args, **kwargs)
            self._finalizer.detach()

        def cleanup(self):
            pass

    tempfile.TemporaryDirectory = RetainedTemporary
    original_serialize = Graph.serialize
    artifacts = []

    def captured(self, *args, **kwargs):
        result = original_serialize(self, *args, **kwargs)
        destination = kwargs.get("destination", args[0] if args else None)
        fmt = kwargs.get("format", "turtle")
        if destination is None:
            raw = result.encode("utf-8") if isinstance(result, str) else result
        elif isinstance(destination, (str, Path)):
            raw = Path(destination).read_bytes()
        elif hasattr(destination, "name"):
            destination.flush()
            raw = Path(destination.name).read_bytes()
        else:
            raise AssertionError("Unexpected serialization destination")
        name = f"graph-{len(artifacts):02d}.rdf"
        (OUT / name).write_bytes(raw)
        artifacts.append(
            {
                "path": name,
                "format": fmt,
                "triples": len(self),
                "bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
            }
        )
        return result

    Graph.serialize = captured

    def module(folder, name):
        sys.path.insert(0, str(W / folder))
        return importlib.import_module(name)

    def method(mod, cls, method_name):
        case = getattr(mod, cls)()
        case.setUp()
        try:
            getattr(case, method_name)()
        finally:
            case.doCleanups()

    if ROUTE == "rism":
        method(
            module("rism/tests", "test_identifier_normalization"),
            "IdentifierNormalizationTests",
            "test_csv_to_turtle_joins_canonical_identifier",
        )
    elif ROUTE == "musicbrainz-role-schema":
        m = module("musicbrainz/tests", "test_relationship_preservation")
        c = m.RelationshipPreservationTests()
        c.setUp()
        c.test_qualifiers_and_original_payload_survive_turtle()
        c.test_precise_and_broad_queries_have_different_answers()
        c.mapping.schema_graph().serialize(format="turtle")
    elif ROUTE == "musicbrainz-auxiliary":
        m = module("musicbrainz/tests", "test_reconciliation_loading")
        c = m.ReconciliationLoadingTests()
        c.setUp()
        try:
            c.write_fixture()
            g = c.convert_via_main()
            c.assertEqual(set(g), c.expected())
            g.serialize(format="turtle")
        finally:
            c.doCleanups()
    elif ROUTE.startswith("ckg-"):
        feed = ROUTE.removeprefix("ckg-")
        m = module("ckg-apsearch/tests", "test_creation_periods")
        path = W / f"ckg-{feed}/src/convert_to_rdf.py"
        spec = importlib.util.spec_from_file_location("matrix_ckg", path)
        c = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(c)
        m.converter = c
        m.SOURCE = path
        cases = [
            ("range", m.source_literal("1909-01-01T00:00:00/1950-01-01T23:59:59")),
            ("year", m.source_literal("1940")),
            ("unknown", m.source_literal("unknown")),
            ("reversed", m.source_literal("1950/1909")),
            ("anomaly", m.source_literal("9009/9009")),
        ]
        g, output, raw = m.run_conversion(OUT / "scratch", cases, feed=feed)
        # CKG writes Turtle itself. Preserve those bytes as well as RDFLib reserialization.
        name = "converter.ttl"
        (OUT / name).write_text(raw)
        artifacts.append(
            {
                "path": name,
                "format": "turtle",
                "triples": len(g),
                "bytes": len(raw.encode()),
                "sha256": hashlib.sha256(raw.encode()).hexdigest(),
            }
        )
        g.serialize(format="turtle")
    elif ROUTE in ("shared-dtl", "shared-jukebox"):
        m = module("shared/tests", "test_identifier_conversion")
        name = (
            "test_real_dtl_mapping_preserves_local_subjects_and_unmatched_values"
            if ROUTE == "shared-dtl"
            else "test_global_jukebox_social_names_preserve_literals"
        )
        method(m, "IdentifierConversionTests", name)
    elif ROUTE == "shared-simssa":
        method(
            module("shared/tests", "test_simssa_mapping"),
            "SimssaMappingTests",
            "test_id_like_original_names_and_work_links_remain_source_specific",
        )
    elif ROUTE == "diamm-identifiers":
        method(
            module("diamm/tests", "test_external_identifier_selection"),
            "ExternalIdentifierSelectionTests",
            "test_actual_extraction_export_and_rdf_cli_keep_all_identifiers",
        )
    elif ROUTE == "diamm-years":
        method(
            module("diamm/tests", "test_person_years"),
            "PersonYearTests",
            "test_exact_and_approximate_years_have_distinct_assertions",
        )
    elif ROUTE == "diamm-provenance":
        m = module("diamm/tests", "test_source_provenance")
        method(
            m,
            "SourceProvenanceTests",
            "test_csv_preserves_paired_qualifiers_and_has_no_unqualified_location",
        )
        method(
            m,
            "SourceProvenanceTests",
            "test_missing_null_invalid_and_reversed_values_keep_raw_evidence",
        )
    else:
        raise ValueError(ROUTE)
    assert artifacts, ROUTE
    sources = {
        Path(m.__file__).resolve()
        for m in list(sys.modules.values())
        if getattr(m, "__file__", None)
        and str(Path(m.__file__).resolve()).startswith(str(W) + "/")
    }
    versions = {
        name: importlib.metadata.version(name)
        for name in ("rdflib", "oxrdflib", "pyoxigraph", "pandas", "isodate")
    }
    inputs = [
        {
            "path": str(p.relative_to(OUT)),
            "bytes": p.stat().st_size,
            "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
        }
        for p in sorted((OUT / "scratch").rglob("*"))
        if p.is_file() and "__pycache__" not in p.parts
    ]
    receipt = {
        "route": ROUTE,
        "python": sys.version,
        "executable": sys.executable,
        "versions": versions,
        "artifacts": artifacts,
        "retained_temporary_files": inputs,
        "loaded_code": [
            {
                "path": str(p.relative_to(W)),
                "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            }
            for p in sorted(sources)
        ],
    }
    (OUT / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(
        json.dumps({"route": ROUTE, "artifacts": len(artifacts), "versions": versions})
    )


def compare(old_python, new_python, output):
    if output.exists():
        raise ValueError("Output directory must be new: " + str(output))
    output.mkdir(parents=True)
    environment = os.environ.copy()
    environment["PYTHONHASHSEED"] = "0"
    for version, python in (("old", old_python), ("new", new_python)):
        (output / version).mkdir()
        for route in ROUTES:
            with (output / version / (route + ".log")).open("w") as log:
                subprocess.run(
                    [
                        str(python),
                        str(Path(__file__).resolve()),
                        "--worker",
                        route,
                        "--output-dir",
                        str(output / version / route),
                    ],
                    cwd=ROOT,
                    env=environment,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    check=True,
                )
    comparisons = []
    input_checks = []
    runtime = {}
    for route in ROUTES:
        before = json.loads((output / "old" / route / "receipt.json").read_text())
        after = json.loads((output / "new" / route / "receipt.json").read_text())
        if before["loaded_code"] != after["loaded_code"]:
            raise ValueError("Code changed between executions: " + route)
        if len(before["artifacts"]) != len(after["artifacts"]):
            raise ValueError("Output count changed: " + route)

        def inputs(receipt):
            # Include source and intermediate CSV/JSON/NT bytes, independent of
            # temporary folder names. Serialized Turtle is compared separately.
            return Counter(
                (Path(item["path"]).name, item["sha256"])
                for item in receipt["retained_temporary_files"]
                if Path(item["path"]).suffix in {".csv", ".json", ".jsonl", ".nt"}
                and "rdf" not in Path(item["path"]).parts
            )

        if inputs(before) != inputs(after):
            raise ValueError("Fixture input/intermediate bytes changed: " + route)
        input_checks.append(
            {
                "route": route,
                "input_and_intermediate_bytes_equal": True,
                "files": sum(inputs(before).values()),
            }
        )
        runtime[route] = {
            "old": {key: before[key] for key in ("python", "executable", "versions")},
            "new": {key: after[key] for key in ("python", "executable", "versions")},
        }
        for a, b in zip(before["artifacts"], after["artifacts"]):
            if a["path"] != b["path"] or a["format"] != b["format"]:
                raise ValueError("Output identity changed: " + route)
            old = (output / "old" / route / a["path"]).read_bytes()
            new = (output / "new" / route / b["path"]).read_bytes()
            left = Graph().parse(data=old, format=a["format"])
            right = Graph().parse(data=new, format=b["format"])
            equal = isomorphic(left, right)
            diff = "".join(
                difflib.unified_diff(
                    old.decode().splitlines(True),
                    new.decode().splitlines(True),
                    fromfile="old/" + route + "/" + a["path"],
                    tofile="new/" + route + "/" + b["path"],
                )
            )
            diff_path = route + "-" + a["path"] + ".diff"
            (output / diff_path).write_text(diff)
            comparisons.append(
                {
                    "route": route,
                    "artifact": a["path"],
                    "triples_before": len(left),
                    "triples_after": len(right),
                    "isomorphic": equal,
                    "byte_equal": old == new,
                    "before_sha256": a["sha256"],
                    "after_sha256": b["sha256"],
                    "diff": diff_path,
                }
            )
    configs = set()
    for pattern in (
        "rism/src/mappings/*.json",
        "musicbrainz/src/rdf_conversion_config/*.json",
        "musicbrainz/tests/fixtures/*.json",
        "shared/rdf_config/*.toml",
        "ckg-*/src/ontology/*.json",
        "diamm/openrefine/export/*.json",
        "diamm/openrefine/history/*.json",
        "diamm/src/relations.json",
    ):
        configs.update(ROOT.glob(pattern))
    record = {
        "code_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "tracked_worktree_dirty": bool(
            subprocess.check_output(["git", "diff", "HEAD", "--name-only"], cwd=ROOT)
        ),
        "lock_sha256": hashlib.sha256((ROOT / "poetry.lock").read_bytes()).hexdigest(),
        "runtime": runtime,
        "input_checks": input_checks,
        "comparisons": comparisons,
        "configuration_files": [
            {
                "path": str(path.relative_to(ROOT)),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
            for path in sorted(configs)
        ],
        "limits": "Same code and tracked synthetic fixtures, with retained inputs and serialization bytes. "
        "No original data, whole-dump conversion, deployment or historical fidelity is established. "
        "Installed versions are recorded; separately retain the lock used to build each environment.",
    }
    (output / "comparison.json").write_text(json.dumps(record, indent=2) + "\n")
    print(
        json.dumps(
            {
                "routes": len(ROUTES),
                "graphs": len(comparisons),
                "all_isomorphic": all(x["isomorphic"] for x in comparisons),
                "byte_different": sum(not x["byte_equal"] for x in comparisons),
            }
        )
    )
    return 0 if all(x["isomorphic"] for x in comparisons) else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old-python", type=Path)
    parser.add_argument("--new-python", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--worker", choices=ROUTES, help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        if args.worker:
            run_fixture(ROOT, args.output_dir.resolve(), args.worker)
            return 0
        if args.old_python is None or args.new_python is None:
            parser.error("--old-python and --new-python are required")
        for python in (args.old_python, args.new_python):
            if not python.resolve().is_file():
                raise ValueError("Interpreter does not exist: " + str(python))
        # Preserve the venv executable path; resolving its symlink would select
        # the base interpreter and lose its installed environment.
        return compare(
            args.old_python.absolute(),
            args.new_python.absolute(),
            args.output_dir.resolve(),
        )
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print("Runtime comparison failed: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
