"""Hand-authored controls for scoped identifier joins, separate from live quality."""

import unittest
from pathlib import Path

from rdflib import Dataset, Literal, Namespace, URIRef
from rdflib.namespace import OWL, RDFS

HERE = Path(__file__).resolve().parents[1]
EX = Namespace("https://example.org/identifier-review/")
WD = Namespace("http://www.wikidata.org/entity/")
WDT = Namespace("http://www.wikidata.org/prop/direct/")
LEFT = URIRef("urn:linkedmusic:identifier:a")
RIGHT = URIRef("urn:linkedmusic:identifier:b")


class IdentifierQueryTests(unittest.TestCase):
    def setUp(self):
        self.dataset = Dataset(default_union=False)
        self.dataset.parse(HERE / "fixtures/identifiers.trig", format="trig")

    def query(self, name):
        return list(self.dataset.query((HERE / f"queries/{name}.rq").read_text()))

    def test_direct_and_one_hop_links_preserve_source_nodes_and_all_targets(self):
        actual = {
            (row.record, row.entity, row.qid, str(row.route))
            for row in self.query("identifier_entities")
        }
        self.assertEqual(
            actual,
            {
                (EX.directWork, WD.Q42, WD.Q42, "direct"),
                (EX.localWork, EX.personA, WD.Q42, "P2888"),
                (EX.localWork, EX.personAlias, WD.Q42, "P2888"),
                (EX.ambiguousWork, EX.ambiguous, WD.Q42, "P2888"),
                (EX.ambiguousWork, EX.ambiguous, WD.Q43, "P2888"),
                (EX.badMatchWork, EX.catalogueRecord, WD.Q42, "P2888"),
            },
        )

    def test_compact_zero_or_one_hop_pattern_has_the_same_distinct_pairs(self):
        query = f"""SELECT DISTINCT ?record ?qid WHERE {{
          GRAPH <{LEFT}> {{
            ?record <{WDT.P86}>/<{WDT.P2888}>? ?qid .
            FILTER(isIRI(?qid) && REGEX(STR(?qid),
              "^http://www[.]wikidata[.]org/entity/Q[1-9][0-9]*$"))
          }}
        }}"""
        expected = {(row.record, row.qid) for row in self.query("identifier_entities")}
        self.assertEqual(set(self.dataset.query(query)), expected)
        self.assertEqual(len(expected), 5)

    def test_cross_graph_agreement_preserves_both_source_entities(self):
        rows = self.query("identifier_cross_graph")
        self.assertEqual(len(rows), 6)
        self.assertEqual(
            {tuple(row) for row in rows},
            {
                (LEFT, RIGHT, EX.directWork, WD.Q42, EX.otherWork, EX.personB, WD.Q42),
                (
                    LEFT,
                    RIGHT,
                    EX.localWork,
                    EX.personA,
                    EX.otherWork,
                    EX.personB,
                    WD.Q42,
                ),
                (
                    LEFT,
                    RIGHT,
                    EX.localWork,
                    EX.personAlias,
                    EX.otherWork,
                    EX.personB,
                    WD.Q42,
                ),
                (
                    LEFT,
                    RIGHT,
                    EX.ambiguousWork,
                    EX.ambiguous,
                    EX.otherWork,
                    EX.personB,
                    WD.Q42,
                ),
                (
                    LEFT,
                    RIGHT,
                    EX.ambiguousWork,
                    EX.ambiguous,
                    EX.differentWork,
                    WD.Q43,
                    WD.Q43,
                ),
                (
                    LEFT,
                    RIGHT,
                    EX.badMatchWork,
                    EX.catalogueRecord,
                    EX.otherWork,
                    EX.personB,
                    WD.Q42,
                ),
            },
        )

    def test_link_must_exist_in_the_selected_source_graph(self):
        self.assertNotIn(
            EX.unmatchedWork, {row.record for row in self.query("identifier_entities")}
        )
        self.dataset.graph(LEFT).add((EX.unmatched, WDT.P2888, WD.Q42))
        self.assertIn(
            EX.unmatchedWork, {row.record for row in self.query("identifier_entities")}
        )

    def test_audit_preserves_variant_literal_external_and_multiple_targets(self):
        rows = self.query("identifier_link_audit")
        targets = {
            (row.entity, row.target, str(row.kind)) for row in rows if row.graph == LEFT
        }
        self.assertIn(
            (
                EX.variant,
                URIRef("https://www.wikidata.org/entity/Q42"),
                "variant-QID-IRI",
            ),
            targets,
        )
        self.assertIn((EX.literalTarget, Literal(str(WD.Q42)), "non-IRI"), targets)
        self.assertIn(
            (EX.external, URIRef("https://example.net/authority/42"), "other-IRI"),
            targets,
        )
        self.assertEqual(
            {target for entity, target, kind in targets if entity == EX.ambiguous},
            {WD.Q42, WD.Q43},
        )
        self.assertTrue(all(row.graph in (LEFT, RIGHT) for row in rows))

    def test_identifier_agreement_is_not_identity_verification_or_node_replacement(
        self,
    ):
        before = set(self.dataset.quads())
        rows = self.query("identifier_cross_graph")
        # An asserted but questionable match is still returned; source review
        # must decide whether a catalogue record and the target denote the same thing.
        self.assertIn(EX.catalogueRecord, {row.leftEntity for row in rows})
        self.assertEqual(set(self.dataset.quads()), before)
        self.assertIn(
            (EX.personA, RDFS.label, Literal("Source A name")), self.dataset.graph(LEFT)
        )
        self.assertFalse(any(predicate == OWL.sameAs for _, predicate, _, _ in before))


if __name__ == "__main__":
    unittest.main()
