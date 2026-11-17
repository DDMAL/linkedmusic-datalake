"""Synthetic CSV-to-RDF regressions for text parsing and lookup isolation."""

import argparse
import csv
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from rdflib import Graph, Literal, Namespace, RDF, RDFS

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import convert_to_rdf as converter
from mapping_schema import MappingSchema

WD = Namespace("http://www.wikidata.org/entity/")
WDT = Namespace("http://www.wikidata.org/prop/direct/")
LM = Namespace("https://linkedmusic.ca/graphs/musicbrainz/")
MB = Namespace("https://musicbrainz.org/")


class ReconciliationLoadingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="musicbrainz-lookups-")
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.reconciled = self.directory / "reconciled"
        self.inputs = self.directory / "inputs"
        self.reconciled.mkdir()
        self.inputs.mkdir()
        self.schema = MappingSchema({})
        self.schema.add_from_formatted_dict(
            json.loads((ROOT / "src/rdf_conversion_config/mappings.json").read_text())
        )

    def write_csv(self, export, rows):
        template = json.loads(
            (ROOT / f"openrefine/export/{export}_export.json").read_text()
        )
        path = self.reconciled / f"{export}-csv.csv"
        with path.open("w", newline="", encoding="utf-8") as output:
            writer = csv.DictWriter(
                output, fieldnames=[c["name"] for c in template["columns"]]
            )
            writer.writeheader()
            writer.writerows(rows)
        return path

    def write_fixture(self):
        # QIDs deliberately differ by field and entity kind. They are synthetic
        # controls, not claims about real MusicBrainz/Wikidata matches.
        for entity, qid in (
            ("artist", "Q101"),
            ("work", "Q102"),
            ("release-group", "Q103"),
        ):
            self.write_csv(f"{entity}-types", [{"type": "Other", "type_@id": qid}])
        self.write_csv("keys", [{"key": "Other", "key_@id": "Q201"}])
        self.write_csv("genders", [{"gender": "Other", "gender_@id": "Q202"}])
        self.write_csv(
            "languages",
            [
                {
                    "language": "Other",
                    "full_language": "Synthetic",
                    "full_language_@id": "Q203",
                },
                {
                    "language": "nan",
                    "full_language": "Synthetic language",
                    "full_language_@id": "Q206",
                },
                {
                    "language": "blank",
                    "full_language": "No match",
                    "full_language_@id": "",
                },
                {
                    "language": "unmatched",
                    "full_language": "NA",
                    "full_language_@id": "NA",
                },
            ],
        )
        self.write_csv(
            "packagings",
            [
                {"packaging": "Other", "packaging_@id": "Q204"},
                {"packaging": "None", "packaging_@id": "Q207"},
            ],
        )
        self.write_csv("statuses", [{"status": "Other", "status_@id": "Q205"}])
        records = {
            "artist": [
                {
                    "id": "artist",
                    "name": "Source artist",
                    "type": "Other",
                    "gender": "Other",
                }
            ],
            "work": [
                {
                    "id": "work",
                    "name": "Source work",
                    "type": "Other",
                    "attributes": [{"type": "Key", "value": "Other"}],
                    "languages": ["Other", "nan", "blank", "unmatched"],
                }
            ],
            "release-group": [
                {
                    "id": "group",
                    "primary-type": "Other",
                    "secondary-types": ["Unmatched"],
                }
            ],
            "release": [
                {
                    "id": "release",
                    "packaging": "Other",
                    "status": "Other",
                    "artist-credit": [{"artist": {"id": "artist"}}],
                    "release-group": {"id": "group"},
                    "media": [
                        {
                            "tracks": [
                                {
                                    "recording": {
                                        "id": "recording",
                                        "title": "Embedded recording",
                                    }
                                }
                            ]
                        }
                    ],
                },
                {"id": "no-packaging", "packaging": "None"},
            ],
        }
        for entity, rows in records.items():
            (self.inputs / f"{entity}.jsonl").write_text(
                "".join(json.dumps(row) + "\n" for row in rows)
            )

    def expected(self):
        return {
            (MB["artist/artist"], RDF.type, LM.Artist),
            (MB["artist/artist"], RDFS.label, Literal("Source artist")),
            (MB["artist/artist"], WDT.P31, WD.Q101),
            (MB["artist/artist"], WDT.P21, WD.Q202),
            (MB["work/work"], RDF.type, LM.Work),
            (MB["work/work"], RDFS.label, Literal("Source work")),
            (MB["work/work"], WDT.P31, WD.Q102),
            (MB["work/work"], WDT.P826, WD.Q201),
            (MB["work/work"], WDT.P407, WD.Q203),
            (MB["work/work"], WDT.P407, WD.Q206),
            (MB["work/work"], WDT.P407, Literal("blank")),
            (MB["work/work"], WDT.P407, Literal("NA")),
            (MB["release-group/group"], RDF.type, LM.ReleaseGroup),
            (MB["release-group/group"], WDT.P31, WD.Q103),
            (MB["release-group/group"], WDT.P31, Literal("Unmatched")),
            (MB["release/release"], RDF.type, LM.Release),
            (MB["release/release"], WDT.P9813, WD.Q204),
            (MB["release/release"], WDT.P31, WD.Q205),
            (MB["release/release"], WDT.P175, MB["artist/artist"]),
            (MB["release/release"], WDT.P361, MB["release-group/group"]),
            (MB["release/release"], WDT.P658, MB["recording/recording"]),
            (MB["recording/recording"], RDF.type, LM.Recording),
            (MB["recording/recording"], RDFS.label, Literal("Embedded recording")),
            (MB["release/no-packaging"], RDF.type, LM.Release),
            (MB["release/no-packaging"], WDT.P9813, WD.Q207),
        }

    def convert_via_main(self):
        graph = Graph()

        async def collect(entity_type, input_file, output_folder, namespaces, mappings):
            nonlocal graph
            graph += converter.process_chunk(
                Path(input_file).read_text().splitlines(),
                entity_type,
                self.schema,
                {},
                mappings,
                {"Key": WDT.P826},
            )

        with patch.object(
            converter,
            "RECONCILIATION_MAPPING",
            converter.load_auxiliary_reconciliations(self.reconciled),
        ), patch.object(converter, "create_graphs", collect):
            for input_file in sorted(self.inputs.glob("*.jsonl")):
                type_file = self.reconciled / f"{input_file.stem}-types-csv.csv"
                converter.main(
                    argparse.Namespace(
                        input_file=str(input_file),
                        type_file=str(type_file) if type_file.is_file() else None,
                        output_folder=str(self.directory / "output"),
                    )
                )
        return graph

    def test_csv_reader_preserves_text_and_empty_candidates(self):
        data = io.StringIO(
            'key,key_@id\nnan,Q42\nNone,None\nNA,NA\nnull,null\n001,001\nblank,\n" spaced "," Q42 "\n,Q43\n'
        )
        self.assertEqual(
            converter.load_reconciliation_csv(data, "key", "key_@id"),
            {
                "nan": "Q42",
                "None": "None",
                "NA": "NA",
                "null": "null",
                "001": "001",
                "blank": "",
                " spaced ": " Q42 ",
            },
        )

    def test_loader_and_main_isolate_fields_and_entity_types(self):
        self.write_fixture()
        self.assertEqual(set(self.convert_via_main()), self.expected())

    def test_missing_tables_do_not_borrow_other_fields_matches(self):
        self.write_fixture()
        cases = (
            ("artist-types", [(MB["artist/artist"], WDT.P31, WD.Q101, "Other")]),
            ("genders", [(MB["artist/artist"], WDT.P21, WD.Q202, "Other")]),
            ("keys", [(MB["work/work"], WDT.P826, WD.Q201, "Other")]),
            (
                "languages",
                [
                    (MB["work/work"], WDT.P407, WD.Q203, "Other"),
                    (MB["work/work"], WDT.P407, WD.Q206, "nan"),
                    (MB["work/work"], WDT.P407, Literal("NA"), "unmatched"),
                ],
            ),
            (
                "packagings",
                [
                    (MB["release/release"], WDT.P9813, WD.Q204, "Other"),
                    (MB["release/no-packaging"], WDT.P9813, WD.Q207, "None"),
                ],
            ),
            ("statuses", [(MB["release/release"], WDT.P31, WD.Q205, "Other")]),
        )
        for name, fallbacks in cases:
            with self.subTest(missing=name):
                path = self.reconciled / f"{name}-csv.csv"
                saved = path.read_bytes()
                path.unlink()
                try:
                    expected = self.expected()
                    for subject, predicate, old, text in fallbacks:
                        expected.remove((subject, predicate, old))
                        expected.add((subject, predicate, Literal(text)))
                    self.assertEqual(set(self.convert_via_main()), expected)
                finally:
                    path.write_bytes(saved)

    def test_real_cli_loads_csvs_and_serializes_complete_graphs(self):
        self.write_fixture()
        output = self.directory / "rdf"
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "src/convert_to_rdf.py"),
                "--input_folder",
                str(self.inputs),
                "--reconciled_folder",
                str(self.reconciled),
                "--config_folder",
                str(ROOT / "src/rdf_conversion_config"),
                "--output_folder",
                str(output),
            ],
            cwd=self.directory,
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        graph = Graph()
        files = list(output.glob("*.ttl"))
        self.assertEqual(len(files), 4, result.stdout + result.stderr)
        for path in files:
            graph.parse(path, format="turtle")
        self.assertEqual(set(graph), self.expected())


if __name__ == "__main__":
    unittest.main()
