"""Synthetic inventory contracts; no historical data or endpoint access."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from evaluation import manifest as m


def legacy():
    return json.loads(
        (Path(__file__).parent / "fixtures/manifests-v1.json").read_text()
    )


def inventory():
    value = m.normalize(legacy())
    value["datasets"] = value["datasets"][:1]
    return value


def artifact(population="stored", identifier="one"):
    value = json.loads(
        (ROOT / "evaluation/templates/population-artifact.json").read_text()
    )
    value.update(id=identifier, population=population)
    return value


def evidence():
    return {
        "location": "evidence/receipt.json",
        "sha256": m.known("a" * 64),
        "description": "Synthetic receipt.",
    }


def environment():
    return {
        "lock_sha256": m.known("a" * 64),
        "python": m.known("3.12.7"),
        "rdflib": m.known("7.1.4"),
        "oxrdflib": m.known("0.4.0"),
        "other": {"runtime": "CPython 3.12.7 with rdflib 7.1.4 and oxrdflib 0.4.0"},
    }


def measurement():
    return {
        "id": "triples",
        "metric": "rdf_triples",
        "denominator": "Entire identified RDF file",
        "status": "complete",
        "value": 0,
        "observed_at": m.known("2026-01-01T00:00:00Z"),
        "method": {
            "kind": "file_parse",
            "description": "Count triples in a synthetic empty graph.",
            "sha256": m.known("a" * 64),
        },
        "evidence": [evidence()],
        "reason": None,
        "environment": environment(),
    }


def generation(a):
    a["source_snapshot_ids"] = ["legacy-source"]
    a["relations"] = [
        {
            "kind": "generated_from",
            "artifact_id": None,
            "source_snapshot_ids": ["legacy-source"],
            "converter_run_id": m.known("synthetic-run"),
            "evidence": [evidence()],
        }
    ]
    return a


class ManifestTests(unittest.TestCase):
    def assert_invalid(self, value, message=None):
        with self.assertRaises(m.ManifestError) as error:
            m.validate(value)
        if message:
            self.assertIn(message, str(error.exception))

    def with_artifact(self, value=None):
        doc = inventory()
        doc["datasets"][0]["artifacts"] = [artifact() if value is None else value]
        return doc

    def test_schema_and_artifact_template_are_valid(self):
        m.validator().check_schema(json.loads(m.SCHEMA_PATH.read_text()))
        m.validator("artifact").validate(artifact())

    def test_live_pilot_is_migration_plus_pinned_graph_evidence(self):
        migrated = m.normalize(legacy())
        live = m.load(ROOT / "evaluation/manifests.json")
        self.assertEqual(len(live["datasets"]), 6)
        self.assertEqual(
            sum(
                row["expected_graph"]["evidence"]["status"] == "known"
                for row in live["datasets"]
            ),
            3,
        )
        for row, original in zip(live["datasets"], migrated["datasets"]):
            if row["key"] in ("musiconn", "detmold", "apsearch"):
                expected = row["expected_graph"]["evidence"]
                self.assertEqual(expected["status"], "known")
                self.assertIn(
                    "/59b4448580ab89ff9ffa2555ebf26843d6e5745b/", expected["value"]
                )
                self.assertIn(row["key"] + "/README.md", expected["value"])
                self.assertIn(
                    row["expected_graph"]["iri"]["value"],
                    (ROOT / ("ckg-" + row["key"]) / "README.md").read_text(),
                )
                row["expected_graph"]["evidence"] = original["expected_graph"][
                    "evidence"
                ]
            else:
                self.assertEqual(row["expected_graph"]["evidence"]["status"], "unknown")
        self.assertEqual(migrated, live)

    def test_migration_preserves_every_legacy_field_without_mutating_input(self):
        old = legacy()
        old["custom_metadata"] = {"unassigned": [0, None]}
        old["datasets"][0]["custom_field"] = {"source_assertion": "retained"}
        old["datasets"][0]["counts"]["rdf_triples"] = 123
        old["datasets"][0]["licence"]["custom_evidence"] = "Preserved legacy detail"
        before = deepcopy(old)
        normalized = m.normalize(old)
        rebuilt = deepcopy(normalized["legacy"])
        rebuilt["datasets"] = [
            deepcopy(row["legacy"]) for row in normalized["datasets"]
        ]
        self.assertEqual(rebuilt, old)
        self.assertEqual(old, before)
        self.assertEqual(normalized["datasets"][0]["artifacts"], [])
        self.assertEqual(
            normalized["datasets"][0]["artifact_inventory"]["status"], "unknown"
        )
        self.assertEqual(m.normalize(normalized), normalized)

    def test_future_converter_reference_is_not_a_required_input(self):
        row = next(
            d for d in m.normalize(legacy())["datasets"] if d["key"] == "musicbrainz"
        )
        entry = next(
            f
            for f in row["code_references"]
            if f["path"].endswith("relationship_mapping.py")
        )
        self.assertEqual(entry["availability"]["status"], "unknown")
        self.assertIsNone(entry["sha256"]["value"])
        self.assertIn("working_tree", row["legacy"]["conversion"]["candidate_revision"])

    def test_more_than_six_datasets_and_multiple_populations(self):
        doc = inventory()
        doc["datasets"] = [deepcopy(doc["datasets"][0]) for _ in range(14)]
        for number, row in enumerate(doc["datasets"]):
            row["key"] = f"synthetic-{number}"
            row["artifacts"] = [
                artifact("stored", "old"),
                artifact("stored", "new"),
                artifact("deployed", "live"),
                artifact("candidate", "candidate"),
            ]
        m.validate(doc)

    def test_new_dataset_does_not_need_an_invented_graph_iri(self):
        doc = inventory()
        doc["datasets"][0]["expected_graph"] = {
            "iri": m.unknown("No graph IRI has been established."),
            "evidence": m.unknown("No graph documentation is available."),
        }
        doc["datasets"][0]["source_snapshots"] = []
        m.validate(doc)

    def test_versions_and_unknown_fields_fail(self):
        for field, value in [
            ("schema_version", "3.0"),
            ("schema_version", "2.1"),
            ("protocol_version", "9.0"),
            ("typo", "bad"),
        ]:
            with self.subTest(field=field, value=value):
                doc = inventory()
                doc[field] = value
                self.assert_invalid(doc)

    def test_invalid_hash_revision_and_iri_fail(self):
        for field, values in [
            ("hash", ["bad", "a" * 63, "A" * 64, "a" * 64 + "\n"]),
            ("revision", ["working_tree", "abc1234", "g" * 40, "a" * 40 + "\n"]),
            (
                "iri",
                [
                    "relative/path",
                    "https://",
                    "https://example.org/a b",
                    "https://example.org/%zz",
                ],
            ),
        ]:
            for value in values:
                with self.subTest(field=field, value=value):
                    a = artifact()
                    if field == "hash":
                        a["file"]["sha256"] = m.known(value)
                    elif field == "revision":
                        a["converter"]["revision"] = m.known(value)
                    else:
                        a["graph"]["iri"] = m.known(value)
                    self.assert_invalid(self.with_artifact(a))

    def test_iri_supports_unicode_and_urn(self):
        for iri in ["https://example.org/œuvre", "urn:example:graph"]:
            a = artifact()
            a["graph"]["iri"] = m.known(iri)
            m.validate(self.with_artifact(a))

    def test_dates_are_valid_calendar_dates_and_times_are_utc(self):
        for date in ["2026-02-30", "20260101"]:
            doc = inventory()
            doc["datasets"][0]["source_snapshots"][0]["snapshot_date"] = m.known(date)
            self.assert_invalid(doc)
        for time in [
            "2026-02-30T00:00:00Z",
            "2026-01-01T00:00:00",
            "2026-01-01T00:00:00+02:00",
        ]:
            a = artifact()
            a["deployment"]["observed_at"] = m.known(time)
            self.assert_invalid(self.with_artifact(a))

    def test_zero_unknown_and_not_applicable_are_distinct(self):
        a = artifact()
        a["file"]["sha256"] = m.known("a" * 64)
        a["measurements"] = [measurement()]
        m.validate(self.with_artifact(a))
        for status in ["failed", "unmeasured", "not_applicable"]:
            a["measurements"][0].update(
                status=status, value=None, reason="No complete measurement."
            )
            m.validate(self.with_artifact(a))
            a["measurements"][0]["value"] = 0
            self.assert_invalid(self.with_artifact(a))

    def test_partial_measurement_requires_reason_and_is_not_zero(self):
        a = artifact()
        a["file"]["sha256"] = m.known("a" * 64)
        partial = measurement()
        partial.update(
            status="partial", value=5, reason="Parsing stopped before end of input."
        )
        a["measurements"] = [partial]
        m.validate(self.with_artifact(a))
        for change in [{"reason": None}, {"value": 0}, {"value": None}]:
            bad = deepcopy(a)
            bad["measurements"][0].update(change)
            self.assert_invalid(self.with_artifact(bad))

    def test_successful_measurement_requires_evidence_method_time_and_environment(self):
        a = artifact()
        a["file"]["sha256"] = m.known("a" * 64)
        a["measurements"] = [measurement()]
        m.validate(self.with_artifact(a))
        for field, value in [
            ("value", None),
            ("value", True),
            ("value", -1),
            ("evidence", []),
            ("observed_at", m.unknown("Unrecorded")),
            ("environment", None),
        ]:
            bad = deepcopy(a)
            bad["measurements"][0][field] = value
            self.assert_invalid(self.with_artifact(bad))
        a["measurements"][0]["method"]["sha256"] = m.unknown("Unrecorded")
        self.assert_invalid(self.with_artifact(a))

    def test_measured_populations_require_identity_even_if_bytes_are_unavailable(self):
        for population in ("stored", "candidate", "deployed"):
            for status in ("complete", "partial"):
                for kind in (
                    ("file_parse", "entity_count", "other")
                    if population != "deployed"
                    else ("remote_query", "entity_count", "other")
                ):
                    with self.subTest(population=population, status=status, kind=kind):
                        a = artifact(population)
                        count = measurement()
                        count.update(
                            status=status,
                            value=42,
                            reason="Interrupted" if status == "partial" else None,
                        )
                        count["method"]["kind"] = kind
                        count["environment"]["other"] = {
                            "runtime": "synthetic counter 1",
                            "endpoint": "https://example.org/sparql",
                            "server": "synthetic server 1",
                        }
                        a["measurements"] = [count]
                        self.assert_invalid(self.with_artifact(a), "known")
                        if population == "deployed":
                            a["graph"]["iri"] = m.known("urn:example:graph")
                        else:
                            a["file"]["sha256"] = m.known("a" * 64)
                        a["availability"] = {
                            "status": "unavailable",
                            "reason": "Historical artifact unavailable",
                        }
                        m.validate(self.with_artifact(a))

    def test_non_file_runtime_can_truthfully_mark_unused_libraries(self):
        for kind in ("remote_query", "source_count", "entity_count", "other"):
            for status in ("complete", "partial"):
                with self.subTest(kind=kind, status=status):
                    a = (
                        artifact("deployed")
                        if kind == "remote_query"
                        else generation(artifact())
                    )
                    a["graph"]["iri"] = m.known("urn:example:graph")
                    a["file"]["sha256"] = m.known("a" * 64)
                    count = measurement()
                    count.update(
                        status=status,
                        value=42,
                        reason="Interrupted" if status == "partial" else None,
                    )
                    count["method"]["kind"] = kind
                    fields = ("lock_sha256", "python", "rdflib", "oxrdflib")
                    count["environment"] = {
                        key: m.unknown("Not used by this method", "not_applicable")
                        for key in fields
                    }
                    count["environment"]["other"] = {
                        "runtime": "isql synthetic version",
                        "endpoint": "https://example.org/sparql",
                        "server": "Virtuoso synthetic version",
                    }
                    a["measurements"] = [count]
                    m.validate(self.with_artifact(a))
                    for key in fields:
                        bad = deepcopy(a)
                        bad["measurements"][0]["environment"][key] = m.unknown(
                            "Not recorded"
                        )
                        self.assert_invalid(self.with_artifact(bad))
                    bad = deepcopy(a)
                    del bad["measurements"][0]["environment"]["other"]["runtime"]
                    self.assert_invalid(self.with_artifact(bad))

    def test_remote_measurements_require_endpoint_and_server(self):
        a = artifact("deployed")
        a["graph"]["iri"] = m.known("urn:example:graph")
        count = measurement()
        count["method"]["kind"] = "remote_query"
        count["environment"]["other"] = {
            "runtime": "isql version",
            "endpoint": "https://example.org/sparql",
            "server": "Virtuoso version",
        }
        a["measurements"] = [count]
        m.validate(self.with_artifact(a))
        for key in ("endpoint", "server"):
            bad = deepcopy(a)
            del bad["measurements"][0]["environment"]["other"][key]
            self.assert_invalid(self.with_artifact(bad))
        count["environment"]["other"]["endpoint"] = "not an endpoint"
        self.assert_invalid(self.with_artifact(a))

    def test_deployed_identity_does_not_depend_on_measurement_kind(self):
        for kind in ("entity_count", "other", "remote_query"):
            for status in ("complete", "partial"):
                a = artifact("deployed")
                a["graph"]["iri"] = m.known("urn:example:graph")
                count = measurement()
                count.update(
                    status=status,
                    value=42,
                    reason="Interrupted" if status == "partial" else None,
                )
                count["method"]["kind"] = kind
                count["environment"]["other"].update(
                    endpoint="https://example.org/sparql", server="Virtuoso version"
                )
                a["measurements"] = [count]
                with self.subTest(kind=kind, status=status):
                    m.validate(self.with_artifact(a))
                for field, value in (
                    ("endpoint", None),
                    ("endpoint", "relative/path"),
                    ("endpoint", "https://example.org/%zz"),
                    ("server", None),
                    ("server", ""),
                ):
                    with self.subTest(
                        kind=kind, status=status, field=field, value=value
                    ):
                        bad = deepcopy(a)
                        other = bad["measurements"][0]["environment"]["other"]
                        if value is None:
                            del other[field]
                        else:
                            other[field] = value
                        self.assert_invalid(self.with_artifact(bad))

    def test_file_parse_requires_known_or_explicitly_unused_environment(self):
        a = artifact()
        a["file"]["sha256"] = m.known("a" * 64)
        a["measurements"] = [measurement()]
        for status in ("complete", "partial"):
            a["measurements"][0].update(
                status=status,
                value=42,
                reason="Interrupted" if status == "partial" else None,
            )
            m.validate(self.with_artifact(a))
            for field in ("lock_sha256", "python", "rdflib", "oxrdflib"):
                for state in ("unknown", "unavailable"):
                    bad = deepcopy(a)
                    bad["measurements"][0]["environment"][field] = m.unknown(
                        "Unrecorded or unused", state
                    )
                    self.assert_invalid(self.with_artifact(bad))

    def test_file_parse_can_record_pyoxigraph_without_unused_rdflib_versions(self):
        a = artifact()
        a["file"]["sha256"] = m.known("a" * 64)
        count = measurement()
        count["environment"]["rdflib"] = m.unknown(
            "Parser uses pyoxigraph directly", "not_applicable"
        )
        count["environment"]["oxrdflib"] = m.unknown(
            "Adapter is not used", "not_applicable"
        )
        count["environment"]["other"] = {
            "runtime": "pyoxigraph 0.4.11 under CPython 3.12.7"
        }
        a["measurements"] = [count]
        for status in ("complete", "partial"):
            count.update(
                status=status,
                value=42,
                reason="Interrupted" if status == "partial" else None,
            )
            m.validate(self.with_artifact(a))
        del count["environment"]["other"]["runtime"]
        self.assert_invalid(self.with_artifact(a))

    def test_generation_sources_must_equal_evidenced_sources(self):
        for population in ("stored", "candidate"):
            a = generation(artifact(population))
            m.validate(self.with_artifact(a))
            a["relations"] = []
            self.assert_invalid(self.with_artifact(a), "evidenced")
            a = generation(artifact(population))
            a["source_snapshot_ids"] = []
            self.assert_invalid(self.with_artifact(a), "evidenced")
            a = generation(artifact(population))
            a["relations"][0]["evidence"] = []
            self.assert_invalid(self.with_artifact(a))
        self.assert_invalid(
            self.with_artifact(generation(artifact("deployed"))), "stored/candidate"
        )

    def test_converter_identity_cannot_bypass_lineage_evidence(self):
        a = artifact()
        a["converter"]["revision"] = m.known("a" * 40)
        self.assert_invalid(self.with_artifact(a), "Converter identity")
        generation(a)
        m.validate(self.with_artifact(a))

    def test_source_count_requires_source_lineage(self):
        a = artifact()
        a["file"]["sha256"] = m.known("a" * 64)
        count = measurement()
        count["method"]["kind"] = "source_count"
        count["environment"]["other"] = {"runtime": "synthetic counter 1"}
        a["measurements"] = [count]
        self.assert_invalid(self.with_artifact(a), "source lineage")
        generation(a)
        m.validate(self.with_artifact(a))

    def test_unknown_state_cannot_smuggle_a_value(self):
        a = artifact()
        a["converter"]["revision"]["value"] = "a" * 40
        self.assert_invalid(self.with_artifact(a))
        a["converter"]["revision"] = m.unknown("")
        self.assert_invalid(self.with_artifact(a))

    def test_available_local_artifact_requires_path_and_hash(self):
        a = artifact()
        a["availability"] = {"status": "available", "reason": "Synthetic fixture"}
        self.assert_invalid(self.with_artifact(a))
        a["file"] = {"path": m.known("data/fixture.nt"), "sha256": m.known("a" * 64)}
        m.validate(self.with_artifact(a))

    def test_live_only_graph_has_explicit_no_file_and_observation(self):
        a = artifact("deployed")
        a["availability"] = {"status": "available", "reason": "Scoped observation"}
        a["file"] = {
            key: m.unknown("Live-only graph", "not_applicable")
            for key in ["path", "sha256"]
        }
        a["graph"] = {"iri": m.known("urn:example:graph"), "evidence": [evidence()]}
        self.assert_invalid(self.with_artifact(a))
        a["deployment"] = {
            "observed_at": m.known("2026-01-01T00:00:00Z"),
            "evidence": [evidence()],
        }
        m.validate(self.with_artifact(a))
        selected = m.select_artifact(self.with_artifact(a), "wjazzd", "deployed")
        with self.assertRaisesRegex(m.ManifestError, "separate observation"):
            m.verify_file(selected)

    def test_file_counts_and_remote_counts_do_not_cross_populations(self):
        for population, kind in [
            ("stored", "remote_query"),
            ("candidate", "remote_query"),
            ("deployed", "file_parse"),
        ]:
            a = artifact(population)
            count = measurement()
            count["method"]["kind"] = kind
            a["measurements"] = [count]
            self.assert_invalid(self.with_artifact(a))

    def test_duplicate_ids_and_dangling_sources_fail(self):
        doc = inventory()
        doc["datasets"].append(deepcopy(doc["datasets"][0]))
        self.assert_invalid(doc, "Duplicate dataset")
        doc = inventory()
        doc["datasets"][0]["artifacts"] = [artifact(), artifact()]
        self.assert_invalid(doc, "Duplicate artifact")
        a = artifact()
        a["source_snapshot_ids"] = ["missing"]
        self.assert_invalid(self.with_artifact(a), "unknown source")

    def test_lineage_requires_evidence_and_correct_population(self):
        stored = artifact("stored", "stored")
        deployed = artifact("deployed", "deployed")
        deployed["relations"] = [
            {
                "kind": "loaded_from",
                "artifact_id": "stored",
                "source_snapshot_ids": [],
                "converter_run_id": m.unknown("Load relation", "not_applicable"),
                "evidence": [evidence()],
            }
        ]
        doc = inventory()
        doc["datasets"][0]["artifacts"] = [stored, deployed]
        m.validate(doc)
        stored["population"] = "candidate"
        self.assert_invalid(doc, "loaded_from")
        stored["population"] = "stored"
        deployed["relations"][0]["evidence"] = []
        self.assert_invalid(doc)

    def test_candidate_lineage_requires_snapshot_and_converter_run(self):
        a = artifact("candidate")
        a["source_snapshot_ids"] = ["legacy-source"]
        relation = {
            "kind": "generated_from",
            "artifact_id": None,
            "source_snapshot_ids": ["legacy-source"],
            "converter_run_id": m.known("synthetic-run"),
            "evidence": [evidence()],
        }
        a["relations"] = [relation]
        m.validate(self.with_artifact(a))
        relation["converter_run_id"] = m.unknown("Unknown")
        self.assert_invalid(self.with_artifact(a), "generated_from")

    def test_dirty_code_needs_exact_file_hashes(self):
        a = artifact()
        a["converter"]["dirty"] = True
        self.assert_invalid(self.with_artifact(a), "Dirty converter")
        a["converter"]["files"] = [
            {
                "path": "converter.py",
                "kind": "code",
                "availability": {"status": "unknown", "reason": "Historical"},
                "sha256": m.known("a" * 64),
            }
        ]
        generation(a)
        m.validate(self.with_artifact(a))

    def test_working_and_durable_locations_have_separate_availability(self):
        a = artifact()
        a["file"]["path"] = m.known("raw_data/fixture.nt")
        a["storage"] = {
            "location": m.known("https://example.org/archive/fixture.nt"),
            "availability": {"status": "unavailable", "reason": "Archive offline"},
        }
        m.validate(self.with_artifact(a))
        self.assertEqual(a["availability"]["status"], "unknown")
        a["storage"]["location"] = m.known("file:///Users/example/archive.nt")
        self.assert_invalid(self.with_artifact(a))

    def test_selection_rejects_missing_unavailable_or_ambiguous_artifact(self):
        doc = self.with_artifact()
        for dataset, population in [
            ("absent", "stored"),
            ("wjazzd", "other"),
            ("wjazzd", "candidate"),
            ("wjazzd", "stored"),
        ]:
            with self.assertRaises(m.ManifestError):
                m.select_artifact(doc, dataset, population)
        a = doc["datasets"][0]["artifacts"][0]
        a["availability"] = {"status": "available", "reason": "Synthetic"}
        a["file"] = {"path": m.known("fixture.nt"), "sha256": m.known("a" * 64)}
        second = deepcopy(a)
        second["id"] = "two"
        doc["datasets"][0]["artifacts"].append(second)
        with self.assertRaisesRegex(m.ManifestError, "exactly one"):
            m.select_artifact(doc, "wjazzd", "stored")
        self.assertEqual(m.select_artifact(doc, "wjazzd", "stored", "two")["id"], "two")

    def test_selected_file_requires_matching_bytes_and_rejects_symlink_escape(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            root.mkdir()
            path = root / "fixture.nt"
            data = b"# synthetic RDF\n"
            path.write_bytes(data)
            a = artifact()
            a["availability"] = {"status": "available", "reason": "Synthetic"}
            a["file"] = {
                "path": m.known("fixture.nt"),
                "sha256": m.known(hashlib.sha256(data).hexdigest()),
            }
            selected = m.select_artifact(self.with_artifact(a), "wjazzd", "stored")
            self.assertEqual(
                m.verify_file(selected, root), hashlib.sha256(data).hexdigest()
            )
            path.write_bytes(data + b"changed")
            with self.assertRaisesRegex(m.ManifestError, "SHA-256"):
                m.verify_file(selected, root)
            path.unlink()
            with self.assertRaisesRegex(m.ManifestError, "missing"):
                m.verify_file(selected, root)
            outside = Path(temp) / "outside.nt"
            outside.write_bytes(data)
            path.symlink_to(outside)
            with self.assertRaisesRegex(m.ManifestError, "outside"):
                m.verify_file(selected, root)

    def test_absolute_and_traversal_paths_fail(self):
        for path in [
            "/tmp/file.nt",
            "../file.nt",
            "data/../file.nt",
            "C:\\file.nt",
            "data//file.nt",
            "~/file.nt",
        ]:
            a = artifact()
            a["file"]["path"] = m.known(path)
            self.assert_invalid(self.with_artifact(a))

    def test_json_duplicate_keys_and_nonfinite_numbers_fail(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "bad.json"
            for content in [
                '{"datasets": [], "datasets": []}',
                '{"value": NaN}',
                '{"value": Infinity}',
                '{"value": 1e999}',
            ]:
                path.write_text(content)
                with self.assertRaises(m.ManifestError):
                    m.load(path)

    def test_python_api_rejects_nonfinite_measurements(self):
        for value in [float("inf"), float("-inf"), float("nan")]:
            a = artifact()
            a["measurements"] = [measurement()]
            a["measurements"][0]["value"] = value
            self.assert_invalid(self.with_artifact(a), "JSON values")

    def test_newline_in_identifier_is_rejected(self):
        a = artifact(identifier="record\n")
        self.assert_invalid(self.with_artifact(a))

    def test_migration_cli_preserves_input_and_existing_outputs(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "old.json"
            source.write_text(json.dumps(legacy()))
            before = source.read_bytes()
            output = Path(temp) / "new.json"
            command = [
                sys.executable,
                str(ROOT / "evaluation/manifest.py"),
                "migrate",
                str(source),
                "--output",
            ]
            self.assertEqual(
                subprocess.run(command + [str(output)], capture_output=True).returncode,
                0,
            )
            after = output.read_bytes()
            self.assertEqual(
                subprocess.run(command + [str(output)], capture_output=True).returncode,
                1,
            )
            self.assertEqual(
                subprocess.run(command + [str(source)], capture_output=True).returncode,
                1,
            )
            self.assertEqual(source.read_bytes(), before)
            self.assertEqual(output.read_bytes(), after)
            self.assertEqual(json.loads(after), m.normalize(legacy()))

    def test_required_ci_suite_fails_when_missing_or_empty(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "scripts").mkdir()
            runner = root / "scripts/check_offline.py"
            runner.write_bytes((ROOT / "scripts/check_offline.py").read_bytes())
            command = [sys.executable, str(runner)]
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 1)
            suite = root / "evaluation/tests"
            suite.mkdir(parents=True)
            (suite / "test_empty.py").write_text("# Contains zero tests.\n")
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 1)
            (suite / "test_example.py").write_text(
                "import unittest\nclass Example(unittest.TestCase):\n    def test_ok(self): self.assertTrue(True)\n"
            )
            # A passing suite no longer substitutes for the mandatory query run.
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 1)
            query_runner = root / "evaluation/run_queries.py"
            stub = (
                "import json, sys\nfrom pathlib import Path\n"
                "output = Path(sys.argv[sys.argv.index('--output-dir') + 1])\n"
                "output.mkdir()\n"
                "(output / 'report.json').write_text(json.dumps({'cases': CASES}))\n"
            )
            query_runner.write_text(stub.replace("CASES", "[]"))
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 1)
            complete = [
                {"id": f"cq{i:02d}", "validation": "fixture_pass"} for i in range(1, 15)
            ]
            query_runner.write_text(stub.replace("CASES", repr(complete)))
            # Each required suite must exist and contain passing tests.
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 1)
            rism_suite = root / "rism/tests"
            rism_suite.mkdir(parents=True)
            (rism_suite / "test_empty.py").write_text("# Contains zero tests.\n")
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 1)
            (rism_suite / "test_example.py").write_bytes(
                (suite / "test_example.py").read_bytes()
            )
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 0)
            complete[0]["validation"] = "fixture_fail"
            query_runner.write_text(stub.replace("CASES", repr(complete)))
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 1)
            (suite / "test_example.py").write_text(
                "import unittest\nclass Example(unittest.TestCase):\n    def test_bad(self): self.fail('expected failure')\n"
            )
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 1)
            (suite / "test_example.py").write_text(
                "import missing_dependency_for_synthetic_test\n"
            )
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn("ModuleNotFoundError", result.stderr)


if __name__ == "__main__":
    unittest.main()
