"""
RISM RDF Conversion

This script will read all the reconciled CSV files for RISM in a given directory,
and will convert them into Turtle RDF using the rdflib module.

Key features:

    - Batch processing of CSV files for efficient RDF conversion.
    - Utilization of multiprocessing to speed up the conversion process.
    - Error handling and logging for robust processing.

Usage:
    `python convert_to_rdf.py --input_folder <input_folder> --mappings_folder <mappings_folder> --output_folder <output_folder>`

    Where:

        - `<input_folder>` is the path to the folder containing the input CSV files.
        - `<mappings_folder>` is the path to the folder containing the mapping files.
        - `<output_folder>` is the path to the folder where the output RDF files will be saved.
    
    The script can also be run without arguments, in which case it will use default paths.
    The output folder will contain the generated Turtle files named after the file number of the CSV files.
    The script will create the output folder if it does not exist.

Exception Handling:

    - Skips any lines that raise errors, after logging the error.
    - Handles missing or malformed data gracefully, logging errors to the terminal without crashing the script.
    - Unexpected exceptions that cause workers to stop are logged, the worker will mark the problematic task
    as complete so that other workers don't get stuck, and the worker will exit.

Potential improvements: Handle a dummy node being in a different file than the subject
"""

import json
import csv
import sys
import os
import re
import argparse
import asyncio
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from isodate.isoerror import ISO8601Error
from isodate.isodates import parse_date
from tqdm import tqdm
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import XSD, RDFS, DCTERMS, RDF

# Define namespaces
WDT = Namespace("http://www.wikidata.org/prop/direct/")
WD = Namespace("http://www.wikidata.org/entity/")
LMRISM = Namespace("https://linkedmusic.ca/graphs/rism/")
RISM = Namespace("https://rism.online/")
RISM_API = Namespace("https://rism.online/api/v1#")
# Define RISM namespaces, to save space in exported RDF
RI = Namespace(f"{RISM}institutions/")
RP = Namespace(f"{RISM}people/")
RS = Namespace(f"{RISM}sources/")

# Max number of file processing processes to run simultaneously
MAX_WORKERS = 6
# Max number of processes to run simultaneously
MAX_PROCESSES = min(MAX_WORKERS, os.cpu_count() or 1)

# Set to True if you want to reprocess entity types that are already present in the output folder
REPROCESSING = False

# Regex patterns for RDF object conversion
WIKIDATA_PATTERN = re.compile(r"^https?:\/\/www\.wikidata\.org\/wiki\/(Q\d+)$")
TYPED_PATTERN = re.compile(r"^(.*)\^\^(.*)$")
LANG_PATTERN = re.compile(r"^(.*)@(.*)$")
URI_PATTERN = re.compile(r"^https?://")
# Entities matching this pattern will not be put in the intermediate graph
INTERMEDIATE_GRAPH_IGNORE_PATTERN = re.compile(
    r"^https://rism.online/(?:sources|institutions|people)/\d+$"
)


def convert_date(date_str: str) -> Literal:
    """
    Convert a date string to an RDF Literal with XSD date datatype.
    If the date string is not in a valid format, it returns a plain Literal.
    """
    try:
        # Validate the date string, and catch any exception that might occur
        return Literal(parse_date(date_str), datatype=XSD.date)
    except (ISO8601Error, ValueError):
        return Literal(date_str)  # Fallback to a plain literal if conversion fails


def convert_literal(lit: str) -> Literal:
    """Convert a string into a Literal object, with the datatype or language tag."""
    if "^^" in lit and (m := TYPED_PATTERN.match(lit)):
        # Handle literals that contain "^^" but that don't have a datatype
        if not URI_PATTERN.match(m.group(2)):
            return Literal(lit)
        return Literal(m.group(1), datatype=m.group(2))
    elif "@" in lit and (m := LANG_PATTERN.match(lit)):
        return Literal(m.group(1), lang=m.group(2))
    else:
        return Literal(lit)


def convert_rdf_object(obj: str) -> URIRef | Literal:
    """
    Convert a string into an RDF object (URIRef or Literal).
    URIs that are stored as a literal with datatype XSD:anyURI are not converted to URIRefs.
    On error,  it will convert the object to a plain literal, with no language tag or datatype.
    """
    try:
        if URI_PATTERN.match(obj) and "^^" not in obj:
            if m := WIKIDATA_PATTERN.match(obj):
                # Convert /wiki/... to /entity/...
                return WD[m.group(1)]
            return URIRef(obj)
        return convert_literal(obj)
    except ValueError:
        return Literal(obj)


def process_triple(s, p, o, mapping, roles, old_graph, g):
    """Process a single triple from the file, and add it to the graph."""
    # Make RDF Objects
    s_rdf = URIRef(s)
    p_rdf = URIRef(p)
    o_rdf = convert_rdf_object(o)
    p_map = mapping.get(p, None)

    if p_rdf == RDF.type:
        g.add((s_rdf, RDF.type, LMRISM[o.removeprefix(str(RISM_API))]))

    elif p_rdf == RISM_API["hasEncoding"]:
        if not isinstance(o_rdf, URIRef) or not p_map:
            return
        # Traverse the blank node
        for obj in old_graph.get((o, str(RDFS.label)), []):
            g.add((s_rdf, p_map, convert_rdf_object(obj)))

    elif p_rdf == RISM_API["hasRelationship"]:
        if not isinstance(o_rdf, URIRef):
            return
        for role in old_graph.get((o, str(RISM_API["hasRole"])), []):
            if not (role_map := roles.get(role, None)):
                continue
            # Add the relationship with the role
            for obj in old_graph.get((o, str(DCTERMS.relation)), []):
                g.add((s_rdf, role_map, convert_rdf_object(obj)))

    elif p_rdf == RISM_API["hasHolding"]:
        if not isinstance(o_rdf, URIRef) or not p_map:
            return
        # Traverse the blank node
        for obj in old_graph.get((o, str(WDT["P195"])), []):
            g.add((s_rdf, p_map, convert_rdf_object(obj)))

    elif p_rdf == WDT["P921"]:
        if not isinstance(o_rdf, URIRef) or not p_map:
            return
        # Traverse the blank node
        for obj in old_graph.get(
            (o, "https://wikidata.org/prop/direct/P2888"), []
        ) or old_graph.get((o, str(RDF.value)), []):
            g.add((s_rdf, p_map, convert_rdf_object(obj)))

    elif p_rdf == RISM_API["hasMaterialGroup"]:
        pass  # TODO: handle, see issue #444

    elif p_rdf == WDT["P585"]:
        if not isinstance(o_rdf, URIRef):
            return
        # Traverse the blank node
        first_prop = mapping.get(str(WDT["P1319"]), None)
        if first_prop:
            for obj in old_graph.get((o, str(WDT["P1319"])), []):
                g.add(
                    (
                        s_rdf,
                        first_prop,
                        convert_date(f"{convert_rdf_object(obj).value}-01-01"),
                    )
                )
        second_prop = mapping.get(str(WDT["P1326"]), None)
        if second_prop:
            for obj in old_graph.get((o, str(WDT["P1326"])), []):
                g.add(
                    (
                        s_rdf,
                        second_prop,
                        convert_date(f"{convert_rdf_object(obj).value}-12-31"),
                    )
                )

    elif p_map:
        g.add((s_rdf, p_map, o_rdf))


def process_file(path, mapping, roles, output_file, namespaces):
    """Process an entire file, loading it, creating a graph, and serializing it."""
    with tqdm.get_lock():
        tqdm.write(f"Processing {path}...")

    # Create a dict with the current data for easier blank node traversal
    # This is more memory-efficient than a full Graph because it stores less indices
    old_graph = {}
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        properties = [x for x in reader.fieldnames if x != "subject"]
        subject = None
        for line in reader:
            # Skip basic RISM entities, we only want blank nodes
            # and sub-entities (like holdings) in this graph
            if INTERMEDIATE_GRAPH_IGNORE_PATTERN.match(line["subject"]):
                continue

            # Handle propagating down the subject to deal with record view
            subject = line["subject"] if line["subject"] else subject
            if not subject:
                continue

            for prop in properties:
                # Skip empty objects
                if not line[prop]:
                    continue
                old_graph.setdefault((subject, prop), []).append(line[prop])

    with tqdm.get_lock():
        tqdm.write(f"Converting {path} to RDF...")
    g = Graph()
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        s = None
        for i, line in enumerate(reader):
            try:
                # Only process RISM entities, blank nodes will be handled elsewhere
                if not re.match(r"https://rism.online/", line["subject"]):
                    continue
                # We ignore entities that start with the (fake) API endpoint
                if re.match(r"https://rism.online/api", line["subject"]):
                    continue

                # Handle propagating down the subject to deal with record view
                s = line["subject"] if line["subject"] else s
                if not s:
                    continue

                for p in properties:
                    o = line[p]
                    # Skip empty objects
                    if not o:
                        continue
                    process_triple(s, p, o, mapping, roles, old_graph, g)
            except (KeyError, AttributeError) as e:
                with tqdm.get_lock():
                    tqdm.write(f"{type(e).__name__} in line {i} of file {path}: {e}")
                continue
            except Exception as e:
                with tqdm.get_lock():
                    tqdm.write(
                        f"Unexpected {type(e).__name__} in line {i} of file {path}: {e}"
                    )
                continue

    with tqdm.get_lock():
        tqdm.write(f"Serializing graph to {output_file}...")
    try:
        for prefix, ns in namespaces.items():
            g.bind(prefix, ns)
        with open(output_file, "wb") as f:
            g.serialize(f, format="turtle", encoding="utf-8")
        with tqdm.get_lock():
            tqdm.write(f"Finished processing {path} to {output_file}")
    except Exception as e:
        with tqdm.get_lock():
            tqdm.write(f"Error serializing graph: {type(e).__name__}: {e}")


async def worker(
    output_folder,
    graph_queue,
    mapping,
    roles,
    file_bar,
    namespaces,
    executor,
):
    """
    Worker function to process the files.
    This function will load a CSV file, create a graph from it, and serialize the graph to a Turtle file,
    and do so in a separate process to increase efficiency.
    """
    loop = asyncio.get_event_loop()
    graph_started = False
    try:
        while not graph_queue.empty():
            path = await graph_queue.get()
            graph_started = True

            output_file = output_folder / f"{path.stem.removesuffix('-ttl')}.ttl"  # Remove the "-ttl" suffix robustly

            # Process the file in a separate process to speed up the processing
            g = await asyncio.gather(
                loop.run_in_executor(
                    executor,
                    process_file,
                    path,
                    mapping,
                    roles,
                    str(output_file),
                    namespaces,
                ),
                return_exceptions=True,
            )
            g = g[0]

            # Handle any exceptions raised by the process
            if isinstance(g, Exception):
                graph_queue.task_done()
                with tqdm.get_lock():
                    tqdm.write(f"Error processing graph: {type(g).__name__}: {g}")
                    file_bar.update(1)
                graph_started = False
                continue

            with tqdm.get_lock():
                file_bar.update(1)

            graph_queue.task_done()
            graph_started = False
    except asyncio.CancelledError:
        pass
    except Exception as e:
        with tqdm.get_lock():
            tqdm.write(f"Error processing graph: {type(e).__name__}: {e}")
    finally:
        # Ensure all tasks are marked as done
        if graph_started:
            graph_queue.task_done()
            # If the graph was not processed, we still need to update the progress bar
            with tqdm.get_lock():
                file_bar.update(1)


async def main(paths, output_folder, mapping, roles):
    """
    Main function to process all the RISM CSV files.
    This function orchestrates the processing of each file and manages the overall workflow.
    """
    # Configure output directory
    output_folder.mkdir(parents=True, exist_ok=True)

    # Initialize namespaces
    namespaces = {
        "wdt": WDT,
        "wd": WD,
        "rism": LMRISM,
        "ri": RI,
        "rp": RP,
        "rs": RS,
    }

    # Create queues
    graph_queue = asyncio.Queue(len(paths))
    for p in paths:
        graph_queue.put_nowait(p)

    # Create the progress bars
    file_bar = tqdm(total=len(paths), desc="Processing files", position=0)

    with ProcessPoolExecutor(max_workers=MAX_PROCESSES) as executor:
        try:
            workers = [
                asyncio.create_task(
                    worker(
                        output_folder,
                        graph_queue,
                        mapping,
                        roles,
                        file_bar,
                        namespaces,
                        executor,
                    )
                )
                for _ in range(min(MAX_WORKERS, len(paths)))
            ]

            await asyncio.gather(*workers)

            file_bar.close()
        except KeyboardInterrupt:
            executor.shutdown(wait=False, cancel_futures=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert RISM CSV data in a folder to RDF Turtle format."
    )
    parser.add_argument(
        "--input_folder",
        default="../../data/rism/reconciled/",
        help="Path to the folder containing line-delimited RISM CSV files.",
    )
    parser.add_argument(
        "--mappings_folder",
        default="./mappings/",
        help="Path to the JSON file containing property mappings.",
    )
    parser.add_argument(
        "--output_folder",
        default="../../data/rism/rdf/",
        help="Directory where the output Turtle files will be saved.",
    )
    args = parser.parse_args()

    input_folder = Path(args.input_folder)
    if not input_folder.is_dir():
        print(f"{input_folder} is not a valid directory.")
        sys.exit(1)

    mappings_folder = Path(args.mappings_folder)
    mapping_file = mappings_folder / "property_mapping.json"
    if not mapping_file.is_file():
        print(f"{mapping_file} is not a valid file.")
        sys.exit(1)

    with open(mapping_file, "r", encoding="utf-8") as f:
        mapping = json.load(f)
    if not mapping:
        print(f"{mapping_file} is empty.")
        sys.exit(1)

    # Convert the values to URIRefs
    for k, v in mapping.items():
        if v:
            mapping[k] = URIRef(v)
        else:
            mapping[k] = None

    roles_file = mappings_folder / "roles.json"
    if not roles_file.is_file():
        print(f"{roles_file} is not a valid file.")
        sys.exit(1)

    with open(roles_file, "r", encoding="utf-8") as f:
        roles = json.load(f)
    if not roles:
        print(f"{roles_file} is empty.")
        sys.exit(1)

    # Convert the values to URIRefs
    for k, v in roles.items():
        if v:
            roles[k] = WDT[v]
        else:
            roles[k] = None

    bad_files = set()
    output_folder = Path(args.output_folder)
    if output_folder.exists() and not REPROCESSING:
        for file in output_folder.iterdir():
            # Grab the numbers for ttl files
            if file.is_file() and (m := re.match(r"^part-(\d+)$", file.stem)):
                bad_files.add(m.group(1))

    paths = []
    for input_file in input_folder.iterdir():
        if not input_file.is_file() or not str(input_file).endswith(".csv"):
            continue
        if (
            not REPROCESSING
            and (m := re.match(r"^part-(\d+)-ttl$", input_file.stem))
            and m.group(1) in bad_files
        ):
            print(f"Skipping {input_file} as it is already processed.")
            continue
        paths.append(input_file)
    if paths:
        asyncio.run(main(paths, output_folder, mapping, roles))
