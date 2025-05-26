"""
Script to extract the 'type' field from MusicBrainz JSON data files.
This script processes each JSON file in the specified input folder, extracts unique entity types,
and saves them to a CSV file in the specified output folder, creating a separate file for each entity type,
and creating the output folder if it does not exist.
"""

import json
import sys
import argparse
from pathlib import Path
import pandas as pd
from tqdm import tqdm

# Set to True if you want to reprocess entity types that are already present in the output folder
REPROCESSING = False

# Entity types to ignore because they don't have types
IGNORE_TYPES = [
    "recording",
    "release-group",
    "release",
]


def main(args):
    """Main function to extract the type field from MusicBrainz JSON data."""
    # Parse command line arguments
    input_file = args.input_file
    entity_type = Path(args.input_file).stem  # Get entity type from filename

    # Configure output directory
    output_folder = Path(args.output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)
    output_file = output_folder / f"{entity_type}_types.csv"

    types = set()

    with open(input_file, "r", encoding="utf-8") as file:
        total_line = sum(1 for _ in file)
        file.seek(0)
        for line in tqdm(file, total=total_line, desc=f"Processing {entity_type}"):
            try:
                data = json.loads(line)
                if "type" in data and data["type"]:
                    types.add(data["type"])
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON in file {input_file}: {e}")
                continue

    df = pd.DataFrame({"type": list(types)})
    with open(output_file, "w", encoding="utf-8") as out_file:
        df.to_csv(out_file, index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract the type field from MusicBrainz JSON data."
    )
    parser.add_argument(
        "--input_folder",
        default="../../data/musicbrainz/raw/extracted_jsonl/mbdump",
        help="Path to the folder containing line-delimited MusicBrainz JSON files.",
    )
    parser.add_argument(
        "--output_folder",
        default="../../data/musicbrainz/raw/types/",
        help="Directory where the output CSV files will be saved.",
    )
    args = parser.parse_args()

    input_folder = Path(args.input_folder)
    if not input_folder.is_dir():
        print(f"{input_folder} is not a valid directory.")
        sys.exit(1)

    bad_files = []
    if Path(args.output_folder).exists() and not REPROCESSING:
        output_folder = Path(args.output_folder)
        for file in output_folder.iterdir():
            if file.is_file():
                bad_files.append(file.stem)

    for input_file in input_folder.iterdir():
        if str(input_file).endswith(".DS_Store"):
            continue
        if input_file.stem in bad_files and not REPROCESSING:
            print(f"Skipping {input_file} as it is already processed.")
            continue
        if input_file.is_file():
            print(f"Processing file: {input_file}")
            # Create a new namespace for the current file using its stem as entity type
            sub_args = argparse.Namespace(
                input_file=str(input_file), output_folder=args.output_folder
            )
            main(sub_args)
