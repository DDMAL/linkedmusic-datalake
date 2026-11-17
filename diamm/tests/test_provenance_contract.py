"""Validate real converter output and uncertainty-aware query behavior."""

import unittest

from pyshacl import validate
from rdflib import Dataset, Graph, Literal, Namespace, RDF

import test_source_provenance as provenance

ROOT = provenance.fixtures.ROOT.parent
LM, DIAMM = provenance.LM, provenance.DIAMM
ONTOLOGY = ROOT / "shared/ontology"
QUERIES = ROOT / "diamm/doc/queries"


class ProvenanceContractTests(unittest.TestCase):
    def setUp(self):
        self.case = provenance.SourceProvenanceTests()
        self.case.setUp()
        self.addCleanup(self.case.doCleanups)
        # Source 1 has explicit disagreement on one city; region 7 is independent.
        # Source 2 is unknown (absent/null/invalid flags and legacy inputs).
        # Source 3 has metadata-only variants, not qualifier disagreement.
        # Source 4 has differing dates, not different uncertainty flags.
        cases = [
            (1, "city", {"city_uncertain": False}),
            (1, "city", {"city_uncertain": True}),
            (1, "region", {"region_uncertain": False}),
            (2, "city", {}),
            (2, "city", {"city_uncertain": None}),
            (2, "city", {"city_uncertain": "false"}),
            (3, "city", {"city_uncertain": False, "name": "first"}),
            (3, "city", {"city_uncertain": False, "name": "second"}),
            (4, "city", {"city_uncertain": False, "earliest_year": 1400}),
            (4, "city", {"city_uncertain": False, "earliest_year": 1500}),
        ]
        rows = [
            self.case.relation(
                field,
                {"url": f"{DIAMM}sources/{source}/", **evidence},
                source=source,
            )
            for source, field, evidence in cases
        ]
        rows += [rows[0], {"key1": "city:7", "key2": "source:2", "type": ""}]
        self.case.write_relations(rows)
        self.graph = self.case.fixture.convert()
        self.dataset = Dataset()
        target = self.dataset.graph(LM)
        for triple in self.graph:
            target.add(triple)
        # An unrelated graph must not supply missing flags or extra observations.
        poison = self.dataset.graph(Namespace("urn:unrelated:"))
        for node in self.graph.objects(DIAMM["sources/2"], LM.sourceProvenance):
            poison.add((node, LM.uncertain, Literal(False)))

    def check(self, graph, expected=True):
        conforms, _, report = validate(
            graph,
            shacl_graph=str(ONTOLOGY / "shapes.ttl"),
            ont_graph=str(ONTOLOGY / "preservation.ttl"),
            inference="none",
        )
        self.assertEqual(conforms, expected, report)

    def query(self, name):
        return self.dataset.query((QUERIES / name).read_text())

    def test_actual_converter_output_satisfies_shapes_including_unknown_evidence(self):
        self.check(self.graph)
        self.assertEqual(
            len(set(self.graph.subjects(RDF.type, LM.SourceProvenanceObservation))),
            11,
        )
        for predicate in set(self.graph.predicates()):
            if str(predicate).startswith(str(LM)):
                schema = Graph().parse(ONTOLOGY / "preservation.ttl")
                self.assertIn((predicate, RDF.type, RDF.Property), schema)

    def test_shapes_reject_mixed_endpoints_and_fabricated_legacy_qualifiers(self):
        node = next(self.graph.objects(DIAMM["sources/1"], LM.sourceProvenance))
        additions = [
            (node, LM.place, DIAMM["cities/8"]),
            (DIAMM["sources/2"], LM.sourceProvenance, node),
            (node, LM.uncertain, Literal("false")),
            (node, LM.sourceField, Literal("country")),
        ]
        for triple in additions:
            with self.subTest(triple=triple):
                graph = self.graph + Graph()
                graph.add(triple)
                self.check(graph, False)
        legacy = next(
            self.graph.subjects(
                LM.validationFlag, Literal("legacy-unqualified-provenance")
            )
        )
        graph = self.graph + Graph()
        graph.add((legacy, LM.uncertain, Literal(False)))
        self.check(graph, False)
        graph = self.graph + Graph()
        graph.remove((node, LM.place, None))
        self.check(graph, False)

    def test_broad_query_preserves_unknowns_and_returns_qualifiers_with_evidence(self):
        rows = list(self.query("source_provenance.rq"))
        states = {}
        for row in rows:
            states.setdefault(str(row.uncertaintyState), set()).add(row.observation)
            if row.source == DIAMM["sources/2"]:
                self.assertIsNone(row.uncertain)
                self.assertEqual(str(row.uncertaintyState), "unknown")
            expected_disagreement = (
                row.source
                in (
                    DIAMM["sources/1"],
                    DIAMM["sources/4"],
                )
                and row.place == DIAMM["cities/7"]
            )
            self.assertEqual(
                row.hasQualifierDisagreement.toPython(), expected_disagreement
            )
        self.assertEqual(
            {key: len(value) for key, value in states.items()},
            {"uncertain": 1, "source-unflagged": 6, "unknown": 4},
        )
        self.assertEqual(
            set().union(*states.values()),
            set(self.graph.subjects(RDF.type, LM.SourceProvenanceObservation)),
        )
        # The documented VALUES edit restricts results without hiding flags.
        query = (
            (QUERIES / "source_provenance.rq")
            .read_text()
            .replace(
                '{ "uncertain" "source-unflagged" "unknown" }',
                '{ "source-unflagged" }',
            )
        )
        self.assertEqual(
            {row.observation for row in self.dataset.query(query)},
            states["source-unflagged"],
        )

    def test_disagreement_query_compares_only_supported_values_for_the_same_pair(self):
        rows = list(self.query("source_provenance_disagreements.rq"))
        self.assertEqual(len(rows), 2)
        self.assertEqual(
            {(row.source, row.place, row.qualifier) for row in rows},
            {
                (DIAMM["sources/1"], DIAMM["cities/7"], LM.uncertain),
                (DIAMM["sources/4"], DIAMM["cities/7"], LM.earliestYear),
            },
        )
        for row in rows:
            self.assertNotEqual(row.left, row.right)
            self.assertNotEqual(row.leftValue, row.rightValue)

    def test_counts_distinguish_manuscripts_from_observations(self):
        rows = self.query("source_provenance_counts.rq")
        self.assertEqual(
            {
                str(row.uncertaintyState): (int(row.manuscripts), int(row.observations))
                for row in rows
            },
            {"uncertain": (1, 1), "source-unflagged": (3, 6), "unknown": (1, 4)},
        )


if __name__ == "__main__":
    unittest.main()
