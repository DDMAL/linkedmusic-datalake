"""
Script to extract relation types from MusicBrainz JSONL files.
This script reads JSONL files from a specified input directory, extracts relation types
and their corresponding target types, and saves the results in a structured JSON file.
The script will load existing relation types if available, and update them with new relations found in the JSONL files.
Each new relation is mapped to None, so that the required dictionary structure is already
present to map them to wikidata.
Homogeneous relations (same source and target type) are suffixed with the direction of the relation.
"""

import os
import json
import argparse
from pathlib import Path
from tqdm import tqdm


def parse_file(file_path, file_relations):
    """
    Parses a JSONL file to extract relation types and their target types.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        total_lines = sum(1 for _ in f)
        f.seek(0)
        for line in tqdm(
            f, total=total_lines, desc=f"Processing {file_path.stem}.jsonl"
        ):
            data = json.loads(line)
            for relation in data.get("relations", []):
                if (relation_type := relation.get("type")) and (
                    target_type := relation.get("target-type").replace("_", "-")
                ) != "url":
                    if file.stem == target_type:
                        relation_type += f"_{relation["direction"]}"
                    if target_type not in file_relations:
                        file_relations[target_type] = {}
                    if relation_type not in file_relations[target_type]:
                        file_relations[target_type][relation_type] = None
    return file_relations


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract relation types from MusicBrainz JSONL files."
    )
    parser.add_argument(
        "--input_folder",
        type=str,
        default="../../data/musicbrainz/raw/extracted_jsonl/mbdump/",
        help="Path to the input directory containing JSONL files.",
    )
    parser.add_argument(
        "--output_folder",
        type=str,
        default="./rdf_conversion_config/",
        help="Path to the output directory for saving relation types.",
    )

    args = parser.parse_args()

    INPUT_PATH = args.input_folder
    OUTPUT_PATH = args.output_folder

    input_dir = Path(INPUT_PATH)
    if not input_dir.exists() or not input_dir.is_dir():
        raise FileNotFoundError(f"The input directory {INPUT_PATH} does not exist.")

    os.makedirs(OUTPUT_PATH, exist_ok=True)

    # Initialize relation types dictionary if it exists
    relation_types = {}
    rel_file = Path(OUTPUT_PATH) / "relations.json"
    if rel_file.exists() and rel_file.is_file():
        with open(rel_file, "r", encoding="utf-8") as fi:
            relation_types = json.load(fi)

    for file in input_dir.glob("*.jsonl"):
        relation_types[file.stem] = parse_file(file, relation_types.get(file.stem, {}))

    with open(os.path.join(OUTPUT_PATH, "relations.json"), "w", encoding="utf-8") as fi:
        json.dump(relation_types, fi, indent=4)
