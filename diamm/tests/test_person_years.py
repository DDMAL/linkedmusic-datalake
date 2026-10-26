"""Preserve DIAMM person-year evidence without inventing date precision."""

import contextlib
import csv
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from rdflib import Graph, Literal, Namespace, RDF, RDFS
from rdflib.namespace import DCTERMS, XSD
from rdflib.compare import isomorphic

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from convert_rdf import build_rdf_graph

WD = Namespace("http://www.wikidata.org/entity/")
WDT = Namespace("http://www.wikidata.org/prop/direct/")
LM = Namespace("https://linkedmusic.ca/graphs/diamm/")
PERSON = Namespace("https://www.diamm.ac.uk/people/")["1"]
COMPOSITION = Namespace("https://www.diamm.ac.uk/compositions/")["1"]


class PersonYearTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="diamm-years-")
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.base = self.directory / "data/reconciled"
        self.base.mkdir(parents=True)
        for template_path in (ROOT / "openrefine/export").glob("*_export.json"):
            table = template_path.stem.removesuffix("_export")
            template = json.loads(template_path.read_text())
            with (self.base / f"{table}-csv.csv").open(
                "w", newline="", encoding="utf-8"
            ) as output:
                writer = csv.DictWriter(
                    output, fieldnames=[c["name"] for c in template["columns"]]
                )
                writer.writeheader()
                if table == "compositions":
                    writer.writerow({"id": "1", "title": "Source work"})
        self.relations = self.directory / "data/csv/relations.csv"
        self.relations.parent.mkdir()
        self.relations.write_text("key1,key2,type\ncomposition:1,people:1,\n")

    def write_people(self, *records):
        template = json.loads(
            (ROOT / "openrefine/export/people_export.json").read_text()
        )
        with (self.base / "people-csv.csv").open(
            "w", newline="", encoding="utf-8"
        ) as output:
            writer = csv.DictWriter(
                output, fieldnames=[c["name"] for c in template["columns"]]
            )
            writer.writeheader()
            for record in records:
                writer.writerow(
                    {
                        "id": "1",
                        "full_name": "Source person",
                        "full_name_@id": "Q42",
                        **record,
                    }
                )

    def convert(self):
        with contextlib.redirect_stdout(io.StringIO()):
            return build_rdf_graph(
                self.base, self.relations, ROOT / "src/relations.json"
            )

    def expected_base(self):
        return {
            (PERSON, RDF.type, LM.Person),
            (PERSON, RDFS.label, Literal("Source person")),
            (PERSON, WDT.P2888, WD.Q42),
            (COMPOSITION, RDF.type, LM.Composition),
            (COMPOSITION, RDFS.label, Literal("Source work")),
            (COMPOSITION, WDT.P86, PERSON),
        }

    def observation(self, graph, field):
        nodes = list(
            graph.subjects(LM.sourceField, Literal(field, datatype=XSD.string))
        )
        self.assertEqual(len(nodes), 1)
        node = nodes[0]
        self.assertIn((PERSON, LM.personYear, node), graph)
        self.assertIn((node, DCTERMS.source, PERSON), graph)
        self.assertIn((node, RDF.type, LM.PersonYearObservation), graph)
        return node

    def test_exact_and_approximate_years_have_distinct_assertions(self):
        self.write_people(
            {
                "earliest_year": "1500.0",
                "earliest_year_@id": "Q1499",
                "earliest_year_approximate": "False",
                "latest_year": "1560",
                "latest_year_@id": "Q1560",
                "latest_year_approximate": "True",
            }
        )
        graph = self.convert()
        expected = self.expected_base()
        expected.add((PERSON, WDT.P569, Literal("1500", datatype=XSD.gYear)))
        for field, predicate, raw_year, year, qid, raw_flag, approximate in (
            ("earliest_year", WDT.P569, "1500.0", "1500", WD.Q1499, "False", False),
            ("latest_year", WDT.P570, "1560", "1560", WD.Q1560, "True", True),
        ):
            node = self.observation(graph, field)
            expected.update(
                {
                    (PERSON, LM.personYear, node),
                    (node, RDF.type, LM.PersonYearObservation),
                    (node, DCTERMS.source, PERSON),
                    (node, LM.sourceField, Literal(field, datatype=XSD.string)),
                    (node, LM.dateProperty, predicate),
                    (node, LM.sourceValue, Literal(raw_year, datatype=XSD.string)),
                    (
                        node,
                        LM.sourceIdentifier,
                        Literal(str(qid).rsplit("/", 1)[1], datatype=XSD.string),
                    ),
                    (
                        node,
                        LM.sourceApproximate,
                        Literal(raw_flag, datatype=XSD.string),
                    ),
                    (node, LM.year, Literal(year, datatype=XSD.gYear)),
                    (node, LM.approximate, Literal(approximate)),
                    (node, LM.reconciledYear, qid),
                }
            )
        self.assertEqual(set(graph), expected)
        restored = Graph().parse(data=graph.serialize(format="turtle"), format="turtle")
        self.assertEqual(set(restored), expected)

    def test_invalid_ids_remain_literal_evidence_for_both_year_fields(self):
        for field, predicate in (
            ("earliest_year", WDT.P569),
            ("latest_year", WDT.P570),
        ):
            for candidate in (
                "Q42suffix",
                "Q42 / Q43",
                "Q0",
                "Q042",
                "Q٤٢",
                "q42",
                "Q42\n",
                " Q42",
                "Q42 ",
                "wd:Q42",
                "P569",
                "1500",
                "nan",
                "NA",
                "None",
                "https://www.wikidata.org/wiki/Q42",
                "",
            ):
                with self.subTest(field=field, candidate=candidate):
                    self.write_people(
                        {
                            field: "1500",
                            f"{field}_@id": candidate,
                            f"{field}_approximate": "False",
                        }
                    )
                    graph = self.convert()
                    node = self.observation(graph, field)
                    self.assertIn(
                        (
                            node,
                            LM.sourceIdentifier,
                            Literal(candidate, datatype=XSD.string),
                        ),
                        graph,
                    )
                    self.assertEqual(list(graph.objects(node, LM.reconciledYear)), [])
                    flags = set(graph.objects(node, LM.validationFlag))
                    self.assertEqual(
                        flags,
                        {Literal("invalid-year-identifier")} if candidate else set(),
                    )
                    self.assertEqual(
                        set(graph.objects(PERSON, predicate)),
                        {Literal("1500", datatype=XSD.gYear)},
                    )
                    self.assertEqual(
                        {o for _, _, o in graph if str(o).startswith(str(WD))}, {WD.Q42}
                    )

    def test_original_year_text_survives_and_only_supported_years_are_typed(self):
        for raw, normalized in (
            ("12", "0012"),
            ("0012", "0012"),
            ("1500.0", "1500"),
            ("1500.00", "1500"),
            ("9999", "9999"),
            ("", None),
            ("0", None),
            ("-1", None),
            ("10000", None),
            ("1500.5", None),
            ("1500.", None),
            ("+1500", None),
            ("1.5e3", None),
            ("ca. 1500", None),
            ("1500/1510", None),
            ("１５００", None),
            ("1500\n", None),
            (" 1500 ", None),
            ("nan", None),
            ("NA", None),
        ):
            with self.subTest(raw=raw):
                # A syntactically valid reconciliation does not supply or override a year.
                self.write_people(
                    {
                        "earliest_year": raw,
                        "earliest_year_@id": "Q1",
                        "earliest_year_approximate": "False",
                    }
                )
                graph = self.convert()
                node = self.observation(graph, "earliest_year")
                self.assertIn(
                    (node, LM.sourceValue, Literal(raw, datatype=XSD.string)), graph
                )
                self.assertIn((node, LM.reconciledYear, WD.Q1), graph)
                expected = (
                    {Literal(normalized, datatype=XSD.gYear)} if normalized else set()
                )
                self.assertEqual(set(graph.objects(node, LM.year)), expected)
                self.assertEqual(set(graph.objects(PERSON, WDT.P569)), expected)
                restored = Graph().parse(
                    data=graph.serialize(format="turtle"), format="turtle"
                )
                self.assertEqual(set(restored.objects(node, LM.year)), expected)
                self.assertIn(
                    (node, LM.sourceValue, Literal(raw, datatype=XSD.string)), restored
                )
                flags = set(graph.objects(node, LM.validationFlag))
                self.assertEqual(
                    flags,
                    (
                        set()
                        if normalized
                        else {Literal("missing-year" if raw == "" else "invalid-year")}
                    ),
                )

    def test_approximation_is_explicit_and_never_defaults_to_false(self):
        for raw, approximate in (
            ("True", True),
            ("TRUE", True),
            ("1", True),
            ("False", False),
            ("false", False),
            ("0", False),
            ("", None),
            ("unknown", None),
            ("False ", None),
            ("nan", None),
        ):
            with self.subTest(raw=raw):
                self.write_people(
                    {"latest_year": "1560", "latest_year_approximate": raw}
                )
                graph = self.convert()
                node = self.observation(graph, "latest_year")
                self.assertIn(
                    (node, LM.sourceApproximate, Literal(raw, datatype=XSD.string)),
                    graph,
                )
                self.assertIn(
                    (node, LM.year, Literal("1560", datatype=XSD.gYear)), graph
                )
                self.assertEqual(
                    set(graph.objects(node, LM.approximate)),
                    {Literal(approximate)} if approximate is not None else set(),
                )
                self.assertEqual(
                    set(graph.objects(PERSON, WDT.P570)),
                    (
                        {Literal("1560", datatype=XSD.gYear)}
                        if approximate is False
                        else set()
                    ),
                )
                self.assertEqual(
                    set(graph.objects(node, LM.validationFlag)),
                    (
                        {
                            Literal(
                                "missing-approximation"
                                if raw == ""
                                else "invalid-approximation"
                            )
                        }
                        if approximate is None
                        else set()
                    ),
                )

    def test_blank_fields_do_not_invent_years_or_observations(self):
        self.write_people({})
        self.assertEqual(set(self.convert()), self.expected_base())
        self.write_people({"earliest_year_approximate": "False"})
        graph = self.convert()
        node = self.observation(graph, "earliest_year")
        self.assertIn((node, LM.validationFlag, Literal("missing-year")), graph)
        self.assertEqual(list(graph.objects(PERSON, WDT.P569)), [])
        self.assertEqual(list(graph.objects(node, LM.year)), [])

    def test_duplicate_and_conflicting_rows_keep_year_evidence_together(self):
        exact = {"earliest_year": "1500", "earliest_year_approximate": "False"}
        approximate = {"earliest_year": "1510", "earliest_year_approximate": "True"}
        self.write_people(exact, approximate)
        graph = self.convert()
        nodes = set(graph.objects(PERSON, LM.personYear))
        self.assertEqual(len(nodes), 2)
        self.assertEqual(
            {
                (
                    str(graph.value(n, LM.sourceValue)),
                    graph.value(n, LM.approximate).toPython(),
                )
                for n in nodes
            },
            {("1500", False), ("1510", True)},
        )
        self.assertEqual(
            set(graph.objects(PERSON, WDT.P569)), {Literal("1500", datatype=XSD.gYear)}
        )
        for node in nodes:
            self.assertRegex(
                str(node),
                r"^https://linkedmusic\.ca/graphs/diamm/person-year/[0-9a-f]{64}$",
            )
        self.write_people(approximate, exact, exact)
        self.assertEqual(set(self.convert()), set(graph))
        self.write_people(
            exact,
            {**exact, "id": "2"},
            {"latest_year": "1500", "latest_year_approximate": "False"},
        )
        self.assertEqual(
            len(set(self.convert().subjects(RDF.type, LM.PersonYearObservation))), 3
        )

    def test_cli_and_queries_distinguish_approximate_evidence_from_direct_dates(self):
        self.write_people(
            {
                "earliest_year": "1500",
                "earliest_year_@id": "Q42 / Q43",
                "earliest_year_approximate": "true",
                "latest_year": "1560",
                "latest_year_@id": "Q1560",
                "latest_year_approximate": "false",
            }
        )
        src = self.directory / "src"
        src.mkdir()
        (src / "relations.json").write_text((ROOT / "src/relations.json").read_text())
        result = subprocess.run(
            [sys.executable, str(ROOT / "src/convert_rdf.py")],
            cwd=src,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        graph = Graph().parse(self.directory / "data/RDF/diamm.ttl", format="turtle")
        self.assertTrue(isomorphic(graph, self.convert()))
        prefixes = f"PREFIX diamm: <{LM}> PREFIX wdt: <{WDT}>"
        rows = graph.query(prefixes + """
            SELECT ?person ?year WHERE {
              ?person a diamm:Person; diamm:personYear ?observation .
              ?observation diamm:dateProperty wdt:P569;
                           diamm:year ?year; diamm:approximate true .
            }
        """)
        self.assertEqual(
            {tuple(row) for row in rows},
            {(PERSON, Literal("1500", datatype=XSD.gYear))},
        )
        rows = graph.query(prefixes + """
            SELECT ?person ?predicate ?year WHERE {
              VALUES ?predicate { wdt:P569 wdt:P570 }
              ?person a diamm:Person; ?predicate ?year .
            }
        """)
        self.assertEqual(
            {tuple(row) for row in rows},
            {(PERSON, WDT.P570, Literal("1560", datatype=XSD.gYear))},
        )


if __name__ == "__main__":
    unittest.main()
