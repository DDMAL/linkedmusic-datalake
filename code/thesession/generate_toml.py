#!/usr/bin/env python3
"""
RDF Configuration Generator

This script generates an `rdf_config.toml` file (default name) based on a
folder of reconciled CSV files.

The generated TOML file will list each CSV file and its column headers.
By default, all headers are paired with empty string values. These values
must be manually filled in to define how the dataset should be converted to
RDF.

Alternatively, the script can update an existing TOML file by scanning
the new CSV structure in the input folder. Only fields with empty
values will be overwritten. No comment is preserved.

Usage:
    python generate_toml.py --input_folder path/to/reconciled/csvs --output rdf_config.toml
    python generate_toml.py --update existing_config.toml
"""


import argparse
import sys
from pathlib import Path
import pandas as pd

# tomli reads TOML files, tomli_w writes TOML files
import tomli
import tomli_w
import asyncio
import aiohttp
from add_labels import add_labels
from wikidata_utilities import WikidataAPIClient


def validate_input_folder(input_folder):
    """
    Validate that the input folder exists and contains at least one CSV file.

    Args:
        input_folder (Path): Path to the directory to check.

    Returns:
        list[Path]: List of CSV file paths within the directory.

    Raises:
        SystemExit: If the folder does not exist or contains no CSV files.
    """
    if not input_folder.is_dir():
        print(f"Error: '{input_folder}' is not a valid directory.")
        sys.exit(1)
    csv_files = list(input_folder.glob("*.csv"))
    if not csv_files:
        print(f"Error: No CSV file found in '{input_folder}'.")
        sys.exit(1)
    return csv_files


def extract_csv_headers(csv_files):
    """
    Extract column headers from a list of CSV files for TOML template generation.

    Args:
        csv_files (list[Path]): List of CSV file paths.

    Returns:
        dict: A dictionary mapping file names to column templates.
    """
    toml_tables = {}
    for csv_file in sorted(csv_files):
        try:
            df = pd.read_csv(csv_file)
            if df.empty:
                print(
                    f"Warning: Could not process '{csv_file.name}' because it is empty."
                )
            else:
                toml_tables[csv_file.name] = {col: "" for col in df.columns}
                print(f"Processed '{csv_file.name}' - {len(df.columns)} columns")
        except Exception as e:
            print(f"Warning: Could not process '{csv_file.name}': {e}")
    return toml_tables


def deep_merge(old_toml, new_toml):
    """
    Merge old TOML into new TOML, any non-null value from the old TOML will overwrite or be added.

    Args:
        old_toml (dict): The original TOML data.
        new_toml (dict): The new TOML data to merge into.

    Returns:
        dict: The merged TOML data.
    """
    # We must create a deep copy of new_toml to avoid modifying the original
    merged_toml = {k: v.copy() for k, v in new_toml.items()}
    for table, fields in old_toml.items():
        if table not in merged_toml:
            merged_toml[table] = {}
        for field, value in fields.items():
            if value != "":
                merged_toml[table][field] = value
    return merged_toml


def make_template(input_folder):
    """
    Generate a TOML configuration dictionary from the structure of CSV files in the input folder.

    Args:
        input_folder (Path): Path to the folder containing CSV files.
    Returns:
        dict: The TOML data as a dictionary.
    """
    csv_files = validate_input_folder(input_folder)
    general_headers = {
        "name": "Name of the Dataset [required]",
        "csv_path": input_folder.as_posix(),
        "rdf_output_path": "output/path/for/rdf/files [required]",
    }
    namespaces = {
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
        "xs": "http://www.w3.org/2001/XMLSchema",
        "wd": "http://www.wikidata.org/entity/",
        "wdt": "http://www.wikidata.org/prop/direct/",
    }
    toml_dict = {"general": general_headers, "namespaces": namespaces}
    csv_tables = extract_csv_headers(csv_files)
    if not csv_tables:
        print("Error: No TOML file was generated: no valid CSV files were processed.")
        sys.exit(1)
    toml_dict.update(csv_tables)
    return toml_dict


def update_toml(toml_path):
    """
    Update an existing TOML file by merging in new tables/fields from the current CSV files.
    The input folder is determined from the [general][csv_path] field in the TOML file.

    Args:
        toml_path (Path): Path to the TOML file to update.
    """
    if not toml_path.exists():
        print(f"Error: '{toml_path}' does not exist.")
        sys.exit(1)
    with open(toml_path, "rb") as fi:
        existing_toml = tomli.load(fi)
        try:
            data_path = existing_toml["general"]["csv_path"]
            input_folder = Path(data_path)
            print(f"[UPDATE] Using csv_path from TOML: {input_folder}")
        except KeyError as e:
            print(f"Error: Could not find [general][csv_path] in TOML: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Error reading TOML file: {e}")
            sys.exit(1)
    updated_toml = make_template(input_folder)
    merged = deep_merge(existing_toml, updated_toml)
    with open(toml_path, "wb") as fi:
        tomli_w.dump(merged, fi)
    print(40 * "-")
    print(f"\nUpdated '{toml_path}' with {len(updated_toml) - 2} tables.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate TOML templates from CSV files."
    )
    parser.add_argument(
        "--input_folder", type=Path, help="Path to folder containing CSV files"
    )
    parser.add_argument(
        "--update",
        metavar="TOML_PATH",
        type=Path,
        help="Update existing TOML file using its general.data_path as input folder",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default="rdf_config.toml",
        help="Output TOML file (default: rdf_config.toml)",
    )
    parser.add_argument(
        "--label",
        type=Path,
        help="Add labels as comment to all Wikidata ID found in the TOML file",
    )
    args = parser.parse_args()

    if args.update:
        update_toml(args.update)
    elif args.label:
        async def add_toml_labels(config_file: Path):
            """Add Wikidata labels as comments to all QIDs found in the TOML file."""
            async with aiohttp.ClientSession() as session:
                client = WikidataAPIClient(session=session)
                # add_labels can write to another file, but we want to overwrite the original
                await add_labels(config_file, config_file, client)
        asyncio.run(add_toml_labels(args.label))
    elif args.input_folder:
        output_path = args.output
        if output_path.exists():
            print(f"Error: '{output_path}' already exists.")
            sys.exit(1)
        toml_data = make_template(args.input_folder)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            tomli_w.dump(toml_data, f)
        print(40 * "-")
        print(f"\nGenerated '{output_path}'")
    else:
        parser.error("You must specify --update, --label, or --input_folder.")
