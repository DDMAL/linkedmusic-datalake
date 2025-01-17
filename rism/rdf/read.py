from rdflib import Graph

FILE_PATH = "rism-test-100000.ttl"  # Replace with your RDF file


def load_rdf(file_path: str, f):
    """
    load RDF data from a file
    """
    # Create a new RDF graph
    graph = Graph()
    # Parse the RDF data from the specified file
    graph.parse(file_path, format=f)

    return graph


# Example usage
if __name__ == "__main__":
    g = load_rdf(FILE_PATH, "ttl")
    g.serialize("output.ttl", format="ttl")
