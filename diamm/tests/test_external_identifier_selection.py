"""Source-list preservation, conservative hints and complete RDF projections."""

import csv
import json
import unittest

from rdflib import Graph, Literal
from rdflib.namespace import XSD

import test_external_identifier_text as fixtures

DIAMM, LM, WD, WDT = fixtures.DIAMM, fixtures.LM, fixtures.WD, fixtures.WDT
ROOT = fixtures.ROOT


class ExternalIdentifierSelectionTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.ExternalIdentifierTextTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)

    def extract(self, lists):
        raw = self.fixture.directory / "data/raw"
        for table in ("archives", "people"):
            (raw / table).mkdir(parents=True, exist_ok=True)
            for index, identifiers in enumerate(lists, 1):
                record = {"pk": index, "identifiers": identifiers}
                if table == "archives":
                    record.update(
                        name=f"Archive {index}",
                        siglum="",
                        city={"url": f"{DIAMM}cities/1/"},
                        sources=[{"url": f"{DIAMM}sources/1/"}] if index == 1 else [],
                    )
                else:
                    record.update(
                        full_name=f"Person {index}",
                        variant_names=[],
                        compositions=(
                            [{"url": f"{DIAMM}compositions/1/"}] if index == 1 else []
                        ),
                        related_sources=[],
                        copied_sources=[],
                    )
                (raw / table / f"{index}.json").write_text(json.dumps(record))
        self.fixture.run_script("to_csv.py")
        rows = {}
        for table in ("archives", "people"):
            with (self.fixture.csv_dir / f"{table}.csv").open(newline="") as stream:
                rows[table] = sorted(
                    csv.DictReader(stream), key=lambda row: int(row["id"])
                )
        return rows

    def test_extraction_keeps_lists_and_uses_only_unambiguous_hints(self):
        lists = [
            [
                {"label": "RISM Online", "identifier": "001"},
                {"label": "RISM Online", "identifier": "002"},
            ],
            [
                {"label": "RISM Online", "identifier": ""},
                {"label": "RISM Online", "identifier": "003"},
                {"label": "RISM Online", "identifier": None},
            ],
            [{"label": "RISM Online", "identifier": "004"}] * 2,
            [
                {"label": "VIAF", "identifier": "005"},
                {"label": "VIAF", "identifier": "006"},
                {"label": "VIAF", "identifier": ""},
            ],
            [
                {"label": "VIAF", "identifier": None},
                {"label": "viaf", "identifier": "007"},
                {"label": "VIAF", "identifier": ""},
            ],
            [{"label": "RISM Online", "identifier": " "}],
            [],
            None,
        ]
        rows = self.extract(lists)
        for table in rows:
            for i, row in enumerate(rows[table]):
                with self.subTest(table=table, index=i):
                    self.assertEqual(
                        json.loads(row.get("source_identifiers", "null")), lists[i]
                    )
                    self.assertEqual(
                        row["rism_id"], ["", "003", "004", "", "", "", "", ""][i]
                    )
                    if table == "people":
                        self.assertEqual(
                            row["viaf_id"], ["", "", "", "", "007", "", "", ""][i]
                        )
        # Reversing input order cannot select a different reconciliation hint.
        reversed_rows = self.extract(
            [list(reversed(value)) if value else value for value in lists]
        )
        for table in rows:
            for before, after in zip(rows[table], reversed_rows[table]):
                for field in fixtures.FIELDS[table]:
                    self.assertEqual(before[field], after[field])

        # The upstream field is optional: absence becomes an explicit empty list.
        for table in rows:
            path = self.fixture.directory / f"data/raw/{table}/1.json"
            record = json.loads(path.read_text())
            record.pop("identifiers")
            path.write_text(json.dumps(record))
        self.fixture.run_script("to_csv.py")
        for table in rows:
            with (self.fixture.csv_dir / f"{table}.csv").open(newline="") as stream:
                row = next(row for row in csv.DictReader(stream) if row["id"] == "1")
            self.assertEqual(row["source_identifiers"], "[]")
            for field in fixtures.FIELDS[table]:
                self.assertEqual(row[field], "")

    def test_actual_extraction_export_and_rdf_cli_keep_all_identifiers(self):
        text = '  É; "007"\nsecond line\t '
        identifiers = [
            {
                "label": "RISM Online",
                "identifier": "",
                "url": "https://example.org/blank",
            },
            {"label": "RISM Online", "identifier": "00123"},
            {"label": "rism online", "identifier": "9007199254740993"},
            {"label": "RISM Online", "identifier": text},
            {"label": "RISM Online", "identifier": "00123"},
            {"label": "VIAF", "identifier": "00042"},
            {"label": "VIAF", "identifier": "NA"},
            {"label": "VIAF", "identifier": "https://www.wikidata.org/entity/Q42"},
            {"label": "VIAF", "identifier": None},
            {
                "label": "Wikidata",
                "identifier": "Q99",
                "url": "https://example.org/Q99",
            },
        ]
        rows = self.extract([identifiers])
        rows["people"][0]["full_name_@id"] = "Q42"
        self.fixture.write_exports(rows)
        self.fixture.run_script("convert_rdf.py")
        graph = Graph().parse(
            self.fixture.directory / "data/RDF/diamm.ttl", format="turtle"
        )
        # Expected assertions are independent of production classification and hints.
        expected = self.fixture.expected_graph(self.fixture.rows_for(("",)))
        expected.update(
            {
                (DIAMM["archives/1"], WDT.P131, DIAMM["cities/1"]),
                (
                    DIAMM["people/1"],
                    LM.sourceFullName,
                    Literal("Person 1", datatype=XSD.string),
                ),
                (DIAMM["people/1"], WDT.P2888, WD.Q42),
            }
        )
        for table in rows:
            subject = DIAMM[f"{table}/1"]
            evidence = rows[table][0].get("source_identifiers", "")
            self.assertEqual(json.loads(evidence or "null"), identifiers)
            expected.add(
                (
                    subject,
                    LM.sourceIdentifiersJson,
                    Literal(evidence, datatype=XSD.string),
                )
            )
            expected.update(
                (subject, WDT.P5504, Literal(v))
                for v in ("00123", "9007199254740993", text)
            )
        expected.update(
            (DIAMM["people/1"], WDT.P214, Literal(v))
            for v in ("00042", "NA", "https://www.wikidata.org/entity/Q42")
        )
        self.fixture.assert_graph_and_roundtrip(graph, expected)
        result = graph.query(
            f'SELECT ?id WHERE {{ <{DIAMM["people/1"]}> <{WDT.P5504}> ?id }}'
        )
        self.assertEqual(
            {str(row.id) for row in result}, {"00123", "9007199254740993", text}
        )

    def test_labels_and_unexpected_values_remain_evidence_without_false_matches(self):
        identifiers = [
            {"label": "RISM", "identifier": "unreviewed-alias"},
            {"label": "Not RISM Online", "identifier": "false-rism"},
            {"label": "VIAF / RISM Online", "identifier": "ambiguous"},
            {"label": "VIAF extra", "identifier": "false-viaf"},
            {"label": " VIAF ", "identifier": "unreviewed-spaces"},
            {"label": "VIAF", "identifier": 123},
            {"label": None, "identifier": "missing-label"},
            {"label": "VIAF"},
            None,
            "unexpected",
            {"label": "VIAF", "identifier": " "},
            {"label": "RISM Online", "identifier": "Q42"},
        ]
        rows = self.extract([identifiers])
        self.assertEqual(rows["people"][0]["rism_id"], "Q42")
        self.assertEqual(rows["people"][0]["viaf_id"], "")
        self.fixture.write_exports(rows)
        graph = self.fixture.convert()
        for table in rows:
            subject = DIAMM[f"{table}/1"]
            self.assertEqual(set(graph.objects(subject, WDT.P5504)), {Literal("Q42")})
            self.assertEqual(
                json.loads(str(graph.value(subject, LM.sourceIdentifiersJson))),
                identifiers,
            )
        self.assertEqual(
            set(graph.objects(DIAMM["people/1"], WDT.P214)), {Literal(" ")}
        )
        self.assertFalse(list(graph.triples((None, WDT.P2888, None))))

    def test_legacy_fallback_and_authoritative_empty_lists(self):
        for evidence in (None, "", "[]", "null"):
            with self.subTest(evidence=evidence):
                rows = self.fixture.rows_for(("00123",))
                if evidence is not None:
                    for table in rows:
                        rows[table][0]["source_identifiers"] = evidence
                self.fixture.write_exports(rows)
                if evidence is None:
                    # Actual old CSVs lack the column altogether.
                    for table in rows:
                        path = self.fixture.reconciled / f"{table}-csv.csv"
                        with path.open(newline="") as stream:
                            reader = csv.DictReader(stream)
                            columns = [
                                c
                                for c in reader.fieldnames
                                if c != "source_identifiers"
                            ]
                            data = list(reader)
                        with path.open("w", newline="") as stream:
                            writer = csv.DictWriter(
                                stream, columns, extrasaction="ignore"
                            )
                            writer.writeheader()
                            writer.writerows(data)
                expected = self.fixture.expected_graph(
                    rows if not evidence else self.fixture.rows_for(("",))
                )
                if evidence:
                    for table in rows:
                        expected.add(
                            (
                                DIAMM[f"{table}/1"],
                                LM.sourceIdentifiersJson,
                                Literal(evidence, datatype=XSD.string),
                            )
                        )
                self.fixture.assert_graph_and_roundtrip(
                    self.fixture.convert(), expected
                )

    def test_malformed_evidence_fails_instead_of_silently_using_stale_hints(self):
        for value in ('[{"label":', "{}", '"00123"', "123"):
            with self.subTest(value=value):
                rows = self.fixture.rows_for(("stale-hint",))
                rows["people"][0]["source_identifiers"] = value
                self.fixture.write_exports(rows)
                with self.assertRaisesRegex(ValueError, "source_identifiers.*people/1"):
                    self.fixture.convert()

    def test_duplicate_and_conflicting_rows_preserve_evidence_and_values(self):
        rows = self.fixture.rows_for(("stale-hint",))
        for table in rows:
            first = rows[table][0]
            first["source_identifiers"] = '[{"label":"RISM Online","identifier":"001"}]'
            second = {
                **first,
                "source_identifiers": '[{"label":"RISM Online","identifier":"002"}]',
            }
            rows[table].extend([dict(first), second])
        self.fixture.write_exports(rows)
        expected = self.fixture.expected_graph(self.fixture.rows_for(("",)))
        for table in rows:
            subject = DIAMM[f"{table}/1"]
            expected.update((subject, WDT.P5504, Literal(v)) for v in ("001", "002"))
            expected.update(
                (
                    subject,
                    LM.sourceIdentifiersJson,
                    Literal(row["source_identifiers"], datatype=XSD.string),
                )
                for row in rows[table]
            )
        self.fixture.assert_graph_and_roundtrip(self.fixture.convert(), expected)
        for table in rows:
            rows[table].reverse()
        self.fixture.write_exports(rows)
        self.assertEqual(set(self.fixture.convert()), expected)

    def test_exports_keep_evidence_and_histories_only_use_scalar_hints(self):
        for table in ("archives", "people"):
            template = json.loads(
                (ROOT / f"openrefine/export/{table}_export.json").read_text()
            )
            self.assertEqual(template["columns"][-1]["name"], "source_identifiers")
            self.assertEqual(
                template["columns"][-1]["reconSettings"]["output"], "entity-name"
            )
            self.assertFalse(
                template["columns"][-1]["reconSettings"]["blankUnmatchedCells"]
            )
            history = json.loads(
                (ROOT / f"openrefine/history/{table}_history.json").read_text()
            )
            for operation in history:
                self.assertNotIn(
                    operation["op"], {"core/column-removal", "core/column-reorder"}
                )
                self.assertNotIn("source_identifiers", json.dumps(operation))


if __name__ == "__main__":
    unittest.main()
