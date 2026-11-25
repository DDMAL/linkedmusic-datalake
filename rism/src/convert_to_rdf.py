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
    - File processing and publication failures are reported per part. Other parts continue,
      and the command exits nonzero if any part failed.

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
from tempfile import TemporaryDirectory
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
WIKIDATA_PATTERN = re.compile(
    r"\Ahttps?://(?:www\.)?wikidata\.org/(?:wiki|entity)/(Q[1-9][0-9]*)\Z"
)
# CSV predicate keys stay as supplied. These explicit aliases are separate from
# item-IRI normalization, so historical intermediate topic lookups still work.
EXACT_MATCH_PREDICATES = (
    str(WDT["P2888"]),
    "http://wikidata.org/prop/direct/P2888",
    "https://www.wikidata.org/prop/direct/P2888",
    "https://wikidata.org/prop/direct/P2888",
)
TYPED_PATTERN = re.compile(r"^(.*)\^\^(.*)$")
LANG_PATTERN = re.compile(r"^(.*)@(.*)$")
URI_PATTERN = re.compile(r"^https?://")
# Characters that cannot appear verbatim inside a Turtle <IRIREF>.
UNSAFE_IRI_CHAR = re.compile(r'[\x00-\x20<>"{}|^`\\]')
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
            if m := WIKIDATA_PATTERN.fullmatch(obj):
                # Normalize item IRIs only; never rewrite literal contents.
                return WD[m.group(1)]
            if UNSAFE_IRI_CHAR.search(obj):
                return Literal(obj)
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
        matches = [
            obj
            for predicate in EXACT_MATCH_PREDICATES
            for obj in old_graph.get((o, predicate), [])
        ]
        for obj in matches or old_graph.get((o, str(RDF.value)), []):
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
    with open(path, "r", encoding="utf-8", newline="") as f:
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
    with open(path, "r", encoding="utf-8", newline="") as f:
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
    for prefix, ns in namespaces.items():
        g.bind(prefix, ns)
    output_file = Path(output_file)
    with TemporaryDirectory(dir=output_file.parent, prefix=".rism-") as staging_dir:
        staged_file = Path(staging_dir) / "export.tmp"
        with staged_file.open("wb") as stream:
            g.serialize(stream, format="turtle", encoding="utf-8")
        staged_file.replace(output_file)
    with tqdm.get_lock():
        tqdm.write(f"Finished processing {path} to {output_file}")


async def worker(
    output_folder, graph_queue, mapping, roles, file_bar, namespaces, executor
):
    """Process queued CSVs in the pool and count failures for the batch exit status."""
    loop = asyncio.get_running_loop()
    failures = 0
    while not graph_queue.empty():
        path = graph_queue.get_nowait()
        output_file = output_folder / f"{path.stem.removesuffix('-ttl')}.ttl"
        try:
            await loop.run_in_executor(
                executor, process_file, path, mapping, roles, output_file, namespaces
            )
        except Exception as exc:
            failures += 1
            tqdm.write(
                f"Failed to export {path} to {output_file}: {type(exc).__name__}: {exc}",
                file=sys.stderr,
            )
        finally:
            graph_queue.task_done()
            file_bar.update(1)
    return failures


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

    with (
        tqdm(total=len(paths), desc="Processing files", position=0) as file_bar,
        ProcessPoolExecutor(max_workers=MAX_PROCESSES) as executor,
    ):
        workers = [
            worker(
                output_folder,
                graph_queue,
                mapping,
                roles,
                file_bar,
                namespaces,
                executor,
            )
            for _ in range(min(MAX_PROCESSES, len(paths)))
        ]
        failures = sum(await asyncio.gather(*workers))
    if failures:
        print(f"{failures} of {len(paths)} exports failed.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert RISM CSV data in a folder to RDF Turtle format."
    )
    parser.add_argument(
        "--input_folder",
        default="../data/reconciled/",
        help="Path to the folder containing line-delimited RISM CSV files.",
    )
    parser.add_argument(
        "--mappings_folder",
        default="./mappings/",
        help="Path to the JSON file containing property mappings.",
    )
    parser.add_argument(
        "--output_folder",
        default="../data/rdf/",
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

    completed_parts = set()
    output_folder = Path(args.output_folder)
    if output_folder.exists() and not REPROCESSING:
        for file in output_folder.iterdir():
            if file.is_file() and (m := re.fullmatch(r"part-(\d+)\.ttl", file.name)):
                completed_parts.add(m.group(1))

    paths = []
    for input_file in input_folder.iterdir():
        if not input_file.is_file() or not str(input_file).endswith(".csv"):
            continue
        if (
            not REPROCESSING
            and (m := re.fullmatch(r"part-(\d+)-ttl", input_file.stem))
            and m.group(1) in completed_parts
        ):
            print(f"Skipping {input_file} as it is already processed.")
            continue
        paths.append(input_file)
    if paths:
        sys.exit(asyncio.run(main(paths, output_folder, mapping, roles)))
