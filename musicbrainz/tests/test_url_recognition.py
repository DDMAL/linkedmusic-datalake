"""Offline URL-boundary regressions using the production entity converter."""

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from rdflib import Graph, Literal, Namespace, RDF, RDFS, URIRef
from rdflib.compare import isomorphic

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from convert_to_rdf import merge_subgraph, process_entity
from mapping_schema import MappingSchema
from relationship_mapping import RelationshipMappings, TERMS

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

    def convert(self, relations, name=None, subject=SUBJECT):
        _, entity_type, entity_id = str(subject).rsplit("/", 2)
        record = {"id": entity_id, "relations": relations}
        if name is not None:
            record["name"] = name
        graph = Graph()
        process_entity(record, entity_type, self.schema, self.relations, {}, {}, graph)
        return graph

    @staticmethod
    def link(url, role="wikidata", **fields):
        return {"target-type": "url", "type": role, "url": {"resource": url}, **fields}

    def assert_evidence(self, graph, subject, relation, target):
        nodes = [
            node
            for node in graph.objects(subject, TERMS.urlRelationship)
            if json.loads(str(graph.value(node, TERMS.sourcePayload))) == relation
        ]
        self.assertEqual(len(nodes), 1)
        node = nodes[0]
        self.assertEqual(graph.value(node, TERMS.urlTarget), target)
        for key, pred in (
            ("type", TERMS.sourceTypeName),
            ("type-id", TERMS.sourceTypeId),
        ):
            value = relation.get(key)
            self.assertEqual(
                graph.value(node, pred),
                Literal(value) if isinstance(value, str) else None,
            )

    def test_complete_item_url_variants_and_idempotence(self):
        for scheme in ("http", "https"):
            for host in ("www.wikidata.org", "wikidata.org"):
                for path in ("wiki", "entity"):
                    url = f"{scheme}://{host}/{path}/Q42"
                    with self.subTest(url=url):
                        relation = self.link(url)
                        graph = self.convert([relation, relation])
                        self.assertEqual(
                            set(graph.objects(SUBJECT, WDT.P2888)), {WD.Q42}
                        )
                        self.assert_evidence(graph, SUBJECT, relation, URIRef(url))
                        self.assertIn((SUBJECT, RDF.type, ARTIST), graph)

    def test_non_item_urls_and_malformed_identifiers_retain_evidence(self):
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
                relation = self.link(url)
                graph = self.convert([relation])
                self.assertFalse(list(graph.objects(SUBJECT, WDT.P2888)))
                node = graph.value(SUBJECT, TERMS.urlRelationship)
                self.assertEqual(str(graph.value(node, TERMS.urlTarget)), url)
                self.assertEqual(
                    json.loads(str(graph.value(node, TERMS.sourcePayload))), relation
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
        relations = [
            self.link(url)
            for url in (
                "https://www.wikidata.org/entity/Q42",
                "http://wikidata.org/wiki/Q43",
                "https://example.org/Q42",
            )
        ]
        graph = self.convert(relations, name="Synthetic artist")
        restored = Graph().parse(data=graph.serialize(format="turtle"), format="turtle")
        self.assertTrue(isomorphic(restored, graph))
        self.assertEqual(set(restored.objects(SUBJECT, WDT.P2888)), {WD.Q42, WD.Q43})
        self.assertEqual(set(restored.subjects(WDT.P2888, WD.Q42)), {SUBJECT})

    def test_cher_identity_and_discography_are_distinct_query_results(self):
        subject = URIRef(
            "https://musicbrainz.org/artist/bfcc6d75-a6a5-4bc6-8282-47aec8531818"
        )
        base = "https://www.wikidata.org/wiki/"
        discographies = [
            self.link(
                base + qid,
                "discography page",
                **{"type-id": "4fb0eeec-a6eb-4ae3-ad52-b55765b94e8f"},
            )
            for qid in ("Q2604791", "Q5264608")
        ]
        identity = self.link(
            base + "Q12003", **{"type-id": "689870a4-a1e4-4912-b17f-7b2664215698"}
        )
        graph = self.convert([identity, *discographies], subject=subject)
        graph = Graph().parse(data=graph.serialize(format="turtle"), format="turtle")
        self.assertEqual(set(graph.objects(subject, WDT.P2888)), {WD.Q12003})
        rows = graph.query(
            """
            SELECT ?item ?page WHERE {
                ?artist wdt:P2888 ?item ; mb:urlRelationship ?rel .
                ?rel mb:sourceTypeName "discography page" ; mb:urlTarget ?page .
            }
        """,
            initNs={"wdt": WDT, "mb": TERMS},
            initBindings={"artist": subject},
        )
        self.assertEqual(
            set(rows),
            {(WD.Q12003, URIRef(base + qid)) for qid in ("Q2604791", "Q5264608")},
        )

    def test_named_web_links_and_unfamiliar_roles_keep_their_targets(self):
        homepage = "https://www.thebeatles.com/"
        examples = [
            (homepage, "official homepage", URIRef(homepage)),
            (
                "https://example.org/listen",
                "free streaming",
                URIRef("https://example.org/listen"),
            ),
            (
                "https://example.org/é",
                "unfamiliar role",
                URIRef("https://example.org/é"),
            ),
            ("bad url", "unfamiliar role", Literal("bad url")),
            (
                "https://example.org/%AZ",
                "discography page",
                Literal("https://example.org/%AZ"),
            ),
            ("https://[bad", "official homepage", Literal("https://[bad")),
            (
                "https://x.example:abc/",
                "official homepage",
                Literal("https://x.example:abc/"),
            ),
            (
                "https://example.org/\n",
                "official homepage",
                Literal("https://example.org/\n"),
            ),
        ]
        relations = [self.link(url, role) for url, role, _ in examples]
        graph = self.convert(relations)
        restored = Graph().parse(data=graph.serialize(format="turtle"), format="turtle")
        self.assertFalse(list(restored.objects(SUBJECT, WDT.P2888)))
        for relation, (_, _, target) in zip(relations, examples):
            self.assert_evidence(restored, SUBJECT, relation, target)

    def test_url_targets_survive_the_disk_store_merge(self):
        targets = [
            Literal("https://example.org/a[1]"),
            Literal("https://example.org/?q=[x]"),
            Literal("https://example.org/#a#b"),
            Literal("https://example.org/\ue000"),
            Literal("https://example.org/a\u00a0b"),
            URIRef("https://[2001:db8::1]:443/é?q=%5Bx%5D#section"),
            URIRef("https://example.org/?q=\ue000"),
        ]
        identity = self.link("https://www.wikidata.org/wiki/Q12003")
        relations = [self.link(str(target), "discography page") for target in targets]
        memory = self.convert([*relations, identity])
        with TemporaryDirectory() as directory:
            disk = Graph("Oxigraph")
            disk.open(directory, create=True)
            try:
                merge_subgraph(disk, memory)
                # Oxigraph reads plain string literals back with explicit xsd:string.
                self.assertEqual(len(disk), len(memory))
                for triple in memory:
                    self.assertIn(triple, disk)
                self.assertEqual(set(disk.objects(SUBJECT, WDT.P2888)), {WD.Q12003})
            finally:
                disk.close()
        for relation, target in zip(relations, targets):
            self.assert_evidence(memory, SUBJECT, relation, target)

    def test_conflicting_incomplete_and_ended_records_keep_evidence(self):
        url = "https://www.wikidata.org/wiki/Q1299"
        for relation in (
            self.link(url, "official homepage"),
            self.link(url, **{"type-id": "4fb0eeec-a6eb-4ae3-ad52-b55765b94e8f"}),
            self.link(url, **{"type-id": "587fdd8f-080e-46a9-97af-6425ebbcb3a2"}),
            self.link(url, **{"type-id": ""}),
            self.link(url, **{"type-id": {}}),
            self.link(url, direction="backward"),
            self.link(url, ended=True),
            self.link(url, end="2001"),
            {"target-type": "url", "url": {"resource": url}},
            self.link(17),
            self.link(None),
            {"target-type": "url", "type": "wikidata", "url": None},
        ):
            with self.subTest(relation=relation):
                graph = self.convert([relation])
                self.assertFalse(list(graph.objects(SUBJECT, WDT.P2888)))
                resource = (relation["url"] or {}).get("resource")
                self.assert_evidence(
                    graph,
                    SUBJECT,
                    relation,
                    URIRef(resource) if isinstance(resource, str) else None,
                )

    def test_wikidata_ids_and_directions_are_endpoint_specific(self):
        url = str(WD.Q42)
        for kind, role_id, direction, valid in (
            ("work", "587fdd8f-080e-46a9-97af-6425ebbcb3a2", "backward", True),
            ("work", "587fdd8f-080e-46a9-97af-6425ebbcb3a2", "forward", False),
            ("release-group", "b988d08c-5d86-4a57-9557-c83b399e3580", "forward", True),
            ("release", "b988d08c-5d86-4a57-9557-c83b399e3580", "forward", False),
        ):
            subject = URIRef(f"https://musicbrainz.org/{kind}/example")
            rel = self.link(url, **{"type-id": role_id, "direction": direction})
            with self.subTest(kind=kind, direction=direction):
                graph = self.convert([rel], subject=subject)
                self.assertEqual((subject, WDT.P2888, WD.Q42) in graph, valid)
                self.assert_evidence(graph, subject, rel, URIRef(url))


if __name__ == "__main__":
    unittest.main()
