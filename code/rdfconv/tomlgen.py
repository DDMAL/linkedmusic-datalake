"""
RDF Configuration Generator

This script generates a TOML configuration file (default: `rdf_config.toml`) based on a
folder of reconciled CSV files, for use with the general RDF conversion workflow.

The generated TOML file will include each CSV file in the folder and its column headers. By
default, all headers are paired with empty string values, which must be manually filled in to
define how the dataset should be converted to RDF.

Alternatively, the script can update an existing TOML file by scanning the current CSV
structure in the input folder. Comments are
not preserved during updating.

Note:

    This script must be run with the current working directory set to `/code`.
Usage:

    python -m rdfconv.tomlgen <path to csv folder> --output <config output path>
    python -m rdfconv.tomlgen --update <config_path>

See the user guide at `doc/rdf_conversion/using_rdfconv_script.md` for detailed instructions
and workflow context.
"""

import argparse
from pathlib import Path
import os
import logging
import pandas as pd

# tomli reads TOML files, tomli_w writes TOML files
import tomli
import tomli_w


logger = logging.getLogger(__name__)
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def diff_nested_keys(old_dict, new_dict):
    """
    Compare two nested dictionaries and return a summary of added and removed keys at each
    level.

    Used to log changes when updating a TOML configuration file to match the current CSV
    structure.

    Args:
        old_dict (dict): The original dictionary (e.g., existing TOML config).
        new_dict (dict): The updated dictionary (e.g., new TOML config from CSVs).

    Returns:
        dict: A dictionary summarizing the added and removed keys for each top-level key.
    """
    diff = {}

    for key in new_dict:
        if key not in old_dict:
            diff.setdefault(key, {})["added"] = new_dict[key]
        else:
            inner_added = {
                k: v for k, v in new_dict[key].items() if k not in old_dict[key]
            }
            if inner_added:
                diff.setdefault(key, {})["added"] = inner_added

    for key in old_dict:
        if key not in new_dict:
            diff.setdefault(key, {})["removed"] = old_dict[key]
        else:
            inner_removed = {
                k: v for k, v in old_dict[key].items() if k not in new_dict[key]
            }
            if inner_removed:
                diff.setdefault(key, {})["removed"] = inner_removed

    return diff


def log_toml_diff(diff_dict):
    """
    Generate a log-style summary of differences between two TOML configurations.

    This function formats the added and removed keys from a nested dictionary diff
    (as produced by `diff_nested_keys`) into a readable string for logging purposes.

    Args:
        diff_dict (dict): The dictionary of differences as produced by diff_nested_keys.

    Returns:
        str: A formatted string representing the changes in TOML log style.
    """
    lines = []
    for table, diff in diff_dict.items():
        lines.append(f"[{table}]")
        removed_fields = diff.get("removed", {})
        for k, v in removed_fields.items():
            if isinstance(v, dict):
                inner = ", ".join(f'{ik} = "{iv}"' for ik, iv in v.items())
                lines.append(f"-{k} = {{ {inner} }}")
            else:
                lines.append(f'-{k} = "{v}"')
        added_fields = diff.get("added", {})
        for k, v in added_fields.items():
            if isinstance(v, dict):
                inner = ", ".join(f'{ik} = "{iv}"' for ik, iv in v.items())
                lines.append(f"+{k} = {{ {inner} }}")
            else:
                lines.append(f'+{k} = "{v}"')
        lines.append("")  # blank line after each table
    return "\n".join(lines)


def create_toml(input_folder: Path):
    """
    Generate a TOML configuration dictionary from CSV files in the input
    folder.

    Two default tables, `general` and `namespaces`, are included in the configuration by default.

    Each CSV file in the folder becomes a TOML table, with each column header
    paired with empty string values. The first column is set as the PRIMARY_KEY for
    each table.

    Args:
        input_folder (Path): Path to the folder containing reconciled CSV files.

    Returns:
        dict: The TOML data as a dictionary, with each table representing a CSV file and its
        columns.

    Raises:
        ValueError: If the input folder is invalid or contains no valid CSV files.
    """
    # === Search input_folder for CSV files ===
    if not input_folder.is_dir():
        raise ValueError(f"'{input_folder}' is not a valid directory.")
    csv_files = list(input_folder.glob("*.csv"))
    if not csv_files:
        raise ValueError(f"No CSV file found in '{input_folder}'.")
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
        raise ValueError(f"No valid CSV file can be processed in {input_folder}.")
    # === Prepare the default TOML tables ===
    # Find the relative path to the input folder from the base path
    script_dir = Path(__file__).parent.resolve()
    rel_path = Path(os.path.relpath(input_folder.resolve(), script_dir))
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
    Update an existing TOML configuration file to match the current structure of the CSV files
    in the specified folder.

    The input folder is determined from the [general][csv_folder] field in the TOML file. New
    columns are added, and outdated columns are removed. Existing values are preserved where
    possible. Changes are logged to standard output.

    Args:
        toml_path (Path): Path to the TOML file to update.

    Raises:
        FileNotFoundError: If the TOML file does not exist.
        RuntimeError: If the TOML file cannot be read.
        ValueError: If the TOML file is missing required fields or no valid CSV files are
        found.
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
    except KeyError as e:
        raise ValueError("'csv_folder' is not defined in the TOML file.") from e
    script_path = Path(__file__).parent.resolve()
    csv_path = (script_path / rel_csv_path).resolve()
    logger.info("[UPDATE] Using csv_folder from TOML: %s", csv_path)
    # === Create a new TOML from the CSV files in the input folder ===
    new_toml = create_toml(csv_path)
    # === Insert the existing general and namespaces headers ===
    new_toml["general"] = existing_toml.get("general", {})
    new_toml["namespaces"] = existing_toml.get("namespaces", {})
    # === Insert values from existing TOML for identical columns ===
    for csv_table, csv_fields in new_toml.items():
        if csv_table in ["general", "namespaces"]:
            continue
        if csv_table in existing_toml:
            existing_table = existing_toml.get(csv_table, {})
            for field in csv_fields:
                new_toml[csv_table][field] = existing_table.get(field, "")
    diff = diff_nested_keys(existing_toml, new_toml)
    logger.info(40 * "-")
    if diff:
        logger.info("\n")
        logger.info("CHANGES")
        logger.info("\n")
        for line in log_toml_diff(diff).splitlines():
            logger.info(line)
    else:
        logger.info("No changes made. The TOML file is already up-to-date.")
        return
    with open(toml_path, "wb") as fi:
        tomli_w.dump(new_toml, fi)
    logger.info(40 * "-")
    logger.info("Successfully updated '%s'", toml_path)


def main():
    """
    Entry point for the TOML configuration generator and updater.

    Parses command-line arguments and executes the appropriate TOML generation or update
    operation. See the user guide for workflow context and usage examples.

    Raises:
        FileExistsError: If the output TOML file already exists and would be overwritten.
        SystemExit: If required arguments are missing or invalid.
    """
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
        help=(
            "Path to an existing TOML file to update; input folder is taken from its "
            "[general][csv_folder]."
        ),
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
        logger.info("Configuration saved to '%s'", output_path)
    else:
        parser.error(
            "You must specify --update or --input. Optionally, you can specify --output."
        )


if __name__ == "__main__":
    main()
