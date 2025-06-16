"""
General CSV to RDF converter driven by a TOML configuration file.
Reads rdf_config.toml, processes all listed CSVs, and generates RDF triples accordingly.
"""

import argparse
from pathlib import Path
from typing import Union
from code.wikidata_utils import extract_wd_id
import pandas as pd
import tomli
from rdflib import Graph, URIRef, Literal, Namespace
import logging



def to_rdf_node(val: str, namespaces: dict, lang: str|None = None, datatype: str|None = None) -> Union[URIRef, Literal, None]:
    """Convert a value to the appropriate RDF node.
    The result is either a URIRef"""
    if pd.isna(val) or val == "":
        return None
    qid = extract_wd_id(val)
    if qid:
        return URIRef(f"{namespaces['wd']}{qid}")
    for prefix ,uri in namespaces.items():
        if val.startswith(uri):
            # Only considered a value URI if it is in a binded namespace
            return URIRef(val)
        if val.startswith(prefix + ":"):
            # If the value starts with a prefix, use the namespace URI
            return URIRef(f"{uri}{val.split(':', 1)[1]}")
    if ":" in datatype:
        prefix, body = datatype.split(":", 1)
        ns_uri = namespaces.get(prefix)
        if ns_uri:
            datatype = (f"{ns_uri}{body}")
    return Literal(str(val), lang=lang, datatype=datatype)

def to_predicate(val: str, namespaces: dict) -> URIRef:
    """
    Convert a property string to a predicate URIRef.
    If the value is a Wikidata property (PID), use the wdt namespace.
    Otherwise, if the value contains a colon, use the prefix to look up the namespace.
    """
    pid = extract_wd_id(val)
    if pid:
        return URIRef(f"{namespaces['wdt']}{pid}")
    if ":" in val:
        prefix, local = val.split(":", 1)
        ns_uri = namespaces.get(prefix)
        if ns_uri:
            return URIRef(f"{ns_uri}{local}")
    raise ValueError(f"Invalid property value: {val}. Expected a Wikidata ID or a valid prefixed URI.")

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
    # === Verify that the CSV can be processed ===
    primary_key = column_mapping.get("PRIMARY_KEY")
    if primary_key is None:
        raise ValueError(f"the 'PRIMARY_KEY' of {table_name}.csv is not defined")
    # PRIMARY_KEY is not a column that exists in the CSV
    property_columns = {col: prop for col, prop in column_mapping.items() if col != "PRIMARY_KEY"}
    for col in property_columns:
        if col not in df.columns:
            raise ValueError(f"'{col}' is not a column in {table_name}.csv ")
    # === Processing Each Row ===
    for row in df.itertuples(index=False):
        primary_val = getattr(row, primary_key, None)
        if pd.isna(primary_val) or primary_val == "":
            continue
        # Useful for record lookup
        primary_row = row
        primary_node = to_rdf_node(primary_val, ns)
    # === Processing Each Column of the Row====
        for col, prop in property_columns.items():
            if not prop:
                continue
            object_val = getattr(row, col, None)
            if pd.isna(object_val) or object_val == "":
                continue
            # === Build the Object Node ===
            if isinstance(prop, str):
                predicate = to_predicate(prop, ns)
                subject_node = primary_node 
            elif isinstance(prop, dict):
                # complex logic
                if condition := prop.get("condition", None):
                    row_dict = row._asdict()  # eval context must be provided as dict
                    if not eval(condition, {}, row_dict): # evaluate the condition using values in this row as variable
                        continue 
                # === Build the subject node ===
                subject_val = getattr(primary_row, prop.get("subj", ""), None)
                if pd.isna(subject_val) or subject_val == "":
                    subject_node = primary_node
                else:
                    subject_node = to_rdf_node(subject_val, ns)
                pred = prop.get("pred", None)
                if not pred:
                    continue
                datatype = prop.get("datatype", None)
                lang = prop.get("lang", None)
                if datatype is not None and lang is not None:
                    raise ValueError("Cannot specify both datatype and lang for column {col} in {table_name}.csv")
                object_node = to_rdf_node(object_val, ns, lang=lang, datatype=datatype)
            else:
                # can not parse toml
                pass

            # === Add the triple to the graph ===    
            graph.add((subject_node, predicate, object_node))

def main():
    # === Setup Logger ===
    logger = logging.getLogger("csv_to_rdf")
    if not logger.hasHandlers():
        logging.basicConfig(
            level=logging.INFO,
            format='[%(levelname)s] %(message)s'
        )
    # === Argument Parsing ===
    parser = argparse.ArgumentParser(
        description="General CSV to RDF converter driven by a TOML configuration file."
    )
    parser.add_argument('--config', type=str, default='rdf_config.toml', help='Path to the TOML configuration file')
    args = parser.parse_args()
    config_path = Path(args.config)
    # === Load TOML config ===
    with open(config_path, "rb") as f:
        config = tomli.load(f)

    # === Initialize RDF Graph ===
    graph = Graph()

    # === Bind Namespaces ===
    rdf_ns = config.get["namespaces"]
    for prefix, ns in rdf_ns.items():
        graph.bind(prefix, Namespace(ns))

    # === Resolve CSV Folder Path ===
    rel_in_dir = Path(config["general"]["csv_folder"])
    script_dir = Path(__file__).parent.resolve()
    csv_folder = (script_dir / rel_in_dir).resolve()

    # === Process CSV Files ===
    for csv_name, col_mapping in config.items():
        # "general" and "namespaces" tables are not CSV files
        if csv_name in ("general", "namespaces"):
            continue
        # csv_name does not have ".csv" extension
        csv_file = (csv_folder / csv_name).with_suffix(".csv")
        if not csv_file.exists():
            logger.warning("CSV file '%s' not found. Skipping.", csv_file)
            continue
        try:
            df = pd.read_csv(csv_file)
        except Exception as e:
            logger.error("Error reading '%s': %e", csv_file, e)
            continue
        logger.info("Processing %s...", csv_file.name)
        process_csv_file(df, csv_name, col_mapping, graph, rdf_ns)

    # === Resolve RDF Folder Path ===
    rel_out_dir = Path(config["general"]["rdf_output_path"])
    rdf_folder = (script_dir / rel_out_dir).resolve()
    rdf_folder.mkdir(parents=True, exist_ok=True)
    ttl_path = (rdf_folder / Path(config["general"]["name"])).with_suffix(".ttl")
    
    # === Serialize RDF Output ===
    graph.serialize(destination=str(ttl_path), format="turtle")
    logger.info("RDF conversion completed. Output saved to: %s", ttl_path.resolve())

if __name__ == "__main__":
    main()
