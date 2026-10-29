"""Offline URL-boundary regressions using the production entity converter."""

import json
import sys
import unittest
from pathlib import Path

from rdflib import Graph, Literal, Namespace, RDF, RDFS, URIRef
from rdflib.compare import isomorphic

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from convert_to_rdf import process_entity
from mapping_schema import MappingSchema
from relationship_mapping import RelationshipMappings

WD = Namespace("http://www.wikidata.org/entity/")
WDT = Namespace("http://www.wikidata.org/prop/direct/")
SUBJECT = URIRef("https://musicbrainz.org/artist/00000000-0000-4000-8000-000000000001")
ARTIST = URIRef("https://linkedmusic.ca/graphs/musicbrainz/Artist")


class UrlRecognitionTests(unittest.TestCase):
    def setUp(self):
        config = ROOT / "src/rdf_conversion_config"
        self.schema = MappingSchema({})
        self.schema.add_from_formatted_dict(
            json.loads((config / "mappings.json").read_text())
        )
        self.relations = RelationshipMappings(
            json.loads((config / "relations.json").read_text())
        )

    def convert(self, urls, name=None):
        record = {
            "id": "00000000-0000-4000-8000-000000000001",
            "relations": [
                {"target-type": "url", "type": "wikidata", "url": {"resource": url}}
                for url in urls
            ],
        }
        if name is not None:
            record["name"] = name
        graph = Graph()
        process_entity(record, "artist", self.schema, self.relations, {}, {}, graph)
        return graph

    def test_complete_item_url_variants_and_idempotence(self):
        for scheme in ("http", "https"):
            for host in ("www.wikidata.org", "wikidata.org"):
                for path in ("wiki", "entity"):
                    url = f"{scheme}://{host}/{path}/Q42"
                    with self.subTest(url=url):
                        graph = self.convert([url])
                        self.assertEqual(
                            set(graph),
                            {
                                (SUBJECT, RDF.type, ARTIST),
                                (SUBJECT, WDT.P2888, WD.Q42),
                            },
                        )
                        self.assertEqual(set(self.convert([str(WD.Q42)])), set(graph))

    def test_non_item_urls_and_malformed_identifiers_remain_original_literals(self):
        for url in (
            "https://example.org/Q42",
            "https://www.wikidata.org.example.org/wiki/Q42",
            "https://www.wikidata.org@evil.example/wiki/Q42",
            "https://www.wikidata.org/wiki/Q42suffix",
            "https://www.wikidata.org/wiki/Q42/",
            "https://www.wikidata.org/wiki/Q42?oldid=1",
            "https://www.wikidata.org/wiki/Q42#section",
            "https://www.wikidata.org/wiki/Q42\n",
            " https://www.wikidata.org/wiki/Q42",
            "https://www.wikidata.org/wiki/Q0",
            "https://www.wikidata.org/wiki/Q042",
            "https://www.wikidata.org/wiki/Q٤٢",
            "https://www.wikidata.org/wiki/q42",
            "https://www.wikidata.org/wiki/Property:P175",
            "https://www.wikidata.org/entity/P175",
            "https://www.wikidata.org/wiki/Special:EntityData/Q42.json",
            "https://www.wikidata.org:443/wiki/Q42",
            "https://www.wikidata.org/wiki/%5142",
            "Q42",
            "wd:Q42",
            "Q42 / Q43",
            "See https://www.wikidata.org/wiki/Q42",
        ):
            with self.subTest(url=url):
                self.assertEqual(
                    set(self.convert([url])),
                    {
                        (SUBJECT, RDF.type, ARTIST),
                        (SUBJECT, WDT.P2888, Literal(url)),
                    },
                )

    def test_identifier_like_names_are_not_normalized(self):
        for name in ("Q42", "https://www.wikidata.org/entity/Q42"):
            with self.subTest(name=name):
                self.assertEqual(
                    set(self.convert([], name=name)),
                    {
                        (SUBJECT, RDF.type, ARTIST),
                        (SUBJECT, RDFS.label, Literal(name)),
                    },
                )

    def test_multiple_targets_round_trip_and_canonical_join(self):
        graph = self.convert(
            [
                "https://www.wikidata.org/entity/Q42",
                "http://wikidata.org/wiki/Q43",
                "https://example.org/Q42",
            ],
            name="Synthetic artist",
        )
        expected = Graph()
        for triple in (
            (SUBJECT, RDF.type, ARTIST),
            (SUBJECT, RDFS.label, Literal("Synthetic artist")),
            (SUBJECT, WDT.P2888, WD.Q42),
            (SUBJECT, WDT.P2888, WD.Q43),
            (SUBJECT, WDT.P2888, Literal("https://example.org/Q42")),
        ):
            expected.add(triple)
        self.assertEqual(set(graph), set(expected))
        restored = Graph().parse(data=graph.serialize(format="turtle"), format="turtle")
        self.assertTrue(isomorphic(restored, expected))
        self.assertEqual(
            list(restored.query("""
            SELECT ?source WHERE {
                VALUES ?qid { <http://www.wikidata.org/entity/Q42> }
                ?source <http://www.wikidata.org/prop/direct/P2888> ?qid .
            }
        """)),
            [(SUBJECT,)],
        )


if __name__ == "__main__":
    unittest.main()
