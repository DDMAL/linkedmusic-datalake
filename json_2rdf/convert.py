"""
This module reads a JSON file and converts it into an RDF graph in Turtle (.ttl) format
using the rdflib library. It processes complex JSON structures with nested dictionaries 
and lists, creating corresponding RDF triples.

The JSON structure should include:
    - A unique ID field, which serves as the main subject URI.
    - Key-value pairs where keys are predicates and values are objects.
    - Nested dictionaries or lists as values, which are recursively processed into 
      RDF blank nodes or additional subjects.

Usage:
    - Place a JSON file in the same directory and name it "input.json".
    - Run this script to generate an "output.ttl" file with RDF triples.

Dependencies:
    - rdflib: Required to create and manipulate the RDF graph.

Example JSON input:
{
    "id": "http://example/id.org",
    "pred1": "example literal obj 1",
    "pred2": {
        "pred2_1": "example literal obj 2_1",
        "pred2_2": "http://example/obj2.org"
    },
    "pred3": [
        {"nested_pred1": "nested_value1"},
        {"nested_pred2": "http://example/nested_value2.org"}
    ]
}
"""

import json
from datetime import datetime
from rdflib import Graph, URIRef, Literal, Namespace, BNode
from rdflib.namespace import RDF, XSD, GEO


# Initialize the RDF graph
g = Graph()

# Define a namespace
with open("namespace_mapping.json", "r", encoding="utf-8") as ns_mp:
    NS = json.load(ns_mp)

with open("./musicbrainz/pred_mapping.json", "r", encoding="utf-8") as pd_mp:
    PD = json.load(pd_mp)

NUM_COLUMN = []
LOC_COLUMN = []
DATE_COLUMN = []
IGNORE_COLUMN = [
    "annotation",
    "ended",
    "video",
    "isrcs",
    "aliases",
    # "tags",
    "rating",
]


# Function to add triples to the graph
def add_triples(subject, predicates):
    """
    Recursively adds RDF triples to the graph from a dictionary of predicates
    and objects. Handles nested dictionaries as blank nodes and lists as sequences
    of blank nodes, allowing for complex JSON structures to be represented in RDF.

    Parameters:
    subject (URIRef or BNode): The RDF subject node to which triples are added.
    predicates (dict): A dictionary where each key is a predicate and each value
                       can be a literal, URI, dictionary, or list:
                       - Literal values are added directly as RDF literals.
                       - URI strings (starting with 'http') are converted to URIRefs.
                       - Nested dictionaries are treated as blank nodes and recursively processed.
                       - Lists create a blank node for each item; nested dictionaries in lists are
                         recursively processed as additional RDF triples.

    Returns:
    None. Modifies the global RDF graph by adding triples based on the predicates dictionary.
    """

    for predicate, obj in predicates.items():

        if predicate in IGNORE_COLUMN:
            continue

        if obj == "" or obj is None:
            continue

        # Define the predicate URI
        namespace_string = NS[list(PD[predicate].keys())[0]]
        namespace = Namespace(namespace_string)
        g.bind(list(PD[predicate].keys())[0], namespace=namespace)
        value = list(PD[predicate].values())[0]
        pred_uri = URIRef(namespace[value])

        if isinstance(obj, str) and obj.startswith("http"):
            # If the object is a URI (starts with http), treat it as URIRef
            obj = URIRef(obj)
        elif isinstance(obj, dict):
            # For nested dictionaries, create a new blank node or subject
            nested_subject = BNode()  # Use a blank node for anonymous nodes
            g.add((subject, pred_uri, nested_subject))
            add_triples(nested_subject, obj)  # Recursively add nested triples
            continue
        elif isinstance(obj, list):
            # Handle lists by creating a blank node for each item in the list
            for item in obj:
                list_node = BNode()
                if isinstance(item, dict):
                    g.add((subject, pred_uri, list_node))
                    add_triples(list_node, item)
                else:
                    # If the item is not a dictionary, treat it as a literal or URI
                    g.add(
                        (
                            list_node,
                            pred_uri,
                            (
                                Literal(item)
                                if not str(item).startswith("http")
                                else URIRef(item)
                            ),
                        )
                    )
            continue
        else:
            # # Otherwise, treat it as a literal
            # if obj == "True" or obj == "False":
            #     obj = Literal(obj, datatype=XSD.boolean)
            # elif pred_uri in NUM_COLUMN:
            #     obj = Literal(obj, datatype=XSD.integer)
            # elif pred_uri in LOC_COLUMN:
            #     obj = Literal(obj.upper(), datatype=GEO.wktLiteral)
            # elif pred_uri in DATE_COLUMN:
            #     datetime_obj = datetime.strptime(obj, "%Y-%m-%d %H:%M:%S")

            #     day_of_week = datetime_obj.strftime("%A")
            #     day_of_week_obj = Literal(day_of_week)
            #     g.add(
            #         (
            #             subject,
            #             URIRef("http://www.wikidata.org/prop/direct/P2894"),
            #             day_of_week_obj,
            #         )
            #     )

            #     day_str = datetime_obj.strftime("%Y-%m-%dT%H:%M:%S")
            #     obj = Literal(day_str, datatype=XSD.dateTime)
            # else:
            obj = Literal(obj)

        # Add the triple
        g.add((subject, pred_uri, obj))


with open("./musicbrainz/recording_test", "r", encoding="utf-8") as f:
    for line in f:
        data = json.loads(line)  # Parse each JSON object in the file

        # Define the main subject based on the "id" field
        main_subject = URIRef(data["id"])

        # Add triples for each JSON object, excluding the "id" field
        add_triples(main_subject, {k: v for k, v in data.items() if k != "id"})


# Serialize the graph to a Turtle (.ttl) file
g.serialize("output.ttl", format="turtle")

print("RDF data successfully saved in Turtle format.")
