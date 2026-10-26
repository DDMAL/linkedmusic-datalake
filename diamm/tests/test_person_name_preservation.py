"""Preserve source person text through extraction, export and RDF conversion."""

import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from rdflib import Graph, Literal, Namespace, RDF, RDFS
from rdflib.namespace import XSD

ROOT = Path(__file__).resolve().parents[1]
DIAMM = Namespace("https://www.diamm.ac.uk/")
LM = Namespace("https://linkedmusic.ca/graphs/diamm/")
WD = Namespace("http://www.wikidata.org/entity/")
WDT = Namespace("http://www.wikidata.org/prop/direct/")
LEGACY_COLUMNS = [
    "id",
    "full_name",
    "full_name_@id",
    "variant_names",
    "earliest_year",
    "earliest_year_@id",
    "latest_year",
    "latest_year_@id",
    "earliest_year_approximate",
    "latest_year_approximate",
    "rism_id",
    "viaf_id",
]


class PersonNamePreservationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="diamm-person-text-")
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.src = self.directory / "src"
        self.src.mkdir()
        (self.src / "relations.json").write_text(
            (ROOT / "src/relations.json").read_text()
        )
        self.csv_dir = self.directory / "data/csv"
        self.reconciled = self.directory / "data/reconciled"
        self.reconciled.mkdir(parents=True)

    def run_script(self, name):
        result = subprocess.run(
            [sys.executable, str(ROOT / "src" / name)],
            cwd=self.src,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def extract(self, records):
        raw = self.directory / "data/raw"
        (raw / "people").mkdir(parents=True)
        (raw / "compositions").mkdir()
        for index, record in enumerate(records, 1):
            person = {
                "pk": index,
                "variant_names": [],
                "identifiers": [],
                "compositions": [],
                "related_sources": [],
                "copied_sources": [],
                **record,
            }
            if index == 1:
                person["compositions"] = [{"url": f"{DIAMM}compositions/1/"}]
                person["copied_sources"] = [{"url": f"{DIAMM}sources/2/"}]
                person["related_sources"] = [
                    {"url": f"{DIAMM}sources/3/", "relationship": "owner"}
                ]
            (raw / "people" / f"{index}.json").write_text(
                json.dumps(person), encoding="utf-8"
            )
        (raw / "compositions/1.json").write_text(
            json.dumps(
                {
                    "pk": 1,
                    "title": "Source work",
                    "anonymous": False,
                    "genres": [],
                    "composers": [{"url": f"{DIAMM}people/1/"}],
                    "sources": [],
                }
            )
        )
        self.run_script("to_csv.py")
        with (self.csv_dir / "people.csv").open(newline="", encoding="utf-8") as source:
            return {row["id"]: row for row in csv.DictReader(source)}

    def export(self, legacy=False):
        # Project the extracted rows through the tracked column selection.
        # This is a synthetic export boundary, not an OpenRefine/service replay.
        for template_path in (ROOT / "openrefine/export").glob("*_export.json"):
            table = template_path.stem.removesuffix("_export")
            columns = [
                c["name"] for c in json.loads(template_path.read_text())["columns"]
            ]
            if legacy and table == "people":
                columns = LEGACY_COLUMNS
            with (self.csv_dir / f"{table}.csv").open(
                newline="", encoding="utf-8"
            ) as source:
                rows = list(csv.DictReader(source))
            with (self.reconciled / f"{table}-csv.csv").open(
                "w", newline="", encoding="utf-8"
            ) as target:
                writer = csv.DictWriter(target, fieldnames=columns)
                writer.writeheader()
                for row in rows:
                    exported = {column: row.get(column, "") for column in columns}
                    if table == "people":
                        exported["full_name_@id"] = (
                            "Q42" if row["id"] == "1" else row["full_name"]
                        )
                        for field in ("earliest_year", "latest_year"):
                            exported[f"{field}_@id"] = row[field]
                    writer.writerow(exported)
        self.run_script("convert_rdf.py")
        return Graph().parse(self.directory / "data/RDF/diamm.ttl", format="turtle")

    def expected_base(self, names):
        graph = {
            (DIAMM["compositions/1"], RDF.type, LM.Composition),
            (DIAMM["compositions/1"], RDFS.label, Literal("Source work")),
            (DIAMM["compositions/1"], WDT.P86, DIAMM["people/1"]),
            (DIAMM["sources/2"], WDT.P11603, DIAMM["people/1"]),
            (DIAMM["sources/3"], WDT.P127, DIAMM["people/1"]),
            (DIAMM["people/1"], WDT.P2888, WD.Q42),
        }
        for index, name in enumerate(names, 1):
            graph.add((DIAMM[f"people/{index}"], RDF.type, LM.Person))
            graph.add((DIAMM[f"people/{index}"], RDFS.label, Literal(name)))
        return graph

    def test_extraction_preserves_original_names_and_optional_floruit(self):
        cases = [
            ({"full_name": "Scribe (fl. ca. 1500–1520?)"}, "Scribe"),
            ({"full_name": "René (ca. 1450–1510)", "floruit": None}, "René"),
            (
                {"full_name": "Scribe (the elder)", "floruit": "after 1500?"},
                "Scribe (the elder)",
            ),
            (
                {
                    "full_name": '  Scribe, "Á" (fl. after 1500)  ',
                    "floruit": "  during 1500\nperhaps later  ",
                },
                '  Scribe, "Á"',
            ),
            ({"full_name": "Plain name", "floruit": ""}, "Plain name"),
        ]
        rows = self.extract([record for record, _ in cases])
        for index, (record, cleaned) in enumerate(cases, 1):
            with self.subTest(record=record):
                row = rows[str(index)]
                self.assertEqual(row["full_name"], cleaned)
                self.assertEqual(row.get("source_full_name"), record["full_name"])
                self.assertEqual(row.get("floruit"), record.get("floruit") or "")
        with (self.csv_dir / "relations.csv").open(newline="") as source:
            relations = {
                (r["key1"], r["key2"], r["type"]) for r in csv.DictReader(source)
            }
        self.assertEqual(
            relations,
            {
                ("composition:1", "people:1", ""),
                ("people:1", "source:2", "copied"),
                ("people:1", "source:3", "related:owner"),
            },
        )

    def test_export_contract_keeps_evidence_columns_out_of_reconciliation(self):
        template = json.loads(
            (ROOT / "openrefine/export/people_export.json").read_text()
        )
        self.assertEqual(
            [c["name"] for c in template["columns"]],
            LEGACY_COLUMNS + ["source_full_name", "floruit"],
        )
        for column in template["columns"][-2:]:
            self.assertEqual(column["reconSettings"]["output"], "entity-name")
            self.assertFalse(column["reconSettings"]["blankUnmatchedCells"])
        history = json.loads(
            (ROOT / "openrefine/history/people_history.json").read_text()
        )
        touched = {
            operation.get(key)
            for operation in history
            for key in ("columnName", "baseColumnName", "newColumnName")
        }
        self.assertTrue({"source_full_name", "floruit"}.isdisjoint(touched))
        for operation in history:
            # Reordering/removing columns can discard appended evidence even
            # without naming it in columnName. Require review if either is added.
            self.assertNotIn(
                operation["op"], {"core/column-reorder", "core/column-removal"}
            )

    def test_extraction_export_and_rdf_keep_text_without_inventing_dates(self):
        cases = [
            ({"full_name": "Scribe (fl. ca. 1500–1520?)"}, "Scribe"),
            ({"full_name": "René (ca. 1450–1510)", "floruit": "after 1520?"}, "René"),
            ({"full_name": "NA", "floruit": "nan"}, "NA"),
            ({"full_name": "0012", "floruit": "0012"}, "0012"),
            (
                {
                    "full_name": "Name\nwith a note",
                    "floruit": "  before 1500\nor later?  ",
                },
                "Name\nwith a note",
            ),
            ({"full_name": "Name (the elder)", "floruit": None}, "Name (the elder)"),
            ({"full_name": "Q42", "floruit": "https://example.org/Q42"}, "Q42"),
            ({"full_name": "(fl. ca. 1500)"}, ""),
        ]
        self.extract([record for record, _ in cases])
        graph = self.export()
        expected = self.expected_base([name for _, name in cases])
        # The seventh unmatched name is itself a syntactically valid QID, so the
        # existing reconciliation-ID policy accepts it. Source text stays literal.
        expected.add((DIAMM["people/7"], WDT.P2888, WD.Q42))
        for index, (record, _) in enumerate(cases, 1):
            person = DIAMM[f"people/{index}"]
            expected.add(
                (
                    person,
                    LM.sourceFullName,
                    Literal(record["full_name"], datatype=XSD.string),
                )
            )
            if record.get("floruit"):
                expected.add(
                    (
                        person,
                        LM.floruit,
                        Literal(record["floruit"], datatype=XSD.string),
                    )
                )
        self.assertEqual(set(graph), expected)
        rows = graph.query(f"""
            PREFIX diamm: <{LM}>
            SELECT ?person ?original WHERE {{
              ?person a diamm:Person; diamm:sourceFullName ?original .
              FILTER(CONTAINS(STR(?original), "(fl."))
            }}
        """)
        self.assertEqual(
            {tuple(row) for row in rows},
            {
                (
                    DIAMM["people/1"],
                    Literal("Scribe (fl. ca. 1500–1520?)", datatype=XSD.string),
                ),
                (
                    DIAMM["people/8"],
                    Literal("(fl. ca. 1500)", datatype=XSD.string),
                ),
            },
        )

    def test_legacy_exports_without_new_columns_keep_existing_graph(self):
        self.extract([{"full_name": "Legacy person (fl. 1500)"}])
        graph = self.export(legacy=True)
        self.assertEqual(set(graph), self.expected_base(["Legacy person"]))
        self.assertEqual(list(graph.objects(None, LM.sourceFullName)), [])
        self.assertEqual(list(graph.objects(None, LM.floruit)), [])


if __name__ == "__main__":
    unittest.main()
