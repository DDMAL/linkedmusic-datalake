import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from queue import Queue
from rdflib import Graph, URIRef, BNode, Literal, Namespace
from rdflib.namespace import RDF

SCHEMA = Namespace("http://schema.org/")
MB = Namespace("https://musicbrainz.org/")
WDT = Namespace("http://www.wikidata.org/prop/direct/")
# Define mapping from MusicBrainz to Wikidata
MB_SCHEMA = {
    "artist": "P434",
    "release-group": "P436",
    "release": "P5813",
    "recording": "P4404",
    "work": "P435",
    "label": "P966",
    "area": "P982",
    "place": "P1004",
    "event": "P6423",
    "series": "P1407",
    "instrument": "P1330",
    "genre": "P8052",
    "url": "P2888"
}

def worker(chunk, entity_type, mb_schema, namespaces):
    """Worker function to process data chunks"""
    g = Graph()
    # Bind namespaces
    for prefix, ns in namespaces.items():
        g.bind(prefix, ns)
    
    MB_ENTITY_TYPES = {
        'artist', 'release', 'recording', 'label', 'work',
        'area', 'genre', 'event', 'place', 'series', 'instrument'
    }
    
    for line in chunk:
        try:
            data = json.loads(line.strip())
            entity_id = data.get('id')
            if not entity_id:
                continue

            # Create subject URI
            subject_uri = URIRef(f"https://musicbrainz.org/{entity_type}/{entity_id}")

            # Process name
            if 'name' in data:
                g.add((subject_uri, URIRef(f"{WDT}P2561"), Literal(data['name'])))

            # Process type
            if 'type' in data:
                g.add((subject_uri, RDF.type, Literal(data['type'])))

            # Process aliases
            if 'aliases' in data:
                for alias in data['aliases']:
                    if alias_name := alias.get('name'):
                        blank_node = BNode()
                        g.add((subject_uri, URIRef(f"{WDT}P4970"), blank_node))
                        try:
                            g.add((blank_node, URIRef(f"{WDT}P2561"), Literal(alias_name, lang=alias.get('locale', 'none'))))
                        except ValueError:
                            g.add((blank_node, URIRef(f"{WDT}P2561"), Literal(alias_name)))
                            # Process alias language
                            if 'locale' in alias:
                                g.add((blank_node, URIRef(f"{WDT}P1412"), Literal(alias['locale'])))

            # Process genres
            if 'genres' in data:
                for genre in data['genres']:
                    if genre_id := genre.get('id'):
                        genre_uri = URIRef(f"https://musicbrainz.org/genre/{genre_id}")
                        g.add((subject_uri, URIRef(f"{WDT}{MB_SCHEMA['genre']}"), genre_uri))

            # Process relationships
            if 'relations' in data:
                for relation in data['relations']:
                    if not (rel_type := relation.get('target-type')):
                        continue
                    
                    target_uri = None
                    for key in relation:
                        if key in MB_ENTITY_TYPES:
                            if target_id := relation[key].get('id'):
                                target_uri = URIRef(f"https://musicbrainz.org/{key}/{target_id}")
                                break
                        elif key == 'url':
                            if url_resource := relation[key].get('resource'):
                                target_uri = URIRef(url_resource)
                                break

                    if target_uri and rel_type in mb_schema:
                        pred_uri = URIRef(f"{WDT}{MB_SCHEMA[rel_type]}")
                        g.add((subject_uri, pred_uri, target_uri))
        except json.JSONDecodeError:
            continue
            
    return g

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 convert_to_rdf.py <input_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    entity_type = Path(input_file).stem  # Get entity type from filename


    # Initialize namespaces
    namespaces = {
        "schema": SCHEMA,
        "mb": MB,
        "wdt": WDT
    }
    

    # Configure output directory
    output_dir = Path('./data/musicbrainz/rdf/')
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{entity_type}.ttl"

    # Create task queue
    chunk_queue = Queue()
    CHUNK_SIZE = 500  # Adjustable chunk size
    
    # Read file and split into chunks
    with open(input_file, 'r', encoding='utf-8') as f:
        chunk = []
        for line in f:
            chunk.append(line)
            if len(chunk) >= CHUNK_SIZE:
                chunk_queue.put(chunk)
                chunk = []
        if chunk:  # Process the remaining last chunk
            chunk_queue.put(chunk)

    # Create thread pool
    main_graph = Graph()
    for prefix, ns in namespaces.items():
        main_graph.bind(prefix, ns)

    with ThreadPoolExecutor() as executor:
        futures = []
        while not chunk_queue.empty():
            chunk = chunk_queue.get()
            futures.append(
                executor.submit(
                    worker,
                    chunk,
                    entity_type,
                    MB_SCHEMA,
                    namespaces
                )
            )

        # Merge all subgraphs
        for future in futures:
            subgraph = future.result()
            main_graph += subgraph

    # Save the final result
    main_graph.serialize(destination=output_file, format='turtle')
    print(f"Successfully saved RDF data to: {output_file}")

if __name__ == "__main__":
    main()