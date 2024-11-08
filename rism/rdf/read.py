from rdflib import Graph
import validators
import pandas as pd

FILE_PATH = "rismTitleRDFexample.ttl"  # Replace with your RDF file

def load_rdf(file_path: str, f):
    """
    load RDF data from a file
    """
    # Create a new RDF graph
    g = Graph()
    # Parse the RDF data from the specified file
    g.parse(file_path, format=f)

    rows = {}
    # Print all triples in the graph
    for subj, pred, obj in g:
        if not validators.url(obj):
            print(f"Subject: {subj}, Predicate: {pred}, Object: {obj}")
            try:
                rows[subj][pred] = obj
            except KeyError:
                rows[subj] = {pred: obj}

    df = pd.DataFrame.from_dict(rows, orient='index')
    df.to_csv("output.csv")


# Example usage
if __name__ == "__main__":
    load_rdf(FILE_PATH, "ttl")
