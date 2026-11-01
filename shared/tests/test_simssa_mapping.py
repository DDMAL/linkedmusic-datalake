"""Offline regression for SIMSSA's actual person mapping and local work links."""

import csv
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

from rdflib import Graph, Literal, Namespace, RDF, RDFS, XSD
from rdflib.compare import isomorphic

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "shared"))
from rdfconv.convert import build_rdf_graph, rdf_process_predicates

SP = Namespace("https://db.simssa.ca/persons/")
SW = Namespace("https://db.simssa.ca/musicalworks/")
LMS = Namespace("https://linkedmusic.ca/graphs/simssadb/")
WD = Namespace("http://www.wikidata.org/entity/")
WDT = Namespace("http://www.wikidata.org/prop/direct/")


class SimssaMappingTests(unittest.TestCase):
    def convert(self, people, works=()):
        config = tomllib.loads((ROOT / "shared/rdf_config/simssadb.toml").read_text())
        config = {
            key: config[key] for key in ("general", "namespaces", "person", "work")
        }
        with tempfile.TemporaryDirectory() as directory:
            config["general"]["csv_folder"] = directory
            for table, rows in (("person", people), ("work", works)):
                with (Path(directory) / f"{table}.csv").open(
                    "w", newline="", encoding="utf-8"
                ) as output:
                    writer = csv.DictWriter(
                        output,
                        fieldnames=[
                            key for key in config[table] if key != "PRIMARY_KEY"
                        ],
                    )
                    writer.writeheader()
                    writer.writerows(rows)
            return build_rdf_graph(rdf_process_predicates(config))

    def assert_round_trip(self, graph, expected):
        self.assertEqual(set(graph), set(expected))
        self.assertTrue(
            isomorphic(
                Graph().parse(data=graph.serialize(format="turtle"), format="turtle"),
                expected,
            )
        )

    def test_wikidata_matches_retain_local_people_and_original_labels(self):
        values = ["Q42", "wd:Q42"] + [
            f"{scheme}://{host}/{path}/Q42"
            for scheme in ("http", "https")
            for host in ("www.wikidata.org", "wikidata.org")
            for path in ("wiki", "entity")
        ]
        rows = []
        expected = Graph()
        for index, value in enumerate(values):
            key = str(index + 1)
            name = f"Original name {key}"
            rows.append(
                {"person_id": key, "person_name": value, "person_name_original": name}
            )
            expected.add((SP[key], RDF.type, LMS.Person))
            expected.add((SP[key], RDFS.label, Literal(name, datatype=XSD.string)))
            expected.add((SP[key], WDT.P2888, WD.Q42))
        self.assert_round_trip(self.convert(rows), expected)

    def test_unmatched_names_and_non_item_targets_preserve_labels_only(self):
        values = [
            "Unmatched name",
            "Study Q42 (draft)",
            "Q42 / Q43",
            "Q42suffix",
            "Q0",
            "Q042",
            "Q٤٢",
            "Q42\n",
            "",
            "https://example.org/Q42",
            "https://www.wikidata.org.example.org/entity/Q42",
            "https://www.wikidata.org/entity/Q42#fragment",
            "https://www.wikidata.org/entity/Q42?oldid=1",
            "http://www.wikidata.org/entity/Q0",
            "http://www.wikidata.org/entity/Q042",
            "http://www.wikidata.org/entity/Q٤٢",
            "http://www.wikidata.org/entity/Q42suffix",
            "P175",
            "https://www.wikidata.org/entity/P175",
        ]
        rows = []
        expected = Graph()
        for index, value in enumerate(values):
            key = str(index + 1)
            original = value or "Unmatched original"
            rows.append(
                {
                    "person_id": key,
                    "person_name": value,
                    "person_name_original": original,
                }
            )
            expected.add((SP[key], RDF.type, LMS.Person))
            expected.add((SP[key], RDFS.label, Literal(original, datatype=XSD.string)))
        self.assert_round_trip(self.convert(rows), expected)

    def test_id_like_original_names_and_work_links_remain_source_specific(self):
        graph = self.convert(
            [
                {
                    "person_id": "Q42",
                    "person_name": "Q43",
                    "person_name_original": "Q42",
                },
                {
                    "person_id": "2",
                    "person_name": "Unmatched",
                    "person_name_original": "https://www.wikidata.org/wiki/Q42",
                },
                {
                    "person_id": "3",
                    "person_name": "",
                    "person_name_original": "  Éwé, name  ",
                },
                {"person_id": "4", "person_name": "", "person_name_original": ""},
            ],
            [{"work_id": "1", "composer_id": "Q42", "author_id": "2"}],
        )
        expected = Graph()
        for key in ("Q42", "2", "3", "4"):
            expected.add((SP[key], RDF.type, LMS.Person))
        for key, name in (
            ("Q42", "Q42"),
            ("2", "https://www.wikidata.org/wiki/Q42"),
            ("3", "  Éwé, name  "),
        ):
            expected.add((SP[key], RDFS.label, Literal(name, datatype=XSD.string)))
        expected.add((SP.Q42, WDT.P2888, WD.Q43))
        expected.add((SW["1"], RDF.type, LMS.Work))
        expected.add((SW["1"], WDT.P86, SP.Q42))
        expected.add((SW["1"], WDT.P50, SP["2"]))
        self.assert_round_trip(graph, expected)


if __name__ == "__main__":
    unittest.main()
