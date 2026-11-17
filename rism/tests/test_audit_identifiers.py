"""Evidence and failure boundaries for the optional RISM audit CLI."""

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from rdflib import Dataset, Literal, URIRef

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import audit_identifiers as audit


class AuditTests(unittest.TestCase):
    def response(self):
        values = [
            ("uri", "https://wikidata.org/wiki/Q1339"),
            ("uri", "http://www.wikidata.org/entity/Q1339"),
            ("uri", "https://www.wikidata.org/entity/Q1339#label"),
            ("literal", "https://wikidata.org/wiki/Q1339"),
            ("uri", "https://rism.online/people/1"),
        ]
        return {
            "head": {"vars": ["s", "p", "o"]},
            "results": {
                "bindings": [
                    {
                        "s": {"type": "uri", "value": "urn:source"},
                        "p": {"type": "uri", "value": str(audit.WDT.P2888)},
                        "o": {"type": kind, "value": value},
                    }
                    for kind, value in values
                ]
            },
        }

    def test_saved_response_preserves_bytes_and_distinguishes_literal_terms(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(
            audit, "execute_remote"
        ) as remote:
            root = Path(directory)
            original = json.dumps(self.response(), indent=4).encode() + b"\n"
            source = root / "input.json"
            source.write_bytes(original)
            output = root / "audit"
            self.assertEqual(
                audit.main(["--response", str(source), "--output-dir", str(output)]), 0
            )
            report = json.loads((output / "report.json").read_text())
            self.assertEqual(report["rows"], 5)
            self.assertEqual(report["would_normalize"], 1)
            self.assertEqual(report["other_terms"], 3)
            self.assertIsNone(report["graph"])
            self.assertEqual(report["row_cap_reached"], "not_established")
            self.assertFalse(report["request_attempted"])
            self.assertEqual((output / "response.json").read_bytes(), original)
            self.assertEqual(source.read_bytes(), original)
            remote.assert_not_called()

    def test_row_cap_is_known_only_for_the_query_this_run_issued(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "input.json"
            body = json.dumps(self.response()).encode()
            source.write_bytes(body)
            for saved in (False, True):
                for limit in (5, 6):
                    with self.subTest(saved=saved, limit=limit), patch.object(
                        audit,
                        "execute_remote",
                        return_value=(
                            {"status": "ok", "result": self.response()},
                            body,
                        ),
                    ) as remote:
                        output = root / f"audit-{saved}-{limit}"
                        args = (
                            ["--response", str(source)]
                            if saved
                            else ["--endpoint", "https://example.org/sparql"]
                        )
                        self.assertEqual(
                            audit.main(
                                args
                                + ["--limit", str(limit), "--output-dir", str(output)]
                            ),
                            0,
                        )
                        report = json.loads((output / "report.json").read_text())
                        self.assertEqual(
                            report["row_cap_reached"],
                            "not_established" if saved else limit == 5,
                        )
                        self.assertEqual(remote.call_count, 0 if saved else 1)

    def test_missing_source_or_existing_output_never_makes_a_request(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(
            audit, "execute_remote"
        ) as remote:
            output = Path(directory) / "existing"
            output.mkdir()
            marker = output / "report.json"
            marker.write_text("preserve")
            for args in (
                ["--output-dir", str(output)],
                [
                    "--endpoint",
                    "https://example.org/sparql",
                    "--output-dir",
                    str(output),
                ],
            ):
                with self.assertRaises(SystemExit):
                    audit.main(args)
            self.assertEqual(marker.read_text(), "preserve")
            remote.assert_not_called()

    def test_invalid_responses_remain_archived_failures(self):
        unbound = self.response()
        del unbound["results"]["bindings"][0]["o"]
        for body in (b"broken", b'{"boolean":true}', json.dumps(unbound).encode()):
            with self.subTest(body=body), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                source = root / "input.json"
                source.write_bytes(body)
                output = root / "audit"
                self.assertEqual(
                    audit.main(
                        ["--response", str(source), "--output-dir", str(output)]
                    ),
                    1,
                )
                report = json.loads((output / "report.json").read_text())
                self.assertEqual(report["status"], "invalid_response")
                self.assertNotIn("would_normalize", report)
                self.assertEqual((output / "response.json").read_bytes(), body)

    def test_remote_failures_and_partial_results_are_not_successful_empty_answers(self):
        for status in ("timeout", "endpoint_error", "partial"):
            execution = {
                "status": status,
                "request_attempted": True,
                "http_status": 200,
                "headers": {"server": "synthetic"},
            }
            if status == "partial":
                execution["result"] = self.response()
            with self.subTest(
                status=status
            ), tempfile.TemporaryDirectory() as directory, patch.object(
                audit, "execute_remote", return_value=(execution, b"partial evidence")
            ) as remote:
                output = Path(directory) / "audit"
                self.assertEqual(
                    audit.main(
                        [
                            "--endpoint",
                            "https://example.org/sparql",
                            "--output-dir",
                            str(output),
                        ]
                    ),
                    1,
                )
                report = json.loads((output / "report.json").read_text())
                self.assertEqual(report["status"], status)
                self.assertEqual(report["http_status"], 200)
                self.assertEqual(
                    (output / "response.json").read_bytes(), b"partial evidence"
                )
                remote.assert_called_once()

    def test_noncanonical_query_rejects_complete_canonical_items_only(self):
        dataset = Dataset(default_union=False)
        graph = dataset.graph(URIRef(audit.GRAPH))
        values = [
            URIRef("http://www.wikidata.org/entity/Q1339"),
            URIRef("http://www.wikidata.org/entity/Q1339#label"),
            URIRef("https://wikidata.org/wiki/Q1339"),
            Literal("https://wikidata.org/wiki/Q1339"),
        ]
        for value in values:
            graph.add((URIRef("urn:source"), audit.WDT.P2888, value))
        rows = list(dataset.query(audit.sample_query(200, True)))
        self.assertEqual({row.o for row in rows}, set(values[1:3]))


if __name__ == "__main__":
    unittest.main()
