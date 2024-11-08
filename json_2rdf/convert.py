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
from rdflib import Graph, URIRef, Literal, Namespace, BNode
from rdflib.namespace import RDF, XSD, GEO

# Load JSON data
with open("input.json", encoding="utf-8") as f:
    data = json.load(f)

# Initialize the RDF graph
g = Graph()

# Define a namespace
EX = Namespace("http://example.org/")
g.bind("ex", EX)

# Define the main subject based on the "id" field
main_subject = URIRef(data["id"])


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
        pred_uri = URIRef(EX[predicate])  # Define the predicate URI

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
                g.add((subject, pred_uri, list_node))
                if isinstance(item, dict):
                    add_triples(list_node, item)
                else:
                    # If the item is not a dictionary, treat it as a literal or URI
                    g.add(
                        (
                            list_node,
                            RDF.value,
                            (
                                Literal(item)
                                if not str(item).startswith("http")
                                else URIRef(item)
                            ),
                        )
                    )
            continue
        else:
            # Otherwise, treat it as a literal
            obj = Literal(item) if not str(item).startswith("http") else URIRef(item)

        # Add the triple
        g.add((subject, pred_uri, obj))


# Add triples for main subject
add_triples(main_subject, {k: v for k, v in data.items() if k != "id"})

# Serialize the graph to a Turtle (.ttl) file
g.serialize("output.ttl", format="turtle")

print("RDF data successfully saved in Turtle format.")
