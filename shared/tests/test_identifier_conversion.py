"""Offline preservation checks for the shared CSV converter's ID boundary."""

import csv
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

from rdflib import Graph, Literal, Namespace, URIRef, XSD
from rdflib.compare import isomorphic

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "shared"))
from rdfconv.convert import (
    build_rdf_graph,
    rdf_process_predicates,
    to_predicate,
    to_rdf_node,
)

WD = Namespace("http://www.wikidata.org/entity/")
WDT = Namespace("http://www.wikidata.org/prop/direct/")
NS = {"wd": str(WD), "wdt": str(WDT), "xsd": str(XSD), "local": "https://example.org/"}


class IdentifierConversionTests(unittest.TestCase):
    def test_complete_item_identifiers(self):
        values = ["Q42", "wd:Q42"]
        for scheme in ("http", "https"):
            for host in ("www.wikidata.org", "wikidata.org"):
                for path in ("entity", "wiki"):
                    values.append(f"{scheme}://{host}/{path}/Q42")
        for value in values:
            with self.subTest(value=value):
                self.assertEqual(to_rdf_node(value, NS), WD.Q42)
                self.assertEqual(to_rdf_node(str(to_rdf_node(value, NS)), NS), WD.Q42)

    def test_text_and_ambiguous_values_stay_literal(self):
        for value in (
            "Study Q42 (draft)",
            "Q42 / Q43",
            "Douglas Adams (Q42)",
            "Q42suffix",
            "Q0",
            "Q042",
            "Q٤٢",
            "q42",
            " Q42 ",
            "wd:Q42suffix",
            "See https://www.wikidata.org/wiki/Q42",
        ):
            with self.subTest(value=value):
                self.assertEqual(to_rdf_node(value, NS), Literal(value))

    def test_external_and_noncanonical_urls_preserved(self):
        for value in (
            "https://example.org/Q42",
            "https://example.org/P175",
            "https://www.wikidata.org.example.org/entity/Q42",
            "https://example.org/?id=Q42",
            "https://www.wikidata.org/wiki/Q42#section",
            "https://www.wikidata.org/wiki/Q42?oldid=1",
            "https://www.wikidata.org/entity/Q042",
            "https://www.wikidata.org/entity/Q42suffix",
        ):
            with self.subTest(value=value):
                self.assertEqual(to_rdf_node(value, NS), URIRef(value))

    def test_explicit_literals_override_identifier_and_uri_detection(self):
        for value in (
            "Q42",
            "wd:Q42",
            "https://www.wikidata.org/wiki/Q42",
            "https://example.org/Q42",
        ):
            for datatype in ("xsd:string", str(XSD.string), XSD.string):
                with self.subTest(value=value, datatype=datatype):
                    self.assertEqual(
                        to_rdf_node(value, NS, datatype=datatype),
                        Literal(value, datatype=XSD.string),
                    )
            self.assertEqual(
                to_rdf_node(value, NS, lang="en"), Literal(value, lang="en")
            )
        for datatype in ("xsd:anyURI", str(XSD.anyURI), XSD.anyURI):
            value = "https://www.wikidata.org/wiki/Q42"
            self.assertEqual(
                to_rdf_node(value, NS, datatype=datatype),
                Literal(value, datatype=XSD.anyURI),
            )

    def test_local_prefix_takes_precedence_over_bare_identifier(self):
        for value in ("Q42", "P175", "123"):
            self.assertEqual(
                to_rdf_node(value, NS, prefix="local"), URIRef(NS["local"] + value)
            )
        value = "https://example.org/Q42"
        self.assertEqual(to_rdf_node(value, NS, prefix="local"), URIRef(value))

    def test_property_entities_and_predicates_have_distinct_namespaces(self):
        for value in (
            "P175",
            "wd:P175",
            "https://www.wikidata.org/entity/P175",
            "https://www.wikidata.org/wiki/Property:P175",
        ):
            self.assertEqual(to_rdf_node(value, NS), WD.P175)
        for value in (
            "P175",
            "wdt:P175",
            "https://www.wikidata.org/prop/direct/P175",
            "https://www.wikidata.org/wiki/Property:P175",
        ):
            self.assertEqual(to_predicate(value, NS), WDT.P175)

    def test_predicates_do_not_extract_ids_from_external_urls_or_text(self):
        value = "https://example.org/P175"
        self.assertEqual(to_predicate(value, NS), URIRef(value))
        for value in ("performer P175", "P175 / P86", "P175suffix", "Q42"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                to_predicate(value, NS)

    def test_empty_and_date_handling(self):
        for value in (None, "", float("nan")):
            self.assertIsNone(to_rdf_node(value, NS))
        self.assertEqual(
            to_rdf_node("2020-01-02", NS, datatype="xsd:date"),
            Literal("2020-01-02", datatype=XSD.date),
        )
        self.assertEqual(
            to_rdf_node("2020-01-02T03:04:05", NS, datatype="xsd:dateTime"),
            Literal("2020-01-02T03:04:05", datatype=XSD.dateTime),
        )

    def test_loadable_tracked_configs_still_validate(self):
        for path in sorted((ROOT / "shared/rdf_config").glob("*.toml")):
            # Existing duplicate mappings make Global Jukebox invalid TOML;
            # resolving its competing predicates is a separate mapping decision.
            if path.name == "theglobaljukebox.toml":
                continue
            with self.subTest(config=path.name):
                rdf_process_predicates(tomllib.loads(path.read_text()))

    def test_real_dtl_mapping_preserves_local_subjects_and_unmatched_values(self):
        config = tomllib.loads(
            (ROOT / "shared/rdf_config/digthatlick.toml").read_text()
        )
        table = "dtl1000-performers-reconciled"
        config = {key: config[key] for key in ("general", "namespaces", table)}
        with tempfile.TemporaryDirectory() as directory:
            config["general"]["csv_folder"] = directory
            with (Path(directory) / f"{table}.csv").open("w", newline="") as output:
                writer = csv.writer(output)
                writer.writerow(["track_id", "performer_names"])
                writer.writerows(
                    [
                        ("Q42", "Q43"),
                        ("2", "https://www.wikidata.org/wiki/Q42"),
                        ("3", "Study Q42 (draft)"),
                        ("4", "Q42 / Q43"),
                        ("5", "https://example.org/Q42"),
                    ]
                )
            graph = build_rdf_graph(rdf_process_predicates(config))
        track = Namespace(config["namespaces"]["dtlt"])
        expected = Graph()
        for subject, obj in (
            (track.Q42, WD.Q43),
            (track["2"], WD.Q42),
            (track["3"], Literal("Study Q42 (draft)")),
            (track["4"], Literal("Q42 / Q43")),
            (track["5"], URIRef("https://example.org/Q42")),
        ):
            expected.add((subject, WDT.P175, obj))
        self.assertEqual(set(graph), set(expected))
        self.assertTrue(
            isomorphic(
                Graph().parse(data=graph.serialize(format="turtle"), format="turtle"),
                expected,
            )
        )


if __name__ == "__main__":
    unittest.main()
