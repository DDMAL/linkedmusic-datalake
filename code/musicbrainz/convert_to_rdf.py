"""
Module: convert_to_rdf.py
This module converts line-delimited MusicBrainz JSON data into RDF Turtle format using the rdflib library.
It reads an input file where each line represents a MusicBrainz entity, processes the data to map various
properties to corresponding Wikidata properties, and serializes the resulting RDF graph to a Turtle file.
Key Features:
    - Reads and counts total lines in the input JSON file.
    - Infers the entity type based on the filename of the input.
    - Processes entity attributes including name, type, aliases, genres, and relationships.
    - Uses a mapping schema (MB_SCHEMA) to convert MusicBrainz entity relationships to corresponding Wikidata properties.
    - Processes data in chunks and utilizes multi-threading (ThreadPoolExecutor) for parallel processing.
    - Merges RDF subgraphs generated by worker threads into a main RDF graph.
    - Serializes the main RDF graph to an output Turtle (.ttl) file specified via command line.
    - Provides progress feedback using tqdm for monitoring both file reading and graph merging processes.
Usage:
    python3 convert_to_rdf.py <input_file> <output_file>
    Where <input_file> is a path to the line-delimited JSON file containing MusicBrainz data 
    and <output_file> is the path to save the generated Turtle file.
Exception Handling:
    - Skips any lines that fail JSON decoding or lack the necessary entity id.
This module is intended for converting MusicBrainz data to RDF format, facilitating integration with other linked data sources.
"""

import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from queue import Queue
from tqdm import tqdm
from rdflib import Graph, URIRef, BNode, Literal, Namespace
from rdflib.namespace import RDF
import argparse

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

def main(args):
    input_file = args.input_file
    entity_type = Path(input_file).stem  # Get entity type from filename

    # Configure output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{entity_type}.ttl"

    # Initialize namespaces
    namespaces = {
        "schema": SCHEMA,
        "mb": MB,
        "wdt": WDT
    }

    with open(input_file, 'r', encoding='utf-8') as f:
        total_lines = sum(1 for _ in f)
    print(f"Total lines in {input_file}: {total_lines}")
    print(f"Processing {input_file}...")

    # Create task queue
    chunk_queue = Queue()
    CHUNK_SIZE = 500  # Adjustable chunk size

    # Read file and split into chunks
    with open(input_file, 'r', encoding='utf-8') as f:
        chunk = []
        for line in tqdm(f, total=total_lines, desc="Reading lines"):
            chunk.append(line)
            if len(chunk) >= CHUNK_SIZE:
                chunk_queue.put(chunk)
                chunk = []
        if chunk:  # Process the remaining last chunk
            chunk_queue.put(chunk)
            
    print(f"Total chunks created: {chunk_queue.qsize()}")
    print("Starting RDF conversion...")

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

        # Process results
        subgraphs = []
        for future in tqdm(as_completed(futures), total=len(futures), desc="Processing chunks"):
            try:
                future.result()  # Raise exception if any occurred in worker
            except Exception as e:
                print(f"Error processing chunk: {e}")
                continue
            subgraphs.append(future.result())

    for subgraph in tqdm(subgraphs, desc="Merging subgraphs"):
        main_graph += subgraph

    # Save the final result
    main_graph.serialize(destination=output_file, format='turtle')
    print(f"Successfully saved RDF data to: {output_file}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 convert_to_rdf.py <input_folder> <output_dir>")
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description="Convert MusicBrainz JSON data in a folder to RDF Turtle format."
    )
    parser.add_argument(
        "--input_folder",
        default="../../data/musicbrainz/raw/extracted_jsonl/mbdump",
        help="Path to the folder containing line-delimited MusicBrainz JSON files."
    )
    parser.add_argument(
        "--output_dir",
        default="../../data/musicbrainz/rdf/",
        help="Directory where the output Turtle files will be saved (default: ../../data/musicbrainz/rdf/)."
    )
    args = parser.parse_args()

    input_folder = Path(args.input_folder)
    if not input_folder.is_dir():
        print(f"{input_folder} is not a valid directory.")
        sys.exit(1)

    for input_file in input_folder.iterdir():
        if str(input_file).endswith(".DS_Store"):
            continue
        if input_file.is_file():
            print(f"Processing file: {input_file}")
            # Create a new namespace for the current file using its stem as entity type
            sub_args = argparse.Namespace(
                input_file=str(input_file),
                output_dir=args.output_dir
            )
            main(sub_args)
