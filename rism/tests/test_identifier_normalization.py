"""Small, offline regression fixtures for RISM identifier conversion."""

import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDF, RDFS, XSD

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "rism_converter", ROOT / "src" / "convert_to_rdf.py"
)
converter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(converter)


def mappings():
    return {
        key: URIRef(value) if value else None
        for key, value in json.loads(
            (ROOT / "src/mappings/property_mapping.json").read_text()
        ).items()
    }


class IdentifierNormalizationTests(unittest.TestCase):
    def test_variants_and_idempotence(self):
        for scheme in ("http", "https"):
            for host in ("www.wikidata.org", "wikidata.org"):
                for path in ("wiki", "entity"):
                    value = f"{scheme}://{host}/{path}/Q1339"
                    with self.subTest(value=value):
                        actual = converter.convert_rdf_object(value)
                        self.assertEqual(actual, converter.WD.Q1339)
                        self.assertEqual(
                            converter.convert_rdf_object(str(actual)), actual
                        )

    def test_literals_preserve_text_language_and_datatype(self):
        url = "https://www.wikidata.org/entity/Q1339"
        for value, expected in (
            (f"See {url}", Literal(f"See {url}")),
            ("Q1339", Literal("Q1339")),
            (f"See {url}@en", Literal(f"See {url}", lang="en")),
            (f"{url}^^{XSD.anyURI}", Literal(url, datatype=XSD.anyURI)),
            (f"{url}^^{XSD.string}", Literal(url, datatype=XSD.string)),
        ):
            with self.subTest(value=value):
                self.assertEqual(converter.convert_rdf_object(value), expected)

    def test_unrelated_and_malformed_iris_are_unchanged(self):
        for value in (
            "https://rism.online/people/40005939",
            "https://example.org/entity/Q1339",
            "https://www.wikidata.org.example.org/entity/Q1339",
            "https://example.org/https://www.wikidata.org/entity/Q1339",
            "https://www.wikidata.org/entity/Q0",
            "https://www.wikidata.org/entity/Q01339",
            "https://www.wikidata.org/entity/Q",
            "https://www.wikidata.org/entity/Q١٣٣٩",
            "https://www.wikidata.org/entity/q1339",
            "https://www.wikidata.org/entity/P31",
            "https://www.wikidata.org/entity/Q1339/",
            "https://www.wikidata.org/entity/Q1339?oldid=1",
            "https://www.wikidata.org/entity/Q1339#label",
            "https://www.wikidata.org/entity/Q1339suffix",
            "https://www.wikidata.org/wiki/Q1339\n",
            "https://wikidata.org/prop/direct/P2888",
        ):
            with self.subTest(value=value):
                self.assertEqual(converter.convert_rdf_object(value), URIRef(value))

    def test_topic_lookup_aliases_and_literal_fallback(self):
        subject = "https://rism.online/sources/1"
        topic = "https://rism.online/api/v1#topic-1"
        for scheme in ("http", "https"):
            for host in ("www.wikidata.org", "wikidata.org"):
                predicate = f"{scheme}://{host}/prop/direct/P2888"
                with self.subTest(predicate=predicate):
                    graph = Graph()
                    converter.process_triple(
                        subject,
                        str(converter.WDT.P921),
                        topic,
                        mappings(),
                        {},
                        {
                            (topic, predicate): [
                                "https://www.wikidata.org/entity/Q26256810"
                            ],
                            (topic, str(RDF.value)): ["Unreconciled topic"],
                        },
                        graph,
                    )
                    self.assertEqual(
                        set(graph),
                        {
                            (
                                URIRef(subject),
                                converter.WDT.P136,
                                converter.WD.Q26256810,
                            )
                        },
                    )
        graph = Graph()
        converter.process_triple(
            subject,
            str(converter.WDT.P921),
            topic,
            mappings(),
            {},
            {(topic, str(RDF.value)): ["Unreconciled topic"]},
            graph,
        )
        self.assertIn(
            (URIRef(subject), converter.WDT.P136, Literal("Unreconciled topic")), graph
        )

    def test_csv_to_turtle_joins_canonical_identifier(self):
        # Synthetic OpenRefine-style CSV. Generated CSV/RDF stays outside Git.
        source = "https://rism.online/sources/1"
        person = "https://rism.online/people/1"
        topic = "https://rism.online/api/v1#topic-1"
        fields = [
            "subject",
            str(converter.WDT.P50),
            "http://wikidata.org/prop/direct/P2888",
            str(converter.WDT.P921),
            "https://wikidata.org/prop/direct/P2888",
            str(RDF.value),
            str(RDFS.label),
        ]
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "fixture.csv"
            ttl_path = Path(directory) / "fixture.ttl"
            with csv_path.open("w", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=fields)
                writer.writeheader()
                writer.writerows(
                    [
                        {
                            "subject": source,
                            str(converter.WDT.P50): person,
                            str(converter.WDT.P921): topic,
                        },
                        {
                            "subject": person,
                            "http://wikidata.org/prop/direct/P2888": (
                                "https://www.wikidata.org/entity/Q1339"
                            ),
                            str(RDFS.label): "Synthetic composer",
                        },
                        {
                            "subject": topic,
                            "https://wikidata.org/prop/direct/P2888": (
                                "https://wikidata.org/wiki/Q26256810"
                            ),
                            str(RDF.value): "Fallback topic",
                        },
                    ]
                )
            converter.process_file(csv_path, mappings(), {}, ttl_path, {})
            graph = Graph().parse(ttl_path)
        rows = list(graph.query("""
                PREFIX wdt: <http://www.wikidata.org/prop/direct/>
                PREFIX wd: <http://www.wikidata.org/entity/>
                SELECT ?source WHERE {
                    ?source wdt:P86/wdt:P2888 wd:Q1339 ;
                            wdt:P136 wd:Q26256810 .
                }
                """))
        self.assertEqual(rows, [(URIRef(source),)])
        self.assertIn((URIRef(source), converter.WDT.P86, URIRef(person)), graph)


if __name__ == "__main__":
    unittest.main()
