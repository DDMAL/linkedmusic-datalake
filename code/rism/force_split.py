import os
import re
import sys
import json
from pathlib import Path

DEFAULT_CHUNK_SIZE_MB = 5e2


def convert_blank_nodes_to_uris(ntriples_str, base_uri="http://dummy.org/bnode/"):
    return re.sub(
        r"_\:([a-zA-Z0-9]+)", lambda m: f"<{base_uri}{m.group(1)}>", ntriples_str
    )


def convert_predicate_to_uri(ntriples_str, mapping_dict):
    for k, v in mapping_dict.items():
        if v == "":
            continue
        if k in ntriples_str:
            ntriples_str = ntriples_str.replace(k, v)
    return ntriples_str


def get_mapping_dict(input_file):
    mapping_dict = {}
    with open(input_file, "r") as infile:
        json_data = json.load(infile)
        for k, v in json_data.items():
            if v == "":  # Skip empty mappings
                continue
            if isinstance(v, str):
                mapping_dict[k] = f"http://www.wikidata.org/prop/direct/{v}"
    return mapping_dict


def force_split_ttl(input_file, output_dir, mapping_file, chunk_size_mb=1e3):
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Convert chunk size to bytes
    chunk_size = chunk_size_mb * 1024 * 1024

    # Initialize counters
    file_number = 1
    current_size = 0
    current_file = None
    with open(input_file, "rb") as infile:
        for line in infile:
            # Open new file if needed
            if current_file is None:
                output_path = os.path.join(output_dir, f"part_{file_number}.ttl")
                current_file = open(output_path, "wb")
                current_size = 0

            # Write line to current file
            line = convert_blank_nodes_to_uris(line.decode("utf-8"))
            line = convert_predicate_to_uri(line, get_mapping_dict(mapping_file))
            line = line.encode("utf-8")
            current_file.write(line)
            current_size += len(line)

            # Check if current file size exceeds chunk_size
            if current_size >= chunk_size:
                current_file.close()
                current_file = None
                file_number += 1

        # Close the last file if it's still open
        if current_file:
            current_file.close()


if __name__ == "__main__":
    BASE_DIR = Path(__file))(.resolve().parent.parent
    input_file = BASE_DIR/"data"/"rism"/"raw"/"rism-dump.ttl"  # Replace with your input file
    output_dir = BASE_DIR/"data"/"rism"/"split_output"  # Replace with your desired output directory
    mapping_file = BASE_DIR/"code"/"rism"/"ontology"/"mapping.json"  # Replace with your mapping file

    if len(sys.argv) > 1:
        DEFAULT_CHUNK_SIZE_MB = float(sys.argv[1])

    force_split_ttl(input_file, output_dir, mapping_file, DEFAULT_CHUNK_SIZE_MB)
