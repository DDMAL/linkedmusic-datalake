import copy
import json
import hashlib
import subprocess
import pickle
import re
import sys
import tempfile
import unittest
from pathlib import Path

from rdflib import Dataset, Graph, Literal, URIRef
from rdflib.namespace import DCTERMS, RDF, RDFS

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from convert_to_rdf import process_entity
from convert_relationship_sample import main as sample_main
from mapping_schema import MappingSchema
from relationship_mapping import (
    ENTITY,
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
    def test_sample_cli_preserves_inputs_outputs_and_scoped_answers(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "sample"
            sample_main(["--output-dir", str(output)])
            report = json.loads((output / "audit.json").read_text())
            self.assertEqual(report["source_kind"], "synthetic")
            self.assertEqual(report["observation_statuses"], {"mapped": 3})
            self.assertEqual(report["distinct_role_assertions"], 3)
            self.assertEqual(len(report["queries"]["contributors"]["rows"]), 3)
            self.assertEqual(len(report["queries"]["recording_engineers"]["rows"]), 1)
            self.assertIn(
                "GRAPH <urn:linkedmusic:pilot:schema>",
                report["queries"]["contributors"]["query"],
            )
            source = report["sources"][0]
            self.assertEqual(
                (output / source["archived_input"]).read_bytes(),
                (ROOT / "tests/fixtures/role_pilot.json").read_bytes(),
            )
            import hashlib

            for name, expected in report["output_sha256"].items():
                self.assertEqual(
                    hashlib.sha256((output / name).read_bytes()).hexdigest(), expected
                )
            self.assertNotEqual(
                report["query_graphs"]["data"], report["query_graphs"]["schema"]
            )

    def test_sample_cli_requires_fresh_output_and_explicit_input_kind(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "sample"
            output.mkdir()
            marker = output / "base.ttl"
            marker.write_text("preserve")
            with self.assertRaises(SystemExit):
                sample_main(["--output-dir", str(output)])
            self.assertEqual(marker.read_text(), "preserve")
            with self.assertRaises(SystemExit):
                sample_main(
                    [
                        "--recording",
                        str(ROOT / "tests/fixtures/role_pilot.json"),
                        "--output-dir",
                        str(Path(directory) / "unlabelled"),
                    ]
                )
            self.assertFalse((Path(directory) / "unlabelled").exists())

    def test_sample_cli_retains_unresolved_evidence_and_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            record = copy.deepcopy(self.record)
            record["relations"][0]["direction"] = "forward"
            source = root / "input.json"
            original = json.dumps(record).encode()
            source.write_bytes(original)
            output = root / "sample"
            with self.assertRaises(SystemExit):
                sample_main(
                    [
                        "--recording",
                        str(source),
                        "--source-kind",
                        "synthetic",
                        "--output-dir",
                        str(output),
                    ]
                )
            report = json.loads((output / "audit.json").read_text())
            self.assertEqual(report["observation_statuses"]["unexpected-direction"], 1)
            self.assertEqual(report["distinct_role_assertions"], 2)
            self.assertEqual(
                (output / report["sources"][0]["archived_input"]).read_bytes(), original
            )

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

    def test_release_photography_and_video_cinematography(self):
        release = MB["release/album"]
        graph = Graph()
        schema = self.mapping.schema_graph()
        for kind, type_id, identifier, range_class in (
            (
                "artist",
                "0b58dc9b-9c49-4b19-bb58-9c06d41c8fbf",
                "photographer",
                ENTITY.Artist,
            ),
            ("label", "813919d5-a93d-4334-89df-ffa2f9b8ff43", "agency", ENTITY.Label),
        ):
            with self.subTest(kind=kind):
                credit = {
                    "type": "photography",
                    "type-id": type_id,
                    "direction": "backward",
                    "target-type": kind,
                    kind: {"id": identifier},
                    "attributes": ["additional"],
                    "attribute-ids": {
                        "additional": "0a5341f8-3b1d-4f99-a0c6-26b7f4e42c7f"
                    },
                }
                self.convert({"id": "album", "relations": [credit]}, "release", graph)
                role = ROLE[type_id]
                endpoint = MB[f"{kind}/{identifier}"]
                self.assertEqual(
                    set(graph.subject_objects(role)), {(release, endpoint)}
                )
                self.assertEqual(
                    set(schema.objects(role, RDFS.domain)), {ENTITY.Release}
                )
                self.assertEqual(set(schema.objects(role, RDFS.range)), {range_class})
                self.assertFalse(list(schema.objects(role, RDFS.subPropertyOf)))
                observation = graph.value(predicate=RDF.predicate, object=role)
                self.assertIn((observation, RDF.subject, release), graph)
                self.assertIn((observation, RDF.object, endpoint), graph)
                self.assertIn(
                    (observation, TERMS.attribute, Literal("additional")), graph
                )
                self.assertEqual(
                    json.loads(str(graph.value(observation, TERMS.sourcePayload))),
                    credit,
                )

        photo = self.record["relations"][1]
        cinema = {
            "type": "cinematographer",
            "type-id": "4b290951-ab5e-4605-a304-650aa1f35377",
            "direction": "backward",
            "target-type": "artist",
            "artist": {"id": "cinematographer"},
        }
        self.convert(
            {"id": "video", "video": True, "relations": [photo, cinema]}, graph=graph
        )
        self.assertEqual(
            set(graph.subject_objects(PHOTOGRAPHER)),
            {(MB["recording/video"], MB[f"artist/{photo['artist']['id']}"])},
        )
        self.assertEqual(
            set(graph.subject_objects(WDT.P344)),
            {(MB["recording/video"], MB["artist/cinematographer"])},
        )
        self.assertFalse(list(graph.subject_objects(WDT.P14574)))

    def test_inverse_label_photography_withholds_invalid_credits(self):
        inverse = {
            "type": "photography",
            "type-id": "813919d5-a93d-4334-89df-ffa2f9b8ff43",
            "direction": "forward",
            "target-type": "release",
            "release": {"id": "album"},
            "attributes": ["additional"],
        }
        for changes, status in (
            ({"direction": "backward"}, "unexpected-direction"),
            ({"type-id": None}, "missing-type-id"),
            ({"type-id": "unknown"}, "unrecognized-type-id"),
            (
                {"type-id": "0b58dc9b-9c49-4b19-bb58-9c06d41c8fbf"},
                "unexpected-endpoints",
            ),
        ):
            with self.subTest(changes=changes):
                credit = inverse | changes
                graph = self.convert({"id": "agency", "relations": [credit]}, "label")
                node = next(graph.subjects(TERMS.mappingStatus, Literal(status)))
                self.assertIn((node, DCTERMS.source, MB["label/agency"]), graph)
                self.assertEqual(
                    json.loads(str(graph.value(node, TERMS.sourcePayload))), credit
                )
                self.assertFalse(list(graph.subjects(RDF.type, RDF.Statement)))
                self.assertFalse(
                    list(graph.triples((MB["release/album"], None, MB["label/agency"])))
                )
                self.assertFalse(list(graph.subject_objects(WDT.P344)))

    def test_recording_remix_qualifiers_control_adaptation(self):
        remix = self.record["relations"][2]
        artist = MB[f"artist/{remix['artist']['id']}"]
        role = ROLE["7950be4d-13a3-48e7-906b-5af562e39544"]
        additional_id = "0a5341f8-3b1d-4f99-a0c6-26b7f4e42c7f"
        assistant_id = "8c4196b1-7053-4b16-921a-f22b2898ed44"
        for qualifiers, adapted in (
            ({"attributes": []}, True),
            ({"attributes": ["additional"]}, True),
            (
                {
                    "attributes": ["additional"],
                    "attribute-ids": {"additional": additional_id},
                },
                True,
            ),
            ({"attributes": ["assistant"]}, False),
            ({"attributes": ["additional", "assistant"]}, False),
            ({"attributes": ["unknown"]}, False),
            ({}, False),
            ({"attributes": None}, False),
            ({"attributes": True}, False),
            ({"attributes": [], "attribute-ids": {"assistant": assistant_id}}, False),
            (
                {
                    "attributes": ["additional"],
                    "attribute-ids": {"additional": assistant_id},
                },
                False,
            ),
            (
                {
                    "attributes": [],
                    "attribute-credits": {"assistant": "assistant remixer"},
                },
                False,
            ),
            ({"attributes": [], "attribute-values": {"task": "one track only"}}, False),
        ):
            with self.subTest(qualifiers=qualifiers):
                relation = {k: v for k, v in remix.items() if k != "attributes"}
                relation.update(qualifiers)
                graph = self.convert(self.record | {"relations": [relation]})
                self.assertEqual((self.subject, WDT.P5202, artist) in graph, adapted)
                self.assertIn((self.subject, role, artist), graph)
                node = next(graph.subjects(RDF.predicate, role))
                self.assertEqual(
                    json.loads(str(graph.value(node, TERMS.sourcePayload))), relation
                )

    def test_remix_credit_is_scoped_to_its_recording_or_release(self):
        remix = self.record["relations"][2]
        artist = MB[f"artist/{remix['artist']['id']}"]
        release_id = "synthetic-release"
        release = {
            "id": release_id,
            "media": [
                {
                    "tracks": [
                        {"recording": self.record},
                        {"recording": {"id": "uncredited-track"}},
                    ]
                }
            ],
        }
        graph = self.convert(release, "release")
        self.assertEqual(
            set(graph.subject_objects(WDT.P5202)), {(self.subject, artist)}
        )

        release_type = "ac6a86db-f757-4815-a07e-744428d2382b"
        release_credit = remix | {
            "type-id": release_type,
            "attributes": [],
            "artist": {"id": "release-remixer"},
        }
        release_artist = MB["artist/release-remixer"]
        graph = self.convert(release | {"relations": [release_credit]}, "release")
        release_uri = MB[f"release/{release_id}"]
        self.assertEqual(
            set(graph.subject_objects(WDT.P5202)),
            {(self.subject, artist), (release_uri, release_artist)},
        )
        self.assertIn((release_uri, ROLE[release_type], release_artist), graph)

        inverse = {k: v for k, v in release_credit.items() if k != "artist"}
        inverse.update(
            {
                "target-type": "release",
                "release": {"id": release_id},
                "direction": "forward",
            }
        )
        graph = self.convert(
            {"id": "release-remixer", "relations": [inverse]}, "artist"
        )
        self.assertEqual(
            set(graph.subject_objects(WDT.P5202)), {(release_uri, release_artist)}
        )

    def test_adaptation_and_remix_role_have_distinct_answers(self):
        remix = self.record["relations"][2]
        role = ROLE["7950be4d-13a3-48e7-906b-5af562e39544"]
        credits = [
            remix | {"type": "renamed role", "artist": {"id": "remixer"}},
            remix | {"attributes": ["assistant"], "artist": {"id": "assistant"}},
            remix
            | {
                "type": "mix",
                "type-id": "3e3102e1-1896-4f50-b5b2-dd9824e46efe",
                "attributes": [],
                "artist": {"id": "mixer"},
            },
            {
                "type": "arranger",
                "target-type": "artist",
                "direction": "backward",
                "artist": {"id": "arranger"},
            },
            remix | {"type-id": "unrecognized", "artist": {"id": "unknown"}},
            remix | {"direction": "forward", "artist": {"id": "wrong-direction"}},
        ]
        graph = self.convert(self.record | {"relations": credits})
        self.assertEqual(
            set(graph.objects(self.subject, WDT.P5202)),
            {MB["artist/remixer"], MB["artist/arranger"]},
        )
        self.assertEqual(
            set(graph.objects(self.subject, role)),
            {MB["artist/remixer"], MB["artist/assistant"]},
        )
        schema = self.mapping.schema_graph()
        for remix_role in (role, ROLE["ac6a86db-f757-4815-a07e-744428d2382b"]):
            self.assertEqual(
                set(schema.objects(remix_role, RDFS.subPropertyOf)), {WDT.P767}
            )
            self.assertNotIn((WDT.P5202, RDFS.subPropertyOf, remix_role), schema)

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
        broad = list(
            graph.query(
                f"""PREFIX rdfs: <{RDFS}>
                SELECT DISTINCT ?artist WHERE {{
                    <{self.subject}> ?role ?artist .
                    ?role rdfs:subPropertyOf* <{WDT.P767}> .
                }}"""
            )
        )
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
        # Several roles and an explicit generic assertion for one pair must
        # still produce one contributor pair, without broadening exact roles.
        engineer = MB["artist/00000000-0000-4000-8000-000000000002"]
        generic = URIRef("urn:generic:artist")
        data.add((self.subject, PHOTOGRAPHER, engineer))
        data.add((self.subject, WDT.P767, engineer))
        data.add((self.subject, WDT.P767, generic))
        for context in (data, dataset.graph(URIRef("urn:unrelated:schema"))):
            decoy = URIRef(f"{context.identifier}:unreviewed-role")
            data.add((URIRef("urn:decoy:record"), decoy, URIRef("urn:decoy:artist")))
            context.add((decoy, RDFS.subPropertyOf, WDT.P767))
        query = (ROOT / "doc/queries/pilot_contributors.rq").read_text()
        results = list(dataset.query(query))
        rows = set(tuple(row) for row in results)
        self.assertEqual(len(results), 5)
        self.assertEqual(len(rows), 5)
        self.assertIn((URIRef("urn:legacy:record"), URIRef("urn:legacy:artist")), rows)
        self.assertNotIn((URIRef("urn:other:record"), URIRef("urn:other:artist")), rows)
        self.assertNotIn((URIRef("urn:decoy:record"), URIRef("urn:decoy:artist")), rows)
        exact = list(
            data.query(
                f"SELECT ?artist WHERE {{ <{self.subject}> <{ENGINEER}> ?artist }}"
            )
        )
        self.assertEqual(exact, [(engineer,)])
        plain = set(data.subject_objects(WDT.P767))
        self.assertEqual(len(plain), 3)
        self.assertTrue(plain < rows)

    def test_every_inventoried_role_accepts_both_source_endpoints(self):
        inventory = (ROOT / "doc/relationship_inventory.md").read_text()
        entries = re.findall(
            r"\| (recording|release) → (artist|label) \| \[([^]]+)\].*?`([0-9a-f-]{36})`",
            inventory,
        )
        self.assertEqual(len(entries), 35)
        self.assertEqual({entry[3] for entry in entries}, set(self.mapping.by_id))
        graph = Graph()
        for kind, target_kind, label, type_id in entries:
            with self.subTest(kind=kind, target_kind=target_kind, label=label):
                record_id = f"synthetic-{type_id}"
                target_id = f"synthetic-{target_kind}"
                relation = {
                    "type": label,
                    "type-id": type_id,
                    "target-type": target_kind,
                    "direction": "backward",
                    target_kind: {"id": target_id},
                }
                self.convert({"id": record_id, "relations": [relation]}, kind, graph)
                inverse = {
                    key: value for key, value in relation.items() if key != target_kind
                }
                inverse.update(
                    {
                        "target-type": kind,
                        "direction": "forward",
                        kind: {"id": record_id},
                    }
                )
                self.convert(
                    {"id": target_id, "relations": [inverse]}, target_kind, graph
                )
                self.assertEqual(
                    list(graph.triples((None, ROLE[type_id], None))),
                    [
                        (
                            MB[f"{kind}/{record_id}"],
                            ROLE[type_id],
                            MB[f"{target_kind}/{target_id}"],
                        )
                    ],
                )
                self.assertEqual(
                    len(list(graph.subjects(RDF.predicate, ROLE[type_id]))), 2
                )
        self.assertEqual(
            len(list(graph.subjects(TERMS.mappingStatus, Literal("mapped")))),
            2 * len(entries),
        )
        self.assertFalse(list(graph.triples((None, WDT.P767, None))))

    def test_observation_query_keeps_duplicate_inverse_and_qualifier_units_distinct(
        self,
    ):
        relation = copy.deepcopy(self.record["relations"][0])
        relation["attributes"] = ["assistant", "additional"]
        later = relation | {"begin": "2005"}
        record = {
            "id": self.record["id"],
            "relations": [relation, copy.deepcopy(relation), later],
        }
        inverse = {key: value for key, value in relation.items() if key != "artist"}
        inverse.update(
            {
                "target-type": "recording",
                "direction": "forward",
                "recording": {"id": self.record["id"]},
            }
        )
        artist_id = relation["artist"]["id"]
        dataset = Dataset()
        graph = dataset.graph(URIRef("urn:linkedmusic:pilot:data"))
        self.convert(record, graph=graph)
        self.convert({"id": artist_id, "relations": [inverse]}, "artist", graph)
        self.assertEqual(len(list(graph.triples((None, ENGINEER, None)))), 1)
        self.assertEqual(len(list(graph.subjects(RDF.type, RDF.Statement))), 3)
        query = (
            (ROOT.parent / "evaluation/queries/cq09.rq")
            .read_text()
            .replace("{{musicbrainz}}", "<urn:linkedmusic:pilot:data>")
        )
        rows = list(
            dataset.query(
                query,
                initNs={"rdf": RDF, "dcterms": DCTERMS, "mbrel": ROLE, "mbterm": TERMS},
            )
        )
        self.assertEqual(len(rows), 6)  # Two attribute bindings per observation.
        self.assertEqual(len({row.observation for row in rows}), 3)
        self.assertEqual(
            {str(row.attribute) for row in rows}, {"assistant", "additional"}
        )
        for row in rows:
            payload = json.loads(str(row.payload))
            self.assertIn(payload, [relation, later, inverse])
            self.assertEqual(str(row.begin), payload["begin"])
            self.assertEqual(str(row.end), payload["end"])
            self.assertEqual(str(row.direction), payload["direction"])
            self.assertEqual(
                row.source,
                MB[f"artist/{artist_id}"] if payload == inverse else self.subject,
            )
            self.assertEqual(
                (row.recording, row.artist), (self.subject, MB[f"artist/{artist_id}"])
            )

    def test_observation_identity_covers_payload_but_not_record_metadata(self):
        record = copy.deepcopy(self.record)
        relation = record["relations"][0]
        record["relations"] = [relation]
        relation["unknown-qualifier"] = {"nested": [None, "café"], "empty": {}}
        graph = self.convert(record)
        node = next(graph.subjects(RDF.type, RDF.Statement))
        # Object key ordering is immaterial, including nested objects.
        record["relations"] = [json.loads(json.dumps(relation, sort_keys=True))]
        record["title"] = "Changed parent metadata outside the relationship payload"
        self.convert(record, graph=graph)
        self.assertEqual(list(graph.subjects(RDF.type, RDF.Statement)), [node])
        roundtrip = Graph().parse(
            data=graph.serialize(format="turtle"), format="turtle"
        )
        self.assertEqual(
            json.loads(str(roundtrip.value(node, TERMS.sourcePayload))), relation
        )
        record["relations"][0]["artist"]["name"] = "Changed embedded target name"
        self.convert(record, graph=graph)
        self.assertEqual(len(list(graph.subjects(RDF.type, RDF.Statement))), 2)
        self.assertEqual(len(list(graph.triples((None, ENGINEER, None)))), 1)

    def test_unresolved_candidate_detection_has_a_bounded_scope(self):
        # An unknown UUID plus a pilot label is retained, not assigned that role.
        # When neither UUID nor endpoint-specific label identifies the pilot,
        # ordinary nonpilot conversion applies and no observation is promised.
        record = copy.deepcopy(self.record)
        record["relations"] = [record["relations"][0]]
        record["relations"][0]["type-id"] = "00000000-0000-4000-8000-000000000099"
        graph = self.convert(record)
        self.assertEqual(
            len(
                list(
                    graph.subjects(TERMS.mappingStatus, Literal("unrecognized-type-id"))
                )
            ),
            1,
        )
        self.assertFalse(list(graph.subjects(RDF.type, RDF.Statement)))
        record["relations"][0]["type"] = "unknown role outside this pilot"
        graph = self.convert(record)
        self.assertFalse(list(graph.subjects(RDF.type, TERMS.RelationshipObservation)))

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

    def test_null_attribute_list_retains_payload_and_role(self):
        record = copy.deepcopy(self.record)
        record["relations"] = [record["relations"][0] | {"attributes": None}]
        graph = self.convert(record)
        node = next(graph.subjects(RDF.predicate, ENGINEER))
        self.assertIsNone(
            json.loads(str(graph.value(node, TERMS.sourcePayload)))["attributes"]
        )
        self.assertFalse(list(graph.objects(node, TERMS.attribute)))
        self.assertEqual(len(list(graph.triples((None, ENGINEER, None)))), 1)

    def test_schema_cli_supplies_broad_query_without_sample_conversion(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "schema"
            mapping = ROOT / "src/rdf_conversion_config/relations.json"
            command = [
                sys.executable,
                str(ROOT / "src/emit_relationship_schema.py"),
                "--relations",
                str(mapping),
                "--output-dir",
                str(output),
            ]
            run = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            dataset = Dataset(default_union=False)
            data = dataset.graph(URIRef("urn:linkedmusic:pilot:data"))
            for triple in self.convert():
                data.add(triple)
            query = (ROOT / "doc/queries/pilot_contributors.rq").read_text()
            self.assertFalse(list(dataset.query(query)))
            dataset.graph(URIRef("urn:linkedmusic:pilot:schema")).parse(
                output / "schema.ttl", format="turtle"
            )
            self.assertEqual(len(list(dataset.query(query))), 3)
            audit = json.loads((output / "audit.json").read_text())
            self.assertEqual(
                audit["relations_sha256"],
                hashlib.sha256(mapping.read_bytes()).hexdigest(),
            )
            self.assertEqual(
                (output / "relations.json").read_bytes(), mapping.read_bytes()
            )
            self.assertEqual(
                audit["schema_sha256"],
                hashlib.sha256((output / "schema.ttl").read_bytes()).hexdigest(),
            )
            before = {p.name: p.read_bytes() for p in output.iterdir()}
            rerun = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(rerun.returncode, 0)
            self.assertEqual(before, {p.name: p.read_bytes() for p in output.iterdir()})

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

    def test_worker_serialization_preserves_schema(self):
        restored = pickle.loads(pickle.dumps(self.mapping))
        self.assertEqual(restored.by_id, self.mapping.by_id)
        schema = restored.schema_graph()
        for role in restored.by_id.values():
            for prop in (RDFS.label, RDFS.comment, RDFS.domain, RDFS.range):
                self.assertIsNotNone(schema.value(role.predicate, prop))


if __name__ == "__main__":
    unittest.main()
