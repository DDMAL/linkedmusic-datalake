"""Offline auxiliary CSV identifier regressions using the real entity converter."""

import csv
import io
import json
import sys
import unittest
from pathlib import Path

import pandas as pd
from rdflib import Graph, Literal, Namespace, RDF, RDFS
from rdflib.compare import isomorphic

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from convert_to_rdf import load_reconciliation_csv, matched_wikidata, process_entity
from mapping_schema import MappingSchema
from relationship_mapping import RelationshipMappings

WD = Namespace("http://www.wikidata.org/entity/")
WDT = Namespace("http://www.wikidata.org/prop/direct/")
LM = Namespace("https://linkedmusic.ca/graphs/musicbrainz/")
MB = Namespace("https://musicbrainz.org/")
ENTITY_ID = "00000000-0000-4000-8000-000000000001"

# Entity type, source fields, lookup key, predicate, unmatched value, lookup field.
# Expectations are independent of the production schema lookup and ID helper.
CASES = (
    ("artist", {"type": "Person"}, "Person", WDT.P31, "Person", "type"),
    (
        "work",
        {"attributes": [{"type": "Key", "value": "C major"}]},
        "C major",
        WDT.P826,
        "C major",
        "key",
    ),
    ("artist", {"gender": "Other"}, "Other", WDT.P21, "Other", "gender"),
    ("work", {"languages": ["syr"]}, "syr", WDT.P407, "syr", "language"),
    ("release", {"packaging": "None"}, "None", WDT.P9813, "None", "packaging"),
    ("release", {"status": "Official"}, "Official", WDT.P31, "Official", "status"),
    ("release", {"status": "Cancelled"}, "Cancelled", WDT.P1534, "Cancelled", "status"),
    ("release", {"status": "Withdrawn"}, "Withdrawn", WDT.P1534, "Withdrawn", "status"),
    ("release", {"status": "Expunged"}, "Expunged", WDT.P1534, "Expunged", "status"),
)
INVALID_IDS = (
    "Q42suffix",
    "Q42 / Q43",
    "Q42,Q43",
    "Q42\n",
    "Q42 ",
    " Q42",
    "Q42#fragment",
    "Q0",
    "Q042",
    "Q٤٢",
    "Q４２",
    "q42",
    "Q-42",
    "P31",
    "wd:Q42",
    "http://www.wikidata.org/entity/Q42",
    "https://www.wikidata.org/wiki/Q42",
    "https://example.org/Q42",
    "See Q42",
    "Unmatched name — é",
)


class AuxiliaryIdentifierTests(unittest.TestCase):
    def setUp(self):
        config = ROOT / "src/rdf_conversion_config"
        self.schema = MappingSchema({})
        self.schema.add_from_formatted_dict(
            json.loads((config / "mappings.json").read_text())
        )
        self.relations = RelationshipMappings(
            json.loads((config / "relations.json").read_text())
        )
        self.attributes = {
            key: WDT[value] if value else None
            for key, value in json.loads(
                (config / "attribute_mapping.json").read_text()
            ).items()
        }

    def convert(self, entity_type, fields, mapping):
        graph = Graph()
        process_entity(
            {"id": ENTITY_ID, "name": "Q42", **fields},
            entity_type,
            self.schema,
            self.relations,
            mapping,
            self.attributes,
            graph,
        )
        return graph

    def scoped_mapping(self, entity_type, field, cells):
        return {field: {entity_type: cells} if field == "type" else cells}

    def expected(self, entity_type, *properties):
        kinds = {
            "area": LM.Area,
            "artist": LM.Artist,
            "event": LM.Event,
            "instrument": LM.Instrument,
            "label": LM.Label,
            "place": LM.Place,
            "release-group": LM.ReleaseGroup,
            "release": LM.Release,
            "series": LM.Series,
            "work": LM.Work,
        }
        subject = MB[f"{entity_type}/{ENTITY_ID}"]
        return {
            (subject, RDF.type, kinds[entity_type]),
            (subject, RDFS.label, Literal("Q42")),
            *((subject, predicate, value) for predicate, value in properties),
        }

    def test_helper_requires_a_complete_positive_ascii_item_id(self):
        for value in ("Q1", "Q42", "Q123456789"):
            with self.subTest(value=value):
                self.assertTrue(matched_wikidata(value))
        for value in (*INVALID_IDS, "", None, float("nan"), pd.NA, 42, True, [], {}):
            with self.subTest(value=value):
                self.assertFalse(matched_wikidata(value))

    def test_valid_ids_use_canonical_iris_at_every_call_site(self):
        for entity_type, fields, key, predicate, _, field in CASES:
            for value, target in (("Q1", WD.Q1), ("Q42", WD.Q42)):
                with self.subTest(fields=fields, value=value):
                    graph = self.convert(
                        entity_type,
                        fields,
                        self.scoped_mapping(entity_type, field, {key: value}),
                    )
                    self.assertEqual(
                        set(graph), self.expected(entity_type, (predicate, target))
                    )

    def test_rejected_ids_preserve_unmatched_text_at_every_call_site(self):
        for entity_type, fields, key, predicate, original, field in CASES:
            for value in INVALID_IDS:
                with self.subTest(fields=fields, value=value):
                    graph = self.convert(
                        entity_type,
                        fields,
                        self.scoped_mapping(entity_type, field, {key: value}),
                    )
                    # Language exports retain an unmatched full name in the
                    # ID column; other fields use their original JSON text.
                    text = value if predicate == WDT.P407 else original
                    self.assertEqual(
                        set(graph),
                        self.expected(entity_type, (predicate, Literal(text))),
                    )

    def test_missing_blank_and_non_string_matches_preserve_source_values(self):
        for entity_type, fields, key, predicate, original, field in CASES:
            mappings = [{}] + [
                {key: value}
                for value in ("", None, float("nan"), pd.NA, 42, True, [], {})
            ]
            for mapping in mappings:
                with self.subTest(fields=fields, mapping=mapping):
                    self.assertEqual(
                        set(
                            self.convert(
                                entity_type,
                                fields,
                                self.scoped_mapping(entity_type, field, mapping),
                            )
                        ),
                        self.expected(entity_type, (predicate, Literal(original))),
                    )

    def test_primary_and_secondary_types_survive_partial_reconciliation(self):
        graph = self.convert(
            "release-group",
            {"primary-type": "Album", "secondary-types": ["Live", "Compilation"]},
            {"type": {"release-group": {"Album": "Q482994", "Live": "Q42suffix"}}},
        )
        self.assertEqual(
            set(graph),
            self.expected(
                "release-group",
                (WDT.P31, WD.Q482994),
                (WDT.P31, Literal("Live")),
                (WDT.P31, Literal("Compilation")),
            ),
        )

    def test_export_shaped_csv_cells_and_turtle_round_trip(self):
        exports = [
            (
                f"{entity}-types",
                "type",
                "type_@id",
                (entity, {"type": "Type"}, "Type", WDT.P31, "Type", "type"),
            )
            for entity in (
                "area",
                "artist",
                "event",
                "instrument",
                "label",
                "place",
                "release-group",
                "series",
                "work",
            )
        ] + [
            ("keys", "key", "key_@id", CASES[1]),
            ("genders", "gender", "gender_@id", CASES[2]),
            ("languages", "language", "full_language_@id", CASES[3]),
            ("packagings", "packaging", "packaging_@id", CASES[4]),
            ("statuses", "status", "status_@id", CASES[5]),
        ]
        for export, key_column, id_column, case in exports:
            entity_type, fields, key, predicate, original, field = case
            template = json.loads(
                (ROOT / f"openrefine/export/{export}_export.json").read_text()
            )
            for value in ("Q42", "Q42suffix", "Syriac", ""):
                with self.subTest(export=export, value=value):
                    csv_text = io.StringIO()
                    writer = csv.DictWriter(
                        csv_text, fieldnames=[c["name"] for c in template["columns"]]
                    )
                    writer.writeheader()
                    row = {key_column: key, id_column: value}
                    if export == "languages":
                        row["full_language"] = "Syriac"
                    writer.writerow(row)
                    csv_text.seek(0)
                    mapping = load_reconciliation_csv(csv_text, key_column, id_column)
                    graph = self.convert(
                        entity_type,
                        fields,
                        self.scoped_mapping(entity_type, field, mapping),
                    )
                    if value == "Q42":
                        target = WD.Q42
                    elif export == "languages" and value:
                        target = Literal(value)
                    else:
                        target = Literal(original)
                    expected = Graph()
                    for triple in self.expected(entity_type, (predicate, target)):
                        expected.add(triple)
                    self.assertEqual(set(graph), set(expected))
                    restored = Graph().parse(
                        data=graph.serialize(format="turtle"), format="turtle"
                    )
                    self.assertTrue(isomorphic(restored, expected))

    def test_source_relationships_and_url_recognition_survive_auxiliary_fallbacks(self):
        graph = self.convert(
            "release",
            {
                "packaging": "Paper sleeve",
                "status": "Cancelled",
                "artist-credit": [{"artist": {"id": "source-artist"}}],
                "release-group": {"id": "source-group"},
                "relations": [
                    {
                        "target-type": "url",
                        "type": "wikidata",
                        "url": {"resource": "https://www.wikidata.org/wiki/Q42"},
                    }
                ],
            },
            {
                "packaging": {"Paper sleeve": "Q42suffix"},
                "status": {"Cancelled": float("nan")},
            },
        )
        self.assertEqual(
            set(graph),
            self.expected(
                "release",
                (WDT.P9813, Literal("Paper sleeve")),
                (WDT.P1534, Literal("Cancelled")),
                (WDT.P175, MB["artist/source-artist"]),
                (WDT.P361, MB["release-group/source-group"]),
                (WDT.P2888, WD.Q42),
            ),
        )


if __name__ == "__main__":
    unittest.main()
