from rdflib import Graph, BNode, URIRef

FILE_PATH = "../data/raw/rism-dump.ttl"  # Replace with your RDF file


def parse_bnode(graph: Graph, bnode: BNode):
    """
    Parse a BNode from an RDF graph
    """
    subgraph = Graph()
    for triples in graph.triples((bnode, None, None)):
        subgraph.add(triples)
        if isinstance(triples[2], BNode):
            subgraph += parse_bnode(graph, triples[2])
    return subgraph


def load_rdf(file_path: str, f, chunk_size=1e6):
    """
    Load RDF data from a file and split into chunks
    Returns: List of Graph objects, each containing chunk_size triples
    """
    # Create a new RDF graph
    graph = Graph()
    # Parse the RDF data from the specified file
    graph.parse(file_path, format=f)
    print("Reading Complete")
    chunks = []
    subgraph = Graph()
    subjects = set([s for s in graph.subjects() if isinstance(s, URIRef)])

    for s in subjects:
        for triples in graph.triples((s, None, None)):
            subgraph.add(triples)

            if isinstance(triples[2], BNode):
                subgraph += parse_bnode(graph, triples[2])

            if len(subgraph) >= chunk_size:
                chunks.append(subgraph)
                print(f"Parsed {len(chunks)}/{len(graph)}")
                subgraph = Graph()

    chunks.append(subgraph)

    return chunks


# Example usage
if __name__ == "__main__":
    graphs = load_rdf(FILE_PATH, "ttl")
    counter = 0
    print("Serializing")
    for g in graphs:
        g.serialize(f"../data/raw/output{counter}.ttl", format="ttl")
        counter += 1
