"""
Converts all the DIAMM reconciled CSV files to RDF (turtle) format.
"""

import json
import re
import os
import pandas as pd
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDFS

BASE_PATH = "../../data/diamm/reconciled/"
RELATIONS_PATH = "../../data/diamm/csv/relations.csv"
OUTPUT_PATH = "../../data/diamm/RDF/"

os.makedirs(OUTPUT_PATH, exist_ok=True)

WDT = Namespace("http://www.wikidata.org/prop/direct/")
WD = Namespace("http://www.wikidata.org/entity/")
DIAMM = Namespace("https://www.diamm.ac.uk/")
DA = Namespace(f"{DIAMM}archives/")
DI = Namespace(f"{DIAMM}cities/")
DM = Namespace(f"{DIAMM}compositions/")
DN = Namespace(f"{DIAMM}countries/")
DO = Namespace(f"{DIAMM}organizations/")
DP = Namespace(f"{DIAMM}people/")
DR = Namespace(f"{DIAMM}regions/")
DS = Namespace(f"{DIAMM}sources/")
DE = Namespace(f"{DIAMM}sets/")

# DIAMM schema properties contained in one location to make it easier to change
DIAMM_SCHEMA = {
    "wikidata_id": WDT["P2888"],
    "name": RDFS.label,
    "title": WDT["P1476"],
    "siglum": WDT["P11550"],
    "website": WDT["P856"],
    "rism_id": WDT["P5504"],
    "city": WDT["P131"],
    "region": WDT["P131"],
    "country": WDT["P17"],
    "location": WDT["P276"],
    "type": WDT["P31"],
    "composer": WDT["P86"],
    "genre": WDT["P136"],
    "variant_names": WDT["P1449"],
    "earliest_year": WDT["P569"],
    "latest_year": WDT["P570"],
    "viaf_id": WDT["P214"],
    "shelfmark": WDT["P217"],
    "cluster_shelfmark": WDT["P217"],
    "holding_archive": WDT["P276"],
    "composition_in_source": WDT["P361"],
    "related_organization": WDT["P2860"],
    "copied_organization": WDT["P1071"],
    "provenance_organization": WDT["P276"],
    "related_people": WDT["P767"],
    "copied_people": WDT["P170"],
    "set_in_source": WDT["P361"],
    "display_name": WDT["P2561"],
}

namespaces = {
    "wdt": WDT,
    "wd": WD,
    "diamm": DIAMM,
    "da": DA,
    "di": DI,
    "dm": DM,
    "dn": DN,
    "do": DO,
    "dp": DP,
    "dr": DR,
    "ds": DS,
    "de": DE,
}


def matched_wikidata(field: str) -> bool:
    """Check if the field is a matched Wikidata ID."""
    return re.match(r"^Q\d+", field) is not None


archives = pd.read_csv(os.path.join(BASE_PATH, "archives-csv.csv"))
cities = pd.read_csv(os.path.join(BASE_PATH, "cities-csv.csv"))
compositions = pd.read_csv(os.path.join(BASE_PATH, "compositions-csv.csv"))
countres = pd.read_csv(os.path.join(BASE_PATH, "countries-csv.csv"))
organizations = pd.read_csv(os.path.join(BASE_PATH, "organizations-csv.csv"))
people = pd.read_csv(os.path.join(BASE_PATH, "people-csv.csv"))
regions = pd.read_csv(os.path.join(BASE_PATH, "regions-csv.csv"))
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

    if matched_wikidata(work["name_@id"]):
        # Use the `same as` property to indicate if the archive has been reconciled
        g.add(
            (
                subject_uri,
                DIAMM_SCHEMA["wikidata_id"],
                URIRef(f"{WD}{work['name_@id']}"),
            )
        )
    g.add((subject_uri, DIAMM_SCHEMA["name"], Literal(work["name"])))

    if work["siglum"] is not None:
        g.add(
            (
                subject_uri,
                DIAMM_SCHEMA["siglum"],
                Literal(work["siglum"]),
            )
        )
    if work["website"] is not None:
        g.add(
            (
                subject_uri,
                DIAMM_SCHEMA["website"],
                URIRef(work["website"]),
            )
        )
    if work["rism_id"] is not None:
        g.add(
            (
                subject_uri,
                DIAMM_SCHEMA["rism_id"],
                Literal(work["rism_id"]),
            )
        )

print("Processing cities...")
json_data = json.loads(cities.to_json(orient="records"))
for work in json_data:
    subject_uri = URIRef(f"{DI}{int(work['id'])}")

    if matched_wikidata(work["name_@id"]):
        # Use the `same as` property to indicate if the city has been reconciled
        g.add(
            (
                subject_uri,
                DIAMM_SCHEMA["wikidata_id"],
                URIRef(f"{WD}{work['name_@id']}"),
            )
        )
    g.add((subject_uri, DIAMM_SCHEMA["name"], Literal(work["name"])))

print("Processing compositions...")
json_data = json.loads(compositions.to_json(orient="records"))
for work in json_data:
    if work["id"] is not None:  # If it is none, skip to the genre
        subject_uri = URIRef(f"{DM}{int(work['id'])}")

        g.add((subject_uri, DIAMM_SCHEMA["title"], Literal(work["title"])))

        if work["anonymous"] is True:
            g.add(
                (
                    subject_uri,
                    DIAMM_SCHEMA["composer"],
                    WD["Q4233718"],  # Q-ID for anonymous
                )
            )

    if work["genres"] is not None:
        if matched_wikidata(work["genres_@id"]):
            g.add(
                (
                    subject_uri,
                    DIAMM_SCHEMA["genre"],
                    URIRef(f"{WD}{work['genres_@id']}"),
                )
            )
        else:
            g.add(
                (
                    subject_uri,
                    DIAMM_SCHEMA["genre"],
                    Literal(work["genres"]),
                )
            )

print("Processing countries...")
json_data = json.loads(countres.to_json(orient="records"))
for work in json_data:
    subject_uri = URIRef(f"{DN}{int(work['id'])}")

    if matched_wikidata(work["name_@id"]):
        # Use the `same as` property to indicate if the country has been reconciled
        g.add(
            (
                subject_uri,
                DIAMM_SCHEMA["wikidata_id"],
                URIRef(f"{WD}{work['name_@id']}"),
            )
        )
    g.add((subject_uri, DIAMM_SCHEMA["name"], Literal(work["name"])))

print("Processing organizations...")
json_data = json.loads(organizations.to_json(orient="records"))
for work in json_data:
    if work["id"] is not None:  # If it is none, skip to the type
        subject_uri = URIRef(f"{DO}{int(work['id'])}")

        if matched_wikidata(work["name_@id"]):
            # Use the `same as` property to indicate if the organization has been reconciled
            g.add(
                (
                    subject_uri,
                    DIAMM_SCHEMA["wikidata_id"],
                    URIRef(f"{WD}{work['name_@id']}"),
                )
            )
        g.add((subject_uri, DIAMM_SCHEMA["name"], Literal(work["name"])))

    if work["organization_type"] is not None:
        if matched_wikidata(work["organization_type_@id"]):
            g.add(
                (
                    subject_uri,
                    DIAMM_SCHEMA["type"],
                    URIRef(f"{WD}{work['organization_type_@id']}"),
                )
            )
        else:
            g.add(
                (
                    subject_uri,
                    DIAMM_SCHEMA["type"],
                    Literal(work["organization_type"]),
                )
            )

print("Processing people...")
json_data = json.loads(people.to_json(orient="records"))
for work in json_data:
    subject_uri = URIRef(f"{DP}{int(work['id'])}")

    if matched_wikidata(work["full_name_@id"]):
        # Use the `same as` property to indicate if the person has been reconciled
        g.add(
            (
                subject_uri,
                DIAMM_SCHEMA["wikidata_id"],
                URIRef(f"{WD}{work['full_name_@id']}"),
            )
        )
    g.add(
        (
            subject_uri,
            DIAMM_SCHEMA["name"],
            Literal(work["full_name"]),
        )
    )

    if work["variant_names"] is not None:
        for name in work["variant_names"].split(", "):
            g.add(
                (
                    subject_uri,
                    DIAMM_SCHEMA["variant_names"],
                    Literal(name),
                )
            )

    if work["earliest_year_@id"] is not None:
        g.add(
            (
                subject_uri,
                DIAMM_SCHEMA["earliest_year"],
                URIRef(f"{WD}{work['earliest_year_@id']}"),
            )
        )
    if work["latest_year_@id"] is not None:
        g.add(
            (
                subject_uri,
                DIAMM_SCHEMA["latest_year"],
                URIRef(f"{WD}{work['latest_year_@id']}"),
            )
        )

    if work["rism_id"] is not None:
        g.add(
            (
                subject_uri,
                DIAMM_SCHEMA["rism_id"],
                Literal(work["rism_id"]),
            )
        )
    if work["viaf_id"] is not None:
        g.add(
            (
                subject_uri,
                DIAMM_SCHEMA["viaf_id"],
                Literal(work["viaf_id"]),
            )
        )

print("Processing regions...")
json_data = json.loads(regions.to_json(orient="records"))
for work in json_data:
    subject_uri = URIRef(f"{DR}{int(work['id'])}")

    if matched_wikidata(work["name_@id"]):
        # Use the `same as` property to indicate if the region has been reconciled
        g.add(
            (
                subject_uri,
                DIAMM_SCHEMA["wikidata_id"],
                URIRef(f"{WD}{work['name_@id']}"),
            )
        )
    g.add((subject_uri, DIAMM_SCHEMA["name"], Literal(work["name"])))

print("Processing sets...")
json_data = json.loads(sets.to_json(orient="records"))
for work in json_data:
    subject_uri = URIRef(f"{DE}{int(work['id'])}")

    if matched_wikidata(work["type_@id"]):
        g.add(
            (
                subject_uri,
                DIAMM_SCHEMA["type"],
                URIRef(f"{WD}{work['type_@id']}"),
            )
        )
    else:
        g.add((subject_uri, DIAMM_SCHEMA["type"], Literal(work["type"])))

    g.add(
        (
            subject_uri,
            DIAMM_SCHEMA["cluster_shelfmark"],
            Literal(work["cluster_shelfmark"]),
        )
    )

print("Processing sources...")
json_data = json.loads(sources.to_json(orient="records"))
for work in json_data:
    subject_uri = URIRef(f"{DS}{int(work['id'])}")

    g.add(
        (
            subject_uri,
            DIAMM_SCHEMA["display_name"],
            Literal(work["display_name"]),
        )
    )
    g.add(
        (
            subject_uri,
            DIAMM_SCHEMA["shelfmark"],
            Literal(work["shelfmark"]),
        )
    )

    if work["source_type"] is not None:
        if matched_wikidata(work["source_type_@id"]):
            g.add(
                (
                    subject_uri,
                    DIAMM_SCHEMA["type"],
                    URIRef(f"{WD}{work['source_type_@id']}"),
                )
            )
        else:
            g.add(
                (
                    subject_uri,
                    DIAMM_SCHEMA["type"],
                    Literal(work["source_type"]),
                )
            )

print("Processing relations...")
json_data = json.loads(relations.to_json(orient="records"))
for work in json_data:
    first_type, first_id = work["key1"].split(":")
    second_type, second_id = work["key2"].split(":")
    first_id, second_id = int(first_id), int(second_id)
    first_uri = pred_uri = second_uri = None
    reverse = False

    if first_type == "archive":
        first_uri = URIRef(f"{DA}{first_id}")
        if second_type == "city":
            second_uri = URIRef(f"{DI}{second_id}")
            pred_uri = DIAMM_SCHEMA["city"]
        elif second_type == "set":
            second_uri = URIRef(f"{DE}{second_id}")
            pred_uri = DIAMM_SCHEMA["holding_archive"]
            reverse = True
        elif second_type == "source":
            second_uri = URIRef(f"{DS}{second_id}")
            pred_uri = DIAMM_SCHEMA["holding_archive"]
            reverse = True
    elif first_type == "city":
        if second_type == "country":
            second_uri = URIRef(f"{DN}{second_id}")
            pred_uri = DIAMM_SCHEMA["country"]
        elif second_type == "organization":
            second_uri = URIRef(f"{DO}{second_id}")
            pred_uri = DIAMM_SCHEMA["city"]
            reverse = True
        elif second_type == "region":
            second_uri = URIRef(f"{DR}{second_id}")
            pred_uri = DIAMM_SCHEMA["region"]
        elif second_type == "source":
            second_uri = URIRef(f"{DS}{second_id}")
            pred_uri = DIAMM_SCHEMA["location"]
            reverse = True
    elif first_type == "composition":
        first_uri = URIRef(f"{DM}{first_id}")
        if second_type == "people":
            second_uri = URIRef(f"{DP}{second_id}")
            pred_uri = DIAMM_SCHEMA["composer"]
        elif second_type == "source":
            second_uri = URIRef(f"{DS}{second_id}")
            pred_uri = DIAMM_SCHEMA["composition_in_source"]
    elif first_type == "country":
        if second_type == "organization":
            second_uri = URIRef(f"{DO}{second_id}")
            pred_uri = DIAMM_SCHEMA["country"]
            reverse = True
        elif second_type == "region":
            second_uri = URIRef(f"{DR}{second_id}")
            pred_uri = DIAMM_SCHEMA["country"]
            reverse = True
    elif first_type == "organization":
        first_uri = URIRef(f"{DO}{first_id}")
        if second_type == "region":
            second_uri = URIRef(f"{DR}{second_id}")
            pred_uri = DIAMM_SCHEMA["region"]
        elif second_type == "source":
            second_uri = URIRef(f"{DS}{second_id}")
            reverse = True
            if work["type"] == "related":
                pred_uri = DIAMM_SCHEMA["related_organization"]
            elif work["type"] == "copied":
                pred_uri = DIAMM_SCHEMA["copied_organization"]
            elif work["type"] == "provenance":
                pred_uri = DIAMM_SCHEMA["provenance_organization"]
    elif first_type == "people":
        first_uri = URIRef(f"{DP}{first_id}")
        if second_type == "source":
            second_uri = URIRef(f"{DS}{second_id}")
            reverse = True
            if work["type"] == "related":
                pred_uri = DIAMM_SCHEMA["related_people"]
            elif work["type"] == "copied":
                pred_uri = DIAMM_SCHEMA["copied_people"]
    elif first_type == "region":
        if second_type == "source":
            second_uri = URIRef(f"{DS}{second_id}")
            pred_uri = DIAMM_SCHEMA["location"]
            reverse = True
    elif first_type == "set":
        first_uri = URIRef(f"{DE}{first_id}")
        if second_type == "source":
            second_uri = URIRef(f"{DS}{second_id}")
            pred_uri = DIAMM_SCHEMA["set_in_source"]

    if first_uri and pred_uri and second_uri:
        if reverse:
            g.add((second_uri, pred_uri, first_uri))
        else:
            g.add((first_uri, pred_uri, second_uri))

# Serialize the graph to RDF format
print("Serializing the graph...")
g.serialize(
    destination=os.path.join(OUTPUT_PATH, "diamm.ttl"),
    format="turtle",
    encoding="utf-8",
)
