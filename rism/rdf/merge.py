import csv
import validators
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
                if obj != "":
                    data[subject].append((pred, obj))
    return data


RECONCILIATION_COLUMNS = [
    "http://www.wikidata.org/prop/direct/P2308",
    "http://www.wikidata.org/prop/direct/P2888"
]


# Merge data into the RDF graph
def merge_data(rdf_graph, csv_data):
    stack = []
    for s0, p0, o0 in rdf_graph.triples((None, None, None)):
        if isinstance(s0, URIRef):
            for p0_csv, o0_csv in csv_data[str(s0)]:
                # If predicate matches, add to stack
                if p0_csv == str(p0):
                    # In stack, we store the subject, predicate, object in RDF, and object in CSV
                    stack.append((s0, p0, o0, o0_csv))
                    if (p0_csv, o0_csv) in csv_data[str(s0)]:
                        csv_data[str(s0)].remove((p0_csv, o0_csv))
                    continue

                # If predicate is in reconciliation column, add to stack. It's not in RDF graph
                if p0_csv in RECONCILIATION_COLUMNS:
                    stack.append((s0, URIRef(p0_csv), o0_csv, o0_csv))
                    csv_data[str(s0)].remove((p0_csv, o0_csv))

        while stack:
            # Get current triple from stack plus the corresponding CSV object
            s, p, o, o_csv = stack.pop()
            if isinstance(o, BNode):
                # Get all triples with the current object as subject
                sn, sn_csv = o, o_csv
                for pn, on in rdf_graph.predicate_objects(sn):
                    for pn_csv, on_csv in csv_data[str(sn_csv)]:
                        if on_csv == "":
                            continue

                        if pn_csv == str(pn):
                            stack.append((sn, pn, on, on_csv))
                            if (pn_csv, on_csv) in csv_data[str(sn_csv)]:
                                csv_data[str(o_csv)].remove((pn_csv, on_csv))
                            break

                        if pn_csv in RECONCILIATION_COLUMNS:
                            stack.append((sn, URIRef(pn), "reconciling", on_csv))
                            csv_data[str(o_csv)].remove((pn_csv, on_csv))
                            break

            else:
                if not validators.url(
                    o_csv,
                    public=True,
                    allow_fragments=False,
                    require_tld=True,
                    require_protocol=True,
                ):
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
    rdf_graph.bind("wd", "http://www.wikidata.org/entity/")
    rdf_graph.bind("wdt", "http://www.wikidata.org/prop/direct/")

    print("Reading CSV data...")
    csv_data = read_csv(csv_input)

    print("Merging data into RDF...")
    reconciled_graph = merge_data(rdf_graph, csv_data)

    print("Saving updated RDF file...")
    save_rdf(reconciled_graph, rdf_output)
    print(f"Updated RDF saved to {rdf_output}")


# Example usage
if __name__ == "__main__":
    rdf_input_file = "./output.ttl"  # Replace with your RDF file
    csv_input_file = "./output-ttl.csv"  # Replace with your CSV file
    rdf_output_file = "./merged.ttl"  # Replace with desired output file name

    main(rdf_input_file, csv_input_file, rdf_output_file)
