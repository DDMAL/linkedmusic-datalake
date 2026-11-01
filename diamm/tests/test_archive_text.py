"""Archive name/siglum fidelity through extraction, CSV loading and RDF."""

import csv
import json
import unittest

from rdflib import Graph, Literal, RDF, RDFS
from rdflib.namespace import XSD

import test_external_identifier_text as fixtures

DIAMM, LM, WD, WDT = fixtures.DIAMM, fixtures.LM, fixtures.WD, fixtures.WDT
ROOT = fixtures.ROOT


class ArchiveTextTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.ExternalIdentifierTextTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.relations.write_text(
            "key1,key2,type\narchive:1,city:1,\narchive:1,source:1,\n"
        )

    def rows_for(self, values):
        return [
            {"id": str(i), "name": value, "siglum": siglum}
            for i, (value, siglum) in enumerate(zip(values, reversed(values)), 1)
        ]

    def expected_graph(self, rows):
        # The expected vocabulary and local subjects are independent of the
        # converter's mappings. Matches are added explicitly by each test.
        expected = {
            (DIAMM["archives/1"], WDT.P131, DIAMM["cities/1"]),
            (DIAMM["sources/1"], WDT.P276, DIAMM["archives/1"]),
        }
        for row in rows:
            subject = DIAMM[f"archives/{row['id']}"]
            expected.add((subject, RDF.type, LM.Archive))
            for field, predicate in (("name", RDFS.label), ("siglum", WDT.P11550)):
                if row.get(field):
                    expected.add((subject, predicate, Literal(row[field])))
        return expected

    def convert(self, rows):
        self.fixture.write_exports({"archives": rows})
        return self.fixture.convert()

    def test_numeric_columns_preserve_zeros_precision_and_lexical_forms(self):
        # Use separate numeric-only columns: ordinary text masks inference.
        for values in (
            ("00123", "00007"),
            ("00123", "9007199254740993", ""),
            ("000123456789012345678901234567890123456789", ""),
            ("0", ""),
            ("1e3", "+0012", "123.0", ""),
        ):
            with self.subTest(values=values):
                rows = self.rows_for(values)
                self.fixture.assert_graph_and_roundtrip(
                    self.convert(rows), self.expected_graph(rows)
                )

    def test_na_like_and_id_like_text_and_supplied_matches_are_independent(self):
        rows = self.rows_for(
            (
                "NA",
                "N/A",
                "nan",
                "None",
                "null",
                "#N/A",
                '  Bibliothèque, "É"\nsecond line\t ',
                "Q42",
                "https://www.wikidata.org/entity/Q42",
                "GB-Lbl",
                " ",
            )
        )
        # Only the dedicated match column supplies P2888. Invalid candidates
        # remain rejected even when names/sigla happen to look like IDs.
        rows[0]["name_@id"] = "Q42"
        rows[1]["name_@id"] = "Q42suffix"
        rows[2]["name_@id"] = "https://www.wikidata.org/entity/Q42"
        rows[3]["name_@id"] = "Q42 / Q43"
        expected = self.expected_graph(rows)
        expected.add((DIAMM["archives/1"], WDT.P2888, WD.Q42))
        self.fixture.assert_graph_and_roundtrip(self.convert(rows), expected)

    def test_empty_cells_omit_labels_and_sigla_without_inventing_fallbacks(self):
        rows = [
            {"id": "1", "name": "", "siglum": "", "name_@id": "Q42"},
            {"id": "2", "name": None, "siglum": None, "rism_id": "00123"},
            {"id": "3"},
        ]
        expected = self.expected_graph(rows)
        expected.add((DIAMM["archives/1"], WDT.P2888, WD.Q42))
        expected.add((DIAMM["archives/2"], WDT.P5504, Literal("00123")))
        self.fixture.assert_graph_and_roundtrip(self.convert(rows), expected)

    def test_duplicate_and_conflicting_rows_keep_all_supplied_text(self):
        rows = [
            {"id": "1", "name": "00123", "siglum": "001"},
            {"id": "1", "name": "NA", "siglum": "002"},
            {"id": "1", "name": "00123", "siglum": "001"},
            {"id": "1", "name": "", "siglum": ""},
        ]
        self.fixture.assert_graph_and_roundtrip(
            self.convert(rows), self.expected_graph(rows)
        )

    def test_json_extraction_export_and_rdf_cli_preserve_archive_text(self):
        raw = self.fixture.directory / "data/raw/archives"
        raw.mkdir(parents=True)
        values = (
            "00123",
            "9007199254740993",
            "NA",
            "None",
            '  Bibliothèque, "É"\nsecond line\t ',
            "Q42",
            "https://www.wikidata.org/entity/Q42",
            " ",
            "",
            None,
        )
        for i, value in enumerate(values, 1):
            record = {
                "pk": i,
                "name": value,
                "siglum": value,
                "identifiers": [],
                "city": {"url": f"{DIAMM}cities/1/"},
                "sources": [{"url": f"{DIAMM}sources/1/"}] if i == 1 else [],
            }
            (raw / f"{i}.json").write_text(json.dumps(record), encoding="utf-8")
        self.fixture.run_script("to_csv.py")
        with (self.fixture.csv_dir / "archives.csv").open(
            newline="", encoding="utf-8"
        ) as source:
            rows = sorted(csv.DictReader(source), key=lambda row: int(row["id"]))
        self.assertEqual(len(rows), len(values))
        for row, value in zip(rows, values):
            self.assertEqual(row["name"], value if value is not None else "")
            self.assertEqual(row["siglum"], value if value is not None else "")
            # Simulate the tracked copy operation for unmatched rows. A whole
            # QID in that copy still meets the existing ID-only validation;
            # this task does not claim verification of reconciliation identity.
            row["name_@id"] = "Q43" if row["id"] == "1" else row["name"]
        self.fixture.write_exports({"archives": rows})
        self.fixture.run_script("convert_rdf.py")
        graph = Graph().parse(
            self.fixture.directory / "data/RDF/diamm.ttl", format="turtle"
        )
        expected = self.expected_graph(rows)
        expected.update(
            {
                (DIAMM["archives/1"], WDT.P2888, WD.Q43),
                (DIAMM["archives/6"], WDT.P2888, WD.Q42),
            }
        )
        for i in range(1, len(values) + 1):
            subject = DIAMM[f"archives/{i}"]
            expected.add((subject, WDT.P131, DIAMM["cities/1"]))
            expected.add(
                (subject, LM.sourceIdentifiersJson, Literal("[]", datatype=XSD.string))
            )
        self.fixture.assert_graph_and_roundtrip(graph, expected)
        result = graph.query(f"""
            SELECT ?archive ?match ?source WHERE {{
              ?archive a <{LM.Archive}>;
                       <{RDFS.label}> "00123";
                       <{WDT.P11550}> "00123";
                       <{WDT.P2888}> ?match;
                       <{WDT.P131}> <{DIAMM['cities/1']}> .
              ?source <{WDT.P276}> ?archive .
            }}
        """)
        self.assertEqual(
            {tuple(row) for row in result},
            {(DIAMM["archives/1"], WD.Q43, DIAMM["sources/1"])},
        )

    def test_export_and_history_keep_original_names_and_sigla(self):
        template = json.loads(
            (ROOT / "openrefine/export/archives_export.json").read_text()
        )
        columns = {column["name"]: column for column in template["columns"]}
        for field in ("name", "siglum"):
            self.assertEqual(columns[field]["reconSettings"]["output"], "entity-name")
            self.assertFalse(columns[field]["reconSettings"]["blankUnmatchedCells"])
        self.assertEqual(columns["name_@id"]["reconSettings"]["output"], "entity-id")
        history = json.loads(
            (ROOT / "openrefine/history/archives_history.json").read_text()
        )
        self.assertEqual(history[0]["op"], "core/column-addition")
        self.assertEqual(history[0]["baseColumnName"], "name")
        self.assertEqual(history[0]["expression"], "grel:value")
        self.assertEqual(history[0]["newColumnName"], "name_@id")
        self.assertEqual(history[0]["engineConfig"]["facets"], [])
        for operation in history:
            self.assertNotIn(operation.get("columnName"), {"name", "siglum"})
            self.assertNotIn(operation.get("newColumnName"), {"name", "siglum"})
            self.assertNotIn(
                operation["op"], {"core/column-removal", "core/column-reorder"}
            )


if __name__ == "__main__":
    unittest.main()
