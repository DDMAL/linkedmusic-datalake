import csv
from rdflib import Graph, URIRef, Literal


# Load RDF file
def load_rdf(rdf_file):
    rdf_graph = Graph()
    rdf_graph.parse(rdf_file, format="turtle")  # Adjust format if necessary
    return rdf_graph


# Read and process CSV data
def read_csv(csv_file):
    data = []
    with open(csv_file, "r", encoding="utf-8") as file:
        reader = csv.reader(file)
        headers = next(reader)  # First row contains subject and predicates
        predicates = headers[1:]
        for row in reader:
            subject = row[0]
            objects = row[1:]
            data.append((subject, dict(zip(predicates, objects))))
    return data


# Merge data into the RDF graph
def merge_data(rdf_graph, csv_data):
    for subject, predicate_objects in csv_data:
        subject_uri = URIRef(subject)
        for predicate, obj in predicate_objects.items():
            predicate_uri = URIRef(predicate)
            obj_node = Literal(obj) if not obj.startswith("http") else URIRef(obj)
            rdf_graph.add((subject_uri, predicate_uri, obj_node))
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
    updated_graph = merge_data(rdf_graph, csv_data)

    print("Saving updated RDF file...")
    save_rdf(updated_graph, rdf_output)
    print(f"Updated RDF saved to {rdf_output}")


# Example usage
if __name__ == "__main__":
    rdf_input_file = "input_data.ttl"  # Replace with your RDF file
    csv_input_file = "reconciliation_data.csv"  # Replace with your CSV file
    rdf_output_file = "updated_data.ttl"  # Replace with desired output file name

    main(rdf_input_file, csv_input_file, rdf_output_file)
