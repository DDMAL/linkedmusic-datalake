"""Executable preservation shapes and optional, explicitly versioned lineage."""

import unittest
from pathlib import Path

from owlrl import DeductiveClosure, RDFS_Semantics
from pyshacl import validate
from rdflib import Graph, Literal, Namespace, RDF, RDFS

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
            DIAMM.PersonYearObservation,
            MB.RelationshipObservation,
            CKG.CreationPeriod,
        ):
            self.assertIn((cls, RDFS.subClassOf, LM.EvidenceObservation), schema)
        for pred, target in (
            (DIAMM.uncertain, LM.sourceUncertain),
            (DIAMM.approximate, LM.dateApproximate),
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
        graph.add((EX.date, DIAMM.approximate, Literal(True)))
        graph.add((EX.relationship, MB.mappingStatus, Literal("mapped")))
        graph.add((EX.period, CKG.parseStatus, Literal("parsed")))
        graph.add((EX.provenance, DIAMM.uncertain, Literal(False)))
        graph.add((EX.source, DIAMM.sourceProvenance, EX.provenance))
        graph.add((EX.provenance, DIAMM.place, EX.city))
        DeductiveClosure(RDFS_Semantics).expand(graph)
        self.assertEqual(
            set(graph.subject_objects(LM.sourceUncertain)),
            {(EX.provenance, Literal(False))},
        )
        self.assertIn((EX.date, LM.dateApproximate, Literal(True)), graph)
        wdt = Namespace("http://www.wikidata.org/prop/direct/")
        for predicate in (wdt.P131, wdt.P276, wdt.P1071):
            self.assertFalse(list(graph.triples((EX.source, predicate, None))))

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
