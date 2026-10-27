"""Preserve selected DIAMM RISM/VIAF text through real CSV loading and CLIs."""

import contextlib
import csv
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from rdflib import Graph, Literal, Namespace, RDF, RDFS
from rdflib.namespace import XSD

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from convert_rdf import build_rdf_graph

DIAMM = Namespace("https://www.diamm.ac.uk/")
LM = Namespace("https://linkedmusic.ca/graphs/diamm/")
WD = Namespace("http://www.wikidata.org/entity/")
WDT = Namespace("http://www.wikidata.org/prop/direct/")
FIELDS = {"archives": ("rism_id",), "people": ("rism_id", "viaf_id")}


class ExternalIdentifierTextTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="diamm-external-ids-")
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.src = self.directory / "src"
        self.src.mkdir()
        (self.src / "relations.json").write_text(
            (ROOT / "src/relations.json").read_text()
        )
        self.reconciled = self.directory / "data/reconciled"
        self.reconciled.mkdir(parents=True)
        self.csv_dir = self.directory / "data/csv"
        self.csv_dir.mkdir()
        self.relations = self.csv_dir / "relations.csv"
        self.relations.write_text(
            "key1,key2,type\narchive:1,source:1,\ncomposition:1,people:1,\n"
        )

    def write_exports(self, rows):
        # Apply the tracked column selection to synthetic rows. This does not
        # replay OpenRefine or contact a reconciliation service.
        for template in (ROOT / "openrefine/export").glob("*_export.json"):
            table = template.stem.removesuffix("_export")
            columns = [c["name"] for c in json.loads(template.read_text())["columns"]]
            with (self.reconciled / f"{table}-csv.csv").open(
                "w", newline="", encoding="utf-8"
            ) as target:
                writer = csv.DictWriter(target, fieldnames=columns)
                writer.writeheader()
                for row in rows.get(table, []):
                    writer.writerow({column: row.get(column, "") for column in columns})

    def rows_for(self, values):
        return {
            "archives": [
                {"id": str(i), "name": f"Archive {i}", "rism_id": value}
                for i, value in enumerate(values, 1)
            ],
            "people": [
                {
                    "id": str(i),
                    "full_name": f"Person {i}",
                    "rism_id": value,
                    "viaf_id": viaf,
                }
                for i, (value, viaf) in enumerate(zip(values, reversed(values)), 1)
            ],
        }

    def expected_graph(self, rows):
        # Specify predicates and source subjects independently of DIAMM_SCHEMA.
        expected = {
            (DIAMM["sources/1"], WDT.P276, DIAMM["archives/1"]),
            (DIAMM["compositions/1"], WDT.P86, DIAMM["people/1"]),
        }
        for table, kind, name in (
            ("archives", LM.Archive, "name"),
            ("people", LM.Person, "full_name"),
        ):
            for row in rows[table]:
                subject = DIAMM[f"{table}/{row['id']}"]
                expected.add((subject, RDF.type, kind))
                expected.add((subject, RDFS.label, Literal(row[name])))
                for field, predicate in (("rism_id", WDT.P5504), ("viaf_id", WDT.P214)):
                    if row.get(field):
                        expected.add((subject, predicate, Literal(row[field])))
        return expected

    def convert(self):
        with contextlib.redirect_stdout(io.StringIO()):
            return build_rdf_graph(
                self.reconciled, self.relations, self.src / "relations.json"
            )

    def assert_graph_and_roundtrip(self, graph, expected):
        self.assertEqual(set(graph), expected)
        restored = Graph().parse(data=graph.serialize(format="turtle"), format="turtle")
        self.assertEqual(set(restored), expected)

    def run_script(self, script):
        result = subprocess.run(
            [sys.executable, str(ROOT / "src" / script)],
            cwd=self.src,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_numeric_columns_keep_zeros_precision_and_skip_empty_cells(self):
        # Separate numeric-only columns are essential: punctuation elsewhere
        # in a column can mask pandas' numeric inference and precision loss.
        for values in (
            ("00123", "00007"),
            ("00123", "9007199254740993", ""),
            ("000123456789012345678901234567890123456789", ""),
            ("0", ""),
            ("", ""),
        ):
            with self.subTest(values=values):
                rows = self.rows_for(values)
                self.write_exports(rows)
                self.assert_graph_and_roundtrip(
                    self.convert(), self.expected_graph(rows)
                )

    def test_na_like_punctuated_and_id_like_text_stays_literal(self):
        rows = self.rows_for(
            (
                "NA",
                "N/A",
                "nan",
                "None",
                "null",
                "#N/A",
                "123.0",
                "1e3",
                "+0012",
                "people/0000123",
                "A/B:001-02?",
                '  É, "007"\nsecond line\t ',
                " ",
                "Q42",
                "https://www.wikidata.org/entity/Q42",
                "",
            )
        )
        self.write_exports(rows)
        graph = self.convert()
        self.assert_graph_and_roundtrip(graph, self.expected_graph(rows))
        self.assertEqual(list(graph.triples((None, WDT.P2888, None))), [])

    def test_duplicate_and_conflicting_rows_keep_supplied_identifier_values(self):
        rows = self.rows_for(("00123", "00456"))
        for table in FIELDS:
            rows[table][1]["id"] = "1"
            name = "name" if table == "archives" else "full_name"
            rows[table][1][name] = rows[table][0][name]
            rows[table].append(dict(rows[table][0]))
        self.write_exports(rows)
        self.assert_graph_and_roundtrip(self.convert(), self.expected_graph(rows))

    def test_json_extraction_export_and_rdf_cli_preserve_identifier_strings(self):
        raw = self.directory / "data/raw"
        for table in FIELDS:
            (raw / table).mkdir(parents=True)
        values = ("00123", "9007199254740993", "", None)
        for i, value in enumerate(values, 1):
            # Empty list, explicit null and empty string are all absent IDs.
            identifiers = (
                [] if i == 3 else [{"label": "RISM Online", "identifier": value}]
            )
            archive = {
                "pk": i,
                "name": f"Archive {i}",
                "siglum": "",
                "identifiers": identifiers,
                "sources": [{"url": f"{DIAMM}sources/1/"}] if i == 1 else [],
                "city": {"url": f"{DIAMM}cities/1/"},
            }
            person = {
                "pk": i,
                "full_name": f"Person {i}",
                "variant_names": [],
                "identifiers": identifiers + [{"label": "VIAF", "identifier": value}],
                "compositions": [{"url": f"{DIAMM}compositions/1/"}] if i == 1 else [],
                "related_sources": [],
                "copied_sources": [],
            }
            for table, record in (("archives", archive), ("people", person)):
                (raw / table / f"{i}.json").write_text(
                    json.dumps(record), encoding="utf-8"
                )
        self.run_script("to_csv.py")
        rows = {}
        for table in FIELDS:
            with (self.csv_dir / f"{table}.csv").open(
                newline="", encoding="utf-8"
            ) as source:
                rows[table] = list(csv.DictReader(source))
            for row in rows[table]:
                value = values[int(row["id"]) - 1] or ""
                for field in FIELDS[table]:
                    self.assertEqual(row[field], value)
        # One supplied match demonstrates independence from external-ID text.
        next(row for row in rows["people"] if row["id"] == "1")["full_name_@id"] = "Q42"
        self.write_exports(rows)
        self.run_script("convert_rdf.py")
        graph = Graph().parse(self.directory / "data/RDF/diamm.ttl", format="turtle")
        expected = self.expected_graph(rows)
        expected.add((DIAMM["people/1"], WDT.P2888, WD.Q42))
        for i in range(1, len(values) + 1):
            expected.add((DIAMM[f"archives/{i}"], WDT.P131, DIAMM["cities/1"]))
            expected.add(
                (
                    DIAMM[f"people/{i}"],
                    LM.sourceFullName,
                    Literal(f"Person {i}", datatype=XSD.string),
                )
            )
        self.assertEqual(set(graph), expected)
        matches = graph.query(f"""
            SELECT ?person WHERE {{
              ?person a <{LM.Person}>; <{WDT.P214}> "00123" .
            }}
        """)
        self.assertEqual({row.person for row in matches}, {DIAMM["people/1"]})

    def test_export_and_history_keep_external_identifier_columns_as_text(self):
        for table, fields in FIELDS.items():
            with self.subTest(table=table):
                template = json.loads(
                    (ROOT / f"openrefine/export/{table}_export.json").read_text()
                )
                columns = {c["name"]: c for c in template["columns"]}
                for field in fields:
                    self.assertEqual(
                        columns[field]["reconSettings"]["output"], "entity-name"
                    )
                    self.assertFalse(
                        columns[field]["reconSettings"]["blankUnmatchedCells"]
                    )
                history = json.loads(
                    (ROOT / f"openrefine/history/{table}_history.json").read_text()
                )
                for operation in history:
                    # Using IDs as reconciliation hints does not edit them.
                    self.assertNotIn(operation.get("columnName"), fields)
                    self.assertNotIn(operation.get("newColumnName"), fields)
                    self.assertNotIn(
                        operation["op"], {"core/column-removal", "core/column-reorder"}
                    )


if __name__ == "__main__":
    unittest.main()
