"""Failure and resume checks for numbered RISM exports."""

import csv
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pyoxigraph import Literal, NamedNode, Quad, RdfFormat, parse
from rdflib import Graph, URIRef
from rdflib.namespace import RDF, RDFS

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))
import convert_to_rdf as converter


def write_part(path, item):
    write_csv(
        path,
        [
            ["subject", str(converter.WDT.P2888)],
            ["https://rism.online/people/1", f"https://wikidata.org/wiki/{item}"],
        ],
    )


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        csv.writer(stream).writerows(rows)


def run_converter(inputs, output):
    return subprocess.run(
        [
            sys.executable,
            str(SRC / "convert_to_rdf.py"),
            "--input_folder",
            str(inputs),
            "--mappings_folder",
            str(SRC / "mappings"),
            "--output_folder",
            str(output),
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )


class PartExportTests(unittest.TestCase):
    def test_continuation_labels_follow_the_latest_explicit_subject(self):
        first = NamedNode("https://rism.online/sources/1")
        second = NamedNode("https://rism.online/sources/2")
        label = NamedNode(str(RDFS.label))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "out"
            part = root / "part-1-ttl.csv"
            write_csv(
                part,
                [
                    ["subject", label.value],
                    ["", ""],
                    ["", "before any subject"],
                    ["", "another leading label"],
                    [first.value, "first"],
                    ["", "second"],
                    ["", "third"],
                    [str(converter.RISM_API.Source), ""],
                    ["", "belongs to the API row"],
                    [second.value, ""],
                    ["", "new record"],
                    [" ", ""],
                    ["", "belongs to the space key"],
                ],
            )
            result = run_converter(root, output)
            self.assertEqual(result.returncode, 0, result.stderr)
            warning = (
                f"Skipped populated rows before the first subject in {part} (count=2)"
            )
            self.assertEqual(result.stderr.count(warning), 1, result.stderr)
            self.assertEqual(
                set(parse(path=output / "part-1.ttl", format=RdfFormat.TURTLE)),
                {
                    Quad(first, label, Literal("first")),
                    Quad(first, label, Literal("second")),
                    Quad(first, label, Literal("third")),
                    Quad(second, label, Literal("new record")),
                },
            )

    def test_holding_lookup_stops_at_the_next_main_record(self):
        source = NamedNode("https://rism.online/sources/1")
        holding = source.value + "/holdings/2"
        second_holding = source.value + "/holdings/3"
        institutions = "https://rism.online/institutions/"
        location = NamedNode(str(converter.WDT.P276))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "out"
            write_csv(
                root / "part-1-ttl.csv",
                [
                    [
                        "subject",
                        str(converter.RISM_API.hasHolding),
                        str(converter.WDT.P195),
                    ],
                    [holding, "", institutions + "10"],
                    ["", "", institutions + "11"],
                    [source.value, holding, ""],
                    ["", second_holding, institutions + "99"],
                    [second_holding, "", institutions + "20"],
                ],
            )
            result = run_converter(root, output)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn(
                "Skipped populated rows before the first subject", result.stderr
            )
            self.assertEqual(
                set(parse(path=output / "part-1.ttl", format=RdfFormat.TURTLE)),
                {
                    Quad(source, location, NamedNode(institutions + "10")),
                    Quad(source, location, NamedNode(institutions + "11")),
                    Quad(source, location, NamedNode(institutions + "20")),
                },
            )

    def test_cli_retries_invalid_subject_and_class(self):
        subject = "https://rism.online/sources/1%20A"
        bad_subject = subject + "%zz"
        bad_class = str(converter.RISM_API.Source) + "\t"
        header = ["subject", str(RDFS.label), str(RDF.type)]
        valid_row = [subject, "first", ""]
        record = NamedNode(subject)
        label = NamedNode(str(RDFS.label))
        first_label = Quad(record, label, Literal("first"))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inputs = root / "input"
            output = root / "output"
            inputs.mkdir()
            first = inputs / "part-1-ttl.csv"
            second = inputs / "part-2-ttl.csv"
            write_csv(first, [header, valid_row, [bad_subject, "second", ""]])
            write_csv(second, [header, valid_row, [subject, "", bad_class]])
            write_csv(inputs / "part-3-ttl.csv", [header, valid_row])

            result = run_converter(inputs, output)
            self.assertNotEqual(result.returncode, 0)
            for part, value in ((first, bad_subject), (second, bad_class)):
                self.assertTrue(
                    any(
                        str(part) in line and repr(value) in line
                        for line in result.stderr.splitlines()
                    ),
                    result.stderr,
                )
            sibling = output / "part-3.ttl"
            self.assertEqual(list(output.iterdir()), [sibling])
            self.assertEqual(
                set(parse(path=sibling, format=RdfFormat.TURTLE)), {first_label}
            )
            stamp = sibling.stat().st_mtime_ns
            content = sibling.read_bytes()

            write_csv(first, [header, valid_row, [subject, "second", ""]])
            write_csv(second, [header, valid_row, [subject, "", "Source"]])
            retry = run_converter(inputs, output)
            self.assertEqual(retry.returncode, 0, retry.stderr)
            source_type = NamedNode("https://linkedmusic.ca/graphs/rism/Source")
            self.assertEqual(
                set(parse(path=output / "part-1.ttl", format=RdfFormat.TURTLE)),
                {first_label, Quad(record, label, Literal("second"))},
            )
            self.assertEqual(
                set(parse(path=output / "part-2.ttl", format=RdfFormat.TURTLE)),
                {first_label, Quad(record, NamedNode(str(RDF.type)), source_type)},
            )
            self.assertEqual(sibling.stat().st_mtime_ns, stamp)
            self.assertEqual(sibling.read_bytes(), content)

    def test_invalid_class_preserves_previous_complete_export(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            part = root / "part-1-ttl.csv"
            final = root / "part-1.ttl"
            previous = b"<urn:s> <urn:p> <urn:o> .\n"
            final.write_bytes(previous)
            stamp = final.stat().st_mtime_ns
            write_csv(
                part,
                [
                    ["subject", str(RDF.type)],
                    ["https://rism.online/sources/1", "Source%zz"],
                ],
            )
            with self.assertRaisesRegex(ValueError, "Source%zz"):
                converter.process_file(part, {}, {}, final, {})
            self.assertEqual(final.read_bytes(), previous)
            self.assertEqual(final.stat().st_mtime_ns, stamp)

    def test_holding_key_is_validated_only_if_emitted(self):
        source = "https://rism.online/sources/1"
        holding = source + "/holding%zz"
        institution = "https://rism.online/institutions/2"
        with tempfile.TemporaryDirectory() as directory:
            part = Path(directory) / "part-1-ttl.csv"
            output = Path(directory) / "part-1.ttl"
            predicate = str(converter.RISM_API.hasHolding)
            write_csv(
                part,
                [
                    ["subject", predicate, str(converter.WDT.P195)],
                    [source, holding, ""],
                    [holding, "", institution],
                ],
            )
            converter.process_file(
                part, {predicate: converter.WDT.P276}, {}, output, {}
            )
            self.assertEqual(
                set(parse(path=output, format=RdfFormat.TURTLE)),
                {
                    Quad(
                        NamedNode(source),
                        NamedNode(str(converter.WDT.P276)),
                        NamedNode(institution),
                    )
                },
            )

    def test_partial_write_leaves_final_path_untouched(self):
        def fail_after_write(graph, stream, **kwargs):
            stream.write(b"incomplete Turtle")
            raise OSError("injected write failure")

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            part = root / "part-1-ttl.csv"
            write_part(part, "Q42")
            output = root / "out"
            output.mkdir()
            final = output / "part-1.ttl"
            with patch.object(Graph, "serialize", fail_after_write):
                for previous in (None, b"<urn:s> <urn:p> <urn:o> .\n"):
                    with self.subTest(previous=previous):
                        if previous is not None:
                            final.write_bytes(previous)
                        with self.assertRaisesRegex(OSError, "injected write failure"):
                            converter.process_file(part, {}, {}, final, {})
                        if previous is None:
                            self.assertEqual(list(output.iterdir()), [])
                        else:
                            self.assertEqual(list(output.iterdir()), [final])
                            self.assertEqual(final.read_bytes(), previous)

    def test_cli_retries_failed_part_and_skips_successful_sibling(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inputs = root / "input"
            output = root / "output"
            inputs.mkdir()
            output.mkdir()
            first = inputs / "part-1-ttl.csv"
            second = inputs / "part-2-ttl.csv"
            write_part(first, "Q42")
            write_part(second, "Q1339")
            blocked = output / "part-1.ttl"
            blocked.mkdir()  # A directory at the destination forces a publication error.
            failed = run_converter(inputs, output)
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn(str(first), failed.stderr)
            sibling = output / "part-2.ttl"
            subject = URIRef("https://rism.online/people/1")
            self.assertEqual(
                set(Graph().parse(sibling)),
                {(subject, converter.WDT.P2888, converter.WD.Q1339)},
            )
            sibling_bytes = sibling.read_bytes()

            blocked.rmdir()
            (output / "part-1.bak").touch()
            write_part(second, "Q1")  # Reprocessing the sibling would change its graph.
            retry = run_converter(inputs, output)
            self.assertEqual(retry.returncode, 0, retry.stderr)
            self.assertEqual(
                set(Graph().parse(blocked)),
                {(subject, converter.WDT.P2888, converter.WD.Q42)},
            )
            self.assertEqual(sibling.read_bytes(), sibling_bytes)
