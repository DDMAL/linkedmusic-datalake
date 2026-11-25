"""Executable preservation shapes and optional, explicitly versioned lineage."""

import re
import unittest
from pathlib import Path

from owlrl import DeductiveClosure, RDFS_Semantics
from pyshacl import validate
from rdflib import Dataset, Graph, Literal, Namespace, RDF, RDFS, URIRef, XSD

ROOT = Path(__file__).resolve().parents[2]
ONTOLOGY = ROOT / "shared/ontology"
LM = Namespace("https://linkedmusic.ca/terms/preservation/")
DIAMM = Namespace("https://linkedmusic.ca/graphs/diamm/")
MB = Namespace("https://linkedmusic.ca/terms/musicbrainz/")
CKG = Namespace("https://linkedmusic.ca/terms/ckg/")
PROV = Namespace("http://www.w3.org/ns/prov#")
EX = Namespace("urn:linkedmusic:synthetic:")


class PreservationContractTests(unittest.TestCase):
    def check(self, graph, expected=True):
        conforms, _, report = validate(
            graph,
            shacl_graph=str(ONTOLOGY / "shapes.ttl"),
            ont_graph=str(ONTOLOGY / "preservation.ttl"),
            inference="none",
            meta_shacl=True,
        )
        self.assertEqual(conforms, expected, report)

    def lineage(self):
        # All IDs and digests are synthetic shape controls, not source evidence.
        return Graph().parse(
            data="""
            @prefix lm: <https://linkedmusic.ca/terms/preservation/> .
            @prefix prov: <http://www.w3.org/ns/prov#> .
            @prefix ex: <urn:linkedmusic:synthetic:> .
            ex:evidence a lm:EvidenceObservation .
            ex:snapshot a lm:SourceSnapshot ; lm:sha256 "%s" .
            ex:record a lm:SourceRecordVersion ;
                prov:wasDerivedFrom ex:snapshot ;
                lm:recordSelector "cities/7.json#/provenance/0" .
            ex:manifest a lm:RunManifest ; lm:sha256 "%s" .
            ex:run a lm:Conversion ; lm:runManifest ex:manifest ;
                prov:used ex:record .
            ex:occurrence a lm:ObservationOccurrence ;
                prov:specializationOf ex:evidence ;
                prov:wasDerivedFrom ex:record ; prov:wasGeneratedBy ex:run .
            """
            % ("a" * 64, "b" * 64),
            format="turtle",
        )

    def test_schema_keeps_uncertainty_approximation_and_processing_distinct(self):
        schema = Graph().parse(ONTOLOGY / "preservation.ttl")
        for cls in (
            DIAMM.SourceProvenanceObservation,
            DIAMM.OrganizationProvenanceObservation,
            DIAMM.PersonYearObservation,
            MB.RelationshipObservation,
            CKG.CreationPeriod,
        ):
            self.assertIn((cls, RDFS.subClassOf, LM.EvidenceObservation), schema)
        for pred, target in (
            (DIAMM.uncertain, LM.sourceUncertain),
            (DIAMM.validationFlag, LM.validationFlag),
            (CKG.reviewFlag, LM.validationFlag),
        ):
            self.assertEqual(set(schema.objects(pred, RDFS.subPropertyOf)), {target})
        self.assertFalse(list(schema.objects(MB.mappingStatus, RDFS.subPropertyOf)))
        for subject in set(schema.subjects(RDF.type, RDF.Property)) | set(
            schema.subjects(RDF.type, RDFS.Class)
        ):
            self.assertTrue(list(schema.objects(subject, RDFS.label)), subject)
            self.assertTrue(list(schema.objects(subject, RDFS.comment)), subject)
        # Evidence-only data must not require fabricated source/version metadata.
        self.check(Graph().add((EX.evidence, RDF.type, MB.RelationshipObservation)))
        # Even with deliberate RDFS inference, approximation/status must not
        # become association uncertainty, nor observations direct locations.
        graph = schema + Graph()
        self.assertIn((LM.approximate, RDFS.range, XSD.boolean), schema)
        graph.add((EX.date, LM.approximate, Literal(True)))
        graph.add((EX.relationship, MB.mappingStatus, Literal("mapped")))
        graph.add((EX.period, CKG.parseStatus, Literal("parsed")))
        graph.add((EX.provenance, DIAMM.uncertain, Literal(False)))
        graph.add((EX.source, DIAMM.sourceProvenance, EX.provenance))
        graph.add((EX.provenance, DIAMM.place, EX.city))
        graph.add((EX.source, DIAMM.organizationProvenance, EX.orgEntry))
        graph.add((EX.orgEntry, DIAMM.cityUncertain, Literal(False)))
        graph.add((EX.orgEntry, DIAMM.entityUncertain, Literal(True)))
        DeductiveClosure(RDFS_Semantics).expand(graph)
        self.assertEqual(
            set(graph.subject_objects(LM.sourceUncertain)),
            {(EX.provenance, Literal(False))},
        )
        wdt = Namespace("http://www.wikidata.org/prop/direct/")
        for predicate in (wdt.P131, wdt.P276, wdt.P1071):
            self.assertFalse(list(graph.triples((EX.source, predicate, None))))

    def test_documented_queries_find_approximate_values_without_inference(self):
        guide = (ONTOLOGY / "date_approximation.md").read_text()
        (turtle,) = re.findall(r"```turtle\n(.*?)\n```", guide, re.S)
        discovery, births = re.findall(r"```sparql\n(.*?)\n```", guide, re.S)
        dataset = Dataset(default_union=False)
        catalogue = Namespace("https://example.org/")
        dataset.graph(catalogue.catalogue).parse(data=turtle, format="turtle")
        diamm_graph = URIRef(str(DIAMM))
        graph = dataset.graph(diamm_graph)
        birth_role = URIRef("http://www.wikidata.org/prop/direct/P569")
        for obs, value, flag in (
            (EX.approxBirth, "1850", True),
            (EX.nonApproxBirth, "1851", False),
            (EX.unknownBirth, "1852", None),
        ):
            graph.add((EX.person, DIAMM.personYear, obs))
            graph.add((obs, DIAMM.dateProperty, birth_role))
            graph.add((obs, DIAMM.year, Literal(value, datatype=XSD.gYear)))
            graph.add((obs, DIAMM.sourceValue, Literal(value, datatype=XSD.string)))
            if flag is not None:
                graph.add((obs, LM.approximate, Literal(flag)))

        self.assertCountEqual(
            (tuple(row) for row in dataset.query(discovery)),
            [
                (catalogue.catalogue, catalogue.birth7),
                (catalogue.catalogue, catalogue.count4),
                (diamm_graph, EX.approxBirth),
            ],
        )
        self.assertCountEqual(
            ((row.obs, row.approximate) for row in dataset.query(births)),
            [
                (catalogue.birth7, Literal(True)),
                (EX.approxBirth, Literal(True)),
                (EX.nonApproxBirth, Literal(False)),
                (EX.unknownBirth, None),
            ],
        )

    def test_approximation_shape_checks_single_boolean_per_flagged_subject(self):
        graph = Graph()
        graph.add((EX.performerCount, LM.approximate, Literal(False)))
        self.check(graph)
        graph.add((EX.performerCount, LM.approximate, Literal(True)))
        self.check(graph, expected=False)
        graph.set((EX.performerCount, LM.approximate, Literal("true")))
        self.check(graph, expected=False)

    def test_legacy_year_check_detects_incompatible_diamm_exports(self):
        query = (ROOT / "diamm/doc/queries/person_year_legacy_flags.rq").read_text()
        dataset = Dataset(default_union=False)
        dataset.graph(EX.other).add((EX.birth, DIAMM.approximate, Literal(True)))
        graph = dataset.graph(URIRef(str(DIAMM)))
        graph.add((EX.birth, RDF.type, DIAMM.PersonYearObservation))
        self.assertFalse(bool(dataset.query(query)))
        graph.add((EX.birth, DIAMM.approximate, Literal(False)))
        self.assertTrue(bool(dataset.query(query)))
        graph.remove((EX.birth, DIAMM.approximate, None))
        graph.add((EX.birth, LM.approximate, Literal(False)))
        for raw, incompatible in (("", True), ("  ", True), ("c. 1855", False)):
            with self.subTest(raw=raw):
                graph.set(
                    (EX.birth, DIAMM.sourceValue, Literal(raw, datatype=XSD.string))
                )
                self.assertEqual(bool(dataset.query(query)), incompatible)

    def test_lineage_retains_separate_occurrences_across_conversion_runs(self):
        graph = self.lineage()
        graph.add((EX.run2, RDF.type, LM.Conversion))
        graph.add((EX.run2, LM.runManifest, EX.manifest))
        graph.add((EX.run2, PROV.used, EX.record))
        graph.add((EX.occurrence2, RDF.type, LM.ObservationOccurrence))
        graph.add((EX.occurrence2, PROV.specializationOf, EX.evidence))
        graph.add((EX.occurrence2, PROV.wasDerivedFrom, EX.record))
        graph.add((EX.occurrence2, PROV.wasGeneratedBy, EX.run2))
        self.check(graph)
        self.assertEqual(
            len(set(graph.subjects(PROV.specializationOf, EX.evidence))), 2
        )
        self.assertFalse(list(graph.objects(EX.evidence, PROV.wasGeneratedBy)))
        graph.add((EX.occurrence, PROV.wasGeneratedBy, EX.run2))
        self.check(graph, False)

    def test_lineage_rejects_missing_version_identity_and_unrelated_inputs(self):
        for triple in (
            (EX.snapshot, LM.sha256, Literal("a" * 64)),
            (EX.record, LM.recordSelector, Literal("cities/7.json#/provenance/0")),
            (EX.record, PROV.wasDerivedFrom, EX.snapshot),
            (EX.manifest, LM.sha256, Literal("b" * 64)),
            (EX.run, LM.runManifest, EX.manifest),
            (EX.run, PROV.used, EX.record),
        ):
            with self.subTest(missing=triple):
                graph = self.lineage()
                graph.remove(triple)
                self.check(graph, False)
        graph = self.lineage()
        graph.set((EX.snapshot, LM.sha256, Literal("unknown")))
        self.check(graph, False)


if __name__ == "__main__":
    unittest.main()
