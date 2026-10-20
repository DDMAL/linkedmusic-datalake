"""Offline, synthetic source-to-RDF checks for the shared CKG converter."""

import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path

from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, XSD

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "ckg-apsearch/src/convert_to_rdf.py"
SPEC = importlib.util.spec_from_file_location("ckg_converter", SOURCE)
converter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(converter)

TERM = Namespace("https://linkedmusic.ca/terms/ckg/")
CTO = Namespace("https://nfdi4culture.de/ontology/")
WDT = Namespace("http://www.wikidata.org/prop/direct/")
EX = Namespace("https://example.org/synthetic/")


def source_literal(value):
    return Literal(value, datatype=URIRef("http://schema.org/DateTime")).n3()


def run_conversion(directory, values, feed="apsearch", predicate=CTO.CTO_0001073):
    directory = Path(directory)
    extracted = directory / "extracted"
    mappings = directory / "mappings"
    extracted.mkdir(exist_ok=True)
    mappings.mkdir(exist_ok=True)
    rows = []
    kinds = {}
    for name, token in values:
        subject = EX[name].n3()
        kinds[subject] = "Work" if feed != "musiconn" else "Event"
        rows.extend(
            [
                f"{subject} {converter.RDF_TYPE} {converter.RECORD_TYPE} .",
                f"{subject} {predicate.n3()} {token} .",
            ]
        )
    (extracted / f"{feed}.norm.nt").write_text("\n".join(rows) + "\n")
    (extracted / f"{feed}.entities.json").write_text(
        json.dumps({"entities": {}, "record_kind": kinds})
    )
    for filename in ("crosswalk.json", "record_types.json"):
        (mappings / filename).write_text("{}")
    outdir = directory / "rdf"
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
        io.StringIO()
    ):
        converter.convert(feed, extracted, mappings, SOURCE.parent / "ontology", outdir)
    output = (outdir / f"{feed}.ttl").read_text()
    return Graph().parse(data=output, format="turtle"), outdir, output


class CreationPeriodTests(unittest.TestCase):
    def test_supported_precision_retains_both_years(self):
        for value, start, end in (
            ("2015-01-01T00:00:00/2015-01-01T23:59:59", "2015", "2015"),
            ("1909-01-01T00:00:00/1950-01-01T23:59:59", "1909", "1950"),
            ("1909-01-01/1950-01-01", "1909", "1950"),
            ("1909/1950", "1909", "1950"),
            ("1909-00-00/1950-00-00", "1909", "1950"),
            ("1909-02-00/1950-03-00", "1909", "1950"),
            ("2015", "2015", "2015"),
        ):
            with self.subTest(value=value):
                self.assertEqual(
                    converter.creation_period(source_literal(value)),
                    (start, end, "parsed", []),
                )

    def test_unresolved_precision_and_invalid_values_are_not_guessed(self):
        for value, start, end, flags in (
            ("unknown", None, None, ["unrecognized-start", "unrecognized-end"]),
            ("1909/..", "1909", None, ["unrecognized-end"]),
            ("?/1950", None, "1950", ["unrecognized-start"]),
            ("1909/1950/1960", None, None, ["unrecognized-interval"]),
            ("1909-02-30/1950-01-01", None, "1950", ["invalid-start"]),
            ("1909-00-01/1950-01-01", None, "1950", ["invalid-start"]),
            ("0000/1950", None, "1950", ["invalid-start"]),
            ("1909-13-00/1950", None, "1950", ["invalid-start"]),
            ("1909-01-01T25:00:00/1950", None, "1950", ["invalid-start"]),
            ("1909-02-01/1950", "1909", "1950", ["unexpected-precision-start"]),
            ("1950/1909", "1950", "1909", ["reversed-interval"]),
            ("1950-12-00/1950-02-00", "1950", "1950", ["reversed-interval"]),
        ):
            with self.subTest(value=value):
                token = source_literal(value)
                self.assertEqual(
                    converter.creation_period(token),
                    (start, end, "unresolved", flags),
                )
                self.assertEqual(converter.coerce_date(token, "apsearch"), token)

    def test_anomalous_9009_is_retained_and_flagged(self):
        token = source_literal("9009-01-01/9009-01-01")
        self.assertEqual(
            converter.creation_period(token),
            ("9009", "9009", "parsed", ["year-9009"]),
        )
        self.assertEqual(converter.coerce_date(token, "apsearch"), '"9009"^^xsd:gYear')
        with tempfile.TemporaryDirectory() as directory:
            graph, _, _ = run_conversion(directory, [("anomaly", token)])
        period = graph.value(EX.anomaly, TERM.creationPeriod)
        self.assertIn(
            (period, TERM.endYear, Literal("9009", datatype=XSD.gYear)), graph
        )
        self.assertIn((period, TERM.reviewFlag, Literal("year-9009")), graph)

    def test_source_literal_datatype_and_language_survive(self):
        # Escape a year digit in the actual NT token: extraction must decode it,
        # while emission preserves the exact token, datatype and language.
        tokens = [
            source_literal("1909/1950"),
            '"1909/1950"',
            '"circa 1909/1950"@en',
            '"19\\u00309/1950"^^<http://schema.org/DateTime>',
            '"unknown \\"date\\""',
        ]
        with tempfile.TemporaryDirectory() as directory:
            graph, _, output = run_conversion(
                directory, [(f"value{i}", token) for i, token in enumerate(tokens)]
            )
        for i, token in enumerate(tokens):
            record = EX[f"value{i}"]
            raw = converter.from_n3(token)
            self.assertIn((record, CTO.CTO_0001073, raw), graph)
            period = graph.value(record, TERM.creationPeriod)
            self.assertIn((period, RDF.value, raw), graph)
            self.assertIn(f"{record.n3()} cto:CTO_0001073 {token} .", output)
        self.assertEqual(graph.value(EX.value2, WDT.P571), None)

    def test_overlap_query_includes_1940_but_not_1960(self):
        query = (
            ROOT / "ckg-apsearch/doc/queries/creation_period_overlap.rq"
        ).read_text()
        with tempfile.TemporaryDirectory() as directory:
            graph, _, _ = run_conversion(
                directory,
                [
                    ("range", source_literal("1909-01-01/1950-01-01")),
                    ("single", source_literal("2015-01-01/2015-01-01")),
                    ("reversed", source_literal("1950/1909")),
                    ("unknown", source_literal("1909/unknown")),
                ],
            )
        # The documented query uses a staging named graph.
        from rdflib import Dataset

        dataset = Dataset()
        named = dataset.graph(
            URIRef("https://linkedmusic.ca/graphs/ckg-apsearch/staging/")
        )
        for triple in graph:
            named.add(triple)
        for year, expected in (
            (1909, {EX.range}),
            (1940, {EX.range}),
            (1950, {EX.range}),
            (1960, set()),
        ):
            with self.subTest(year=year):
                actual = {
                    row.record
                    for row in dataset.query(
                        query.replace(
                            "VALUES ?year { 1940 }", f"VALUES ?year {{ {year} }}"
                        )
                    )
                }
                self.assertEqual(actual, expected)
        self.assertIn((EX.range, WDT.P571, Literal("1909", datatype=XSD.gYear)), graph)
        self.assertFalse(
            any(isinstance(node, BNode) for triple in graph for node in triple)
        )
        self.assertFalse(list(graph.triples((None, WDT.P585, None))))
        self.assertFalse(
            list(graph.triples((None, None, Literal("1909-01-01", datatype=XSD.date))))
        )

    def test_multiple_periods_keep_endpoint_pairs_and_stable_nodes(self):
        values = [
            ("record", source_literal("1909/1950")),
            ("record", source_literal("1960/1970")),
            ("other", source_literal("1909/1950")),
        ]
        with tempfile.TemporaryDirectory() as directory:
            first, _, _ = run_conversion(directory, values + values[:1])
            second, _, _ = run_conversion(directory, list(reversed(values)))
        self.assertEqual(set(first), set(second))
        self.assertEqual(len(set(first.objects(EX.record, TERM.creationPeriod))), 2)
        self.assertEqual(
            {
                (
                    str(first.value(node, TERM.startYear)),
                    str(first.value(node, TERM.endYear)),
                )
                for node in first.objects(EX.record, TERM.creationPeriod)
            },
            {("1909", "1950"), ("1960", "1970")},
        )
        self.assertEqual(len(set(first.subjects(RDF.type, TERM.CreationPeriod))), 3)

    def test_unresolved_source_survives_without_p571_projection(self):
        values = [
            ("reverse", source_literal("1950/1909")),
            ("unknown", source_literal("unknown")),
            ("partial", source_literal("1909/..")),
            ("invalid", source_literal("1909-02-30/1950")),
            ("uri", "<https://example.org/unknown-period>"),
        ]
        with tempfile.TemporaryDirectory() as directory:
            graph, _, _ = run_conversion(directory, values)
        for name, token in values:
            record = EX[name]
            node = graph.value(record, TERM.creationPeriod)
            self.assertIn((record, CTO.CTO_0001073, converter.from_n3(token)), graph)
            self.assertIn((node, TERM.parseStatus, Literal("unresolved")), graph)
            self.assertIsNone(graph.value(record, WDT.P571))
        reverse = graph.value(EX.reverse, TERM.creationPeriod)
        self.assertIn(
            (reverse, TERM.startYear, Literal("1950", datatype=XSD.gYear)), graph
        )
        self.assertIn(
            (reverse, TERM.endYear, Literal("1909", datatype=XSD.gYear)), graph
        )

    def test_audit_denominators_and_duplicate_collapse(self):
        values = [
            ("range", source_literal("1909/1950")),
            ("range", source_literal("1909/1950")),
            ("reversed", source_literal("1950/1909")),
            ("partial", source_literal("1909/..")),
            ("unknown", source_literal("unknown")),
            ("anomaly", source_literal("9009/9009")),
        ]
        with tempfile.TemporaryDirectory() as directory:
            _, outdir, _ = run_conversion(directory, values)
            audit = json.loads(
                (outdir / "apsearch.creation-period-audit.json").read_text()
            )
        self.assertEqual(
            audit["counts"],
            {
                "input_occurrences": 6,
                "distinct_periods": 5,
                "duplicate_occurrences": 1,
                "parsed": 2,
                "unresolved": 3,
                "startYear": 4,
                "endYear": 3,
                "flagged_periods": 4,
            },
        )
        self.assertIsNone(audit["source_snapshot_date"])
        for key in ("converter_sha256", "mapping_sha256", "output_sha256"):
            self.assertRegex(audit[key], r"^[0-9a-f]{64}$")

    def test_other_feed_date_coercions_are_unchanged(self):
        for feed, value, expected in (
            ("musiconn", "1919-11-15", '"1919-11-15"^^xsd:date'),
            ("musiconn", "1919-11-00", '"1919-11"^^xsd:gYearMonth'),
            ("musiconn", "1919-00-00", '"1919"^^xsd:gYear'),
            ("musiconn", "1919", '"1919"^^xsd:gYear'),
            (
                "detmold",
                "1850-02-01T00:00:00/1850-02-01T23:59:59",
                '"1850-02-01"^^xsd:date',
            ),
            (
                "detmold",
                "1850-02-01T00:00:00/1850-02-28T23:59:59",
                '"1850-02"^^xsd:gYearMonth',
            ),
            ("detmold", "1850-01-01T00:00:00/1850-12-31T23:59:59", '"1850"^^xsd:gYear'),
            (
                "detmold",
                "1850-01-01T00:00:00/1850-01-01T23:59:59",
                '"1850-01-01"^^xsd:date',
            ),
        ):
            with self.subTest(feed=feed, value=value):
                self.assertEqual(
                    converter.coerce_date(source_literal(value), feed), expected
                )

    def test_other_feed_output_has_no_period_nodes_or_audit(self):
        for feed, predicate, value, result_predicate, result in (
            (
                "musiconn",
                CTO.CTO_0001070,
                "1919-11-15",
                WDT.P585,
                Literal("1919-11-15", datatype=XSD.date),
            ),
            (
                "detmold",
                CTO.CTO_0001073,
                "1850-02-01T00:00:00/1850-02-28T23:59:59",
                WDT.P571,
                Literal("1850-02", datatype=XSD.gYearMonth),
            ),
        ):
            with self.subTest(feed=feed), tempfile.TemporaryDirectory() as directory:
                graph, outdir, output = run_conversion(
                    directory, [("record", source_literal(value))], feed, predicate
                )
                self.assertIn((EX.record, result_predicate, result), graph)
                self.assertNotIn("ckgterm:", output)
                self.assertFalse(list(outdir.glob("*.json")))

    def test_three_converter_copies_are_identical(self):
        for feed in ("detmold", "musiconn"):
            self.assertEqual(
                SOURCE.read_bytes(),
                (ROOT / f"ckg-{feed}/src/convert_to_rdf.py").read_bytes(),
            )
            self.assertEqual(
                (SOURCE.parent / "ontology/mapping.json").read_bytes(),
                (ROOT / f"ckg-{feed}/src/ontology/mapping.json").read_bytes(),
            )


if __name__ == "__main__":
    unittest.main()
