import requests
import rdflib
import os


def get_wikidata_id(graph, type, auto_match=True):

    for s, p, o in graph_persons.triples((None, None, None)):
        query_string = QUERY.replace("<object>", str(o).split("@", maxsplit=1)[0])
        query_string = query_string.replace("<type>", f"{type}")

        payload = {"queries": query_string}

        response = requests.post(RECON_SERVICE, data=payload, timeout=10)
        response_json = response.json()["q0"]["result"]

        # Check for exact matches first
        matches = [result for result in response_json if result["match"]]
        if matches:
            result = matches[0]
            print(
                f"Exact match: {result['name']}, {result['description']}, {result['id']}"
            )
            graph.add(
                (
                    s,
                    rdflib.URIRef("http://www.wikidata.org/prop/direct/P31"),
                    rdflib.URIRef(f"http://www.wikidata.org/entity/{result['id']}"),
                )
            )
        else:
            # Check for high scoring matches
            high_scores = [result for result in response_json if result["score"] > 90]
            if len(high_scores) == 1:
                result = high_scores[0]
                print(
                    f"Single high score match: {result['name']}, {result['description']}, {result['id']}"
                )
                graph.add(
                    (
                        s,
                        rdflib.URIRef("http://www.wikidata.org/prop/direct/P31"),
                        rdflib.URIRef(f"http://www.wikidata.org/entity/{result['id']}"),
                    )
                )
            elif len([r for r in high_scores if r["score"] == 100]) > 1:
                if not auto_match:
                    print(
                        f"""Multiple perfect matches for
{(str(s), str(p), str(o))}
Please choose manually:"""
                    )
                    print("----------------")
                    for i, result in enumerate(high_scores):
                        if result["score"] == 100:
                            print(
                                f"{i + 1}: {result['name']}, {result['description']}, {result['id']}, {result['score']}"
                            )
                    print("----------------")
                    choice = input("Enter number of correct match (or skip with 's'): ")
                    if choice.isdigit() and 0 <= int(choice) < len(high_scores):
                        result = high_scores[int(choice)]
                        graph.add(
                            (
                                s,
                                rdflib.URIRef("http://www.wikidata.org/prop/direct/P31"),
                                rdflib.URIRef(
                                    f"http://www.wikidata.org/entity/{result['id']}"
                                ),
                            )
                        )
                else:
                    result = [r for r in high_scores if r["score"] == 100][0]
                    print(
                        f"Auto-matching perfect match: {result['name']}, {result['description']}, {result['id']}"
                    )
                    graph.add(
                        (
                            s,
                            rdflib.URIRef("http://www.wikidata.org/prop/direct/P31"),
                            rdflib.URIRef(f"http://www.wikidata.org/entity/{result['id']}"),
                        )
                    )


GRAPH_PATH = "split_output/"
RECON_SERVICE = "https://wikidata.reconci.link/en/api"
QUERY = """{
    "q0": {
        "query": "<object>",
        "type": "<type>",
        "limit": 5,
        "type_strict": "should"
    }
}"""

for file in os.listdir(GRAPH_PATH):
    print(f"Parsing file {GRAPH_PATH + file}")
    graph = rdflib.Graph()
    graph.parse(GRAPH_PATH + file, format="ttl")

    graph_sources = rdflib.Graph()
    graph_persons = rdflib.Graph()

    for s, p, o in graph.triples(
        (None, rdflib.URIRef("http://www.w3.org/2000/01/rdf-schema#label"), None)
    ):
        person_triple = (
            s,
            rdflib.URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
            rdflib.URIRef("https://rism.online/api/v1#Person"),
        )
        source_triple = (
            s,
            rdflib.URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
            rdflib.URIRef("https://rism.online/api/v1#Person"),
        )

        if person_triple in graph:
            graph_persons.add((s, p, o))
        elif source_triple in graph:
            graph_sources.add((s, p, o))
    
    print(f"Parsing graph {GRAPH_PATH + file} completed")

    get_wikidata_id(graph_persons, "Q5", auto_match=True)
    get_wikidata_id(graph_sources, "Q166118")

    graph.serialize("../data/reconciled/rism-dump-wikidata-{file}.ttl", format="ttl")
