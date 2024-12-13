import csv
from rdflib import Graph, URIRef, Literal, BNode


# Load RDF file
def load_rdf(rdf_file):
    rdf_graph = Graph()
    rdf_graph.parse(rdf_file, format="turtle")  # Adjust format if necessary
    return rdf_graph


# Read and process CSV data
def read_csv(csv_file):
    data = {}
    with open(csv_file, "r", encoding="utf-8") as file:
        reader = csv.reader(file)
        headers = next(reader)  # First row contains subject and predicates
        predicates = headers[1:]
        for row in reader:
            subject = row[0]
            objects = row[1:]
            data[subject] = dict(zip(predicates, objects))
    return data


# Merge data into the RDF graph
def merge_data(csv_data):
    rdf_graph = Graph()
    blank_nodes = {}  # To store blank nodes as we encounter them
    prev_subject = None

    for subject, predicate_objects in csv_data.items():
        if subject != "":
            # Check if the subject is a blank node by its length and content
            if len(subject) == 32 and all(c in "0123456789abcdef" for c in subject):
                # Create or retrieve the blank node
                subj_node = blank_nodes.setdefault(subject, BNode())
            else:
                # Create a URI for non-blank-node subjects
                subj_node = URIRef(subject)
            prev_subject = URIRef(subj_node)
        else:
            subj_node = prev_subject

        for predicate, obj in predicate_objects.items():
            if obj == "" or obj is None:
                continue

            # Reference another blank node if the object is a blank node
            if len(obj) == 32 and all(c in "0123456789abcdef" for c in obj):
                # Retrieve or create the referenced blank node
                if subject == "":
                    obj_node = rdf_graph.value(subj_node, URIRef(predicate),any=False)
                    print(obj_node)
                else:
                    obj_node = blank_nodes.setdefault(obj, BNode())
            else:
                obj_node = Literal(obj) if not obj.startswith("http") else URIRef(obj)
            # Add triple to the graph
            rdf_graph.add((subj_node, URIRef(predicate), obj_node))

    # print(blank_nodes)
    return rdf_graph


# Save the updated RDF graph
def save_rdf(rdf_graph, output_file):
    rdf_graph.serialize(
        destination=output_file, format="turtle"
    )  # Adjust format if necessary


# Main function
def main(rdf_input, csv_input, rdf_output):
    print("Loading RDF data...")
    rdf_graph = load_rdf(rdf_input)

    print("Reading CSV data...")
    csv_data = read_csv(csv_input)

    print("Merging data into RDF...")
    reconciled_graph = merge_data(csv_data)

    print("Saving updated RDF file...")
    save_rdf(reconciled_graph, rdf_output)
    print(f"Updated RDF saved to {rdf_output}")


# Example usage
if __name__ == "__main__":
    rdf_input_file = "./musicbrainz/output_test.ttl"  # Replace with your RDF file
    csv_input_file = "./musicbrainz/output-test-ttl.csv"  # Replace with your CSV file
    rdf_output_file = "./musicbrainz/final.ttl"  # Replace with desired output file name

    main(rdf_input_file, csv_input_file, rdf_output_file)
