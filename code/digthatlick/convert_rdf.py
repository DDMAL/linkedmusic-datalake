"""
Converts all the Dig That Lick reconciled CSV files to RDF (turtle) format.
Run this sript from its own directory.
"""

from typing import Union
import re
import os
import pandas as pd
from rdflib import Graph, URIRef, Literal, Namespace

SOLOS_CSV = "../../data/digthatlick/reconciled/dtl1000_solos.csv"
TRACKS_CSV = "../../data/digthatlick/reconciled/dtl1000_tracks.csv"
PERFORMERS_CSV = "../../data/digthatlick/reconciled/dtl1000_performers.csv"

OUTPUT_PATH = "../../data/digthatlick/RDF/"

WDT = Namespace("http://www.wikidata.org/prop/direct/")
WD = Namespace("http://www.wikidata.org/entity/")
RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
# http://www.DTL.org/JE/ is the official namespace used in DDL1000.ttl, which is hosted at https://osf.io/bwg42/files/osfstorage.
# Dig That Lick does not own the domain.
DTLS = Namespace("http://www.DTL.org/JE/solo_performances/")
DTLT = Namespace("http://www.DTL.org/JE/tracks/")

# These prefixes are used as shorthand in the Turtle file
namespace_prefixes = {
    "wdt": WDT,
    "wd": WD,
    "rdfs": RDFS,
    "dtls": DTLS,
    "dtlt": DTLT,
}


# The key is the column name in the CSV file; the value is the equivalent Wikidata property ID.
# This schema is for solos.csv
DTL_SOLOS_SCHEMA = {
    # We will not add qualifiers to distinguish between possible and confirmed solo performers
    "possible_solo_performer_names": "P175",  
    "solo_performer_name": "P175",
    "instrument_label": "P870",
    "track_id": "P361",
}

# This schema is for tracks.csv
DTL_TRACKS_SCHEMA = {
    "track_title": "rdfs:label",
    "band_name": "P175",
    "session_date": "P10135",
    "area": "P8546",
}

# This schema is also for tracks.csv
# It maps the special relation between:
# - disk_title (album),
# - medium_title (part of the album)
# - track_title (tracks on the album)
DTL_ALBUMS_SCHEMA = {
    "part of": "P361",  # the predicate between medium_title and disk_title
    "tracklist": "P658",  # the predicate between track_title and medium_title
}

# The primary key in the performers.csv is track_id
# This csv was split from tracks.csv because it contains many performers per track
DTL_PERFORMERS_SCHEMA = {
    "performer_names": "P175",
}


def matched_wikidata(field: str) -> bool:
    """Check if the field is a matched Wikidata URI."""
    return re.match(r"Q\d+", field) is not None


def to_rdf_node(
    val: str,
    namespace: Namespace = WD
) -> Union[None,URIRef, Literal]:  # Unreconciled values will be returned as RDF Literal
    """Convert a value to an RDF node (URIRef or Literal) to allow usage within RDF triple"""
    if pd.isna(val):
        return None
    if namespace != WD:
        # DTL1000 ids need the prefix prepended
        return URIRef(f"{namespace}{val}")
    if matched_wikidata(val):
        # If the value is a Wikidata ID, return it as a URIRef
        return URIRef(f"{namespace}{val}")
    else:
        return Literal(str(val))


os.makedirs(OUTPUT_PATH, exist_ok=True)
print("Output directory created or already exists:", os.path.abspath(OUTPUT_PATH))

if not os.path.exists(SOLOS_CSV):
    raise FileNotFoundError(f"The file {SOLOS_CSV} does not exist.")
if not os.path.exists(TRACKS_CSV):
    raise FileNotFoundError(f"The file {TRACKS_CSV} does not exist.")
if not os.path.exists(PERFORMERS_CSV):
    raise FileNotFoundError(f"The file {PERFORMERS_CSV} does not exist.")

solos = pd.read_csv(SOLOS_CSV)
tracks = pd.read_csv(TRACKS_CSV)
performers = pd.read_csv(PERFORMERS_CSV)

# Intialize RDF graph
g = Graph()
for prefix, ns in namespace_prefixes.items():
    g.bind(prefix, ns)


print("Processing dtl1000_solos.csv...")
dict_data = solos.to_dict(
    orient="records"
)  # this converts the DataFrame to a list of dictionaries
try:
    for row in dict_data:
        subject_node = to_rdf_node(
            row["solo_id"], namespace=DTLS
        )  # solos_id is the only column using DTLS namespace
        if subject_node is None:
            continue
        for column, wikidata_property in DTL_SOLOS_SCHEMA.items():
            predicate = URIRef(f"{WDT}{wikidata_property}")
            if column == "track_id":
                # For track_id, we use the DTLT namespace
                object_node = to_rdf_node(row[column], namespace=DTLT)
            else:
                object_node = to_rdf_node(row[column])

            if object_node is None:
                continue
            g.add((subject_node, predicate, object_node))

except KeyError as e:
    print(f"KeyError: The column '{e.args[0]}' is missing from the input CSV file.")
    exit(1)

print("Processing dtl1000_tracks.csv...")
dict_data = tracks.to_dict(
    orient="records"
)  # this converts the DataFrame to a list of dictionaries
try:
    for row in dict_data:
        subject_node = to_rdf_node(
            row["track_id"], namespace=DTLT
        )  # track_id is the only column using DTLT namespace
        if subject_node is None:
            continue
        for column, wikidata_property in DTL_TRACKS_SCHEMA.items():
            if column == "track_title":
                predicate = RDFS.label  # Use rdfs:label for track titles
            else:
                predicate = URIRef(f"{WDT}{wikidata_property}")
            object_node = to_rdf_node(row[column])

            if object_node is None:
                continue
            g.add((subject_node, predicate, object_node))

except KeyError as e:
    print(f"KeyError: The column '{e.args[0]}' is missing from the input CSV file.")
    exit(1)


print("Mapping track and albums relation from dtl1000_tracks.csv...")
try:
    for row in dict_data:
        track_id = to_rdf_node(row["track_id"], namespace=DTLT)
        medium_title = to_rdf_node(row["medium_title"])
        disc_title = to_rdf_node(row["disk_title"])

        if medium_title is not None and disc_title is not None:
            # Add the "part of" relation between medium_title and disk_title
            predicate = URIRef(f"{WDT}{DTL_ALBUMS_SCHEMA['part of']}")
            g.add((medium_title, predicate, disc_title))

        if track_id is not None and medium_title is not None:
            # Add the "tracklist" relation between medium_title and track_title
            predicate = URIRef(f"{WDT}{DTL_ALBUMS_SCHEMA['tracklist']}")
            g.add((medium_title, predicate, track_id))


except KeyError as e:
    print(f"KeyError: The column '{e.args[0]}' is missing from the input CSV file.")
    exit(1)

print("Processing dtl1000_performers.csv...")
dict_data = performers.to_dict(
    orient="records"
)  # this converts the DataFrame to a list of dictionaries
try:
    for row in dict_data:
        subject_node = to_rdf_node(
            row["track_id"], namespace=DTLT
        )  # track_id is the only column using DTLT namespace
        if subject_node is None:
            continue
        for column, wikidata_property in DTL_PERFORMERS_SCHEMA.items():
            predicate = URIRef(f"{WDT}{wikidata_property}")
            object_node = to_rdf_node(row[column])

            if object_node is None:
                continue
            g.add((subject_node, predicate, object_node))

except KeyError as e:
    print(f"KeyError: The column '{e.args[0]}' is missing from the input CSV file.")
    exit(1)

# Serialize the graph to RDF format
print("Serializing RDF graph to Turtle format...")
g.serialize(destination=os.path.join(OUTPUT_PATH, "dtl1000.ttl"), format="turtle")
print(
    "RDF conversion completed. The serialized output is saved to:",
    os.path.join(os.path.abspath(OUTPUT_PATH), "dtl1000.ttl"),
)
