"""CSV-to-RDF regressions for multi-row OpenRefine records."""

import sys
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from rdflib import Literal, Namespace, RDF

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "shared"))
from rdfconv.convert import build_rdf_graph, fill_down_until_key, rdf_process_predicates

EX = Namespace("https://example.org/")
WD = Namespace("http://www.wikidata.org/entity/")
WDT = Namespace("http://www.wikidata.org/prop/direct/")


def convert_csv(table, schema, namespaces, csv_text, test_mode=False):
    with tempfile.TemporaryDirectory() as directory:
        (Path(directory) / f"{table}.csv").write_text(csv_text, encoding="utf-8")
        config = {
            "general": {"csv_folder": directory, "test_mode": test_mode},
            "namespaces": namespaces,
            table: schema,
        }
        return build_rdf_graph(rdf_process_predicates(config))


class RecordFillDownTests(unittest.TestCase):
    def test_empty_string_keys_continue_the_record_without_changing_input(self):
        frame = pd.DataFrame(
            {"id": ["", "A", "", "A"], "value": [None, "first", None, None]}
        )
        filled = fill_down_until_key(frame, "id").fillna("")
        self.assertEqual(filled["id"].tolist(), ["", "A", "A", "A"])
        self.assertEqual(filled["value"].tolist(), ["", "first", "first", ""])
        self.assertEqual(frame["id"].tolist(), ["", "A", "", "A"])

    def test_weimar_track_credits_stay_with_their_record(self):
        config = tomllib.loads((ROOT / "shared/rdf_config/wjazzd.toml").read_text())
        graph = convert_csv(
            "track_info",
            config["track_info"],
            config["namespaces"],
            "trackid,filename_track,recordid,lineup,instrument,mbzid,trackno,recordingdate,compid\n"
            ",,9,Q100,Q200,,,,\n"
            "1,,7,Q101,Q201,,,,\n"
            ",,,Q102,Q202,,,,\n"
            ",,,Q103,,,,,\n"
            "2,,8,Q104,Q204,,,,\n",
        )
        track = Namespace(config["namespaces"]["jt"])
        record = Namespace(config["namespaces"]["jr"])
        track_type = Namespace(config["namespaces"]["lmwj"]).Track
        self.assertEqual(
            set(graph),
            {
                (track["1"], RDF.type, track_type),
                (track["1"], WDT.P175, WD.Q101),
                (track["1"], WDT.P175, WD.Q102),
                (track["1"], WDT.P175, WD.Q103),
                (track["1"], WDT.P870, WD.Q201),
                (track["1"], WDT.P870, WD.Q202),
                (track["1"], WDT.P361, record["7"]),
                (track["2"], RDF.type, track_type),
                (track["2"], WDT.P175, WD.Q104),
                (track["2"], WDT.P870, WD.Q204),
                (track["2"], WDT.P361, record["8"]),
            },
        )

    def test_guide_example_keeps_both_emails_and_both_phone_numbers(self):
        graph = convert_csv(
            "contacts",
            {
                "PRIMARY_KEY": "Name",
                "Name": {"prefix": "ex"},
                "Email": "ex:email",
                "Phone": {"pred": "ex:phone", "if": "row['Name'] == subj"},
            },
            {"ex": str(EX)},
            "Name,Email,Phone\n"
            "Alice,a@example.com,123-456\n"
            ",a.work@example.com,\n"
            "Bob,b@example.com,789-000\n"
            ",,789-001\n"
            "Charlie,c@example.com,\n",
        )
        self.assertEqual(
            set(graph),
            {
                (EX.Alice, EX.email, Literal("a@example.com")),
                (EX.Alice, EX.email, Literal("a.work@example.com")),
                (EX.Alice, EX.phone, Literal("123-456")),
                (EX.Bob, EX.email, Literal("b@example.com")),
                (EX.Bob, EX.phone, Literal("789-000")),
                (EX.Bob, EX.phone, Literal("789-001")),
                (EX.Charlie, EX.email, Literal("c@example.com")),
            },
        )

    def test_explicit_subject_fills_within_the_record_and_resets_at_next_key(self):
        graph = convert_csv(
            "credits",
            {
                "PRIMARY_KEY": "track",
                "track": {"prefix": "ex"},
                "artist": {"prefix": "ex"},
                "name": {"subj": "artist", "pred": "ex:name"},
            },
            {"ex": str(EX)},
            "track,artist,name\n"
            ",Orphan,Leading\n"
            "Track1,A,First\n"
            ",,Alias\n"
            ",B,Second\n"
            "Track2,,Unattributed\n",
        )
        self.assertEqual(
            set(graph),
            {
                (EX.Orphan, EX.name, Literal("Leading")),
                (EX.A, EX.name, Literal("First")),
                (EX.A, EX.name, Literal("Alias")),
                (EX.B, EX.name, Literal("Second")),
            },
        )

    def test_sampled_continuations_keep_their_unsampled_record_headers(self):
        # Select exactly the 20 continuation rows, in reverse file order.
        def sample_continuations(frame, n):
            self.assertEqual(n, 20)
            return frame.drop(index=[0, 11]).iloc[::-1].head(n)

        rows = ["track,credit"]
        expected = set()
        for track in ("A", "B"):
            rows.append(f"{track},header-only credit")
            for index in range(10):
                rows.append(f",{track}{index}")
                expected.add((EX[track], EX.credit, Literal(f"{track}{index}")))
        with patch.object(pd.DataFrame, "sample", sample_continuations):
            graph = convert_csv(
                "tracks",
                {
                    "PRIMARY_KEY": "track",
                    "track": {"prefix": "ex"},
                    "credit": "ex:credit",
                },
                {"ex": str(EX)},
                "\n".join(rows),
                test_mode=True,
            )
        self.assertEqual(set(graph), expected)
