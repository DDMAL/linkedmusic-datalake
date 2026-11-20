"""Synthetic DIAMM CSV conversion, with no historical data or services."""

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
from rdflib.compare import isomorphic

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from convert_rdf import build_rdf_graph, matched_wikidata

WD = Namespace("http://www.wikidata.org/entity/")
WDT = Namespace("http://www.wikidata.org/prop/direct/")
DIAMM = Namespace("https://www.diamm.ac.uk/")
LM = Namespace("https://linkedmusic.ca/graphs/diamm/")


class IdentifierConversionTests(unittest.TestCase):
    def write_fixture(self, directory, identifier):
        base = directory / "data/reconciled"
        base.mkdir(parents=True)
        rows = {
            "archives": {"name": "Archive", "name_@id": identifier},
            "cities": {"name": "City", "name_@id": identifier},
            "countries": {"name": "Country", "name_@id": identifier},
            "regions": {"name": "Region", "name_@id": identifier},
            "people": {"full_name": "Person", "full_name_@id": identifier},
            "organizations": {
                "name": "Organization",
                "name_@id": identifier,
                "organization_type": "Organization type",
                "organization_type_@id": identifier,
            },
            "compositions": {
                "title": "Composition",
                "genres": "Genre",
                "genres_@id": identifier,
            },
            "sets": {
                "type": "Set type",
                "type_@id": identifier,
                "cluster_shelfmark": "Set shelfmark",
            },
            "sources": {
                "display_name": "Source",
                "shelfmark": "Source shelfmark",
                "source_type": "Source type",
                "source_type_@id": identifier,
            },
        }
        # Use all exported columns, including empty optional fields. Data and
        # expected RDF are synthetic; no source snapshot is read.
        for table, row in rows.items():
            template = json.loads(
                (ROOT / f"openrefine/export/{table}_export.json").read_text()
            )
            with (base / f"{table}-csv.csv").open(
                "w", newline="", encoding="utf-8"
            ) as output:
                writer = csv.DictWriter(
                    output, fieldnames=[c["name"] for c in template["columns"]]
                )
                writer.writeheader()
                writer.writerow({"id": "1", **row})
        relations = directory / "data/csv/relations.csv"
        relations.parent.mkdir()
        relations.write_text(
            "key1,key2,type\ncomposition:1,people:1,\narchive:1,source:1,\n"
        )
        return base, relations

    def expected_graph(self, matched):
        expected = Graph()
        for table, kind, label in (
            ("archives", "Archive", "Archive"),
            ("cities", "City", "City"),
            ("countries", "Country", "Country"),
            ("regions", "Region", "Region"),
            ("people", "Person", "Person"),
            ("organizations", "Organization", "Organization"),
            ("compositions", "Composition", "Composition"),
            ("sets", "Set", None),
            ("sources", "Source", "Source"),
        ):
            subject = DIAMM[f"{table}/1"]
            expected.add((subject, RDF.type, LM[kind]))
            if label:
                expected.add((subject, RDFS.label, Literal(label)))
        if matched:
            for table in (
                "archives",
                "cities",
                "countries",
                "regions",
                "people",
                "organizations",
            ):
                expected.add((DIAMM[f"{table}/1"], WDT.P2888, WD.Q42))
        for table, predicate, label in (
            ("compositions", WDT.P136, "Genre"),
            ("organizations", WDT.P31, "Organization type"),
            ("sets", WDT.P31, "Set type"),
            ("sources", WDT.P31, "Source type"),
        ):
            expected.add(
                (DIAMM[f"{table}/1"], predicate, WD.Q42 if matched else Literal(label))
            )
        expected.add((DIAMM["sets/1"], WDT.P217, Literal("Set shelfmark")))
        expected.add((DIAMM["sources/1"], RDFS.label, Literal("Source shelfmark")))
        expected.add((DIAMM["compositions/1"], WDT.P86, DIAMM["people/1"]))
        expected.add((DIAMM["sources/1"], WDT.P276, DIAMM["archives/1"]))
        return expected

    def test_complete_bare_qids(self):
        for value in ("Q1", "Q42", "Q123456789"):
            self.assertTrue(matched_wikidata(value))

    def test_non_ids_and_missing_values_are_not_matches(self):
        for value in (
            "Q42suffix",
            "Q42 / Q43",
            "Q0",
            "Q042",
            "Q٤٢",
            "q42",
            "Q42\n",
            " Q42",
            "Q42 ",
            "wd:Q42",
            "P175",
            "Unmatched name",
            "https://www.wikidata.org/wiki/Q42",
            "https://www.wikidata.org/entity/Q42",
            "https://example.org/Q42",
            "",
            None,
            float("nan"),
            42,
        ):
            with self.subTest(value=value):
                self.assertFalse(matched_wikidata(value))

    def test_csv_conversion_preserves_names_and_local_relations(self):
        for value in (
            "Q42",
            "Q42suffix",
            "Q42 / Q43",
            "",
            "https://www.wikidata.org/wiki/Q42",
        ):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as directory:
                base, relations = self.write_fixture(Path(directory), value)
                with contextlib.redirect_stdout(io.StringIO()):
                    graph = build_rdf_graph(
                        base, relations, ROOT / "src/relations.json"
                    )
                expected = self.expected_graph(value == "Q42")
                self.assertEqual(set(graph), set(expected))
                restored = Graph().parse(
                    data=graph.serialize(format="turtle"), format="turtle"
                )
                self.assertTrue(isomorphic(restored, expected))

    def test_import_does_not_read_data_or_create_output(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    "import sys; sys.path.insert(0, sys.argv[1]); import convert_rdf",
                    str(ROOT / "src"),
                ],
                cwd=directory,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_script_entrypoint_uses_existing_relative_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_fixture(root, "Q42")
            src = root / "src"
            src.mkdir()
            (src / "relations.json").write_text(
                (ROOT / "src/relations.json").read_text()
            )
            result = subprocess.run(
                [sys.executable, str(ROOT / "src/convert_rdf.py")],
                cwd=src,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            graph = Graph().parse(root / "data/RDF/diamm.ttl", format="turtle")
            self.assertTrue(isomorphic(graph, self.expected_graph(True)))


if __name__ == "__main__":
    unittest.main()
