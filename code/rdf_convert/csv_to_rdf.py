"""
General CSV to RDF converter driven by a TOML configuration file.

Reads rdf_config.toml, processes all CSVs listed in the config, 
and generates RDF triples accordingly.
"""

import argparse
from pathlib import Path
from typing import Union
from wikidata_utils import extract_wd_id
import numpy as np
import pandas as pd
import tomli
from rdflib import Graph, URIRef, Literal, Namespace
import logging


def to_rdf_node(
    val: str, namespaces: dict, lang: str | None = None, datatype: str | None = None, prefix: str = None
) -> Union[URIRef, Literal, None]:
    """Convert a value to the appropriate RDF node:

    A URIRef is returned if:
    1. The value is a Wikidata ID (e.g. Q3 or P1234)
    2. The value starts with a bound namespace URI or prefix

    None is returned if the value is empty or NaN.

    In all others cases, a Literal is returned.
    The Literal can have a language label or a datatype specified"""
    if not isinstance(val, str) or val == "":
        return None
    qid = extract_wd_id(val)
    if qid:
        return URIRef(f"{namespaces['wd']}{qid}")
    if val.startswith("http") and datatype not in ("xsd:anyURI", XSD.anyURI):
        return URIRef(val)
    if prefix:
        return URIRef(f"{namespaces.get(prefix)}{val}")
    # Expand datatype if it is prefixed
    if datatype is not None and ":" in datatype:
        prefix, body = datatype.split(":", 1)
        ns_uri = namespaces.get(prefix)
        if ns_uri:
            datatype = f"{ns_uri}{body}"
    return Literal(str(val), lang=lang, datatype=datatype)


def to_predicate(val: str, namespaces: dict) -> URIRef:
    """
    Convert a property string to a predicate URIRef.
    
    A URIRef is returned if:
    1. The value is a Wikidata PID (e.g. P1234)
    2. The value starts with a bound namespace prefix or URI.

    This function raises a ValueError is none of the above conditions are met.
    It will never return Literal, since a predicate can not be a Literal.
    """
    # The function extracts both QID and PID
    wiki_id = extract_wd_id(val)
    if wiki_id and wiki_id.startswith("P"):
        return URIRef(f"{namespaces['wdt']}{wiki_id}")
    for prefix, uri in namespaces.items():
        if val.startswith(uri):
            # Only considered a value URI if it is in a binded namespace
            return URIRef(val)
        if val.startswith(prefix + ":"):
            # If the value starts with a prefix, expand to full URI
            return URIRef(f"{uri}{val.split(':', 1)[1]}")
    raise ValueError(
        f"Invalid property value: {val}. Expected a Wikidata ID or a valid prefixed URI."
    )


def process_csv_file(
    df: pd.DataFrame, table_name: str, column_mapping: dict, graph: Graph, ns: dict
) -> None:
    """
    Convert a CSV DataFrame to RDF triples and add them to the graph.

    column_mapping example:
    {
        "primary_key": "subject_column_name",
        "col1": "predicate1",
        "col2": "predicate2",
        ...
    }
    """
    # === Verifying configuration ===
    primary_key = column_mapping.get("PRIMARY_KEY", None)
    if primary_key is None:
        raise ValueError(f"Missing 'PRIMARY_KEY' in config section: [{table_name}]")
    property_columns = {
        col: prop for col, prop in column_mapping.items() if col != "PRIMARY_KEY"
    }
    for col in property_columns:
        if col not in df.columns:
            raise ValueError(f"'{col}' is not a column in {table_name}.csv ")
    # === Processing Each Row ===
    for row in df.itertuples(index=False):
        # Preserve the first row of a multi-row record,
        # Subsequent rows of the record may be incomplete
        primary_val = getattr(row, primary_key, "")
        if pd.isna(primary_val) or primary_val == "":
            continue
        primary_row = row
        primary_node = to_rdf_node(primary_val, ns)
        # === Processing Each Column of the Row ====
        for col, prop in property_columns.items():
            if not prop:
                continue
            object_val = getattr(row, col, "")
            if pd.isna(object_val) or object_val == "":
                continue
            # === Build the Object Node ===
            if isinstance(prop, str):
                # simple logic
                predicate = to_predicate(prop, ns)
                subject_node = primary_node
                object_node = to_rdf_node(getattr(row, col, ""), ns)
            elif isinstance(prop, dict):
                # complex logic
                if condition := prop.get("condition"):
                    row_dict = row._asdict()  # eval context must be provided as dict
                    if not eval(
                        condition, {}, row_dict
                    ):  # evaluate the condition using values in this row as variable
                        continue
                # === Build subject node ===
                subj_field = prop.get("subj")
                subject_val = (
                    getattr(primary_row, subj_field, "") if subj_field else None
                )
                if pd.isna(subject_val) or subject_val == "":
                    subject_node = primary_node
                else:
                    subject_node = to_rdf_node(subject_val, ns)
                # === Build predicate ===
                pred = prop.get("pred", None)
                if not pred:
                    continue
                predicate = to_predicate(pred, ns)
                # === Build object node ===
                datatype = prop.get("datatype", None)
                lang = prop.get("lang", None)
                if datatype is not None and lang is not None:
                    raise ValueError(
                        f"Cannot specify both datatype and lang for column {col} in {table_name}.csv"
                    )
                object_node = to_rdf_node(object_val, ns, lang=lang, datatype=datatype)
            else:
                raise ValueError(
                    f"Invalid property mapping for column '{col}' in [{table_name}]. Expected a string or a dict, got {type(prop)}"
                )
            # === Add triple to graph ===
            graph.add((subject_node, predicate, object_node))


def main():
    # === Setup Logger ===
    logger = logging.getLogger("csv_to_rdf")
    if not logger.hasHandlers():
        logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    # === Argument Parsing ===
    parser = argparse.ArgumentParser(
        description="General CSV to RDF converter driven by a TOML configuration file."
    )
    parser.add_argument(
        "--config",
        type=str,
        default="rdf_config.toml",
        help="Path to the TOML configuration file",
    )
    args = parser.parse_args()
    config_path = Path(args.config)
    # === Load TOML config ===
    with open(config_path, "rb") as f:
        config = tomli.load(f)

    # == Extract general variables from RDF config ===
    try:
        rdf_ns = config["namespaces"]
        rel_inp_dir = Path(config["general"]["csv_folder"])
        rel_out_dir = Path(config["general"]["rdf_output_path"])
        ttl_name = config["general"]["name"]
    except KeyError as e:
        raise ValueError(f" {config} is missing required key: {e}")
    # === Initialize RDF Graph ===
    graph = Graph()

    # === Bind Namespaces ===
    for prefix, ns in rdf_ns.items():
        graph.bind(prefix, Namespace(ns))

    # === Resolve CSV Folder Path ===
    script_dir = Path(__file__).parent.resolve()
    csv_folder = (script_dir / rel_inp_dir).resolve()

    # === Resolve RDF Folder Path ===
    rdf_folder = (script_dir / rel_out_dir).resolve()
    rdf_folder.mkdir(parents=True, exist_ok=True)
    ttl_path = (rdf_folder / ttl_name).with_suffix(".ttl")

    # === Process CSV Files ===
    for csv_name, col_mapping in config.items():
        # "general" and "namespaces" are default tables in the config file
        if csv_name in ("general", "namespaces"):
            continue
        # the table names do not have ".csv" extension
        csv_file = (csv_folder / csv_name).with_suffix(".csv")
        if not csv_file.exists():
            logger.warning("'%s' not found. Skipping.", csv_file)
            continue
        try:
            df = pd.read_csv(csv_file)
            df = df.replace({None: "", np.nan: ""})
        except Exception as e:
            logger.error("Error reading '%s'. Skipping. %s", csv_file, e)
            continue
        logger.info("Processing %s...", csv_file.name)
        process_csv_file(df, csv_name, col_mapping, graph, rdf_ns)

    # === Serialize RDF Output ===
    graph.serialize(destination=str(ttl_path), format="turtle")
    logger.info("RDF conversion completed. Output saved to: %s", ttl_path.resolve())


if __name__ == "__main__":
    main()
