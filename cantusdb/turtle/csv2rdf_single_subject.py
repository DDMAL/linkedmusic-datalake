import csv
import validators
import sys
import json

# a main operation function
def convert_csv_to_turtle(filename) -> Graph:
    """
    Adds all informations as RDF triples from the input filename into a graph and return it.
    @Pre: input filename must be type string.
    @Post: Returns a RDF.Graph that has all the triples
    """
    
    if len(sys.argv) != 2:
        raise ValueError("Invalid number of input filename")
    
    with open(filename, "r", encoding="utf-8") as csv_file:
        # TODO: maybe change this one to accomadate for multiple files

        g = Graph()

        csv_reader = csv.reader(csv_file)
        with open("relations_mapping.json", "r") as mapper:
            ontology_dict = json.load(mapper)
        
        header = next(csv_reader)

        # Convert each row to Turtle format and add it to the output
        for row in csv_reader:
            # the first column as the subject
            key_attribute = URIRef(row[0])
            if "type" in list(ontology_dict.keys()):
                g.add((key_attribute, RDF.type, URIRef(ontology_dict["type"])))
            else:
                raise ValueError("No type specifications in the mapper file.")

            # extracting other informations
            # TODO: is the source description texts needed?
            for i, element in enumerate(row[1:]):
                predicate_cur = header[i]
                # finding the predicate from csv in the config dictionary, if not exit, skip
                if predicate_cur in list(ontology_dict.keys()):
                    predicate = URIRef(ontology_dict[predicate_cur])
                else:
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
