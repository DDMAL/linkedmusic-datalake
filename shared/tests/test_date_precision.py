"""Temporal precision from the shipped CSV mappings through serialized Turtle."""

import csv
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest.mock import patch

import tomli_w
from rdflib import Graph, Literal, Namespace, RDF, URIRef, XSD

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from shared.rdfconv.convert import main, to_rdf_node
from simssa.src.merge import merge_person_data

WDT = Namespace("http://www.wikidata.org/prop/direct/")


def convert_table(feed, table, rows):
    config = tomllib.loads((ROOT / f"shared/rdf_config/{feed}.toml").read_text())
    schema = config[table]
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory)
        config["general"].update(csv_folder=directory, rdf_output_folder=directory)
        with (path / f"{table}.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(
                stream, [key for key in schema if key != "PRIMARY_KEY"]
            )
            writer.writeheader()
            writer.writerows(rows)
        config_file = path / f"{feed}.toml"
        config_file.write_text(
            tomli_w.dumps({k: config[k] for k in ("general", "namespaces", table)})
        )
        with patch.object(sys, "argv", ["convert", str(config_file)]):
            main()
        # Inspect the written terms before RDFLib normalizes offsets or fractions.
        with patch("rdflib.NORMALIZE_LITERALS", False):
            return Graph().parse(path / (config["general"]["name"] + ".ttl"))


class DatePrecisionTests(unittest.TestCase):
    def check_cells(self, feed, table, key, field, predicate, record_type, cases):
        rows = []
        expected = set()
        subjects = set()
        for index, (cell, lexical, datatype) in enumerate(cases):
            subject = URIRef(f"https://example.org/records/{index}")
            subjects.add(subject)
            rows.append({key: str(subject), field: cell})
            if lexical is not None:
                expected.add(
                    (
                        subject,
                        predicate,
                        Literal(lexical, datatype=datatype, normalize=False),
                    )
                )
        graph = convert_table(feed, table, rows)
        self.assertEqual(set(graph.subjects(RDF.type, URIRef(record_type))), subjects)
        self.assertEqual(set(graph.triples((None, predicate, None))), expected)

    def test_weimar_recording_dates(self):
        self.check_cells(
            "wjazzd",
            "track_info",
            "trackid",
            "recordingdate",
            WDT.P10135,
            "https://linkedmusic.ca/graphs/wjazzd/Track",
            [
                ("1850", "1850", XSD.gYear),
                ("1850-01-01", "1850-01-01", XSD.date),
                ("2000-02-29-03:30", "2000-02-29-03:30", XSD.date),
                ("1850-06-15Z", "1850-06-15Z", XSD.date),
                ("1850-06", "1850-06", None),
                ("c. 1850", "c. 1850", None),
                ("  circa 1850?  ", "  circa 1850?  ", None),
                ("abc", "abc", None),
                ("1900-02-29", "1900-02-29", None),
                ("1850-06-15+14:01", "1850-06-15+14:01", None),
                ("1850-06-15T12:00:00", "1850-06-15T12:00:00", None),
                ("", None, None),
            ],
        )

    def test_session_event_timestamps(self):
        self.check_cells(
            "thesession",
            "events-reconciled",
            "events_id",
            "dtstart",
            WDT.P580,
            "https://linkedmusic.ca/graphs/thesession/Events",
            [
                ("1850-06-15T12:34:56", "1850-06-15T12:34:56", XSD.dateTime),
                (
                    "2000-02-29 12:34:56.123456789+05:30",
                    "2000-02-29T12:34:56.123456789+05:30",
                    XSD.dateTime,
                ),
                ("1999-12-31T24:00:00Z", "2000-01-01T00:00:00Z", XSD.dateTime),
                ("1850-01-01", "1850-01-01", XSD.date),
                ("1850", "1850", XSD.gYear),
                ("c. 1850", "c. 1850", None),
                ("abc", "abc", None),
                ("1850-06-15T12:34", "1850-06-15T12:34", None),
                ("1850-06-15T24:00:01", "1850-06-15T24:00:01", None),
                ("1850-06-15T12:34:56+15:00", "1850-06-15T12:34:56+15:00", None),
                ("", None, None),
            ],
        )

    def test_simssa_years_from_raw_person_ranges(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "person"
            path.mkdir()
            (path / "person.csv").write_text(
                "id,given_name,surname,birth_date_range_year_only,death_date_range_year_only,authority_control_url\n"
                '1,Example,One,"[950, 951)","[0990,0990]",\n'
                '2,Example,Two,"[1850, 1853)",c. 1900,\n'
                '3,Example,Three,"(, 1850)",1850-01-01,\n'
                "4,Example,Four,1850,,\n"
            )
            people = merge_person_data(path.parent).fillna("").to_dict("records")
        graph = convert_table("simssadb", "person", people)
        person = Namespace("https://db.simssa.ca/persons/")
        self.assertEqual(
            set(graph.triples((None, WDT.P569, None)))
            | set(graph.triples((None, WDT.P570, None))),
            {
                (person["1"], WDT.P569, Literal("0950", datatype=XSD.gYear)),
                (person["1"], WDT.P570, Literal("0990", datatype=XSD.gYear)),
                (person["2"], WDT.P569, Literal("[1850, 1853)")),
                (person["2"], WDT.P570, Literal("c. 1900")),
                (person["3"], WDT.P569, Literal("(, 1850)")),
                (person["3"], WDT.P570, Literal("1850-01-01")),
                (person["4"], WDT.P569, Literal("1850", datatype=XSD.gYear)),
            },
        )

    def test_explicit_year_declarations_accept_signed_and_extended_years(self):
        for cell in ("-0044", "10000", "1850+14:00"):
            self.assertEqual(
                to_rdf_node(cell, {"xsd": str(XSD)}, datatype="xsd:gYear"),
                Literal(cell, datatype=XSD.gYear, normalize=False),
            )
        # A compact date in a date column is ambiguous as an extended year.
        self.assertEqual(
            to_rdf_node("18500615", {}, datatype=XSD.date), Literal("18500615")
        )

    def test_absolute_datatype_iris_use_the_same_rules(self):
        for datatype in (XSD.date, XSD.dateTime, XSD.gYear):
            for declaration in (datatype, str(datatype)):
                with self.subTest(declaration=repr(declaration)):
                    self.assertEqual(
                        to_rdf_node("abc", {}, datatype=declaration), Literal("abc")
                    )
