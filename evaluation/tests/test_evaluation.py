"""Offline regression checks for query semantics and evaluation evidence handling."""

from copy import deepcopy
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
import sample_review
from sample_review import select


class EvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = json.loads((runner.HERE / "cases.json").read_text())["cases"]
        cls.manifests = runner.manifest.load(runner.HERE / "manifests.json")
        cls.graphs = dict(runner.FIXTURE_GRAPHS)
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
        session.get.return_value.raw.read1.side_effect = [body, b""]
        return session

    def test_all_questions_against_hand_authored_fixture_answers(self):
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
            self.cases[12], {**self.graphs, "detmold": "urn:staging:detmold"}
        )
        self.assertIn("GRAPH <urn:staging:detmold>", query)
        self.assertIn("<https://linkedmusic.ca/graphs/ckg/Work>", query)

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
            b'{"head":{"vars":[]},"results":{"bindings":[]},"metadata":NaN}',
            b'{"head":{"vars":[]},"results":{"bindings":[]},"metadata":1e999}',
            b'{"head":{"vars":[]},"results":{"bindings":[]},"results":{}}',
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

    def write_inventory(self, root, keys, population="deployed", payload=None):
        document = deepcopy(self.manifests)
        for entry in document["datasets"]:
            if entry["key"] not in keys:
                continue
            artifact = json.loads(
                (runner.HERE / "templates/population-artifact.json").read_text()
            )
            artifact.update(
                id="test",
                population=population,
                availability={
                    "status": "available",
                    "reason": "Synthetic available artifact.",
                },
            )
            artifact["graph"] = {
                "iri": runner.manifest.known("urn:staging:" + entry["key"]),
                "evidence": [
                    {
                        "location": "receipt.json",
                        "sha256": runner.manifest.known("a" * 64),
                        "description": "Synthetic observation",
                    }
                ],
            }
            if population == "deployed":
                artifact["deployment"] = {
                    "observed_at": runner.manifest.known("2026-01-01T00:00:00Z"),
                    "evidence": artifact["graph"]["evidence"],
                }
            else:
                name = entry["key"] + ".ttl"
                (root / name).write_bytes(payload if payload is not None else b"")
                artifact["file"] = {
                    "path": runner.manifest.known(name),
                    "sha256": runner.manifest.known(
                        runner.sha256((root / name).read_bytes())
                    ),
                }
            entry["artifacts"] = [artifact]
        runner.manifest.validate(document)
        path = root / "inventory.json"
        path.write_text(json.dumps(document))
        return path

    def run_cli(self, root, arguments):
        output = root / "run"
        result = runner.main([*arguments, "--output-dir", str(output)])
        report = json.loads((output / "report.json").read_text())
        for row in report["cases"]:
            if "query_file" in row:
                self.assertEqual(
                    row["query_sha256"],
                    runner.sha256((output / row["query_file"]).read_bytes()),
                )
        return result, report

    def test_fixture_reports_v1_and_v2_provenance_without_inventing_artifacts(self):
        for version, path in (
            ("1.0", runner.HERE / "tests/fixtures/manifests-v1.json"),
            ("2.0", runner.HERE / "manifests.json"),
        ):
            with self.subTest(
                version=version
            ), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                result, report = self.run_cli(
                    root, ["--fixture", "--case", "cq01", "--manifest", str(path)]
                )
                self.assertEqual(result, 0)
                self.assertEqual(report["manifest_input_schema_version"], version)
                self.assertEqual(report["manifest_schema_version"], "2.0")
                self.assertEqual(
                    report["manifest_input_sha256"], runner.sha256(path.read_bytes())
                )
                self.assertEqual(report["artifacts"], {})
                self.assertIsNone(report["population"])
                self.assertEqual(report["cases"][0]["validation"], "fixture_pass")
                for name in ("manifest.py", "manifest_schema.json"):
                    self.assertEqual(
                        report["provenance"]["file_sha256"]["evaluation/" + name],
                        runner.sha256((runner.HERE / name).read_bytes()),
                    )
        requests.get.assert_not_called()

    def test_cli_checkpoints_errors_and_continues_without_claiming_validation(self):
        empty = b'{"head":{"vars":["person"]},"results":{"bindings":[]}}'
        responses = [
            self.response(b"failed", status=503).get.return_value,
            self.response(empty).get.return_value,
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inventory = self.write_inventory(root, ["wjazzd", "musicbrainz", "detmold"])
            output = root / "run"
            argv = [
                "run_queries.py",
                "--endpoint",
                "https://example.org",
                "--population",
                "deployed",
                "--manifest",
                str(inventory),
                "--artifact",
                "wjazzd=test",
                "--artifact",
                "musicbrainz=test",
                "--artifact",
                "detmold=test",
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

    def test_local_population_verifies_identity_and_uses_selected_graph(self):
        payload = b"<urn:solo> a <https://linkedmusic.ca/graphs/wjazzd/Solo>; <http://www.wikidata.org/prop/direct/P175> <http://www.wikidata.org/entity/Q103767> ."
        for population in ("stored", "candidate"):
            with self.subTest(
                population=population
            ), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                inventory = self.write_inventory(root, ["wjazzd"], population, payload)
                result, report = self.run_cli(
                    root,
                    [
                        "--local",
                        "--population",
                        population,
                        "--manifest",
                        str(inventory),
                        "--root",
                        str(root),
                        "--artifact",
                        "wjazzd=test",
                        "--case",
                        "cq01",
                    ],
                )
                self.assertEqual(result, 0)
                row = report["cases"][0]
                self.assertEqual(
                    row["result"]["results"]["bindings"],
                    [{"solo": {"type": "uri", "value": "urn:solo"}}],
                )
                self.assertEqual(row["artifacts"]["wjazzd"]["population"], population)
                self.assertTrue(row["artifacts"]["wjazzd"]["file_verified"])
                self.assertEqual(report["graphs"]["wjazzd"], "urn:staging:wjazzd")
                self.assertFalse(row["request_attempted"])
                self.assertEqual(
                    row["validation"], "requires_independent_source_review"
                )
        requests.get.assert_not_called()

    def test_local_missing_corrupt_and_unparseable_files_never_become_empty_success(
        self,
    ):
        for change in ("missing", "hash", "syntax", "relative"):
            with self.subTest(
                change=change
            ), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                payload = (
                    b"not turtle"
                    if change == "syntax"
                    else (
                        b"<relative> <urn:p> <urn:o> ." if change == "relative" else b""
                    )
                )
                inventory = self.write_inventory(root, ["wjazzd"], "stored", payload)
                if change == "missing":
                    (root / "wjazzd.ttl").unlink()
                if change == "hash":
                    (root / "wjazzd.ttl").write_bytes(b"# changed")
                result, report = self.run_cli(
                    root,
                    [
                        "--local",
                        "--population",
                        "stored",
                        "--manifest",
                        str(inventory),
                        "--root",
                        str(root),
                        "--artifact",
                        "wjazzd=test",
                        "--case",
                        "cq01",
                    ],
                )
                self.assertEqual(result, 1)
                self.assertEqual(report["cases"][0]["status"], "configuration_error")
                self.assertNotIn("result", report["cases"][0])
        requests.get.assert_not_called()

    def test_legacy_pilot_cannot_supply_a_measured_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            result, report = self.run_cli(
                Path(directory),
                [
                    "--endpoint",
                    "https://example.org",
                    "--population",
                    "deployed",
                    "--artifact",
                    "wjazzd=imaginary",
                    "--case",
                    "cq01",
                    "--manifest",
                    str(runner.HERE / "tests/fixtures/manifests-v1.json"),
                ],
            )
            self.assertEqual(result, 1)
            self.assertFalse(report["cases"][0]["request_attempted"])
            self.assertEqual(report["manifest_input_schema_version"], "1.0")
        requests.get.assert_not_called()

    def test_unknown_version_is_archived_and_fails_before_request(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "future.json"
            path.write_text('{"schema_version":"9.0"}')
            result, report = self.run_cli(root, ["--fixture", "--manifest", str(path)])
            self.assertEqual(result, 1)
            self.assertEqual(report["status"], "configuration_error")
            self.assertEqual(
                (root / "run/manifest.input.json").read_bytes(), path.read_bytes()
            )
        requests.get.assert_not_called()

    def test_row_cap_and_unsupported_question_remain_visible(self):
        body = json.dumps(
            {
                "head": {"vars": ["work"]},
                "results": {
                    "bindings": [{"work": {"type": "uri", "value": "urn:work"}}] * 25
                },
            }
        ).encode()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inventory = self.write_inventory(root, ["apsearch"])
            with patch(
                "requests.get", return_value=self.response(body).get.return_value
            ):
                result, report = self.run_cli(
                    root,
                    [
                        "--endpoint",
                        "https://example.org",
                        "--population",
                        "deployed",
                        "--artifact",
                        "apsearch=test",
                        "--case",
                        "cq12",
                        "--manifest",
                        str(inventory),
                    ],
                )
            self.assertEqual(result, 0)
            row = report["cases"][0]
            self.assertEqual(row["question_support"], "unsupported")
            self.assertEqual(row["validation"], "unsupported_question")
            self.assertTrue(row["at_row_limit"])
            self.assertEqual(row["completeness"], "row_cap_reached")
            self.assertTrue(row["request_attempted"])

    def test_cli_persists_timeout_partial_and_invalid_results(self):
        body = b'{"head":{"vars":["solo"]},"results":{"bindings":[]}}'
        attempts = [
            (requests.Timeout("timed out"), "timeout"),
            (self.response(body, status=206).get.return_value, "partial"),
            (self.response(b"broken").get.return_value, "invalid_response"),
        ]
        for response, status in attempts:
            with self.subTest(
                status=status
            ), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                inventory = self.write_inventory(root, ["wjazzd"])
                with patch("requests.get", side_effect=[response]):
                    result, report = self.run_cli(
                        root,
                        [
                            "--endpoint",
                            "https://example.org",
                            "--population",
                            "deployed",
                            "--artifact",
                            "wjazzd=test",
                            "--case",
                            "cq01",
                            "--manifest",
                            str(inventory),
                        ],
                    )
                self.assertEqual(result, 1)
                row = report["cases"][0]
                self.assertEqual(row["status"], status)
                self.assertEqual(row["validation"], "not_evaluated")
                raw = (root / "run/cq01.response").read_bytes()
                self.assertEqual(row["response_sha256"], runner.sha256(raw))
                self.assertIsNotNone(report["finished_at_utc"])

    def test_from_and_nonselect_queries_cannot_fetch_data(self):
        for query in (
            "SELECT * FROM <https://example.org/data> WHERE { ?s ?p ?o }",
            "CONSTRUCT { ?s ?p ?o } WHERE { ?s ?p ?o }",
            "SELECT broken",
        ):
            with self.subTest(query=query), self.assertRaises(ValueError):
                runner.execute_remote(query, "https://example.org", 1)
        requests.get.assert_not_called()

    def test_artifact_aliases_and_duplicate_graphs_fail_closed(self):
        self.assertEqual(
            runner.artifact_bindings(
                ["musicbrainz_schema=musicbrainz/schema"], {"musicbrainz_schema"}
            ),
            {"musicbrainz_schema": ("musicbrainz", "schema")},
        )
        for bindings in (
            ["unknown=test"],
            ["wjazzd=test", "wjazzd=other"],
            ["wjazzd="],
        ):
            with self.assertRaises(ValueError):
                runner.artifact_bindings(bindings, {"wjazzd"})
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inventory = self.write_inventory(root, ["musicbrainz"])
            result, report = self.run_cli(
                root,
                [
                    "--endpoint",
                    "https://example.org",
                    "--population",
                    "deployed",
                    "--artifact",
                    "musicbrainz=test",
                    "--artifact",
                    "musicbrainz_schema=musicbrainz/test",
                    "--case",
                    "cq08",
                    "--manifest",
                    str(inventory),
                ],
            )
            self.assertEqual(result, 1)
            self.assertEqual(report["cases"][0]["status"], "configuration_error")
        requests.get.assert_not_called()

    def test_literal_metadata_and_rdf_term_comparison(self):
        def result(term):
            return {"head": {"vars": ["x"]}, "results": {"bindings": [{"x": term}]}}

        plain = {"type": "literal", "value": "01"}
        string = {**plain, "datatype": "http://www.w3.org/2001/XMLSchema#string"}
        integer = {**plain, "datatype": "http://www.w3.org/2001/XMLSchema#integer"}
        self.assertEqual(
            runner.comparable(result(plain)), runner.comparable(result(string))
        )
        self.assertNotEqual(
            runner.comparable(result(integer)),
            runner.comparable(result({**integer, "value": "1"})),
        )
        for term in (
            {"type": "uri", "value": "urn:x", "xml:lang": "en"},
            {**plain, "datatype": 3},
            {**plain, "xml:lang": ""},
            {**plain, "type": "typed-literal"},
            {**string, "xml:lang": "en"},
        ):
            with self.subTest(term=term), self.assertRaises(ValueError):
                runner.parse_result(json.dumps(result(term)), "SelectQuery")
        empty = {"head": {"vars": ["x"]}, "results": {"bindings": []}}
        self.assertNotEqual(
            runner.comparable(empty),
            runner.comparable({**empty, "head": {"vars": ["y"]}}),
        )

    def test_parse_preserves_literal_lexical_form(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "literal.ttl"
            path.write_text(
                '<urn:s> <urn:p> "01"^^<http://www.w3.org/2001/XMLSchema#integer> .'
            )
            graph = Dataset().graph(URIRef("urn:g"))
            runner.parse_graph(graph, path, "turtle")
            self.assertEqual(str(next(graph.objects())), "01")

    def test_existing_output_is_never_replaced(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "run"
            output.mkdir()
            (output / "report.json").write_text("original")
            with self.assertRaises(SystemExit):
                runner.main(["--fixture", "--output-dir", str(output)])
            self.assertEqual((output / "report.json").read_text(), "original")

    def test_fixture_detects_weakened_query_constraints(self):
        import re

        dataset = self.dataset()
        mutants = []
        for number in (1, 2, 3, 5, 6, 12, 13, 14):
            query = runner.render(self.cases[number - 1], self.graphs)
            for index, match in enumerate(
                re.finditer(r"(\?\w+) a <[^>]+>\s*([;.])", query)
            ):
                replacement = match[1] + " " if match[2] == ";" else ""
                mutants.append(
                    (
                        number,
                        f"type-{index}",
                        query[: match.start()] + replacement + query[match.end() :],
                    )
                )
        query = runner.render(self.cases[2], self.graphs)
        without_uuid = re.sub(r"    FILTER\(REGEX\(STR\(\?mbid\).*\n", "", query)
        mutants.extend(
            [
                (3, "UUID", without_uuid),
                (
                    3,
                    "both ID filters",
                    without_uuid.replace("FILTER(isLiteral(?mbid))", ""),
                ),
            ]
        )
        for number in (4, 5):
            query = runner.render(self.cases[number - 1], self.graphs)
            mutants.append(
                (number, "unbounded P2888", query.replace("wdt:P2888?", "wdt:P2888*"))
            )
        query = runner.render(self.cases[9], self.graphs)
        mutants.extend(
            [
                (10, "start exclusive", query.replace("<= 1940", "< 1940")),
                (10, "end exclusive", query.replace(">= 1940", "> 1940")),
            ]
        )
        query = runner.render(self.cases[11], self.graphs)
        mutants.extend(
            [
                (12, "inclusive 1950", query.replace("< 1950", "<= 1950")),
                (12, "no year filter", re.sub(r"    FILTER\(datatype.*\n", "", query)),
                (
                    12,
                    "no datatype",
                    query.replace("datatype(?year) = xsd:gYear && ", ""),
                ),
            ]
        )
        query = runner.render(self.cases[13], self.graphs)
        mutants.append(
            (
                14,
                "wildcard hostname",
                query.replace("www[.]wikidata[.]org", "www.wikidata.org"),
            )
        )
        for number, label, query in mutants:
            with self.subTest(case=number, mutant=label):
                result = json.loads(dataset.query(query).serialize(format="json"))
                self.assertNotEqual(
                    runner.comparable(result),
                    runner.comparable(self.expected[f"cq{number:02d}"]),
                )

    def test_ckg_queries_match_the_converter_namespace(self):
        # Read the documented converter constant without importing its CLI.
        import ast

        source = runner.ROOT / "ckg-musiconn/src/convert_to_rdf.py"
        namespaces = next(
            ast.literal_eval(node.value)
            for node in ast.parse(source.read_text()).body
            if isinstance(node, ast.Assign)
            and isinstance(node.value, ast.Dict)
            and any(
                isinstance(key, ast.Constant) and key.value == "lmckg"
                for key in node.value.keys
            )
        )
        payload = (
            f'<urn:work> a <{namespaces["lmckg"]}Work>; '
            '<http://www.wikidata.org/prop/direct/P571> "1835"^^<http://www.w3.org/2001/XMLSchema#gYear> .\n'
            f'<urn:person> a <{namespaces["lmckg"]}Person> .\n'
        ).encode()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inventory = self.write_inventory(root, ["detmold"], "stored", payload)
            result, report = self.run_cli(
                root,
                [
                    "--local",
                    "--population",
                    "stored",
                    "--artifact",
                    "detmold=test",
                    "--manifest",
                    str(inventory),
                    "--root",
                    str(root),
                    "--case",
                    "cq13",
                    "--case",
                    "cq14",
                ],
            )
            self.assertEqual(result, 0)
            self.assertEqual([row["row_count"] for row in report["cases"]], [1, 1])
            self.assertEqual(
                report["cases"][0]["result"]["results"]["bindings"][0]["work"]["value"],
                "urn:work",
            )
            self.assertEqual(
                report["cases"][1]["result"]["results"]["bindings"][0]["person"][
                    "value"
                ],
                "urn:person",
            )

    def test_colon_artifact_ids_cannot_select_another_dataset(self):
        self.assertEqual(
            runner.artifact_bindings(["wjazzd=export:2026-11"], {"wjazzd"}),
            {"wjazzd": ("wjazzd", "export:2026-11")},
        )
        self.assertEqual(
            runner.artifact_bindings(["wjazzd=rism:stored-1"], {"wjazzd"}),
            {"wjazzd": ("wjazzd", "rism:stored-1")},
        )
        with self.assertRaises(ValueError):
            runner.artifact_bindings(["wjazzd=rism/stored-1"], {"wjazzd"})
        for value in ("rism/schema", "musicbrainz:schema", "musicbrainz/schema/part"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                runner.artifact_bindings(
                    [f"musicbrainz_schema={value}"], {"musicbrainz_schema"}
                )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inventory = self.write_inventory(root, ["wjazzd"], "stored")
            document = json.loads(inventory.read_text())
            entry = next(d for d in document["datasets"] if d["key"] == "wjazzd")
            entry["artifacts"][0]["id"] = "rism:stored-1"
            inventory.write_text(json.dumps(document))
            result, report = self.run_cli(
                root,
                [
                    "--local",
                    "--population",
                    "stored",
                    "--artifact",
                    "wjazzd=rism:stored-1",
                    "--case",
                    "cq01",
                    "--manifest",
                    str(inventory),
                    "--root",
                    str(root),
                ],
            )
            self.assertEqual(result, 0)
            self.assertEqual(report["cases"][0]["status"], "ok")

    def test_response_body_timeouts_preserve_received_bytes_and_headers(self):
        from urllib3.exceptions import ReadTimeoutError

        for error in (
            ReadTimeoutError(None, "https://example.org", "stalled"),
            requests.ConnectionError(
                ReadTimeoutError(None, "https://example.org", "stalled")
            ),
            requests.ConnectionError("connection reset"),
        ):
            session = self.response(
                b'{"head":',
                headers={"Server": "test-server", "Set-Cookie": "not archived"},
            )
            response = session.get.return_value
            response.raw.read1.side_effect = [b'{"head":', error]

            # Non-streaming requests raises before returning a response, losing
            # even the headers. This mock models that boundary on the old runner.
            def get(*args, **kwargs):
                if not kwargs.get("stream"):
                    raise requests.ConnectionError(error)
                return response

            session.get.side_effect = get
            report, body = runner.execute_remote(
                "ASK { ?s ?p ?o }", "https://example.org", 1, session
            )
            expected_status = (
                "endpoint_error" if str(error) == "connection reset" else "timeout"
            )
            self.assertEqual(report["status"], expected_status)
            self.assertEqual(report["http_status"], 200)
            self.assertEqual(report["headers"], {"server": "test-server"})
            self.assertEqual(body, b'{"head":')
            self.assertNotIn("result", report)
            response.close.assert_called_once()

    def test_local_invalid_response_keeps_serialized_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(
                runner, "parse_result", side_effect=ValueError("test rejection")
            ):
                result, report = self.run_cli(root, ["--fixture", "--case", "cq01"])
            row = report["cases"][0]
            self.assertEqual(result, 1)
            self.assertEqual(row["status"], "query_error")
            body = (root / "run/cq01.response").read_bytes()
            self.assertIn(b'"bindings"', body)
            self.assertEqual(row["response_sha256"], runner.sha256(body))


class SamplingTests(unittest.TestCase):
    def frame(self):
        return {
            "schema_version": "1.0",
            "protocol_version": "1.0",
            "manifest_schema_version": "2.0",
            "complete": True,
            "provenance": {
                "snapshot_id": "synthetic",
                "snapshot_sha256": "a" * 64,
                "reconciliation_export_sha256": "b" * 64,
                "extraction_command": "synthetic test frame",
                "extracted_at_utc": "2026-01-01T00:00:00Z",
                "unit_definition": "One source entity with its full target set",
                "exclusions": [],
            },
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

    def test_multitarget_units_remain_whole_and_census_probabilities_are_one(self):
        frame = self.frame()
        frame["units"][0]["target"] = ["urn:first", "urn:second"]
        quotas = {key: 10 for key in self.quotas()}
        result = select(frame, quotas, "seed")
        row = next(r for r in result["selected"] if r["id"] == "0")
        self.assertEqual(row["target"], ["urn:first", "urn:second"])
        self.assertEqual(row["identity_verdict"], "unreviewed")
        self.assertTrue(
            all(r["inclusion_probability"] == 1 for r in result["selected"])
        )
        self.assertEqual(len(result["selected"]), 20)

    def test_invalid_targets_versions_provenance_seed_and_quotas_are_rejected(self):
        for field, value in (
            ("schema_version", "3.0"),
            ("protocol_version", "9.0"),
            ("manifest_schema_version", "1.0"),
            ("provenance", {}),
        ):
            with self.subTest(field=field), self.assertRaises(ValueError):
                select({**self.frame(), field: value}, self.quotas(), "seed")
        for target in (None, [], "Q42", ["urn:a", "urn:a"], ["urn:a", None]):
            frame = self.frame()
            frame["units"][0]["target"] = target
            with self.subTest(target=target), self.assertRaises(ValueError):
                select(frame, self.quotas(), "seed")
        frame = self.frame()
        frame["units"][-1]["target"] = "urn:accepted"
        with self.assertRaises(ValueError):
            select(frame, self.quotas(), "seed")
        frame = self.frame()
        frame["units"][0]["method"] = "a|b"
        with self.assertRaises(ValueError):
            select(frame, self.quotas(), "seed")
        for seed in ("", " ", 1, None):
            with self.assertRaises(ValueError):
                select(self.frame(), self.quotas(), seed)
        for n in (0, -1, True, 1.5):
            with self.assertRaises(ValueError):
                select(
                    self.frame(),
                    {**self.quotas(), "synthetic|Person|authority|true": n},
                    "seed",
                )

    def test_empty_complete_frame_is_a_zero_census(self):
        result = select({**self.frame(), "units": []}, {}, "seed")
        self.assertEqual(result["strata"], [])
        self.assertEqual(result["selected"], [])

    def test_ambiguous_json_and_missing_target_sets_are_rejected(self):
        for data in ('{"x": 1, "x": 2}', '{"x": NaN}', '{"x": 1e999}'):
            with self.subTest(data=data), self.assertRaises(ValueError):
                sample_review.read_json(data)
        frame = self.frame()
        del frame["units"][-1]["target"]
        with self.assertRaises(ValueError):
            select(frame, self.quotas(), "seed")

    def test_unknown_unit_fields_are_rejected_before_sampling(self):
        for field in (
            "identity_verdict",
            "prior_reviewer_note",
            "qid_label",
            "confidence",
        ):
            frame = self.frame()
            frame["units"][0][field] = "prior judgment"
            with self.subTest(field=field), self.assertRaises(ValueError):
                select(frame, self.quotas(), "seed")

    def test_sampler_cli_archives_identity_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            frame, quotas, output = (
                root / "frame.json",
                root / "quotas.json",
                root / "sample.json",
            )
            frame.write_text(json.dumps(self.frame()))
            quotas.write_text(json.dumps(self.quotas()))
            args = [
                "--frame",
                str(frame),
                "--quotas",
                str(quotas),
                "--seed",
                "frozen",
                "--output",
                str(output),
            ]
            sample_review.main(args)
            original = output.read_bytes()
            result = json.loads(original)
            self.assertEqual(result["frame_sha256"], runner.sha256(frame.read_bytes()))
            self.assertEqual(
                result["quotas_sha256"], runner.sha256(quotas.read_bytes())
            )
            self.assertEqual(result["seed"], "frozen")
            self.assertEqual(result["manifest_schema_version"], "2.0")
            with self.assertRaises(SystemExit):
                sample_review.main(args)
            self.assertEqual(output.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
