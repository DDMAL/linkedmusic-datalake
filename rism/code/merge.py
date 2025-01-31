import csv
import validators
import json
from rdflib import Graph, URIRef, Literal, BNode


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
    "http://www.wikidata.org/prop/direct/P2888",
]

LANG_COLUMNS = ["en", "de", "fr", "none"]


def merge_data(csv_data):
    g = Graph()
    for s in csv_data:
        for p, o in csv_data[s]:
            p = URIRef(p)
            datatype = None
            lang = None

            if "^^" in o and validators.url(o.split("^^")[1]):
                datatype = URIRef(o.split("^^")[1])
                o = o.split("^^")[0]

            if "@" in o and o.split("@")[1] in LANG_COLUMNS:
                lang = o.split("@")[1]
                o = o.split("@")[0]

            if validators.url(s):
                s = URIRef(s)
            elif len(s) == 32 and s.isalnum():
                s = BNode(s)
            else:
                break

            if validators.url(o):
                o = URIRef(o)
            elif len(o) == 32 and o.isalnum():
                o = BNode(o)
            else:
                o = Literal(o, lang=lang, datatype=datatype)

            g.add((s, p, o))

    return g


# Save the updated RDF graph
def save_rdf(rdf_graph, output_file):
    rdf_graph.serialize(
        destination=output_file, format="turtle"
    )  # Adjust format if necessary


def parse_mapping(mapping, graph):
    for p in graph.predicates(unique=True):
        if str(p) in mapping and mapping[str(p)] != "":
            for s, o in graph.subject_objects(p):
                graph.remove((s, p, o))
                graph.add((s, URIRef(f"http://www.wikidata.org/prop/direct/{mapping[str(p)]}"), o))
    return graph


# Main function
def main(csv_input, rdf_output, mapping_file):
    print("Reading mapping data...")
    mapping = json.load(open(mapping_file, "r", encoding="utf-8"))

    print("Reading CSV data...")
    csv_data = read_csv(csv_input)

    print("Merging data into RDF...")
    reconciled_graph = merge_data(csv_data)
    reconciled_graph = parse_mapping(mapping, reconciled_graph)
    reconciled_graph.bind("wd", "http://www.wikidata.org/entity/")
    reconciled_graph.bind("wdt", "http://www.wikidata.org/prop/direct/")

    print("Saving updated RDF file...")
    save_rdf(reconciled_graph, rdf_output)
    print(f"Updated RDF saved to {rdf_output}")


# Example usage
if __name__ == "__main__":
    csv_input_file = "../data/reconciled/output-ttl.csv"  # Replace with your CSV file
    rdf_output_file = (
        "../data/output/merged.ttl"  # Replace with desired output file name
    )
    json_file = "../data/reconciled/mapping.json"

    main(csv_input_file, rdf_output_file, json_file)
