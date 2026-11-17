"""
Converts all the DIAMM reconciled CSV files to RDF (turtle) format.

The script will also load a relations mapping file to handle the relationships
between organizations/people and sources.
"""

import hashlib
import json
import re
import os
import pandas as pd
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import DCTERMS, RDFS, RDF, SKOS, XSD
from external_identifiers import identifier_values

BASE_PATH = "../data/reconciled/"
RELATIONS_PATH = "../data/csv/relations.csv"
RELATIONS_MAPPING_PATH = "./relations.json"
OUTPUT_PATH = "../data/RDF/"

WDT = Namespace("http://www.wikidata.org/prop/direct/")
WD = Namespace("http://www.wikidata.org/entity/")
LMDIAMM = Namespace("https://linkedmusic.ca/graphs/diamm/")
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
    "variant_names": SKOS.altLabel,
    "earliest_year": WDT["P569"],
    "latest_year": WDT["P570"],
    "viaf_id": WDT["P214"],
    "shelfmark": RDFS.label,
    "cluster_shelfmark": WDT["P217"],
    "holding_archive": WDT["P276"],
    "composition_in_source": WDT["P361"],
    "copied_organization": WDT["P1071"],
    "provenance_organization": WDT["P276"],
    "copied_people": WDT["P11603"],
    "set_in_source": WDT["P361"],
    "display_name": RDFS.label,
}

namespaces = {
    "wdt": WDT,
    "wd": WD,
    "diamm": LMDIAMM,
    "da": DA,
    "di": DI,
    "dm": DM,
    "dn": DN,
    "do": DO,
    "dp": DP,
    "dr": DR,
    "ds": DS,
    "de": DE,
    "dcterms": DCTERMS,
    "xsd": XSD,
}

PERSON_YEAR_FIELDS = ("earliest_year", "latest_year")
PERSON_SOURCE_TEXT = {
    "source_full_name": LMDIAMM.sourceFullName,
    "floruit": LMDIAMM.floruit,
}


def matched_wikidata(field: str) -> bool:
    """Accept only complete bare item IDs from reconciled entity-ID columns."""
    return isinstance(field, str) and re.fullmatch(r"Q[1-9][0-9]*", field) is not None


def add_person_year(graph, person, row, field):
    """Keep each exported year/ID/approximation together; see doc/person_years.md."""
    raw_year = row.get(field) or ""
    raw_identifier = row.get(f"{field}_@id") or ""
    raw_approximate = row.get(f"{field}_approximate") or ""
    if not any((raw_year, raw_identifier, raw_approximate)):
        return

    # Include all evidence in the identity: duplicate rows collapse, while
    # conflicting rows cannot combine one row's year with another's qualifier.
    identity = json.dumps(
        [str(person), field, raw_year, raw_identifier, raw_approximate],
        ensure_ascii=False,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()
    observation = LMDIAMM[f"person-year/{digest}"]
    graph.add((person, LMDIAMM.personYear, observation))
    graph.add((observation, RDF.type, LMDIAMM.PersonYearObservation))
    graph.add((observation, DCTERMS.source, person))
    graph.add((observation, LMDIAMM.dateProperty, DIAMM_SCHEMA[field]))
    for predicate, value in (
        (LMDIAMM.sourceField, field),
        (LMDIAMM.sourceValue, raw_year),
        (LMDIAMM.sourceIdentifier, raw_identifier),
        (LMDIAMM.sourceApproximate, raw_approximate),
    ):
        graph.add((observation, predicate, Literal(value, datatype=XSD.string)))

    year = None
    match = re.fullmatch(r"([0-9]{1,4})(?:\.0+)?", raw_year)
    if match and 1 <= int(match[1]) <= 9999:
        year = Literal(f"{int(match[1]):04d}", datatype=XSD.gYear, normalize=False)
        graph.add((observation, LMDIAMM.year, year))
    else:
        graph.add(
            (
                observation,
                LMDIAMM.validationFlag,
                Literal("invalid-year" if raw_year else "missing-year"),
            )
        )

    approximate = {"true": True, "1": True, "false": False, "0": False}.get(
        raw_approximate.lower()
    )
    if approximate is not None:
        graph.add((observation, LMDIAMM.approximate, Literal(approximate)))
    else:
        graph.add(
            (
                observation,
                LMDIAMM.validationFlag,
                Literal(
                    "invalid-approximation"
                    if raw_approximate
                    else "missing-approximation"
                ),
            )
        )

    if matched_wikidata(raw_identifier):
        graph.add((observation, LMDIAMM.reconciledYear, WD[raw_identifier]))
    elif raw_identifier:
        graph.add(
            (observation, LMDIAMM.validationFlag, Literal("invalid-year-identifier"))
        )

    # Never turn approximate or unqualified evidence into an exact date, nor
    # infer a calendar year from a reconciled entity ID.
    if year is not None and approximate is False:
        graph.add((person, DIAMM_SCHEMA[field], year))


def add_external_identifiers(graph, subject, row, fields):
    """Project the complete source list, falling back only for legacy CSV cells."""
    evidence = row.get("source_identifiers")
    if evidence:
        try:
            values = identifier_values(json.loads(evidence), fields)
        except (ValueError, TypeError) as error:
            raise ValueError(
                f"Invalid source_identifiers for {subject}: {error}"
            ) from error
        graph.add(
            (
                subject,
                LMDIAMM.sourceIdentifiersJson,
                Literal(evidence, datatype=XSD.string),
            )
        )
    else:
        values = {field: {row[field]} if row.get(field) else set() for field in fields}
    for field, identifiers in values.items():
        for identifier in identifiers:
            graph.add((subject, DIAMM_SCHEMA[field], Literal(identifier)))


def build_rdf_graph(
    base_path=BASE_PATH,
    relations_path=RELATIONS_PATH,
    relations_mapping_path=RELATIONS_MAPPING_PATH,
):
    """Convert supplied CSV paths without writing output or reading on import."""
    with open(relations_mapping_path, "r", encoding="utf-8") as file:
        relations_mapping = json.load(file)

    archives = pd.read_csv(
        os.path.join(base_path, "archives-csv.csv"),
        # Names, sigla and external identifiers are source text, including
        # leading zeros and NA-like strings. See doc/archive_text.md and
        # doc/external_identifier_text.md. Other columns retain their loading.
        converters={
            field: str for field in ("name", "siglum", "rism_id", "source_identifiers")
        },
    )
    cities = pd.read_csv(os.path.join(base_path, "cities-csv.csv"))
    compositions = pd.read_csv(os.path.join(base_path, "compositions-csv.csv"))
    countres = pd.read_csv(os.path.join(base_path, "countries-csv.csv"))
    organizations = pd.read_csv(os.path.join(base_path, "organizations-csv.csv"))
    people = pd.read_csv(
        os.path.join(base_path, "people-csv.csv"),
        # Preserve year evidence, person names and external identifier text.
        # Other columns retain their old loading.
        converters={
            **{
                field: str
                for field in (
                    "full_name",
                    *PERSON_SOURCE_TEXT,
                    "rism_id",
                    "viaf_id",
                    "source_identifiers",
                )
            },
            **{
                column: str
                for field in PERSON_YEAR_FIELDS
                for column in (field, f"{field}_@id", f"{field}_approximate")
            },
        },
    )
    regions = pd.read_csv(os.path.join(base_path, "regions-csv.csv"))
    sets = pd.read_csv(os.path.join(base_path, "sets-csv.csv"))
    sources = pd.read_csv(os.path.join(base_path, "sources-csv.csv"))

    relations = pd.read_csv(relations_path)

    g = Graph()

    # Bind namespaces
    for prefix, ns in namespaces.items():
        g.bind(prefix, ns)

    print("Processing archives...")
    json_data = json.loads(archives.to_json(orient="records"))
    for work in json_data:
        subject_uri = URIRef(f"{DA}{int(work['id'])}")

        # Add the entity type
        g.add(
            (
                subject_uri,
                RDF.type,
                LMDIAMM["Archive"],
            )
        )

        if matched_wikidata(work["name_@id"]):
            # Use the `same as` property to indicate if the archive has been reconciled
            g.add(
                (
                    subject_uri,
                    DIAMM_SCHEMA["wikidata_id"],
                    URIRef(f"{WD}{work['name_@id']}"),
                )
            )
        if work["name"]:
            g.add((subject_uri, DIAMM_SCHEMA["name"], Literal(work["name"])))

        if work["siglum"]:
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
        add_external_identifiers(g, subject_uri, work, ("rism_id",))

    print("Processing cities...")
    json_data = json.loads(cities.to_json(orient="records"))
    for work in json_data:
        subject_uri = URIRef(f"{DI}{int(work['id'])}")

        # Add the entity type
        g.add(
            (
                subject_uri,
                RDF.type,
                LMDIAMM["City"],
            )
        )

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

            # Add the entity type
            g.add(
                (
                    subject_uri,
                    RDF.type,
                    LMDIAMM["Composition"],
                )
            )

            g.add((subject_uri, DIAMM_SCHEMA["name"], Literal(work["title"])))

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

        # Add the entity type
        g.add(
            (
                subject_uri,
                RDF.type,
                LMDIAMM["Country"],
            )
        )

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

            # Add the entity type
            g.add(
                (
                    subject_uri,
                    RDF.type,
                    LMDIAMM["Organization"],
                )
            )

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

        # Add the entity type
        g.add(
            (
                subject_uri,
                RDF.type,
                LMDIAMM["Person"],
            )
        )

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

        for field, predicate in PERSON_SOURCE_TEXT.items():
            # Legacy exports lack these optional columns. Never reconstruct the
            # original display name or activity dates from a cleaned label.
            value = work.get(field)
            if isinstance(value, str) and value != "":
                g.add((subject_uri, predicate, Literal(value, datatype=XSD.string)))

        if work["variant_names"] is not None:
            for name in work["variant_names"].split(", "):
                g.add(
                    (
                        subject_uri,
                        DIAMM_SCHEMA["variant_names"],
                        Literal(name),
                    )
                )

        for field in PERSON_YEAR_FIELDS:
            add_person_year(g, subject_uri, work, field)

        add_external_identifiers(g, subject_uri, work, ("rism_id", "viaf_id"))

    print("Processing regions...")
    json_data = json.loads(regions.to_json(orient="records"))
    for work in json_data:
        subject_uri = URIRef(f"{DR}{int(work['id'])}")

        # Add the entity type
        g.add(
            (
                subject_uri,
                RDF.type,
                LMDIAMM["Region"],
            )
        )

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

        # Add the entity type
        g.add(
            (
                subject_uri,
                RDF.type,
                LMDIAMM["Set"],
            )
        )

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

        # Add the entity type
        g.add(
            (
                subject_uri,
                RDF.type,
                LMDIAMM["Source"],
            )
        )

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
            elif second_type == "source":
                second_uri = URIRef(f"{DS}{second_id}")
                pred_uri = DIAMM_SCHEMA["holding_archive"]
                reverse = True
        elif first_type == "city":
            first_uri = URIRef(f"{DI}{first_id}")
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
                pred_uri = DIAMM_SCHEMA["city"]
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
            first_uri = URIRef(f"{DN}{first_id}")
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
            if second_type == "source":
                second_uri = URIRef(f"{DS}{second_id}")
                reverse = True
                if work["type"] == "copied":
                    pred_uri = DIAMM_SCHEMA["copied_organization"]
                elif work["type"] == "provenance":
                    pred_uri = DIAMM_SCHEMA["provenance_organization"]
                elif work["type"].startswith("related:"):
                    if pred_map := relations_mapping["organizations"].get(
                        work["type"].split(":")[1]
                    ):
                        if pred_map.startswith("r"):
                            reverse = False
                            pred_map = pred_map[1:]  # Remove 'r' prefix
                        pred_uri = WDT[pred_map]
        elif first_type == "people":
            first_uri = URIRef(f"{DP}{first_id}")
            if second_type == "source":
                second_uri = URIRef(f"{DS}{second_id}")
                reverse = True
                if work["type"] == "copied":
                    pred_uri = DIAMM_SCHEMA["copied_people"]
                elif work["type"].startswith("related"):
                    if pred_map := relations_mapping["people"].get(
                        work["type"].split(":")[1]
                    ):
                        if pred_map.startswith("r"):
                            reverse = False
                            pred_map = pred_map[1:]  # Remove 'r' prefix
                        pred_uri = WDT[pred_map]
        elif first_type == "set":
            first_uri = URIRef(f"{DE}{first_id}")
            if second_type == "source":
                second_uri = URIRef(f"{DS}{second_id}")
                pred_uri = DIAMM_SCHEMA["set_in_source"]
                reverse = True

        if first_uri and pred_uri and second_uri:
            if reverse:
                g.add((second_uri, pred_uri, first_uri))
            else:
                g.add((first_uri, pred_uri, second_uri))

    return g


def main():
    graph = build_rdf_graph()
    os.makedirs(OUTPUT_PATH, exist_ok=True)
    print("Serializing the graph...")
    graph.serialize(
        destination=os.path.join(OUTPUT_PATH, "diamm.ttl"),
        format="turtle",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
