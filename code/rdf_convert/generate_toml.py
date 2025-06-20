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
    python generate_toml.py --input path/to/reconciled/csvs --output rdf_config.toml
    python generate_toml.py --update existing_config.toml
"""

import argparse
from pathlib import Path
import logging
import pandas as pd
# tomli reads TOML files, tomli_w writes TOML files
import tomli
import tomli_w


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def deep_merge(old_dict, new_dict):
    """
    Merge old TOML into new TOML, any non-null value from the old TOML will overwrite or be added.

    Args:
        old_toml (dict): The original TOML data.
        new_toml (dict): The new TOML data to merge into.

    Returns:
        dict: The merged TOML data.
    """
    # Create a deep copy of new_toml to avoid modifying the original
    combined_toml = {k: v.copy() for k, v in new_dict.items()}
    for table, fields in old_dict.items():
        if table not in combined_toml:
            combined_toml[table] = {}
        for field, value in fields.items():
            if value != "":
                combined_toml[table][field] = value
    return combined_toml


def create_toml(input_folder: Path):
    """
    Generate a TOML configuration dictionary from the structure of CSV files in the input folder.

    Args:
        input_folder (Path): Path to the folder containing CSV files.
    Returns:
        dict: The TOML data as a dictionary.
    """
    # === Search input_folder for CSV files ===
    if not input_folder.is_dir():
        raise ValueError(f"Error: '{input_folder}' is not a valid directory.")
    csv_files = list(input_folder.glob("*.csv"))
    if not csv_files:
        raise ValueError(f"Error: No CSV file found in '{input_folder}'.")
    # === Process CSV files ===
    logger.info("Processing CSV files in '%s':", input_folder)
    csv_tables = {}
    for csv_file in sorted(csv_files):
        try:
            df = pd.read_csv(csv_file)
            if df.empty:
                logger.warning(
                    "Could not process '%s' because it is empty.", csv_file.name
                )
                continue
            table_name = csv_file.stem  # Use file name without extension
            csv_tables[table_name] = {
                # Each table must have a PRIMARY_KEY field
                "PRIMARY_KEY": df.columns[0],
                **{col: "" for col in df.columns},
            }
            logger.info("Processed '%s' - %d columns", csv_file.name, len(df.columns))
        except Exception as e:
            logger.warning("Could not process '%s': %s", csv_file.name, e)
            continue
    if not csv_tables:
        raise ValueError(
            f"Error: no valid CSV file can be processed in {input_folder}."
        )
    # === Prepare the default TOML tables ===
    # Find the relative path to the input folder from the base path
    script_dir = Path(__file__).parent.resolve()
    rel_path = input_folder.resolve().relative_to(script_dir)
    general_headers = {
        "name": "",
        "csv_folder": rel_path.as_posix(),
        "rdf_output_folder": "",
        "test_mode": False,
    }
    namespaces = {
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
        "xsd": "http://www.w3.org/2001/XMLSchema#",
        "wd": "http://www.wikidata.org/entity/",
        "wdt": "http://www.wikidata.org/prop/direct/",
    }
    toml_dict = {"general": general_headers, "namespaces": namespaces, **csv_tables}
    return toml_dict


def update_toml(toml_path: Path):
    """
    Update an existing TOML file by merging in new tables/fields from the current CSV files.
    The input folder is determined from the [general][csv_folder] field in the TOML file.

    Args:
        toml_path (Path): Path to the TOML file to update.
    """
    if not toml_path.exists():
        raise FileNotFoundError(f"Error: '{toml_path}' does not exist.")
    try:
        with open(toml_path, "rb") as fi:
            existing_toml = tomli.load(fi)
    except Exception as e:
        raise RuntimeError(f"Error reading TOML file: {e}") from e
    # === Finding the path to the input folder ===
    try:
        rel_csv_path = existing_toml["general"]["csv_folder"]
    except KeyError:
        raise ValueError("Error: 'csv_folder' is not defined in the TOML file.") from e
    script_path = Path(__file__).parent.resolve()
    csv_path = (script_path / rel_csv_path).resolve()
    logger.info("[UPDATE] Using csv_folder from TOML: %s", csv_path)
    # === Create a new TOML from the CSV files in the input folder ===
    new_toml = create_toml(csv_path)
    updated_toml = deep_merge(existing_toml, new_toml)
    with open(toml_path, "wb") as fi:
        tomli_w.dump(updated_toml, fi)
    logger.info(40 * "-")
    logger.info("\nSuccessfully updated '%s'", toml_path)


def main():
    parser = argparse.ArgumentParser(
        description="Generate TOML template from CSV files."
    )
    parser.add_argument(
        "--input",
        metavar="CSV_PATH",
        type=Path,
        help="Path to folder containing CSV files",
    )
    parser.add_argument(
        "--output",
        type=Path,
        metavar="TOML_PATH",
        default="rdf_config.toml",
        help="Path to the output TOML file. Default: 'rdf_config.toml'",
    )
    parser.add_argument(
        "--update",
        metavar="EXISTING_TOML_PATH",
        type=Path,
        help="Path to an existing TOML file to update; input folder is taken from its [general][csv_folder].",
    )
    args = parser.parse_args()
    if args.update:
        update_toml(Path(args.update))
    elif args.input and args.output:
        # === Ensure that output does not overwrite an existing file ===
        output_path = args.output
        if output_path.exists():
            raise FileExistsError(f"Error: '{output_path}' already exists.")
        # === Create TOML data from the input folder ===
        toml_data = create_toml(Path(args.input))
        # === Write TOML data to file ===
        logger.info("Finish processing. Saving configuration to '%s'", output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            tomli_w.dump(toml_data, f)
        logger.info(40 * "-")
        logger.info("\n Configuration saved to '%s'", output_path)
    else:
        parser.error(
            "You must specify --update or --input. Optionally, you can specify --output."
        )


if __name__ == "__main__":
    main()
