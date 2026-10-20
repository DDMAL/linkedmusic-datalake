import copy
import json
import pickle
import sys
import unittest
from pathlib import Path

from rdflib import Dataset, Graph, Literal, URIRef
from rdflib.namespace import RDF, RDFS

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from convert_to_rdf import process_entity
from mapping_schema import MappingSchema
from relationship_mapping import (
    MB,
    ROLE,
    TERMS,
    WDT,
    RelationshipMappings,
    predicate_iri,
)

ENGINEER = ROLE["a01ee869-80a8-45ef-9447-c59e91aa7926"]
PHOTOGRAPHER = ROLE["a7e408a1-8c64-4122-9ec2-906068955187"]
RELEASE_ENGINEER = ROLE["023a6c6d-80af-4f88-ae69-f5f6213f9bf4"]


class RelationshipPreservationTests(unittest.TestCase):
    def setUp(self):
        self.raw = json.loads(
            (ROOT / "src/rdf_conversion_config/relations.json").read_text()
        )
        self.mapping = RelationshipMappings(self.raw)
        self.schema = MappingSchema({})
        self.schema.add_from_formatted_dict(
            json.loads((ROOT / "src/rdf_conversion_config/mappings.json").read_text())
        )
        self.record = json.loads((ROOT / "tests/fixtures/role_pilot.json").read_text())
        self.subject = MB[f"recording/{self.record['id']}"]

    def convert(self, record=None, entity_type="recording", graph=None):
        if graph is None:
            graph = Graph()
        process_entity(
            record if record is not None else self.record,
            entity_type,
            self.schema,
            self.mapping,
            {},
            {},
            graph,
        )
        return graph

    def test_precise_and_broad_queries_have_different_answers(self):
        graph = self.convert()
        graph += self.mapping.schema_graph()
        rows = list(
            graph.query(
                f"SELECT ?artist WHERE {{ <{self.subject}> <{ENGINEER}> ?artist }}"
            )
        )
        engineer = MB["artist/00000000-0000-4000-8000-000000000002"]
        photographer = MB["artist/00000000-0000-4000-8000-000000000003"]
        self.assertEqual(rows, [(engineer,)])
        self.assertNotIn((self.subject, ENGINEER, photographer), graph)
        broad = list(graph.query(f"""PREFIX rdfs: <{RDFS}>
                SELECT DISTINCT ?artist WHERE {{
                    <{self.subject}> ?role ?artist .
                    ?role rdfs:subPropertyOf* <{WDT.P767}> .
                }}"""))
        self.assertEqual(
            {row[0] for row in broad},
            {engineer, photographer, MB["artist/00000000-0000-4000-8000-000000000004"]},
        )
        self.assertNotIn((WDT.P767, RDFS.subPropertyOf, ENGINEER), graph)
        self.assertFalse(list(graph.triples((None, WDT.P767, None))))

    def test_qualifiers_and_original_payload_survive_turtle(self):
        graph = Graph().parse(
            data=self.convert().serialize(format="turtle"), format="turtle"
        )
        node = next(graph.subjects(RDF.predicate, ENGINEER))
        self.assertIn((node, TERMS.begin, Literal("2001")), graph)
        self.assertIn((node, TERMS.end, Literal("2002-03")), graph)
        self.assertIn((node, TERMS.ended, Literal(False)), graph)
        self.assertIn((node, TERMS.attribute, Literal("assistant")), graph)
        self.assertEqual(
            json.loads(str(graph.value(node, TERMS.sourcePayload))),
            self.record["relations"][0],
        )
        for key, pred in (
            ("attribute-ids", TERMS.attributeIds),
            ("attribute-values", TERMS.attributeValues),
            ("attribute-credits", TERMS.attributeCredits),
        ):
            self.assertEqual(
                json.loads(str(graph.value(node, pred))),
                self.record["relations"][0][key],
            )
        photo_node = next(graph.subjects(RDF.predicate, PHOTOGRAPHER))
        self.assertIsNone(graph.value(photo_node, TERMS.ended))
        self.assertEqual(len(list(graph.subjects(RDF.type, RDF.Statement))), 3)

    def test_named_graph_contributor_query_preserves_scope_and_legacy_assertions(self):
        dataset = Dataset()
        data = dataset.graph(URIRef("urn:linkedmusic:pilot:data"))
        data += self.convert()
        data.add((URIRef("urn:legacy:record"), WDT.P767, URIRef("urn:legacy:artist")))
        schema = dataset.graph(URIRef("urn:linkedmusic:pilot:schema"))
        schema += self.mapping.schema_graph()
        dataset.graph(URIRef("urn:unrelated:data")).add(
            (URIRef("urn:other:record"), ENGINEER, URIRef("urn:other:artist"))
        )
        query = (ROOT / "doc/queries/pilot_contributors.rq").read_text()
        rows = set(tuple(row) for row in dataset.query(query))
        self.assertEqual(len(rows), 4)
        self.assertIn((URIRef("urn:legacy:record"), URIRef("urn:legacy:artist")), rows)
        self.assertNotIn((URIRef("urn:other:record"), URIRef("urn:other:artist")), rows)

    def test_inverse_source_has_the_same_rdf_direction(self):
        original = self.record["relations"][0]
        artist_id = original["artist"]["id"]
        inverse = {k: v for k, v in original.items() if k != "artist"}
        inverse.update(
            direction="forward",
            **{"target-type": "recording", "recording": {"id": self.record["id"]}},
        )
        graph = self.convert({"id": artist_id, "relations": [inverse]}, "artist")
        artist = MB[f"artist/{artist_id}"]
        self.assertIn((self.subject, ENGINEER, artist), graph)
        self.assertNotIn((artist, ENGINEER, self.subject), graph)

    def test_stable_id_is_authoritative_even_when_label_changes(self):
        self.record["relations"][0]["type"] = "a changed source label"
        graph = self.convert()
        self.assertEqual(len(list(graph.triples((None, ENGINEER, None)))), 1)

    def test_invalid_evidence_is_preserved_without_asserting_a_role(self):
        for changes, status in (
            ({"type-id": None}, "missing-type-id"),
            (
                {"type-id": "00000000-0000-4000-8000-000000000099"},
                "unrecognized-type-id",
            ),
            ({"direction": "forward"}, "unexpected-direction"),
            ({"direction": None}, "unexpected-direction"),
            ({"target-type": "work"}, "unexpected-endpoints"),
            ({"artist": {}}, "missing-target"),
            ({"artist": None}, "missing-target"),
        ):
            with self.subTest(changes=changes):
                record = copy.deepcopy(self.record)
                record["relations"] = [record["relations"][0] | changes]
                graph = self.convert(record)
                self.assertFalse(list(graph.triples((None, ENGINEER, None))))
                node = next(graph.subjects(TERMS.mappingStatus, Literal(status)))
                self.assertEqual(
                    json.loads(str(graph.value(node, TERMS.sourcePayload))),
                    record["relations"][0],
                )

    def test_distinct_qualifiers_do_not_overwrite_and_repeats_are_stable(self):
        graph = self.convert()
        triples = set(graph)
        self.convert(graph=graph)
        self.assertEqual(set(graph), triples)
        record = copy.deepcopy(self.record)
        record["relations"] = [record["relations"][0]]
        record["relations"][0]["begin"] = "2005"
        self.convert(record, graph=graph)
        self.assertEqual(len(list(graph.subjects(RDF.predicate, ENGINEER))), 2)
        self.assertEqual(len(list(graph.triples((None, ENGINEER, None)))), 1)

    def test_same_label_in_release_has_its_own_type(self):
        record = copy.deepcopy(self.record)
        record["relations"] = [record["relations"][0]]
        record["relations"][0]["type-id"] = str(RELEASE_ENGINEER).split("/")[-1]
        graph = self.convert(record, "release")
        self.assertEqual(len(list(graph.triples((None, RELEASE_ENGINEER, None)))), 1)
        self.assertFalse(list(graph.triples((None, ENGINEER, None))))

    def test_embedded_recording_is_processed(self):
        release = {
            "id": "synthetic-release",
            "media": [{"tracks": [{"recording": self.record}]}],
        }
        graph = self.convert(release, "release")
        self.assertEqual(len(list(graph.triples((self.subject, ENGINEER, None)))), 1)

    def test_legacy_mappings_and_full_iris(self):
        self.assertEqual(predicate_iri("P767"), WDT.P767)
        self.assertEqual(predicate_iri(str(PHOTOGRAPHER)), PHOTOGRAPHER)
        self.assertEqual(predicate_iri("urn:example:role"), URIRef("urn:example:role"))
        self.assertEqual(self.mapping["recording"]["work"]["performance"], WDT.P2550)
        legacy = RelationshipMappings(
            {"artist": {"artist": {"ignored": None, "member": "P463"}}}
        )
        self.assertIsNone(legacy["artist"]["artist"]["ignored"])
        self.assertEqual(legacy["artist"]["artist"]["member"], WDT.P463)
        self.record["relations"] = [
            {
                "type": "performance",
                "target-type": "work",
                "work": {"id": "synthetic-work"},
                "direction": "forward",
            }
        ]
        self.assertIn(
            (self.subject, WDT.P2550, MB["work/synthetic-work"]), self.convert()
        )

    def test_invalid_configuration_fails_before_conversion(self):
        for value in (
            "P0",
            "P767suffix",
            "not-a-uri",
            "https://",
            "https://example.org/a b",
        ):
            with self.subTest(value=value), self.assertRaises(ValueError):
                predicate_iri(value)
        for key, value in (
            ("type_id", "invalid"),
            ("predicate", str(WDT.P767)),
            ("subject_type", "artist"),
            ("source", "https://musicbrainz.org/relationship/wrong"),
            ("broader", "P175"),
        ):
            raw = copy.deepcopy(self.raw)
            raw["recording"]["artist"]["recording"][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                RelationshipMappings(raw)

    def test_inventory_and_worker_serialization(self):
        self.assertEqual(len(self.mapping.by_id), 33)
        restored = pickle.loads(pickle.dumps(self.mapping))
        self.assertEqual(restored.by_id, self.mapping.by_id)
        schema = restored.schema_graph()
        for role in restored.by_id.values():
            for prop in (RDFS.label, RDFS.comment, RDFS.domain, RDFS.range):
                self.assertIsNotNone(schema.value(role.predicate, prop))


if __name__ == "__main__":
    unittest.main()
