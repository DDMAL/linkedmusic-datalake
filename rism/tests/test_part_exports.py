"""Failure and resume checks for numbered RISM exports."""

import csv
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from rdflib import Graph, URIRef

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))
import convert_to_rdf as converter


def write_part(path, item):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["subject", str(converter.WDT.P2888)])
        writer.writerow(
            ["https://rism.online/people/1", f"https://wikidata.org/wiki/{item}"]
        )


class PartExportTests(unittest.TestCase):
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
            command = [
                sys.executable,
                str(SRC / "convert_to_rdf.py"),
                "--input_folder",
                str(inputs),
                "--mappings_folder",
                str(SRC / "mappings"),
                "--output_folder",
                str(output),
            ]
            failed = subprocess.run(command, capture_output=True, text=True, timeout=60)
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
            retry = subprocess.run(command, capture_output=True, text=True, timeout=60)
            self.assertEqual(retry.returncode, 0, retry.stderr)
            self.assertEqual(
                set(Graph().parse(blocked)),
                {(subject, converter.WDT.P2888, converter.WD.Q42)},
            )
            self.assertEqual(sibling.read_bytes(), sibling_bytes)
