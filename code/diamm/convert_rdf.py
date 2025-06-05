"""
Converts all the DIAMM reconciled CSV files to RDF (turtle) format.
"""

import json
import re
import os
import pandas as pd
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF

BASE_PATH = "../../data/diamm/reconciled/"
RELATIONS_PATH = "../../data/diamm/csv/relations.csv"
OUTPUT_PATH = "../../data/diamm/RDF/"

os.makedirs(OUTPUT_PATH, exist_ok=True)

SCHEMA = Namespace("http://schema.org/")
WDT = Namespace("http://www.wikidata.org/prop/direct/")
WD = Namespace("http://www.wikidata.org/entity/")
DIAMM = Namespace("https://www.diamm.ac.uk/")
DA = Namespace(f"{DIAMM}archives/")
DC = Namespace(f"{DIAMM}cities/")
DN = Namespace(f"{DIAMM}countries/")
DM = Namespace(f"{DIAMM}compositions/")
DO = Namespace(f"{DIAMM}organizations/")
DP = Namespace(f"{DIAMM}people/")
DS = Namespace(f"{DIAMM}sources/")
DE = Namespace(f"{DIAMM}sets/")

# DIAMM schema properties contained in one location to make it easier to change
DIAMM_SCHEMA = {
    "wikidata_id": "P2888",
    "name": "P2561",
    "title": "P1476",
    "siglum": "P11550",
    "website": "P856",
    "rism_id": "P5504",
    "city": "P131",
    "country": "P17",
    "type": "P31",
    "composer": "P86",
    "genre": "P136",
    "variant_names": "P1449",
    "earliest_year": "P569",
    "latest_year": "P570",
    "viaf_id": "P214",
    "shelfmark": "P217",
    "cluster_shelfmark": "P217",
    "holding_archive": "P276",
    "composition_in_source": "P361",
    "related_organization": "P2860",
    "copied_organization": "P1071",
    "provenance_organization": "P276",
    "related_people": "P767",
    "copied_people": "P170",
    "set_in_source": "P361",
    "display_name": "P2561",
}

namespaces = {
    "schema": SCHEMA,
    "wdt": WDT,
    "wd": WD,
    "diamm": DIAMM,
    "da": DA,
    "dc": DC,
    "dn": DN,
    "dm": DM,
    "do": DO,
    "dp": DP,
    "ds": DS,
    "de": DE,
}


def matched_wikidata(field: str) -> bool:
    """Check if the field is a matched Wikidata ID."""
    return re.match(r"^Q\d+", field) is not None


archives = pd.read_csv(os.path.join(BASE_PATH, "archives-csv.csv"))
compositions = pd.read_csv(os.path.join(BASE_PATH, "compositions-csv.csv"))
organizations = pd.read_csv(os.path.join(BASE_PATH, "organizations-csv.csv"))
people = pd.read_csv(os.path.join(BASE_PATH, "people-csv.csv"))
sets = pd.read_csv(os.path.join(BASE_PATH, "sets-csv.csv"))
sources = pd.read_csv(os.path.join(BASE_PATH, "sources-csv.csv"))

relations = pd.read_csv(RELATIONS_PATH)

g = Graph()

# Bind namespaces
for prefix, ns in namespaces.items():
    g.bind(prefix, ns)

print("Processing archives...")
json_data = json.loads(archives.to_json(orient="records"))
for work in json_data:
    subject_uri = URIRef(f"{DA}{int(work['id'])}")
    g.add((subject_uri, RDF.type, URIRef(f"{DIAMM}Archive")))

    if matched_wikidata(work["name_@id"]):
        # Use the `same as` property to indicate if the archive has been reconciled
        g.add(
            (
                subject_uri,
                URIRef(f"{WDT}{DIAMM_SCHEMA["wikidata_id"]}"),
                URIRef(f"{WD}{work['name_@id']}"),
            )
        )
    g.add((subject_uri, URIRef(f"{WDT}{DIAMM_SCHEMA["name"]}"), Literal(work["name"])))

    if work["siglum"] is not None:
        g.add(
            (
                subject_uri,
                URIRef(f"{WDT}{DIAMM_SCHEMA["siglum"]}"),
                Literal(work["siglum"]),
            )
        )
    if work["website"] is not None:
        g.add(
            (
                subject_uri,
                URIRef(f"{WDT}{DIAMM_SCHEMA["website"]}"),
                URIRef(work["website"]),
            )
        )
    if work["rism_id"] is not None:
        g.add(
            (
                subject_uri,
                URIRef(f"{WDT}{DIAMM_SCHEMA["rism_id"]}"),
                Literal(work["rism_id"]),
            )
        )

    if matched_wikidata(work["city_@id"]):
        g.add(
            (
                subject_uri,
                URIRef(f"{WDT}{DIAMM_SCHEMA["city"]}"),
                URIRef(f"{WD}{work['city_@id']}"),
            )
        )
        if work["city_id"]:
            # Add a statement saying that the city is the same as the Wikidata entity
            g.add(
                (
                    URIRef(f"{DC}{work['city_id']}"),
                    URIRef(f"{WDT}{DIAMM_SCHEMA["wikidata_id"]}"),
                    URIRef(f"{WD}{work['city_@id']}"),
                )
            )
    else:
        g.add(
            (subject_uri, URIRef(f"{WDT}{DIAMM_SCHEMA["city"]}"), Literal(work["city"]))
        )

    if matched_wikidata(work["country_@id"]):
        g.add(
            (
                subject_uri,
                URIRef(f"{WDT}{DIAMM_SCHEMA["country"]}"),
                URIRef(f"{WD}{work['country_@id']}"),
            )
        )
    else:
        g.add(
            (
                subject_uri,
                URIRef(f"{WDT}{DIAMM_SCHEMA["country"]}"),
                Literal(work["country"]),
            )
        )

print("Processing compositions...")
json_data = json.loads(compositions.to_json(orient="records"))
for work in json_data:
    if work["id"] is None:  # There is just the genre to deal with
        if matched_wikidata(work["genres_@id"]):
            g.add(
                (
                    subject_uri,
                    URIRef(f"{WDT}{DIAMM_SCHEMA["genre"]}"),
                    URIRef(f"{WD}{work['genres_@id']}"),
                )
            )
        else:
            g.add(
                (
                    subject_uri,
                    URIRef(f"{WDT}{DIAMM_SCHEMA["genre"]}"),
                    Literal(work["genres"]),
                )
            )
        continue

    subject_uri = URIRef(f"{DM}{int(work['id'])}")
    g.add((subject_uri, RDF.type, URIRef(f"{DIAMM}Composition")))
    g.add(
        (subject_uri, URIRef(f"{WDT}{DIAMM_SCHEMA["title"]}"), Literal(work["title"]))
    )

    if work["anonymous"] is True:
        g.add(
            (
                subject_uri,
                URIRef(f"{WDT}{DIAMM_SCHEMA["composer"]}"),
                Literal("Anonymous"),
            )
        )

    if work["genres"] is not None:
        if matched_wikidata(work["genres_@id"]):
            g.add(
                (
                    subject_uri,
                    URIRef(f"{WDT}{DIAMM_SCHEMA["genre"]}"),
                    URIRef(f"{WD}{work['genres_@id']}"),
                )
            )
        else:
            g.add(
                (
                    subject_uri,
                    URIRef(f"{WDT}{DIAMM_SCHEMA["genre"]}"),
                    Literal(work["genres"]),
                )
            )

print("Processing organizations...")
json_data = json.loads(organizations.to_json(orient="records"))
for work in json_data:
    if work["id"] is None:  # There is just the type to deal with
        if matched_wikidata(work["organization_type_@id"]):
            g.add(
                (
                    subject_uri,
                    URIRef(f"{WDT}{DIAMM_SCHEMA["type"]}"),
                    URIRef(f"{WD}{work['organization_type_@id']}"),
                )
            )
        else:
            g.add(
                (
                    subject_uri,
                    URIRef(f"{WDT}{DIAMM_SCHEMA["type"]}"),
                    Literal(work["organization_type"]),
                )
            )
        continue

    subject_uri = URIRef(f"{DO}{int(work['id'])}")
    g.add((subject_uri, RDF.type, URIRef(f"{DIAMM}Organization")))

    if matched_wikidata(work["name_@id"]):
        # Use the `same as` property to indicate if the organization has been reconciled
        g.add(
            (
                subject_uri,
                URIRef(f"{WDT}{DIAMM_SCHEMA["wikidata_id"]}"),
                URIRef(f"{WD}{work['name_@id']}"),
            )
        )
    g.add((subject_uri, URIRef(f"{WDT}{DIAMM_SCHEMA["name"]}"), Literal(work["name"])))

    if work["organization_type"] is not None:
        if matched_wikidata(work["organization_type_@id"]):
            g.add(
                (
                    subject_uri,
                    URIRef(f"{WDT}{DIAMM_SCHEMA["type"]}"),
                    URIRef(f"{WD}{work['organization_type_@id']}"),
                )
            )
        else:
            g.add(
                (
                    subject_uri,
                    URIRef(f"{WDT}{DIAMM_SCHEMA["type"]}"),
                    Literal(work["organization_type"]),
                )
            )

    if work["city_@id"] is not None:
        if matched_wikidata(work["city_@id"]):
            g.add(
                (
                    subject_uri,
                    URIRef(f"{WDT}{DIAMM_SCHEMA["city"]}"),
                    URIRef(f"{WD}{work['city_@id']}"),
                )
            )
            if work["city_id"]:
                # Add a statement saying that the city is the same as the Wikidata entity
                g.add(
                    (
                        URIRef(f"{DC}{work['city_id']}"),
                        URIRef(f"{WDT}{DIAMM_SCHEMA["wikidata_id"]}"),
                        URIRef(f"{WD}{work['city_@id']}"),
                    )
                )
        else:
            g.add(
                (
                    subject_uri,
                    URIRef(f"{WDT}{DIAMM_SCHEMA["city"]}"),
                    Literal(work["city"]),
                )
            )

    if work["country_@id"] is not None:
        if matched_wikidata(work["country_@id"]):
            g.add(
                (
                    subject_uri,
                    URIRef(f"{WDT}{DIAMM_SCHEMA["country"]}"),
                    URIRef(f"{WD}{work['country_@id']}"),
                )
            )
            if work["country_id"]:
                # Add a statement saying that the country is the same as the Wikidata entity
                g.add(
                    (
                        URIRef(f"{DN}{work['country_id']}"),
                        URIRef(f"{WDT}{DIAMM_SCHEMA["wikidata_id"]}"),
                        URIRef(f"{WD}{work['country_@id']}"),
                    )
                )
        else:
            g.add(
                (
                    subject_uri,
                    URIRef(f"{WDT}{DIAMM_SCHEMA["country"]}"),
                    Literal(work["country"]),
                )
            )

print("Processing people...")
json_data = json.loads(people.to_json(orient="records"))
for work in json_data:
    subject_uri = URIRef(f"{DP}{int(work['id'])}")
    g.add((subject_uri, RDF.type, URIRef(f"{DIAMM}Person")))

    if matched_wikidata(work["full_name_@id"]):
        # Use the `same as` property to indicate if the person has been reconciled
        g.add(
            (
                subject_uri,
                URIRef(f"{WDT}{DIAMM_SCHEMA["wikidata_id"]}"),
                URIRef(f"{WD}{work['full_name_@id']}"),
            )
        )
    g.add(
        (
            subject_uri,
            URIRef(f"{WDT}{DIAMM_SCHEMA["name"]}"),
            Literal(work["full_name"]),
        )
    )

    if work["variant_names"] is not None:
        for name in work["variant_names"].split(", "):
            g.add(
                (
                    subject_uri,
                    URIRef(f"{WDT}{DIAMM_SCHEMA["variant_names"]}"),
                    Literal(name),
                )
            )

    if work["earliest_year_@id"] is not None:
        g.add(
            (
                subject_uri,
                URIRef(f"{WDT}{DIAMM_SCHEMA["earliest_year"]}"),
                URIRef(f"{WD}{work['earliest_year_@id']}"),
            )
        )
    if work["latest_year_@id"] is not None:
        g.add(
            (
                subject_uri,
                URIRef(f"{WDT}{DIAMM_SCHEMA["latest_year"]}"),
                URIRef(f"{WD}{work['latest_year_@id']}"),
            )
        )

    if work["rism_id"] is not None:
        g.add(
            (
                subject_uri,
                URIRef(f"{WDT}{DIAMM_SCHEMA["rism_id"]}"),
                Literal(work["rism_id"]),
            )
        )
    if work["viaf_id"] is not None:
        g.add(
            (
                subject_uri,
                URIRef(f"{WDT}{DIAMM_SCHEMA["viaf_id"]}"),
                Literal(work["viaf_id"]),
            )
        )

print("Processing sets...")
json_data = json.loads(sets.to_json(orient="records"))
for work in json_data:
    subject_uri = URIRef(f"{DE}{int(work['id'])}")
    g.add((subject_uri, RDF.type, URIRef(f"{DIAMM}Set")))

    if matched_wikidata(work["type_@id"]):
        g.add(
            (
                subject_uri,
                URIRef(f"{WDT}{DIAMM_SCHEMA["type"]}"),
                URIRef(f"{WD}{work['type_@id']}"),
            )
        )
    else:
        g.add(
            (subject_uri, URIRef(f"{WDT}{DIAMM_SCHEMA["type"]}"), Literal(work["type"]))
        )

    g.add(
        (
            subject_uri,
            URIRef(f"{WDT}{DIAMM_SCHEMA["cluster_shelfmark"]}"),
            Literal(work["cluster_shelfmark"]),
        )
    )

print("Processing sources...")
json_data = json.loads(sources.to_json(orient="records"))
for work in json_data:
    subject_uri = URIRef(f"{DS}{int(work['id'])}")
    g.add((subject_uri, RDF.type, URIRef(f"{DIAMM}Source")))

    g.add(
        (
            subject_uri,
            URIRef(f"{WDT}{DIAMM_SCHEMA["display_name"]}"),
            Literal(work["display_name"]),
        )
    )
    g.add(
        (
            subject_uri,
            URIRef(f"{WDT}{DIAMM_SCHEMA["shelfmark"]}"),
            Literal(work["shelfmark"]),
        )
    )

    if work["source_type"] is not None:
        if matched_wikidata(work["source_type_@id"]):
            g.add(
                (
                    subject_uri,
                    URIRef(f"{WDT}{DIAMM_SCHEMA["type"]}"),
                    URIRef(f"{WD}{work['source_type_@id']}"),
                )
            )
        else:
            g.add(
                (
                    subject_uri,
                    URIRef(f"{WDT}{DIAMM_SCHEMA["type"]}"),
                    Literal(work["source_type"]),
                )
            )

print("Processing relations...")
json_data = json.loads(relations.to_json(orient="records"))
for work in json_data:
    first_type, first_id = work["key1"].split(":")
    second_type, second_id = work["key2"].split(":")
    first_id, second_id = int(first_id), int(second_id)

    if first_type == "archive" and second_type == "source":
        first_uri = URIRef(f"{DA}{first_id}")
        second_uri = URIRef(f"{DS}{second_id}")
        g.add(
            (second_uri, URIRef(f"{WDT}{DIAMM_SCHEMA["holding_archive"]}"), first_uri)
        )
    elif first_type == "composition" and second_type == "people":
        first_uri = URIRef(f"{DM}{first_id}")
        second_uri = URIRef(f"{DP}{second_id}")
        g.add((first_uri, URIRef(f"{WDT}{DIAMM_SCHEMA["composer"]}"), second_uri))
    elif first_type == "composition" and second_type == "source":
        first_uri = URIRef(f"{DM}{first_id}")
        second_uri = URIRef(f"{DS}{second_id}")
        g.add(
            (
                first_uri,
                URIRef(f"{WDT}{DIAMM_SCHEMA["composition_in_source"]}"),
                second_uri,
            )
        )
    elif first_type == "organization" and second_type == "source":
        first_uri = URIRef(f"{DO}{first_id}")
        second_uri = URIRef(f"{DS}{second_id}")

        if work["type"] == "related":
            g.add(
                (
                    first_uri,
                    URIRef(f"{WDT}{DIAMM_SCHEMA["related_organization"]}"),
                    second_uri,
                )
            )
        elif work["type"] == "copied":
            g.add(
                (
                    first_uri,
                    URIRef(f"{WDT}{DIAMM_SCHEMA["copied_organization"]}"),
                    second_uri,
                )
            )
        elif work["type"] == "provenance":
            g.add(
                (
                    first_uri,
                    URIRef(f"{WDT}{DIAMM_SCHEMA["provenance_organization"]}"),
                    second_uri,
                )
            )
    elif first_type == "people" and second_type == "source":
        first_uri = URIRef(f"{DP}{first_id}")
        second_uri = URIRef(f"{DS}{second_id}")

        if work["type"] == "related":
            g.add(
                (
                    second_uri,
                    URIRef(f"{WDT}{DIAMM_SCHEMA["related_people"]}"),
                    first_uri,
                )
            )
        elif work["type"] == "copied":
            g.add(
                (second_uri, URIRef(f"{WDT}{DIAMM_SCHEMA["copied_people"]}"), first_uri)
            )
    elif first_type == "archive" and second_type == "set":
        first_uri = URIRef(f"{DA}{first_id}")
        second_uri = URIRef(f"{DE}{second_id}")
        g.add(
            (second_uri, URIRef(f"{WDT}{DIAMM_SCHEMA["holding_archive"]}"), first_uri)
        )
    elif first_type == "set" and second_type == "source":
        first_uri = URIRef(f"{DE}{first_id}")
        second_uri = URIRef(f"{DS}{second_id}")
        g.add((first_uri, URIRef(f"{WDT}{DIAMM_SCHEMA["set_in_source"]}"), second_uri))

# Serialize the graph to RDF format
print("Serializing the graph...")
g.serialize(destination=os.path.join(OUTPUT_PATH, "diamm.ttl"), format="turtle")
