"""Offline regression checks for query semantics and evaluation evidence handling."""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import requests
from rdflib import Dataset, URIRef

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import run_queries as runner
from sample_review import select


class EvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = json.loads((runner.HERE / "cases.json").read_text())["cases"]
        cls.manifests = json.loads((runner.HERE / "manifests.json").read_text())
        cls.graphs = {row["key"]: row["graph_iri"] for row in cls.manifests["datasets"]}
        cls.graphs["musicbrainz_schema"] = "urn:linkedmusic:evaluation:schema"
        cls.expected = json.loads((runner.HERE / "fixtures/expected.json").read_text())

    def setUp(self):
        self.network = patch(
            "requests.get", side_effect=AssertionError("Unmocked network request")
        )
        self.network.start()
        self.addCleanup(self.network.stop)

    def dataset(self):
        result = Dataset(default_union=False)
        result.parse(runner.HERE / "fixtures/pilot.trig", format="trig")
        return result

    def query(self, dataset, number):
        return json.loads(
            dataset.query(runner.render(self.cases[number - 1], self.graphs)).serialize(
                format="json"
            )
        )

    def response(self, body, status=200, headers=None):
        session = Mock()
        session.get.return_value = Mock(
            content=body, status_code=status, headers=headers or {}
        )
        return session

    def test_all_questions_against_independently_authored_answers(self):
        dataset = self.dataset()
        self.assertEqual(len(self.cases), 14)
        for case in self.cases:
            with self.subTest(case=case["id"]):
                result = json.loads(
                    dataset.query(runner.render(case, self.graphs)).serialize(
                        format="json"
                    )
                )
                self.assertEqual(
                    runner.comparable(result),
                    runner.comparable(self.expected[case["id"]]),
                )

    def test_negative_role_control_detects_an_added_composer_assertion(self):
        dataset = self.dataset()
        graph = dataset.graph(URIRef(self.graphs["musiconn"]))
        graph.add(
            (
                URIRef("https://example.org/lm-evaluation/associatedWork"),
                URIRef("http://www.wikidata.org/prop/direct/P86"),
                URIRef("http://www.wikidata.org/entity/Q132232"),
            )
        )
        self.assertEqual(self.query(dataset, 6)["results"]["bindings"], [])
        self.assertNotEqual(
            runner.comparable(self.query(dataset, 6)),
            runner.comparable(self.expected["cq06"]),
        )

    def test_missing_schema_is_not_a_zero_answer(self):
        with self.assertRaisesRegex(ValueError, "Unconfigured"):
            runner.render(self.cases[7], {**self.graphs, "musicbrainz_schema": None})

    def test_graph_override_changes_graph_not_class_namespace(self):
        query = runner.render(
            self.cases[0], {**self.graphs, "wjazzd": "urn:staging:wjazzd"}
        )
        self.assertIn("GRAPH <urn:staging:wjazzd>", query)
        self.assertIn("<https://linkedmusic.ca/graphs/wjazzd/Solo>", query)

    def test_updates_and_service_are_rejected_before_request(self):
        for query in (
            "DELETE WHERE { ?s ?p ?o }",
            "SELECT * WHERE { SERVICE <https://example.org/sparql> { ?s ?p ?o } }",
            "SELECT * WHERE { { SELECT * WHERE { SERVICE SILENT <urn:remote> { ?s ?p ?o } } } }",
        ):
            with self.subTest(query=query), self.assertRaises(Exception):
                runner.execute_remote(query, "https://example.org", 1)
        requests.get.assert_not_called()

    def test_iri_injection_is_rejected(self):
        with self.assertRaises(ValueError):
            runner.iri("urn:test> } SERVICE <https://example.org>")

    def test_valid_empty_select_is_retained_without_accuracy_claim(self):
        body = b'{"head":{"vars":["s"]},"results":{"bindings":[]}}'
        report, raw = runner.execute_remote(
            "SELECT ?s WHERE { ?s ?p ?o } LIMIT 1",
            "https://example.org",
            1,
            self.response(body),
        )
        self.assertEqual(report["status"], "ok")
        self.assertEqual(raw, body)
        self.assertNotIn("accuracy", report)

    def test_partial_signals_preserve_rows_and_raw_response(self):
        body = b'{"head":{"vars":["s"]},"results":{"bindings":[]}}'
        for status, headers in (
            (200, {"X-SPARQL-Anytime": "S1TAT"}),
            (200, {"X-SQL-State": "S1TAT"}),
            (206, {}),
        ):
            with self.subTest(status=status, headers=headers):
                report, raw = runner.execute_remote(
                    "SELECT ?s WHERE { ?s ?p ?o } LIMIT 1",
                    "https://example.org",
                    1,
                    self.response(body, status=status, headers=headers),
                )
                self.assertEqual(report["status"], "partial")
                self.assertEqual(raw, body)
                self.assertIn("result", report)

    def test_http_error_body_is_preserved(self):
        report, body = runner.execute_remote(
            "ASK { ?s ?p ?o }",
            "https://example.org",
            1,
            self.response(b"endpoint failed", 503),
        )
        self.assertEqual(report["status"], "endpoint_error")
        self.assertEqual(report["http_status"], 503)
        self.assertEqual(body, b"endpoint failed")

    def test_timeout_is_not_an_empty_result(self):
        session = Mock()
        session.get.side_effect = requests.Timeout("timed out")
        report, _ = runner.execute_remote(
            "ASK { ?s ?p ?o }", "https://example.org", 1, session
        )
        self.assertEqual(report["status"], "timeout")
        self.assertNotIn("result", report)

    def test_malformed_json_shapes_are_rejected(self):
        for body in (
            b"<html>SQL error</html>",
            b"[]",
            b'{"head":[],"results":{}}',
            b'{"head":{"vars":["x"]},"results":{"bindings":[{"x":"wrong"}]}}',
        ):
            with self.subTest(body=body):
                report, raw = runner.execute_remote(
                    "SELECT ?x WHERE { ?x ?p ?o }",
                    "https://example.org",
                    1,
                    self.response(body),
                )
                self.assertEqual(report["status"], "invalid_response")
                self.assertEqual(raw, body)

    def test_ask_false_and_literal_types_are_preserved(self):
        self.assertFalse(
            runner.parse_result(b'{"boolean":false}', "AskQuery")["boolean"]
        )
        literal = {
            "results": {"bindings": [{"x": {"type": "literal", "value": "1909"}}]}
        }
        typed = json.loads(json.dumps(literal))
        typed["results"]["bindings"][0]["x"][
            "datatype"
        ] = "http://www.w3.org/2001/XMLSchema#gYear"
        self.assertNotEqual(runner.comparable(literal), runner.comparable(typed))
        duplicate = json.loads(json.dumps(literal))
        duplicate["results"]["bindings"] *= 2
        self.assertNotEqual(runner.comparable(literal), runner.comparable(duplicate))

    def test_manifest_files_exist_and_unknown_counts_remain_unknown(self):
        for manifest in self.manifests["datasets"]:
            self.assertIsNone(manifest["source"]["snapshot_date"])
            self.assertIsNone(manifest["counts"]["source_records"])
            for path in manifest["conversion"]["files"]:
                self.assertTrue((runner.ROOT / path).is_file(), path)

    def test_cli_checkpoints_errors_and_continues_without_claiming_validation(self):
        empty = b'{"head":{"vars":["person"]},"results":{"bindings":[]}}'
        responses = [
            Mock(content=b"failed", status_code=503, headers={}),
            Mock(content=empty, status_code=200, headers={}),
        ]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "run"
            argv = [
                "run_queries.py",
                "--endpoint",
                "https://example.org",
                "--case",
                "cq01",
                "--case",
                "cq08",
                "--case",
                "cq14",
                "--output-dir",
                str(output),
            ]
            with patch.object(sys, "argv", argv), patch(
                "requests.get", side_effect=responses
            ):
                self.assertEqual(runner.main(), 1)
            report = json.loads((output / "report.json").read_text())
            self.assertEqual(
                [row["status"] for row in report["cases"]],
                ["endpoint_error", "configuration_error", "ok"],
            )
            self.assertEqual(
                report["cases"][2]["validation"], "requires_independent_source_review"
            )
            self.assertEqual((output / "cq01.response").read_bytes(), b"failed")
            self.assertEqual(
                report["cases"][0]["response_sha256"], runner.sha256(b"failed")
            )
            self.assertTrue((output / "cq14.rq").is_file())


class SamplingTests(unittest.TestCase):
    def frame(self):
        return {
            "complete": True,
            "provenance": {"snapshot": "synthetic"},
            "units": [
                {
                    "id": str(i),
                    "dataset": "synthetic",
                    "entity_type": "Person",
                    "method": "authority",
                    "linked": i < 10,
                    "target": f"urn:target:{i}" if i < 10 else None,
                    "source_locator": f"fixture:{i}",
                }
                for i in range(20)
            ],
        }

    def quotas(self):
        return {
            "synthetic|Person|authority|true": 4,
            "synthetic|Person|authority|false": 3,
        }

    def test_selection_is_reproducible_without_replacement_and_includes_unlinked(self):
        frame = self.frame()
        first = select(frame, self.quotas(), "fixed-seed")
        frame["units"].reverse()
        self.assertEqual(first, select(frame, self.quotas(), "fixed-seed"))
        self.assertEqual(len({row["id"] for row in first["selected"]}), 7)
        self.assertEqual(sum(row["linked"] for row in first["selected"]), 4)
        for row in first["selected"]:
            self.assertEqual(
                row["inclusion_probability"], 0.4 if row["linked"] else 0.3
            )
            self.assertEqual(row["identity_verdict"], "unreviewed")

    def test_incomplete_frame_duplicates_missing_and_oversize_quotas_fail(self):
        frame = self.frame()
        frame["complete"] = False
        with self.assertRaises(ValueError):
            select(frame, self.quotas(), "seed")
        frame = self.frame()
        frame["units"].append(frame["units"][0])
        with self.assertRaises(ValueError):
            select(frame, self.quotas(), "seed")
        with self.assertRaises(ValueError):
            select(self.frame(), {}, "seed")
        with self.assertRaises(ValueError):
            select(
                self.frame(),
                {**self.quotas(), "synthetic|Person|authority|true": 11},
                "seed",
            )


if __name__ == "__main__":
    unittest.main()
