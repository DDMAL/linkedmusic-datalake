"""Qualified city/region provenance through the extraction and RDF CLIs."""

import csv
import json
import unittest

from rdflib import Graph, Literal, RDF
from rdflib.namespace import DCTERMS, XSD

import test_external_identifier_text as fixtures

DIAMM, LM, WDT = fixtures.DIAMM, fixtures.LM, fixtures.WDT


def observation_triples(
    graph,
    source,
    place,
    field,
    evidence=None,
    *,
    uncertain=None,
    earliest=None,
    latest=None,
    flags=(),
):
    """Specify the expected vocabulary; discover only the opaque observation IRI."""
    candidates = {
        node
        for node in graph.objects(source, LM.sourceProvenance)
        if (node, LM.place, place) in graph
        and (
            set(graph.objects(node, LM.sourceProvenanceJson))
            == (
                {Literal(evidence, datatype=XSD.string)}
                if evidence is not None
                else set()
            )
        )
    }
    if len(candidates) != 1:
        raise AssertionError(
            f"Expected one observation for {source}, {place}, {evidence}; got {candidates}"
        )
    node = candidates.pop()
    expected = {
        (source, LM.sourceProvenance, node),
        (node, RDF.type, LM.SourceProvenanceObservation),
        (node, LM.place, place),
        (node, DCTERMS.source, place),
        (node, LM.sourceField, Literal(field, datatype=XSD.string)),
    }
    if evidence is not None:
        expected.add(
            (node, LM.sourceProvenanceJson, Literal(evidence, datatype=XSD.string))
        )
    if uncertain is not None:
        expected.add((node, LM.uncertain, Literal(uncertain)))
    for value, predicate in ((earliest, LM.earliestYear), (latest, LM.latestYear)):
        if value is not None:
            expected.add(
                (node, predicate, Literal(value, datatype=XSD.gYear, normalize=False))
            )
    expected.update((node, LM.validationFlag, Literal(flag)) for flag in flags)
    return expected


class SourceProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.ExternalIdentifierTextTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.write_exports({})

    def write_relations(self, rows):
        with self.fixture.relations.open("w", newline="", encoding="utf-8") as target:
            writer = csv.DictWriter(
                target, fieldnames=("key1", "key2", "type", "source_provenance")
            )
            writer.writeheader()
            writer.writerows(rows)

    def relation(self, field, evidence, source=5, place=7):
        return {
            "key1": f"{field}:{place}",
            "key2": f"source:{source}",
            "type": "provenance",
            "source_provenance": json.dumps(evidence, ensure_ascii=False),
        }

    def test_csv_preserves_paired_qualifiers_and_has_no_unqualified_location(self):
        rows = []
        expected_cases = []
        for field in ("city", "region"):
            for i, (uncertain, start, end) in enumerate(
                ((False, 1400, 1450), (True, 1500, 1550)), 1
            ):
                evidence = {
                    "url": f"{DIAMM}sources/{i}/",
                    f"{field}_uncertain": uncertain,
                    "earliest_year": start,
                    "latest_year": end,
                    "name": '  NA, "É"\nQ42  ',
                    "extra": {"unknown": [None, "00123"]},
                }
                row = self.relation(field, evidence, source=i)
                rows.append(row)
                expected_cases.append(
                    (
                        field,
                        i,
                        row["source_provenance"],
                        uncertain,
                        str(start),
                        str(end),
                    )
                )
        self.write_relations(rows)
        graph = self.fixture.convert()
        expected = set()
        for field, i, evidence, uncertain, start, end in expected_cases:
            place = DIAMM[f"{'cities' if field == 'city' else 'regions'}/7"]
            expected.update(
                observation_triples(
                    graph,
                    DIAMM[f"sources/{i}"],
                    place,
                    field,
                    evidence,
                    uncertain=uncertain,
                    earliest=start,
                    latest=end,
                )
            )
        self.fixture.assert_graph_and_roundtrip(graph, expected)
        self.assertFalse(
            graph.query(
                f"""ASK {{
            VALUES ?p {{ <{WDT.P131}> <{WDT.P276}> <{WDT.P1071}> <{WDT.P571}> }}
            ?s ?p ?o . }}"""
            )
        )

    def test_missing_null_invalid_and_reversed_values_keep_raw_evidence(self):
        cases = [
            (
                {},
                None,
                None,
                None,
                ("missing-uncertainty", "missing-earliest-year", "missing-latest-year"),
            ),
            (
                {"city_uncertain": None, "earliest_year": None, "latest_year": None},
                None,
                None,
                None,
                ("null-uncertainty", "null-earliest-year", "null-latest-year"),
            ),
            (
                {
                    "city_uncertain": "false",
                    "earliest_year": "0012",
                    "latest_year": "NA",
                },
                None,
                None,
                None,
                ("invalid-uncertainty", "invalid-earliest-year", "invalid-latest-year"),
            ),
            (
                {"city_uncertain": 0, "earliest_year": True, "latest_year": 1400.0},
                None,
                None,
                None,
                ("invalid-uncertainty", "invalid-earliest-year", "invalid-latest-year"),
            ),
            (
                {"city_uncertain": False, "earliest_year": 1500, "latest_year": 1400},
                False,
                "1500",
                "1400",
                ("reversed-year-bounds",),
            ),
            (
                {"city_uncertain": True, "earliest_year": 12, "latest_year": None},
                True,
                "0012",
                None,
                ("null-latest-year",),
            ),
            (
                {"region_uncertain": False, "earliest_year": 0, "latest_year": 10000},
                None,
                None,
                None,
                ("missing-uncertainty", "invalid-earliest-year", "invalid-latest-year"),
            ),
            (
                {
                    "city_uncertain": [],
                    "earliest_year": -44,
                    "latest_year": {"year": 1400},
                },
                None,
                None,
                None,
                ("invalid-uncertainty", "invalid-earliest-year", "invalid-latest-year"),
            ),
        ]
        rows = [
            self.relation("city", {"url": f"{DIAMM}sources/{i}/", **evidence}, source=i)
            for i, (evidence, *_) in enumerate(cases, 1)
        ]
        self.write_relations(rows)
        graph = self.fixture.convert()
        expected = set()
        for i, ((_, uncertain, start, end, flags), row) in enumerate(
            zip(cases, rows), 1
        ):
            expected.update(
                observation_triples(
                    graph,
                    DIAMM[f"sources/{i}"],
                    DIAMM["cities/7"],
                    "city",
                    row["source_provenance"],
                    uncertain=uncertain,
                    earliest=start,
                    latest=end,
                    flags=flags,
                )
            )
        self.fixture.assert_graph_and_roundtrip(graph, expected)

    def test_legacy_rows_are_unknown_provenance_and_keep_other_relationships(self):
        self.fixture.relations.write_text(
            "key1,key2,type\ncity:7,source:5,\nregion:7,source:5,\n"
            "city:7,source:5,\narchive:1,source:5,\norganization:1,region:7,\n"
        )
        graph = self.fixture.convert()
        expected = {
            (DIAMM["sources/5"], WDT.P276, DIAMM["archives/1"]),
            (DIAMM["organizations/1"], LM.organizationLocation, DIAMM["regions/7"]),
        }
        for field, table in (("city", "cities"), ("region", "regions")):
            expected.update(
                observation_triples(
                    graph,
                    DIAMM["sources/5"],
                    DIAMM[f"{table}/7"],
                    field,
                    flags=("legacy-unqualified-provenance",),
                )
            )
        self.fixture.assert_graph_and_roundtrip(graph, expected)
        # Adding the optional column with blank cells must have the same meaning.
        self.write_relations(
            [
                {"key1": "city:7", "key2": "source:5", "type": ""},
                {"key1": "region:7", "key2": "source:5", "type": ""},
            ]
        )
        legacy_graph = self.fixture.convert()
        self.assertEqual(
            set(legacy_graph),
            expected
            - {
                (DIAMM["sources/5"], WDT.P276, DIAMM["archives/1"]),
                (DIAMM["organizations/1"], LM.organizationLocation, DIAMM["regions/7"]),
            },
        )

    def test_duplicate_conflicting_and_reordered_rows_have_stable_distinct_observations(
        self,
    ):
        rows = []
        for field in ("city", "region"):
            for uncertain, start in ((False, 1400), (True, 1500)):
                rows.append(
                    self.relation(
                        field,
                        {
                            "url": f"{DIAMM}sources/5/",
                            f"{field}_uncertain": uncertain,
                            "earliest_year": start,
                            "latest_year": start + 50,
                        },
                    )
                )
        self.write_relations(rows + [rows[0]])
        graph = self.fixture.convert()
        self.assertEqual(
            len(set(graph.objects(DIAMM["sources/5"], LM.sourceProvenance))), 4
        )
        self.write_relations(list(reversed(rows)))
        self.assertEqual(set(graph), set(self.fixture.convert()))
        # A query must join qualifiers on the same observation, never on a source/place pair.
        result = graph.query(
            f"""
            SELECT ?place WHERE {{
              <{DIAMM['sources/5']}> <{LM.sourceProvenance}> ?observation .
              ?observation <{LM.place}> ?place; <{LM.uncertain}> false;
                           <{LM.earliestYear}> "1400"^^<{XSD.gYear}>;
                           <{LM.latestYear}> "1450"^^<{XSD.gYear}> .
            }}"""
        )
        self.assertEqual(
            {row[0] for row in result}, {DIAMM["cities/7"], DIAMM["regions/7"]}
        )
        self.assertFalse(
            graph.query(
                f"""ASK {{
            ?observation <{LM.uncertain}> false; <{LM.earliestYear}> "1500"^^<{XSD.gYear}> . }}"""
            )
        )

    def test_malformed_or_mismatched_evidence_fails_with_relation_context(self):
        for raw in (
            "NA",
            "{",
            "null",
            "[]",
            "true",
            '"text"',
            json.dumps({"url": f"{DIAMM}sources/6/"}),
            json.dumps({"url": "https://example.org/sources/5/"}),
            "{}",
            '{"url":"https://www.diamm.ac.uk/sources/5/","earliest_year":NaN}',
            '{"url":"https://www.diamm.ac.uk/sources/5/","city_uncertain":true,"city_uncertain":false}',
        ):
            with self.subTest(raw=raw):
                self.write_relations(
                    [
                        {
                            "key1": "city:7",
                            "key2": "source:5",
                            "type": "provenance",
                            "source_provenance": raw,
                        }
                    ]
                )
                with self.assertRaisesRegex(ValueError, "city:7.*source:5"):
                    self.fixture.convert()
        for relation_type in ("copied", "NA", "null", "1"):
            with self.subTest(relation_type=relation_type):
                self.write_relations(
                    [{"key1": "city:7", "key2": "source:5", "type": relation_type}]
                )
                with self.assertRaisesRegex(ValueError, "city:7.*source:5"):
                    self.fixture.convert()

    def test_extraction_and_rdf_clis_preserve_both_routes_and_conflicts(self):
        expected_entries = []
        for field, table in (("city", "cities"), ("region", "regions")):
            entries = [
                {
                    "url": f"{DIAMM}sources/5/",
                    "name": '  É, "NA"\n00123  ',
                    f"{field}_uncertain": False,
                    "earliest_year": 1400,
                    "latest_year": 1450,
                },
                {
                    "url": f"{DIAMM}sources/5/",
                    f"{field}_uncertain": True,
                    "earliest_year": None,
                    "latest_year": 1550,
                },
                {"url": f"{DIAMM}sources/5/"},
            ]
            record = {
                "pk": 7,
                "name": "Place",
                "organizations": [],
                "provenance": entries + [entries[0]],
            }
            if field == "city":
                record.update(
                    {
                        "country": {"url": f"{DIAMM}countries/9/", "name": "Hint"},
                        "archives": [],
                    }
                )
            else:
                record.update({"parent": "Hint", "cities": []})
            raw = self.fixture.directory / "data/raw" / table
            raw.mkdir(parents=True)
            (raw / "7.json").write_text(json.dumps(record), encoding="utf-8")
            expected_entries.extend((field, table, entry) for entry in entries)
        self.fixture.run_script("to_csv.py")
        with self.fixture.relations.open(newline="", encoding="utf-8") as source:
            rows = list(csv.DictReader(source))
        provenance = [row for row in rows if row["key2"] == "source:5"]
        self.assertEqual(
            len(provenance), 6
        )  # old pair-only deduplication loses conflicts
        for field, table, entry in expected_entries:
            self.assertTrue(
                any(
                    row["key1"] == f"{field}:7"
                    and json.loads(row["source_provenance"]) == entry
                    for row in provenance
                )
            )
        # Relation evidence bypasses OpenRefine; no entity rows are required.
        self.fixture.run_script("convert_rdf.py")
        graph = Graph().parse(
            self.fixture.directory / "data/RDF/diamm.ttl", format="turtle"
        )
        expected = {(DIAMM["cities/7"], WDT.P17, DIAMM["countries/9"])}
        for field, table, entry in expected_entries:
            raw = next(
                row["source_provenance"]
                for row in provenance
                if row["key1"] == f"{field}:7"
                and json.loads(row["source_provenance"]) == entry
            )
            if "earliest_year" not in entry:
                qualifiers = {
                    "flags": (
                        "missing-uncertainty",
                        "missing-earliest-year",
                        "missing-latest-year",
                    )
                }
            elif entry["earliest_year"] is None:
                qualifiers = {
                    "uncertain": True,
                    "latest": "1550",
                    "flags": ("null-earliest-year",),
                }
            else:
                qualifiers = {"uncertain": False, "earliest": "1400", "latest": "1450"}
            expected.update(
                observation_triples(
                    graph,
                    DIAMM["sources/5"],
                    DIAMM[f"{table}/7"],
                    field,
                    raw,
                    **qualifiers,
                )
            )
        self.fixture.assert_graph_and_roundtrip(graph, expected)


if __name__ == "__main__":
    unittest.main()
