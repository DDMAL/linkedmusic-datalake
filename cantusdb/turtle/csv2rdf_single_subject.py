import csv
import validators
import sys
import json
import os
from rdflib import Graph, URIRef, Literal
from rdflib.namespace import RDF
from typing import Optional, List

DIRNAME = os.path.dirname(__file__)
mapping_filename = os.path.join(DIRNAME, 'relations_mapping_mb.json')
dest_filename = os.path.join(DIRNAME, 'out_rdf.ttl')

def convert_csv_to_turtle(filenames: List[str]) -> Graph:
    """
    (List[str]) -> Graph

    Adds all informations as RDF triples from the input filenames into a graph and return it.
    *Important: Each input file must have the first column as subjects of all triples
    
    @Pre: type(filenames) == List[str]
    """
    g = Graph()

    ontology_dict = json.load(open(mapping_filename, "r"))
    try:
        ontology_list : Optional[list] = ontology_dict["type"]
    except KeyError:
        ontology_list = None

    for i, filename in enumerate(filenames):
        ontology_type = ontology_list[i]
        with open(filename, "r", encoding="utf-8") as csv_file:
            csv_reader = csv.reader(csv_file)

            header = next(csv_reader)
            header_without_subject = header[1:]
            predicates = []
            for column in header_without_subject:
                if column in ontology_dict:
                    predicates.append(URIRef(ontology_dict[column]))

            # Convert each row to Turtle format and add it to the output
            for row in csv_reader:
                # the first column as the subject
                key_attribute = URIRef(row[0])
                if ontology_type:
                    g.add((key_attribute, RDF.type, URIRef(ontology_type)))

                # extracting other informations
                for i, element in enumerate(row[1:]):
                    if element == "":
                        continue

                    # the object might be an URI or a literal
                    if validators.url(element):
                        obj = URIRef(element)
                    else:
                        obj = Literal(element)

                    g.add((key_attribute, predicates[i], obj))

    return g

# Run this file in the command line.
# Args = the input reconciled csv files using openrefine
# Convert the CSV data to Turtle format
# out_rdf.ttl can be safely imported into Virtuoso.
if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise ValueError("Invalid number of input filenames")

    filenames = sys.argv[1:]
    turtle_data = convert_csv_to_turtle(filenames)
    turtle_data.serialize(format="turtle", destination=dest_filename)
