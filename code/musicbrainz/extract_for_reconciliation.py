"""
This script will extract all the data that needs to be reconciled from MusicBrainz JSON data files.
The script will ignore the entity types in the `IGNORE_TYPES` list,
which are known to not have types, and will create the output folder if it does not exist.
It will process all JSON files in the specified input folder,
skipping files that have already been processed
unless the `REPROCESSING` flag is set to True.

The 'type' field is extracted for each entity type, and are saved to a CSV file in the
specified output folder with the name `f"{entity_type}_types.csv"`.

Keys are also extracted from the `attributes` field that are of type "Key".
They are saved to a separate CSV file named `keys.csv`.
Normally, only the `work` entity type has keys, but this script is designed to be flexible.

Genders are also extracted from the `gender` field, if present, and saved to a separate CSV file named `genders.csv`.
Normally, only the `artist` entity type has a gender, but this script is designed to be flexible.

Languages are extracted from the `languages` field, if present, and saved to a separate CSV file named `languages.csv`.
The languages are extracted as ISO 639-3 codes and their full names are added in a separate column
using the `pycountry` library.
Normally, only the `work` entity type has languages, but this script is designed to be flexible.

Packagings are extracted from the `packaging` field, if present, and saved to a separate CSV file named `packagings.csv`.
Normally, only the `release` entity type has packagings, but this script is designed to be flexible.

Statuses are extracted from the `status` field, if present, and saved to a separate CSV file named `statuses.csv`.
Normally, only the `release` entity type has statuses, but this script is designed to be flexible.
"""

import json
import sys
import argparse
from pathlib import Path
import pandas as pd
from tqdm import tqdm
from pycountry import languages as langs

# Set to True if you want to reprocess entity types that are already present in the output folder
REPROCESSING = False

# Entity types to ignore because they don't have any fields we want to extract
IGNORE_TYPES = [
    "recording",
]

# Entity types that will be processed but that do not have type fields
PROCESS_NO_TYPES = [
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

    keys = set()
    types = set()
    genders = set()
    languages = set()
    packagings = set()
    statuses = set()

    with open(input_file, "r", encoding="utf-8") as f:
        total_line = sum(1 for _ in f)
        f.seek(0)
        for line in tqdm(f, total=total_line, desc=f"Processing {entity_type}"):
            try:
                data = json.loads(line)
                if t := data.get("type"):
                    types.add(t)
                if t := data.get("primary-type"):
                    types.add(t)
                for t in data.get("secondary-types", []):
                    types.add(t)
                for attr in data.get("attributes", []):
                    if attr.get("type") == "Key" and (key := attr.get("value")):
                        keys.add(key)
                if g := data.get("gender"):
                    genders.add(g)
                for lang in data.get("languages", []):
                    languages.add(lang)
                if p := data.get("packaging"):
                    packagings.add(p)
                if s := data.get("status"):
                    statuses.add(s)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON in file {input_file}: {e}")
                continue

    if entity_type in PROCESS_NO_TYPES:
        df = pd.DataFrame({"type": list(types)})
        with open(output_file, "w", encoding="utf-8") as out_file:
            df.to_csv(out_file, index=False)

    if keys:
        keys_file = output_folder / "keys.csv"
        keys_df = pd.DataFrame({"key": list(keys)})
        with open(keys_file, "w", encoding="utf-8") as keys_out_file:
            keys_df.to_csv(keys_out_file, index=False)

    if genders:
        genders_file = output_folder / "genders.csv"
        genders_df = pd.DataFrame({"gender": list(genders)})
        with open(genders_file, "w", encoding="utf-8") as genders_out_file:
            genders_df.to_csv(genders_out_file, index=False)

    if languages:
        languages_file = output_folder / "languages.csv"
        languages_df = pd.DataFrame({"language": list(languages)})
        languages_df["full_language"] = languages_df["language"].apply(
            lambda x: langs.get(alpha_3=x).name if langs.get(alpha_3=x) else x
        )
        with open(languages_file, "w", encoding="utf-8") as languages_out_file:
            languages_df.to_csv(languages_out_file, index=False)

    if packagings:
        packagings_file = output_folder / "packagings.csv"
        packagings_df = pd.DataFrame({"packaging": list(packagings)})
        with open(packagings_file, "w", encoding="utf-8") as packagings_out_file:
            packagings_df.to_csv(packagings_out_file, index=False)

    if statuses:
        statuses_file = output_folder / "statuses.csv"
        statuses_df = pd.DataFrame({"status": list(statuses)})
        with open(statuses_file, "w", encoding="utf-8") as statuses_out_file:
            statuses_df.to_csv(statuses_out_file, index=False)


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
        default="../../data/musicbrainz/raw/unreconciled/",
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
                # Ignore the _types suffix
                bad_files.append(
                    file.stem[:-6] if file.stem.endswith("_types") else file.stem
                )

    if "packagings" in bad_files and "statuses" in bad_files:
        bad_files.append("release")  # Special case for release entity type

    for input_file in input_folder.iterdir():
        if str(input_file).endswith(".DS_Store"):
            continue
        if input_file.stem in bad_files and not REPROCESSING:
            print(f"Skipping {input_file} as it is already processed.")
            continue
        if input_file.stem in IGNORE_TYPES:
            print(f"Skipping {input_file} as it is in the ignore list.")
            continue
        if input_file.is_file():
            print(f"Processing file: {input_file}")
            # Create a new namespace for the current file using its stem as entity type
            sub_args = argparse.Namespace(
                input_file=str(input_file), output_folder=args.output_folder
            )
            main(sub_args)
