"""Validate real converter output and uncertainty-aware query behavior."""

import csv
import json
import unittest

from pyshacl import validate
from rdflib import Dataset, Graph, Literal, Namespace, RDF, URIRef
from rdflib.namespace import DCTERMS, SDO, XSD

import test_source_provenance as provenance

ROOT = provenance.fixtures.ROOT.parent
LM, DIAMM = provenance.LM, provenance.DIAMM
ONTOLOGY = ROOT / "shared/ontology"
QUERIES = ROOT / "diamm/doc/queries"


class ShapeTestCase(unittest.TestCase):
    def check_shape(self, graph, expected=True):
        conforms, _, report = validate(
            graph,
            shacl_graph=str(ONTOLOGY / "shapes.ttl"),
            ont_graph=str(ONTOLOGY / "preservation.ttl"),
            inference="none",
        )
        self.assertEqual(conforms, expected, report)


class ProvenanceContractTests(ShapeTestCase):
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

    def query(self, name):
        return self.dataset.query((QUERIES / name).read_text())

    def test_actual_converter_output_satisfies_shapes_including_unknown_evidence(self):
        self.check_shape(self.graph)
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
                self.check_shape(graph, False)
        legacy = next(
            self.graph.subjects(
                LM.validationFlag, Literal("legacy-unqualified-provenance")
            )
        )
        graph = self.graph + Graph()
        graph.add((legacy, LM.uncertain, Literal(False)))
        self.check_shape(graph, False)
        graph = self.graph + Graph()
        graph.remove((node, LM.place, None))
        self.check_shape(graph, False)

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


class OrganizationProvenanceTests(ShapeTestCase):
    def setUp(self):
        self.case = provenance.SourceProvenanceTests()
        self.case.setUp()
        self.addCleanup(self.case.doCleanups)
        self.fixture = self.case.fixture

    def test_organization_entries_survive_both_clis_and_query_in_pairs(self):
        first = {
            "url": f"{DIAMM}sources/5/",
            "city": "Siena",
            "city_uncertain": False,
            "entity_uncertain": True,
            "region": "Tuscany",
            "region_uncertain": False,
            "country": "Italy",
            "country_uncertain": True,
            "protectorate": "A",
            "source": "MS A",
            "extra": ["001"],
        }
        second = dict(
            first,
            city="Bologna",
            city_uncertain=True,
            entity_uncertain=False,
            region="Emilia-Romagna",
            region_uncertain=True,
            country_uncertain=False,
            protectorate="B",
        )
        unknown = {
            "url": f"{DIAMM}sources/6/",
            "city": '  É, "NA"  ',
            "region_uncertain": None,
            "country_uncertain": "false",
        }
        entity_only = {
            "url": f"{DIAMM}sources/9/",
            "source": "MS entity-only",
            "entity_uncertain": False,
            "city_uncertain": False,
            "region_uncertain": False,
            "country_uncertain": False,
        }
        record = {
            "pk": 1,
            "name": "Institution",
            "organization_type": "Institution",
            "location": {
                "name": "Florence",
                "url": f"{DIAMM}cities/7/",
                "parent": "Italy",
            },
            "source_provenance": [
                first,
                second,
                dict(reversed(first.items())),
                unknown,
                entity_only,
            ],
            "copied_sources": [{"url": f"{DIAMM}sources/7/"}],
            "related_sources": [{"url": f"{DIAMM}sources/8/", "relationship": "owner"}],
        }
        raw = self.fixture.directory / "data/raw/organizations"
        raw.mkdir(parents=True)
        (raw / "1.json").write_text(json.dumps(record))
        self.fixture.run_script("to_csv.py")
        with self.fixture.relations.open(newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertCountEqual(
            [
                json.loads(row["source_provenance"])
                for row in rows
                if row["source_provenance"]
            ],
            [first, second, unknown, entity_only],
        )
        self.fixture.run_script("convert_rdf.py")
        graph = Graph().parse(
            self.fixture.directory / "data/RDF/diamm.ttl", format="turtle"
        )
        dataset = Dataset()
        target = dataset.graph(URIRef(str(LM)))
        target += graph
        # A different named graph must not fill in the missing source flag.
        (unknown_node,) = graph.objects(DIAMM["sources/6"], LM.organizationProvenance)
        dataset.graph(URIRef("urn:other")).add(
            (unknown_node, LM.cityUncertain, Literal(False))
        )
        query = (QUERIES / "organization_provenance.rq").read_text()
        answers = list(dataset.query(query))
        self.assertEqual(len(answers), 4)
        self.assertEqual(len({row.observation for row in answers}), 4)
        self.assertEqual(
            {row.organization for row in answers}, {DIAMM["organizations/1"]}
        )
        self.assertCountEqual(
            [json.loads(row.evidence) for row in answers],
            [first, second, unknown, entity_only],
        )
        for row in answers:
            entry = json.loads(row.evidence)
            self.assertEqual(row.source, URIRef(entry["url"].rstrip("/")))
            for field in ("city", "region", "country", "protectorate"):
                expected = (
                    Literal(entry[field], datatype=XSD.string)
                    if field in entry
                    else None
                )
                self.assertEqual(row[field], expected, field)
            for field in ("city", "entity", "region", "country"):
                value = entry.get(f"{field}_uncertain")
                has_target = field == "entity" or field in entry
                expected = (
                    Literal(value) if has_target and type(value) is bool else None
                )
                self.assertEqual(row[f"{field}Uncertain"], expected, field)
        # A direct filter on the graph must also exclude entity-only entries.
        unflagged_city = dataset.query(
            f"""PREFIX d: <{LM}>
            SELECT DISTINCT ?source WHERE {{ GRAPH d: {{
              ?source d:organizationProvenance ?entry . ?entry d:cityUncertain false
            }} }}"""
        )
        self.assertEqual([row.source for row in unflagged_city], [DIAMM["sources/5"]])
        org = DIAMM["organizations/1"]
        self.assertIn((org, SDO.location, DIAMM["cities/7"]), graph)
        for source in (5, 6):
            self.assertEqual(
                set(graph.predicates(DIAMM[f"sources/{source}"])),
                {LM.organizationProvenance},
            )
        self.assertEqual(
            set(graph.predicate_objects(DIAMM["sources/7"])),
            {(provenance.WDT.P1071, org)},
        )
        self.assertEqual(
            set(graph.predicate_objects(DIAMM["sources/8"])),
            {(provenance.WDT.P127, org)},
        )
        self.check_shape(graph)

    def test_legacy_organization_evidence_and_mixed_rows(self):
        legacy = {"key1": "organization:7", "key2": "source:5", "type": "provenance"}
        self.fixture.relations.write_text(
            "key1,key2,type\norganization:7,source:5,provenance\n"
        )
        graph = self.fixture.convert()
        source = DIAMM["sources/5"]
        (node,) = graph.objects(source, LM.organizationProvenance)
        self.assertEqual(
            set(graph),
            {
                (source, LM.organizationProvenance, node),
                (node, RDF.type, LM.OrganizationProvenanceObservation),
                (node, DCTERMS.source, DIAMM["organizations/7"]),
                (node, LM.validationFlag, Literal("legacy-unqualified-provenance")),
            },
        )
        fresh = self.case.relation(
            "organization",
            {
                "url": f"{DIAMM}sources/5/",
                "country_uncertain": False,
                "city": " \u00a0 ",
                "city_uncertain": True,
            },
        )
        self.case.write_relations([legacy, fresh, legacy, fresh])
        mixed = self.fixture.convert()
        self.assertTrue(all(triple in mixed for triple in graph))
        self.assertEqual(len(set(mixed.objects(source, LM.organizationProvenance))), 2)
        dataset = Dataset()
        target = dataset.graph(URIRef(str(LM)))
        target += mixed
        rows = list(dataset.query((QUERIES / "organization_provenance.rq").read_text()))
        self.assertCountEqual(
            [
                (
                    row.evidence,
                    row.city,
                    row.cityUncertain,
                    row.country,
                    row.countryUncertain,
                )
                for row in rows
            ],
            [
                (None, None, None, None, None),
                (
                    Literal(fresh["source_provenance"], datatype=XSD.string),
                    Literal(" \u00a0 ", datatype=XSD.string),
                    None,
                    None,
                    None,
                ),
            ],
        )
        self.check_shape(mixed)
        mixed.add((node, LM.cityName, Literal("Florence", datatype=XSD.string)))
        self.check_shape(mixed, False)

    def test_organization_shape_requires_a_named_place_for_each_place_flag(self):
        self.case.write_relations(
            [self.case.relation("organization", {"url": f"{DIAMM}sources/5/"})]
        )
        graph = self.fixture.convert()
        (node,) = graph.objects(DIAMM["sources/5"], LM.organizationProvenance)
        for field in ("city", "region", "country"):
            with self.subTest(field=field):
                flagged = graph + Graph()
                flagged.add((node, LM[f"{field}Uncertain"], Literal(False)))
                self.check_shape(flagged, False)
                flagged.add(
                    (node, LM[f"{field}Name"], Literal("  ", datatype=XSD.string))
                )
                self.check_shape(flagged, False)
                flagged.set(
                    (node, LM[f"{field}Name"], Literal(" Pavia ", datatype=XSD.string))
                )
                self.check_shape(flagged)

    def test_organization_provenance_requires_matching_source_endpoint(self):
        self.case.write_relations(
            [self.case.relation("organization", {"url": f"{DIAMM}sources/6/"})]
        )
        with self.assertRaisesRegex(ValueError, "organization:7.*source:5"):
            self.fixture.convert()


if __name__ == "__main__":
    unittest.main()
