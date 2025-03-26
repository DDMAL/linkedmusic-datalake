import requests
import rdflib
import os
from typing import Tuple

# Constant definitions
RECON_SERVICE = "https://wikidata.reconci.link/en/api"
WD_EXACT_MATCH = rdflib.URIRef("http://www.wikidata.org/prop/direct/P2888")
RISM_PERSON_TYPE = rdflib.URIRef("https://rism.online/api/v1#Person")
RISM_SOURCE_TYPE = rdflib.URIRef("https://rism.online/api/v1#Source")
RISM_INSTITUTION_TYPE = rdflib.URIRef("https://rism.online/api/v1#Institution")
RDFS_LABEL = rdflib.URIRef("http://www.w3.org/2000/01/rdf-schema#label")
RDF_TYPE = rdflib.URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")
WD_TYPE = rdflib.URIRef("http://www.wikidata.org/prop/direct/P31")
WD_CLASS = {
    RISM_PERSON_TYPE: rdflib.URIRef("http://www.wikidata.org/entity/Q5"),
    RISM_SOURCE_TYPE: rdflib.URIRef("http://www.wikidata.org/entity/Q3142800"),
    RISM_INSTITUTION_TYPE: rdflib.URIRef("http://www.wikidata.org/entity/Q166118"),
}

class WikidataReconciler:
    def __init__(self, recon_service: str, graph=None, auto_match: bool = True):
        self.recon_service = recon_service
        self.auto_match = auto_match
        if graph:
            self.graph = graph
        else:
            self.graph = rdflib.Graph()

    def build_query(self, search_term: str, entity_type: str) -> dict:
        """Construct query template"""
        query = """{"q0": {"query": "search_term","type": "entity_type","limit": 5,"type_strict": "should"}}"""
        return query.replace("search_term", search_term).replace("entity_type", entity_type)

    def get_wikidata_matches(self, search_term: str, entity_type: str) -> list:
        """Retrieve Wikidata matches"""
        query = self.build_query(search_term, entity_type)
        try:
            response = requests.post(
                self.recon_service, data={"queries": str(query)}, timeout=30
            )
            response.raise_for_status()
            return response.json()["q0"]["result"]
        except (requests.exceptions.RequestException, KeyError) as e:
            print(f"Failed search: {str(e)}. Error response:")
            return []

    def handle_matches(self, subject: rdflib.URIRef, matches: list) -> bool:
        """Process match results and update RDF graph"""
        # Process exact matches
        exact_matches = [m for m in matches if m.get("match")]
        if exact_matches:
            self._add_wikidata_uri(subject, exact_matches[0])
            return True

        # Process high score matches (>90)
        high_scores = [m for m in matches if m.get("score", 0) > 90]
        if not high_scores:
            return False

        # Handle multiple perfect matches
        perfect_scores = [m for m in high_scores if m["score"] == 100]
        if len(perfect_scores) > 1:
            return self._handle_multiple_perfect_matches(subject, perfect_scores)

        if high_scores:
            self._add_wikidata_uri(subject, high_scores[0])
            return True
        return False

    def _add_wikidata_uri(self, subject: rdflib.URIRef, match: dict):
        """Add Wikidata URI to RDF graph"""
        print(f"Match Success: {match['name']} (http://www.wikidata.org/entity/{match['id']})")
        predicate = WD_EXACT_MATCH
        obj = rdflib.URIRef(f"http://www.wikidata.org/entity/{match['id']}")
        self.graph.add((subject, predicate, obj))

    def _handle_multiple_perfect_matches(
        self, subject: rdflib.URIRef, matches: list
    ) -> bool:
        # TODO: use prompts to ask AI to choose
        if self.auto_match:
            print(f"Multiple high scores, auto-matching: {subject}")
            self._add_wikidata_uri(subject, matches[0])
            return True

        print(f"Multiple high scores, please choose: {subject}")
        for i, match in enumerate(matches, 1):
            print(f"{i}: {match['name']} ({match['id']})")

        while True:
            choice = input("Enter choice (s to skip): ").strip().lower()
            if choice == "s":
                return False
            if choice.isdigit() and 0 < int(choice) <= len(matches):
                self._add_wikidata_uri(subject, matches[int(choice) - 1])
                return True
            print("Invalid, please retry.")


def get_subject_context(
    original_graph: rdflib.Graph,
) -> Tuple[rdflib.Graph, rdflib.Graph]:
    """Split the graph into person graph and resource graph based on type"""
    persons_graph = rdflib.Graph()
    sources_graph = rdflib.Graph()
    institutions_graph = rdflib.Graph()

    for entity_type, entity_graph in (
        (RISM_PERSON_TYPE, persons_graph),
        (RISM_SOURCE_TYPE, sources_graph),
        (RISM_INSTITUTION_TYPE, institutions_graph),
    ):
        wd_class = WD_CLASS[entity_type]
        for s in original_graph.subjects(RDF_TYPE, entity_type):
            entity_graph.add((s, WD_TYPE, wd_class))
            for triple in original_graph.triples((s, None, None)):
                entity_graph.add(triple)

    return persons_graph, sources_graph, institutions_graph


def process_file(file_path: str, output_dir: str, reconciler: WikidataReconciler):
    """Process a single file"""
    print(f"Parsing: {file_path}")

    # Parse the input graph
    graph = rdflib.Graph()
    graph.parse(file_path, format="ttl")

    # Split the graph
    persons_graph, sources_graph, institutions_graph = get_subject_context(graph)

    # Handle 'Person'
    print("Handling 'Person'...")
    reconciler.graph = persons_graph
    for subject in set(persons_graph.subjects(RDFS_LABEL)):
        label = persons_graph.value(subject, RDFS_LABEL)
        if label:
            matches = reconciler.get_wikidata_matches(str(label), "Q5")
            reconciler.handle_matches(subject, matches)

    # Handle 'Institution'
    print("Handling 'Institution'...")
    reconciler.graph = institutions_graph
    for subject in set(institutions_graph.subjects(RDFS_LABEL)):
        label = institutions_graph.value(subject, RDFS_LABEL)
        if label:
            matches = reconciler.get_wikidata_matches(str(label), "Q166118")
            reconciler.handle_matches(subject, matches)

    # Merge results and save
    graph += (persons_graph + sources_graph + institutions_graph)
    output_path = os.path.join(output_dir, f"reconciled_{os.path.basename(file_path)}")
    graph.serialize(output_path, format="nt", encoding="utf-8")
    print(f"Saved processed results to: {output_path}")


def main():
    # Configuration parameters
    input_dir = "split_output/"
    output_dir = "../data/reconciled/"
    os.makedirs(output_dir, exist_ok=True)

    # Initialize reconciler
    reconciler = WikidataReconciler(RECON_SERVICE, auto_match=True)

    # Process all files
    for filename in os.listdir(input_dir):
        if filename.endswith(".ttl"):
            file_path = os.path.join(input_dir, filename)
            process_file(file_path, output_dir, reconciler)


if __name__ == "__main__":
    main()
