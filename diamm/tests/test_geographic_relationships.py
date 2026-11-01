"""Preserve source-supported organization/region locations without inference."""

import csv
import json
import unittest

from rdflib import Graph, Literal, RDF, RDFS

import test_external_identifier_text as fixtures

DIAMM, LM, WD, WDT = fixtures.DIAMM, fixtures.LM, fixtures.WD, fixtures.WDT


class GeographicRelationshipTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.ExternalIdentifierTextTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.relations.write_text("key1,key2,type\n")

    def test_legacy_relation_rows_keep_local_endpoints_and_distinct_locations(self):
        self.fixture.write_exports({})
        self.fixture.relations.write_text(
            "key1,key2,type\norganization:7,region:7,\n"
            "organization:7,region:7,\norganization:7,region:8,\n"
            "organization:8,region:7,\n"
        )
        self.fixture.assert_graph_and_roundtrip(
            self.fixture.convert(),
            {
                (DIAMM["organizations/7"], LM.organizationLocation, DIAMM["regions/7"]),
                (DIAMM["organizations/7"], LM.organizationLocation, DIAMM["regions/8"]),
                (DIAMM["organizations/8"], LM.organizationLocation, DIAMM["regions/7"]),
            },
        )

    def test_existing_city_country_and_source_links_remain_distinct(self):
        self.fixture.write_exports({})
        self.fixture.relations.write_text(
            "key1,key2,type\ncity:2,organization:1,\n"
            "country:3,organization:1,\norganization:1,region:4,\n"
            "organization:1,source:5,copied\n"
            "organization:1,source:6,provenance\n"
        )
        # An organization's location does not imply that a manuscript was
        # copied or held there. Preserve the source's existing assertions only.
        expected = {
            (DIAMM["organizations/1"], WDT.P131, DIAMM["cities/2"]),
            (DIAMM["organizations/1"], WDT.P17, DIAMM["countries/3"]),
            (DIAMM["organizations/1"], LM.organizationLocation, DIAMM["regions/4"]),
            (DIAMM["sources/5"], WDT.P1071, DIAMM["organizations/1"]),
            (DIAMM["sources/6"], WDT.P276, DIAMM["organizations/1"]),
        }
        graph = self.fixture.convert()
        self.fixture.assert_graph_and_roundtrip(graph, expected)
        self.assertFalse(graph.query(f"""
            ASK {{
              VALUES ?source {{ <{DIAMM['sources/5']}> <{DIAMM['sources/6']}> }}
              VALUES ?property {{ <{WDT.P1071}> <{WDT.P276}> <{WDT.P131}>
                                 <{LM.organizationLocation}> }}
              ?source ?property <{DIAMM['regions/4']}> .
            }}
        """))

    def test_matching_hints_and_shared_matches_do_not_create_locations(self):
        self.fixture.write_exports(
            {
                "organizations": [
                    {
                        "id": "1",
                        "name": "Organization",
                        "name_@id": "Q42",
                        "country": "Region",
                        "country_@id": "Q43",
                    }
                ],
                "regions": [
                    {
                        "id": "2",
                        "name": "Region",
                        "name_@id": "Q42",
                        "country": "Country",
                        "country_@id": "Q43",
                    }
                ],
            }
        )
        self.fixture.assert_graph_and_roundtrip(
            self.fixture.convert(),
            {
                (DIAMM["organizations/1"], RDF.type, LM.Organization),
                (DIAMM["organizations/1"], RDFS.label, Literal("Organization")),
                (DIAMM["organizations/1"], WDT.P2888, WD.Q42),
                (DIAMM["regions/2"], RDF.type, LM.Region),
                (DIAMM["regions/2"], RDFS.label, Literal("Region")),
                (DIAMM["regions/2"], WDT.P2888, WD.Q42),
            },
        )

    def test_extraction_and_rdf_cli_keep_reverse_region_membership(self):
        # At the pinned upstream revision an organization located in a region
        # has no URL in its own location object. Region.organizations exposes
        # the same foreign key in the reverse direction with an explicit URL.
        raw = self.fixture.directory / "data/raw"
        records = {
            "organizations": [
                {
                    "pk": 7,
                    "name": "Institution",
                    "organization_type": "Institution",
                    "location": {
                        "url": None,
                        "name": "Cultural area",
                        "parent": "Hint",
                    },
                    "related_sources": [],
                    "copied_sources": [],
                    "source_provenance": [],
                },
                {
                    "pk": 8,
                    "name": "No supplied link",
                    "organization_type": "Institution",
                    "location": {
                        "url": None,
                        "name": "Cultural area",
                        "parent": "Hint",
                    },
                    "related_sources": [],
                    "copied_sources": [],
                    "source_provenance": [],
                },
            ],
            "regions": [
                {
                    "pk": 7,
                    "name": "Cultural area",
                    "parent": "Hint",
                    "organizations": [
                        {"url": f"{DIAMM}organizations/7/"},
                        {"url": f"{DIAMM}organizations/7/"},
                    ],
                    "cities": [],
                    "provenance": [],
                },
                {
                    "pk": 8,
                    "name": "Second supplied location",
                    "parent": "Other hint",
                    "organizations": [{"url": f"{DIAMM}organizations/7/"}],
                    "cities": [],
                    "provenance": [],
                },
            ],
        }
        for table, items in records.items():
            (raw / table).mkdir(parents=True)
            for item in items:
                (raw / table / f"{item['pk']}.json").write_text(
                    json.dumps(item), encoding="utf-8"
                )
        self.fixture.run_script("to_csv.py")
        with self.fixture.relations.open(newline="", encoding="utf-8") as source:
            relations = list(csv.DictReader(source))
        self.assertEqual(len(relations), 2)
        self.assertEqual(
            {tuple(row[k] for k in ("key1", "key2", "type")) for row in relations},
            {("organization:7", "region:7", ""), ("organization:7", "region:8", "")},
        )
        rows = {}
        for table in records:
            with (self.fixture.csv_dir / f"{table}.csv").open(
                newline="", encoding="utf-8"
            ) as source:
                rows[table] = list(csv.DictReader(source))
            self.assertEqual(len(rows[table]), 2)
            for row in rows[table]:
                row["name_@id"] = "Q42" if row["id"] == "7" else ""
                row["country_@id"] = "Q999"  # not evidence for a location
        self.fixture.write_exports(rows)
        self.fixture.run_script("convert_rdf.py")
        graph = Graph().parse(
            self.fixture.directory / "data/RDF/diamm.ttl", format="turtle"
        )
        expected = {
            (DIAMM["organizations/7"], LM.organizationLocation, DIAMM["regions/7"]),
            (DIAMM["organizations/7"], LM.organizationLocation, DIAMM["regions/8"]),
        }
        for table, kind in (("organizations", LM.Organization), ("regions", LM.Region)):
            for row in rows[table]:
                subject = DIAMM[f"{table}/{row['id']}"]
                expected.add((subject, RDF.type, kind))
                expected.add((subject, RDFS.label, Literal(row["name"])))
                if table == "organizations":
                    expected.add((subject, WDT.P31, Literal("Institution")))
                if row["id"] == "7":
                    expected.add((subject, WDT.P2888, WD.Q42))
        self.fixture.assert_graph_and_roundtrip(graph, expected)
        result = graph.query(f"""
            SELECT ?organization ?region ?name WHERE {{
              ?organization a <{LM.Organization}>; <{LM.organizationLocation}> ?region .
              ?region a <{LM.Region}>; <{RDFS.label}> ?name .
            }}
        """)
        self.assertEqual(
            {tuple(row) for row in result},
            {
                (
                    DIAMM["organizations/7"],
                    DIAMM["regions/7"],
                    Literal("Cultural area"),
                ),
                (
                    DIAMM["organizations/7"],
                    DIAMM["regions/8"],
                    Literal("Second supplied location"),
                ),
            },
        )


if __name__ == "__main__":
    unittest.main()
