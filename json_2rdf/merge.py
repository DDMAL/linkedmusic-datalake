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
        prev_subject = None
        for row in reader:
            if row[0] != "":
                prev_subject = row[0]
                subject = row[0]
            else:
                subject = prev_subject
            objects = row[1:]
            if data.get(subject) is None:
                data[subject] = []
            for pred, obj in zip(predicates, objects):
                data[subject].append((pred, obj))
    return data


# Merge data into the RDF graph
def merge_data(rdf_graph, csv_data):

    stack = []
    for s0, p0, o0 in rdf_graph.triples((None, None, None)):
        if isinstance(s0, URIRef):
            o1 = next((o for x, o in csv_data[str(s0)] if x == str(p0)))
            stack.append((s0, p0, o0, o1))
            csv_data[str(s0)].remove((str(p0), o1))

    while stack:
        s, p, o, o_csv = stack.pop()
        if isinstance(o, BNode):
            for pn, on in rdf_graph.predicate_objects(o):
                on_csv = next((o for x, o in csv_data[str(o_csv)] if x == str(pn)))
                stack.append((o, pn, on, on_csv))
                csv_data[str(o_csv)].remove((str(pn), on_csv))
        else:
            if not o_csv.startswith("http"):
                rdf_graph.set((s, p, Literal(o_csv)))
            else:
                rdf_graph.set((s, p, URIRef(o_csv)))

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
    reconciled_graph = merge_data(rdf_graph, csv_data)

    print("Saving updated RDF file...")
    save_rdf(reconciled_graph, rdf_output)
    print(f"Updated RDF saved to {rdf_output}")


# Example usage
if __name__ == "__main__":
    rdf_input_file = "./musicbrainz/recording_test_2.ttl"  # Replace with your RDF file
    csv_input_file = "./musicbrainz/recording-test-2-ttl.csv"  # Replace with your CSV file
    rdf_output_file = "./musicbrainz/final.ttl"  # Replace with desired output file name

    main(rdf_input_file, csv_input_file, rdf_output_file)
