"""Preserve explicit organization locations at the geographic level supplied."""

import csv
import json
import unittest

from rdflib import Graph, Literal, RDF, RDFS
from rdflib.namespace import DCTERMS, SDO

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
                (DIAMM["organizations/7"], SDO.location, DIAMM["regions/7"]),
                (DIAMM["organizations/7"], SDO.location, DIAMM["regions/8"]),
                (DIAMM["organizations/8"], SDO.location, DIAMM["regions/7"]),
            },
        )

    def test_direct_locations_keep_city_country_region_and_manuscript_links_distinct(
        self,
    ):
        self.fixture.write_exports({})
        self.fixture.relations.write_text(
            "key1,key2,type\ncity:2,organization:1,\n"
            "country:3,organization:2,\norganization:3,region:4,\n"
            "city:2,country:3,\ncity:2,region:4,\n"
            "organization:1,source:5,copied\n"
            "organization:1,source:6,provenance\n"
        )
        # An organization's location does not imply that a manuscript was
        # copied or held there. Preserve the source's existing assertions only.
        graph = self.fixture.convert()
        (legacy,) = graph.objects(DIAMM["sources/6"], LM.organizationProvenance)
        expected = {
            (DIAMM["organizations/1"], SDO.location, DIAMM["cities/2"]),
            (DIAMM["organizations/2"], SDO.location, DIAMM["countries/3"]),
            (DIAMM["organizations/3"], SDO.location, DIAMM["regions/4"]),
            (DIAMM["cities/2"], WDT.P17, DIAMM["countries/3"]),
            (DIAMM["cities/2"], WDT.P131, DIAMM["regions/4"]),
            (DIAMM["sources/5"], WDT.P1071, DIAMM["organizations/1"]),
            (DIAMM["sources/6"], LM.organizationProvenance, legacy),
            (legacy, RDF.type, LM.OrganizationProvenanceObservation),
            (legacy, DCTERMS.source, DIAMM["organizations/1"]),
            (legacy, LM.validationFlag, Literal("legacy-unqualified-provenance")),
        }
        self.fixture.assert_graph_and_roundtrip(graph, expected)
        locations = graph.query(
            "SELECT ?org ?place WHERE { ?org <https://schema.org/location> ?place }"
        )
        self.assertEqual(
            {tuple(row) for row in locations},
            {
                (DIAMM["organizations/1"], DIAMM["cities/2"]),
                (DIAMM["organizations/2"], DIAMM["countries/3"]),
                (DIAMM["organizations/3"], DIAMM["regions/4"]),
            },
        )
        self.assertFalse(
            graph.query(
                f"""
            ASK {{
              VALUES ?source {{ <{DIAMM['sources/5']}> <{DIAMM['sources/6']}> }}
              VALUES ?property {{ <{WDT.P1071}> <{WDT.P276}> <{WDT.P131}>
                                 <{SDO.location}> }}
              ?source ?property <{DIAMM['regions/4']}> .
            }}
        """
            )
        )

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

    def test_extraction_and_rdf_cli_preserve_direct_organization_locations(self):
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
        for org_id, place_path in ((9, "cities/7/"), (10, "countries/7/")):
            records["organizations"].append(
                {
                    "pk": org_id,
                    "name": "Institution with a location URL",
                    "organization_type": "Institution",
                    "location": {
                        "url": f"{DIAMM}{place_path}",
                        "name": "Listed place",
                        "parent": "Hint",
                    },
                    "related_sources": [],
                    "copied_sources": [],
                    "source_provenance": [],
                }
            )
        for table, items in records.items():
            (raw / table).mkdir(parents=True)
            for item in items:
                (raw / table / f"{item['pk']}.json").write_text(
                    json.dumps(item), encoding="utf-8"
                )
        self.fixture.run_script("to_csv.py")
        with self.fixture.relations.open(newline="", encoding="utf-8") as source:
            relations = list(csv.DictReader(source))
        self.assertEqual(len(relations), 4)
        self.assertEqual(
            {tuple(row[k] for k in ("key1", "key2", "type")) for row in relations},
            {
                ("organization:7", "region:7", ""),
                ("organization:7", "region:8", ""),
                ("city:7", "organization:9", ""),
                ("country:7", "organization:10", ""),
            },
        )
        rows = {}
        for table in records:
            with (self.fixture.csv_dir / f"{table}.csv").open(
                newline="", encoding="utf-8"
            ) as source:
                rows[table] = list(csv.DictReader(source))
            self.assertEqual(len(rows[table]), len(records[table]))
            for row in rows[table]:
                row["name_@id"] = "Q42" if row["id"] == "7" else ""
                row["country_@id"] = "Q999"  # not evidence for a location
        self.fixture.write_exports(rows)
        self.fixture.run_script("convert_rdf.py")
        graph = Graph().parse(
            self.fixture.directory / "data/RDF/diamm.ttl", format="turtle"
        )
        expected = {
            (DIAMM["organizations/7"], SDO.location, DIAMM["regions/7"]),
            (DIAMM["organizations/9"], SDO.location, DIAMM["cities/7"]),
            (DIAMM["organizations/10"], SDO.location, DIAMM["countries/7"]),
            (DIAMM["organizations/7"], SDO.location, DIAMM["regions/8"]),
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
        result = graph.query(
            f"""
            SELECT ?organization ?region ?name WHERE {{
              ?organization a <{LM.Organization}>; <{SDO.location}> ?region .
              ?region a <{LM.Region}>; <{RDFS.label}> ?name .
            }}
        """
        )
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
