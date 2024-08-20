"""
Run this file in the command line to convert csv files containing
reconciled data to turtle files.
The script takes an arbitrary number of positional arguments.
The first argument is a relative path from the directory containing this file to a relation 
mapping file for the data in the csvs. The relations mapping file is a json file where the
keys are headers in the csv file and the values are URIs to Wikidata/Schema.org properties.
The following arguments are relative paths from the directory containing this file to 
reconciled csv files to be converted.
The script creates a file containing the turtle in the directory containing this
file called 'out_rdf.ttl'.
"""

import csv
from typing import List
import sys
import json
import os
import validators
import re
from rdflib import Graph, URIRef, Literal
from rdflib.namespace import RDF, XSD, WGS

# The "type" attribute of each CSV file must be entered in the mapper file in the
# same order as the input in commandline.

DIRNAME = os.path.dirname(__file__)
mapping_filename = os.path.join(DIRNAME, sys.argv[1])
dest_filename = os.path.join(os.path.dirname(mapping_filename), "out_rdf.ttl")
DT_PATTERN = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$'


def convert_csv_to_turtle(filenames: List[str]) -> Graph:
    """
    (List[str]) -> Graph

    Adds all informations as RDF triples from the input filenames into a graph and return it.
    *Important: Each input file must have the first column as subjects of all triples

    @Pre: type(filenames) == List[str]
    """
    g = Graph()

    ontology_dict = json.load(open(mapping_filename, "r", encoding="utf-8"))
    type_dict = ontology_dict.get("entity_type")

    for filename in filenames:
        # If we use the get_relations.py to generate a mapping file, then
        # the ontology_list is guaranteed to have a value.
        try:
            ontology_type = type_dict[filename.rsplit("/", -1)[-1]]
        except IndexError:
            ontology_type = None

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
                        element = element.replace(
                            "https://www.wikidata.org/wiki/",
                            "http://www.wikidata.org/entity/",
                        )
                        obj = URIRef(element)
                    else:
                        if element == "True" or element == "False":
                            obj = Literal(element, datatype=XSD.boolean)
                        elif element.isnumeric():
                            obj = Literal(element, datatype=XSD.integer)
                        elif element.startswith("Point("):
                            obj = Literal(element[5:], datatype=WGS.Point)
                        elif re.match(DT_PATTERN, element):
                            obj = Literal(element, datatype=XSD.dateTime)
                        else:
                            obj = Literal(element)

                    g.add((key_attribute, predicates[i], obj))

    return g


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise ValueError("Invalid number of input filenames")

    fns = sys.argv[2:]
    turtle_data = convert_csv_to_turtle(fns)
    turtle_data.serialize(format="turtle", destination=dest_filename,)
