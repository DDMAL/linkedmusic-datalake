"""Geographic name fidelity through extraction, tracked CSV layouts and RDF."""

import csv
import json
import unittest

from rdflib import Graph, Literal, RDF, RDFS

import test_external_identifier_text as fixtures

DIAMM, LM, WD, WDT = fixtures.DIAMM, fixtures.LM, fixtures.WD, fixtures.WDT
ROOT = fixtures.ROOT
TABLES = {"cities": LM.City, "countries": LM.Country, "regions": LM.Region}


class GeographicNameTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.ExternalIdentifierTextTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.relations.write_text(
            "key1,key2,type\narchive:1,city:1,\ncity:1,country:1,\n"
            "city:1,region:1,\ncountry:1,region:1,\ncity:1,source:1,\n"
            "city:1,organization:1,\ncountry:1,organization:2,\n"
        )
        # Explicit expected directions and local endpoints, independent of
        # DIAMM_SCHEMA and the converter's relationship branches.
        self.links = {
            (DIAMM["archives/1"], WDT.P131, DIAMM["cities/1"]),
            (DIAMM["cities/1"], WDT.P17, DIAMM["countries/1"]),
            (DIAMM["cities/1"], WDT.P131, DIAMM["regions/1"]),
            (DIAMM["regions/1"], WDT.P17, DIAMM["countries/1"]),
            (DIAMM["sources/1"], WDT.P131, DIAMM["cities/1"]),
            (DIAMM["organizations/1"], WDT.P131, DIAMM["cities/1"]),
            (DIAMM["organizations/2"], WDT.P17, DIAMM["countries/1"]),
        }

    def rows_for(self, values):
        return {
            table: [{"id": str(i), "name": value} for i, value in enumerate(values, 1)]
            for table in TABLES
        }

    def expected_graph(self, rows):
        expected = set(self.links)
        for table, kind in TABLES.items():
            for row in rows[table]:
                subject = DIAMM[f"{table}/{row['id']}"]
                expected.add((subject, RDF.type, kind))
                if row.get("name"):
                    expected.add((subject, RDFS.label, Literal(row["name"])))
        return expected

    def convert(self, rows):
        self.fixture.write_exports(rows)
        return self.fixture.convert()

    def test_numeric_only_columns_keep_zeros_precision_and_spelling(self):
        # Other text in the column would mask pandas' numeric inference.
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

    def test_na_like_unicode_and_id_like_names_remain_literal(self):
        rows = self.rows_for(
            (
                "NA",
                "N/A",
                "nan",
                "None",
                "null",
                "#N/A",
                "Q42",
                "https://www.wikidata.org/entity/Q42",
                '  Île, "É"\nline\t ',
                "Place (historic name)",
                " ",
            )
        )
        expected = self.expected_graph(rows)
        for table in TABLES:
            rows[table][0]["name_@id"] = "Q43"
            for row, candidate in zip(
                rows[table][1:],
                (
                    "Q42suffix",
                    "Q42 / Q43",
                    "https://www.wikidata.org/entity/Q42",
                    "Q042",
                    "Q４２",
                ),
            ):
                row["name_@id"] = candidate
            expected.add((DIAMM[f"{table}/1"], WDT.P2888, WD.Q43))
        self.fixture.assert_graph_and_roundtrip(self.convert(rows), expected)

    def test_empty_names_omit_labels_but_keep_subjects_matches_and_links(self):
        rows = self.rows_for(("", None))
        expected = self.expected_graph(rows)
        for table in TABLES:
            rows[table].append({"id": "3"})
            rows[table][0]["name_@id"] = "Q42"
            expected.update(
                {
                    (DIAMM[f"{table}/1"], WDT.P2888, WD.Q42),
                    (DIAMM[f"{table}/3"], RDF.type, TABLES[table]),
                }
            )
        self.fixture.assert_graph_and_roundtrip(self.convert(rows), expected)

    def test_country_hints_do_not_supply_labels_or_relationships(self):
        rows = self.rows_for(("", "Local name"))
        for table in ("cities", "regions"):
            for row in rows[table]:
                row.update({"country": "Hint only", "country_@id": "Q999"})
        self.fixture.assert_graph_and_roundtrip(
            self.convert(rows), self.expected_graph(rows)
        )
        # Removing the source relations must not promote a hint to P17.
        self.fixture.relations.write_text("key1,key2,type\n")
        self.links.clear()
        self.fixture.assert_graph_and_roundtrip(
            self.convert(rows), self.expected_graph(rows)
        )

    def test_conflicting_rows_keep_all_names_and_supplied_matches(self):
        rows = self.rows_for(("00123", "NA", "00123", ""))
        for table in TABLES:
            for row in rows[table]:
                row["id"] = "1"
            rows[table][0]["name_@id"] = "Q42"
            rows[table][1]["name_@id"] = "Q43"
        expected = self.expected_graph(rows)
        for table in TABLES:
            expected.update(
                {
                    (DIAMM[f"{table}/1"], WDT.P2888, WD.Q42),
                    (DIAMM[f"{table}/1"], WDT.P2888, WD.Q43),
                }
            )
        self.fixture.assert_graph_and_roundtrip(self.convert(rows), expected)

    def test_extraction_export_and_rdf_cli_preserve_names_and_source_links(self):
        values = (
            "00123",
            "9007199254740993",
            "NA",
            "None",
            "Q42",
            "https://www.wikidata.org/entity/Q42",
            '  Île, "É"\nline\t ',
            "Place (historic name)",
            " ",
            "",
            None,
        )
        for table in TABLES:
            raw = self.fixture.directory / "data/raw" / table
            raw.mkdir(parents=True)
            for i, value in enumerate(values, 1):
                record = {"pk": i, "name": value}
                if table == "cities":
                    record.update(
                        {
                            "country": {"url": f"{DIAMM}countries/1/", "name": "NA"},
                            "archives": [{"url": f"{DIAMM}archives/1/"}],
                            "provenance": [{"url": f"{DIAMM}sources/1/"}],
                            "organizations": [{"url": f"{DIAMM}organizations/1/"}],
                        }
                    )
                elif table == "countries":
                    record.update(
                        {
                            "cities": [],
                            "regions": [{"url": f"{DIAMM}regions/{i}/"}],
                            "states": [{"url": f"{DIAMM}regions/{i}/"}],
                        }
                    )
                else:
                    record.update(
                        {
                            "parent": "00123",
                            "organizations": [],
                            "provenance": [],
                            "cities": [{"url": f"{DIAMM}cities/{i}/"}],
                        }
                    )
                (raw / f"{i}.json").write_text(json.dumps(record), encoding="utf-8")
        self.fixture.run_script("to_csv.py")
        rows = {}
        for table in TABLES:
            with (self.fixture.csv_dir / f"{table}.csv").open(
                newline="", encoding="utf-8"
            ) as source:
                rows[table] = sorted(
                    csv.DictReader(source), key=lambda row: int(row["id"])
                )
            self.assertEqual(len(rows[table]), len(values))
            for row, value in zip(rows[table], values):
                self.assertEqual(row["name"], value if value is not None else "")
                if table in ("cities", "regions"):
                    self.assertEqual(
                        row["country"], "NA" if table == "cities" else "00123"
                    )
                    row["country_@id"] = "Q999"  # deliberately unrelated hint
                # Supplied matches, unmatched text and parenthesis removal on
                # the copied name only; no OpenRefine/service replay is claimed.
                row["name_@id"] = (
                    "Q43" if row["id"] == "1" else row["name"].split(" (")[0]
                )
        self.links = set()
        for i in range(1, len(values) + 1):
            self.links.update(
                {
                    (DIAMM["archives/1"], WDT.P131, DIAMM[f"cities/{i}"]),
                    (DIAMM["sources/1"], WDT.P131, DIAMM[f"cities/{i}"]),
                    (DIAMM["organizations/1"], WDT.P131, DIAMM[f"cities/{i}"]),
                    (DIAMM[f"cities/{i}"], WDT.P17, DIAMM["countries/1"]),
                    (DIAMM[f"cities/{i}"], WDT.P131, DIAMM[f"regions/{i}"]),
                    (DIAMM[f"regions/{i}"], WDT.P17, DIAMM[f"countries/{i}"]),
                }
            )
        self.fixture.write_exports(rows)
        self.fixture.run_script("convert_rdf.py")
        graph = Graph().parse(
            self.fixture.directory / "data/RDF/diamm.ttl", format="turtle"
        )
        expected = self.expected_graph(rows)
        for table in TABLES:
            expected.update(
                {
                    (DIAMM[f"{table}/1"], WDT.P2888, WD.Q43),
                    # Existing unmatched-QID export ambiguity is outside this fix.
                    (DIAMM[f"{table}/5"], WDT.P2888, WD.Q42),
                }
            )
        self.fixture.assert_graph_and_roundtrip(graph, expected)
        result = graph.query(f"""
            SELECT ?source ?city ?region ?country ?match WHERE {{
              ?source <{WDT.P131}> ?city .
              ?city <{RDFS.label}> "00123"; <{WDT.P2888}> ?match;
                    <{WDT.P131}> ?region; <{WDT.P17}> ?country .
              ?region <{RDFS.label}> "00123"; <{WDT.P17}> ?country .
              ?country <{RDFS.label}> "00123" .
              VALUES ?source {{ <{DIAMM['sources/1']}> }}
            }}
        """)
        self.assertEqual(
            {tuple(row) for row in result},
            {
                (
                    DIAMM["sources/1"],
                    DIAMM["cities/1"],
                    DIAMM["regions/1"],
                    DIAMM["countries/1"],
                    WD.Q43,
                )
            },
        )

    def test_histories_and_exports_preserve_original_names(self):
        for table in TABLES:
            with self.subTest(table=table):
                template = json.loads(
                    (ROOT / f"openrefine/export/{table}_export.json").read_text()
                )
                columns = {c["name"]: c for c in template["columns"]}
                self.assertEqual(
                    columns["name"]["reconSettings"]["output"], "entity-name"
                )
                self.assertFalse(
                    columns["name"]["reconSettings"]["blankUnmatchedCells"]
                )
                self.assertEqual(
                    columns["name_@id"]["reconSettings"]["output"], "entity-id"
                )
                self.assertFalse(
                    columns["name_@id"]["reconSettings"]["blankUnmatchedCells"]
                )
                history = json.loads(
                    (ROOT / f"openrefine/history/{table}_history.json").read_text()
                )
                copies = [op for op in history if op.get("newColumnName") == "name_@id"]
                self.assertEqual(len(copies), 1)
                self.assertEqual(copies[0]["baseColumnName"], "name")
                # The region history has a pre-existing judgment facet on
                # this copy. Its replay behavior needs separate validation;
                # original name preservation does not imply match coverage.
                if table != "regions":
                    self.assertEqual(copies[0]["engineConfig"]["facets"], [])
                self.assertEqual(
                    copies[0]["expression"],
                    (
                        "grel:value"
                        if table == "countries"
                        else 'grel:value.replace(/(.*?)(?: \\(.*\\))?/, "$1")'
                    ),
                )
                for op in history:
                    self.assertNotIn(op.get("columnName"), {"name", "country"})
                    self.assertNotIn(op.get("newColumnName"), {"name", "country"})
                    self.assertNotIn(
                        op["op"], {"core/column-removal", "core/column-reorder"}
                    )


if __name__ == "__main__":
    unittest.main()
