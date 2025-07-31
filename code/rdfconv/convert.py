"""
General CSV to RDF converter driven by a TOML configuration file.

This script reads a TOML RDF configuration file (see user and syntax guides in
`doc/rdf_conversion/`) and processes all CSVs listed in the config, generating RDF triples
according to the specified ontology and mappings. The output is a Turtle (TTL) file suitable
for loading into a triple store.

- The config file must be generated and completed as described in the documentation.
"""

import argparse
import time
from pathlib import Path
from typing import Union, Any
import logging
from wikidata_utils import extract_wd_id
import pandas as pd
import tomli
from tqdm import tqdm
from rdflib import Graph, URIRef, Literal, Namespace, XSD, RDF
from isodate.isoerror import ISO8601Error
from isodate.isodates import parse_date
from isodate.isodatetime import parse_datetime

# === Setup Logger ===
logger = logging.getLogger(__name__)
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

# === Suppress rdflib Warnings ===
logging.getLogger("rdflib").setLevel(logging.ERROR)


def to_rdf_node(
    val: str,
    namespaces: dict,
    lang: str | None = None,
    datatype: str | None = None,
    prefix: str | None = None,
) -> Union[URIRef, Literal, None]:
    """
    Convert a value to the appropriate RDF node (URIRef or Literal) for RDF triple creation.

    - Returns a URIRef if the value is a Wikidata ID, a full URI, or a value with a specified
      prefix.
    - Returns None if the value is empty or NaN.
    - Otherwise, returns a Literal, optionally with language or datatype.
    - Handles special logic for date and datetime datatypes.

    Args:
        val (str): The value to convert.
        namespaces (dict): Mapping of prefixes to namespace URIs from the config.
        lang (str, optional): Language code for the literal.
        datatype (str, optional): Datatype URI or prefixed datatype.
        prefix (str, optional): Namespace prefix to expand the value to a full URI.

    Returns:
        Union[URIRef, Literal, None]: The RDF node representation of the value.
    """
    if not isinstance(val, str) or val == "":
        return None
    qid = extract_wd_id(val)
    if qid:
        return URIRef(f"{namespaces['wd']}{qid}")
    if val.startswith("http") and datatype not in ("xsd:anyURI", XSD.anyURI):
        return URIRef(val)
    # A prefix can be specified to expand the value to a full URI
    if prefix:
        return URIRef(f"{namespaces.get(prefix)}{val}")
    # Expand datatype if it is prefixed
    if datatype is not None and ":" in datatype:
        prefix, body = datatype.split(":", 1)
        ns_uri = namespaces.get(prefix)
        if ns_uri:
            datatype = f"{ns_uri}{body}"
    # Special logic for handling date datatype
    if datatype == XSD.date:
        try:
            # Validate the date string, and catch any exception that might occur
            return Literal(parse_date(val), datatype=XSD.date)
        except (ISO8601Error, ValueError):
            return Literal(val)  # Fallback to a plain literal if conversion fails
    # Special logic for handling datetime datatype
    if datatype == XSD.dateTime:
        try:
            # Validate the datetime string, and catch any exception that might occur
            return Literal(parse_datetime(val), datatype=XSD.dateTime)
        except (ISO8601Error, ValueError):
            return Literal(val)  # Fallback to a plain literal if conversion fails
    return Literal(str(val), lang=lang, datatype=datatype)


def to_predicate(val: str, namespaces: dict) -> URIRef:
    """
    Convert a predicate string to a URIRef.

    - Any predicate starting with "http" is treated as a full URI.
    - Expands Wikidata property IDs and prefixed URIs to full URIs.
    - Raises ValueError if the value cannot be resolved to a valid predicate URI.

    Args:
        val (str): The property string (e.g., Wikidata PID, prefixed URI).
        namespaces (dict): Mapping of prefixes to namespace URIs from the config.

    Returns:
        URIRef: The resolved predicate URI.

    Raises:
        ValueError: If the property string is invalid or cannot be resolved.
    """
    # The function extracts both QID and PID
    wiki_id = extract_wd_id(val)
    if wiki_id and wiki_id.startswith("P"):
        return URIRef(f"{namespaces['wdt']}{wiki_id}")
    elif val.startswith("http"):
        return URIRef(val)
    else:
        for prefix, prefix_uri in namespaces.items():
            if val.startswith(prefix + ":"):
                # If the value starts with a prefix, expand to full URI
                return URIRef(f"{prefix_uri}{val.split(':', 1)[1]}")
        raise ValueError(
            f"Invalid property value: {val}. Expected a Wikidata ID or a valid prefixed URI."
        )


def rdf_process_predicates(
    toml_config: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """
    Valide RDF config TOML and normalize predicate + RDF classes.

    - Validates the structure of each column definition and filters out incomplete
      entries.
    - Resolves predicate strings and RDF classes (i.e. defined by `type` keyword) into full
      `rdflib.URIRef` objects.

    Behavior:
        - Skips the "general" and "namespaces" sections without modification.
        - Ensures each data table has a valid PRIMARY_KEY and that it refers to an existing
          column.
        - Converts simple string predicates into URIRef.
        - Validates and transforms complex column definitions (inline dictionaries) by:
            - Converting the 'pred' key into a URIRef.
            - Expanding 'type' prefixed values into full URIs.
            - Ensuring that 'datatype' and 'lang' are not both specified.
            - Removing any empty fields from the configuration.
        - Ignores entirely empty columns or configurations.

    Args:
        toml_config (dict[str, dict[str, Any]]): The raw TOML configuration as parsed from
            file.

    Returns:
        dict[str, dict[str, Any]]: A cleaned and normalized configuration dictionary with
            RDF-ready values.

    Raises:
        ValueError: If required keys are missing, unknown config keys are found,
            or field types/values are invalid.
    """

    ns = toml_config["namespaces"]
    new_config = {}

    for file, file_schema in toml_config.items():
        # == Verify that each file has a PRIMARY_KEY ==
        if file in ("general", "namespaces"):
            new_config[file] = file_schema
            continue
        primary_key = file_schema.get("PRIMARY_KEY")
        if not primary_key:
            raise ValueError(f"Config [{file}]: missing 'PRIMARY_KEY' value.")
        if primary_key not in file_schema:
            raise ValueError(
                f"Config [{file}]: 'PRIMARY_KEY' does not point to an existing column."
            )

        new_file_schema = {}
        for col, col_schema in file_schema.items():
            if col == "PRIMARY_KEY":
                new_file_schema["PRIMARY_KEY"] = col_schema  # Keep PRIMARY_KEY as is
                continue

            if isinstance(col_schema, str):
                # Skip empty fields
                if not col_schema:
                    continue
                # Transform predicate to URIRef
                new_file_schema[col] = to_predicate(col_schema, ns)
            elif isinstance(col_schema, dict):
                # Complex config value
                for key, val in col_schema.items():
                    if key not in (
                        "pred",
                        "datatype",
                        "lang",
                        "subj",
                        "if",
                        "prefix",
                        "type",
                    ):
                        raise ValueError(
                            f"Config[{file}]: invalid key '{key}' in column '{col}'"
                        )
                    if not isinstance(val, str):
                        raise ValueError(
                            f"Config[{file}]: '{key}' in column '{col}' must a string value"
                        )
                # Verifying that datatype and lang are not both specified
                datatype = col_schema.get("datatype")
                lang = col_schema.get("lang")
                if datatype and lang:
                    raise ValueError(
                        f"Config[{file}]: cannot specify both datatype and lang for column '{col}'"
                    )
                new_col_schema = {k: v for k, v in col_schema.items() if v != ""}
                # Skip empty dict
                if not new_col_schema:
                    continue
                # Transform predicate to URIRef, if it exists
                if "type" in new_col_schema:
                    rdf_type = new_col_schema["type"]
                    if ":" in rdf_type:
                        prefix, body = rdf_type.split(":", 1)
                        ns_uri = ns.get(prefix)
                        if ns_uri:
                            new_col_schema["type"] = f"{ns_uri}{body}"
                if "pred" in new_col_schema:
                    new_col_schema["pred"] = to_predicate(new_col_schema["pred"], ns)
                new_file_schema[col] = new_col_schema
            else:
                raise ValueError(
                    f"Config[{file}]: invalid value type for column '{col}'. Expected a string or a dict, got {type(col_schema)}"
                )
        # Ensure that there is at least one other column besides PRIMARY_KEY
        if len(new_file_schema) > 1:
            new_config[file] = new_file_schema
    return new_config


def rdf_transform_csv(
    df: pd.DataFrame, col_mapping: dict[str, str | dict], ns: dict
) -> pd.DataFrame:
    """
    Transform values of a DataFrame to RDF nodes based on provided column mappings from the
    config.

    - Applies to_rdf_node for each value, using config info (predicate, datatype, lang,
      prefix, etc).
    - Handles both simple and complex column mappings as described in the config syntax
      guide.

    Args:
        df (pd.DataFrame): The input DataFrame loaded from a CSV file.
        col_mapping (dict): Mapping of column names to predicate or config dicts.
        ns (dict): Namespaces from the config.

    Returns:
        pd.DataFrame: The transformed DataFrame with values as RDF nodes.
    """
    cols_processed = set()
    subj_columns = []

    # Process columns based on property_columns
    for column, mapping in col_mapping.items():
        if column in cols_processed:
            continue
        if column == "PRIMARY_KEY":
            # mapping is itself a column name in the case of "PRIMARY_KEY"
            if not col_mapping.get(mapping):
                # Default processing for PRIMARY_KEY column
                df[mapping] = df[mapping].apply(lambda x: to_rdf_node(x, ns))
                cols_processed.add(mapping)
                continue
        elif isinstance(mapping, str) and mapping:
            # Processing all columns with a string value
            df[column] = df[column].apply(lambda x: to_rdf_node(x, ns))
            cols_processed.add(column)

        elif isinstance(mapping, dict) and mapping:
            # Processing all columns with an inline dict value
            df[column] = df[column].apply(
                lambda x, mapping=mapping: to_rdf_node(
                    x,
                    ns,
                    lang=mapping.get("lang"),
                    datatype=mapping.get("datatype"),
                    prefix=mapping.get("prefix"),
                )
            )
            cols_processed.add(column)

            if subj := mapping.get("subj"):
                # Columns acting as subjects need to be processed if not already
                subj_columns.append(subj)
        else:
            continue

    # Default process for columns only specified as subjects
    for column in subj_columns:
        if column not in cols_processed:
            df[column] = df[column].apply(lambda x: to_rdf_node(x, ns))
            cols_processed.add(column)
        else:
            continue
    return df


def fill_down_until_key(df: pd.DataFrame, primary_key: str) -> pd.DataFrame:
    """
    Fill down all columns in the DataFrame, but only until a non-empty value is encountered
    in the PRIMARY_KEY column.

    - Implements the fill-down logic required for OpenRefine record exports, as described in
      the user guide.
    - Each block of rows with the same PRIMARY_KEY is filled down from the last non-empty
      value.

    Args:
        df (pd.DataFrame): The input DataFrame.
        primary_key (str): The column name to use as the block marker for fill-down.

    Returns:
        pd.DataFrame: The DataFrame with fill-down applied.
    """
    df = df.copy()
    # Any value not None and not empty string becomes True
    mask = df[primary_key].notna() & (df[primary_key] != "")
    group = mask.cumsum()

    filled_df = df.groupby(group).ffill()
    # Restore original primary key column to avoid overwriting with filled values
    filled_df[primary_key] = df[primary_key]

    return filled_df


def build_rdf_graph(
    config: dict[str, dict],
) -> Graph:
    """
    Build an RDF graph from CSV files and a processed config dict.

    For each CSV listed in the config:
        - convert all values to RDF nodes (URIRef or Literal)
        - applies fill-down
        - generates RDF triples according to config mapping.
    - Handles both test mode and full conversion.
    - Adds rdf:type triples for columns with a 'type' key.
    - Add prefixes to column with `prefix` key

    Args:
        config (dict): The processed config dict with predicates/types resolved to RDF URIs
            and objects.

    Returns:
        Graph: The constructed RDFLib Graph containing all triples.

    Raises:
        ValueError: If required config fields are missing or if triple creation fails.
    """
    try:
        rdf_ns = config["namespaces"]
        rel_inp_dir = Path(config["general"]["csv_folder"])
    except KeyError as e:
        raise ValueError(f" {config} is missing required key: {e}") from e
    # === Initialize RDF Graph ===
    graph = Graph()
    # === Bind Namespaces ===
    for prefix, ns in rdf_ns.items():
        graph.bind(prefix, Namespace(ns))

    # === Resolve CSV Folder Path ===
    script_dir = Path(__file__).parent.resolve()
    csv_folder = (script_dir / rel_inp_dir).resolve()
    # === Check for Test Mode ===
    # If test_mode is set to True, only sample up to 20 rows per CSV
    test_mode = config["general"].get("test_mode")
    if test_mode is True:
        logger.info("Running in test mode — sampling up to 20 rows per CSV file.")
    # === Opening csv files ===
    for csv_name, csv_schema in config.items():
        # "general" and "namespaces" are not CSV files
        if csv_name in ("general", "namespaces"):
            continue
        # table names do not have ".csv" extension
        csv_file = (csv_folder / csv_name).with_suffix(".csv")
        if not csv_file.exists():
            logger.warning("'%s' not found. Skipping.", csv_file)
            continue
        try:
            df = pd.read_csv(
                csv_file,
                dtype=str,
                keep_default_na=False,
                na_values=[
                    "",  # Empty string
                    " ",  # Space
                    "NA",  # Capitalized NA
                    "N/A",  # Common spreadsheet notation
                    "na",  # lowercase
                    "n/a",  # lowercase
                    "-",  # Often used to indicate "no data"
                    "--",  # Sometimes double-dash
                    "None",  # Pythonic
                    "none",  # lowercase variant
                    "NULL",  # SQL style
                    "null",  # lowercase
                    "NaN",  # Python/NumPy/Pandas
                    "nan",  # lowercase
                    "?",  # Occasionally used for unknowns
                ],
            )
        except Exception as e:
            logger.error("Error reading '%s'. Skipping. %s", csv_file, e)
            continue
        if test_mode is True:
            df = df.sample(n=min(20, len(df)))
        logger.info("Processing %s...", csv_file.name)
        # === Convert entire csv to rdf node ===
        df = rdf_transform_csv(df, csv_schema, rdf_ns)
        # === Fill down records using PRIMARY_KEY as block marker ===
        primary_key = csv_schema["PRIMARY_KEY"]
        df = fill_down_until_key(df, primary_key)
        # === Make sure that Pandas does not store any NaN ===
        df = df.where(pd.notna(df), None)
        # === Iterate through all the rows of the CSV file ===
        for _, row in tqdm(df.iterrows(), total=len(df)):
            primary_node = row[primary_key]
            # == Process each column according to the config ==
            for col, col_value in csv_schema.items():
                if col == "PRIMARY_KEY":
                    continue
                object_node = row.get(col, None)
                # == No object value found ==
                if object_node is None:
                    continue
                # == Process String Mapping ==
                if isinstance(col_value, URIRef):
                    subject_node = primary_node
                    predicate = col_value
                # == Process Inline Dict Mapping ==
                elif isinstance(col_value, dict):
                    predicate = col_value.get("pred")
                    if subj_col := col_value.get("subj"):
                        subject_node = row.get(subj_col, None)
                    else:
                        # Use the value from "PRIMARY_KEY" column
                        subject_node = primary_node
                    if not eval(
                        col_value.get("if", "True"),
                        {"URIRef": URIRef, "Literal": Literal, "None": None},
                        {"subj": subject_node, "obj": object_node, "row": row},
                    ):
                        continue
                    rdf_type = col_value.get("type")
                    if rdf_type:
                        graph.add((object_node, RDF.type, URIRef(rdf_type)))
                else:
                    continue
                if subject_node and predicate and object_node:
                    try:
                        graph.add((subject_node, predicate, object_node))
                    except Exception as e:
                        raise ValueError(
                            f"Error adding triple ({subject_node}, {predicate}, {object_node}): defined by '{col}={col_value}'"
                        ) from e

    # dynamically add the number of triples as a attribute of graph
    return graph


def main():
    """
    Main entry point for the general RDF conversion script.

    - Parses command-line arguments and loads the TOML config file.
    - Processes the config and builds the RDF graph from all CSVs listed.
    - Serializes the graph to a TTL file at the specified output location.

    Raises:
        ValueError: If required config fields are missing or invalid.
    """
    # == Timer keeps track of script execution time ==
    start_time = time.time()
    # === Argument Parsing ===
    parser = argparse.ArgumentParser(
        description="Convert a CSV to RDF using a TOML configuration file."
    )
    parser.add_argument("config", type=str, help="Path to the TOML configuration file")
    args = parser.parse_args()
    config_path = Path(args.config)
    # === Load TOML config ===
    with open(config_path, "rb") as f:
        config = tomli.load(f)
    # == Retrieve output information from config ==
    try:
        rel_out_dir = Path(config["general"]["rdf_output_folder"])
        ttl_name = config["general"]["name"]
    except KeyError as e:
        raise ValueError(f" {config} is missing required key: {e}") from e
    # == Process predicates in config ==
    processed_config = rdf_process_predicates(config)
    # == Convert CSVs to RDF graph
    rdf_graph = build_rdf_graph(processed_config)

    if rdf_graph:
        logger.info("RDF graph built successfully")
        logger.info("Serializing... (this may take a while)")

    # === Find Output Directory ===
    script_dir = Path(__file__).parent.resolve()
    rdf_folder = (script_dir / rel_out_dir).resolve()
    ttl_path = rdf_folder / ttl_name
    if config["general"].get("test_mode") is True:
        ttl_path = ttl_path.with_name(f"{ttl_path.stem}_test").with_suffix(".ttl")
    else:
        ttl_path = ttl_path.with_suffix(".ttl")

    # === Serializing RDF Graph ===
    rdf_folder.mkdir(parents=True, exist_ok=True)
    rdf_graph.serialize(destination=ttl_path, format="turtle")
    logger.info("RDF conversion completed. Output saved to: %s", ttl_path.resolve())
    elapsed_time = time.time() - start_time
    logger.info("Script finished in %.2f seconds.", elapsed_time)
    # Each non-empty line in ttl (except prefix) is a triple
    non_empty_lines = sum(
        1
        for line in ttl_path.open("r", encoding="utf-8")
        if line.strip() and not line.lstrip().startswith("@prefix")
    )
    logger.info("TTL file contains %d triples.", non_empty_lines)


if __name__ == "__main__":
    main()
