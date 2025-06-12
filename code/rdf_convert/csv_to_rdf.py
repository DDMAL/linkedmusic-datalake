"""
General CSV to RDF converter driven by a TOML configuration file.
Reads rdf_config.toml, processes all listed CSVs, and generates RDF triples accordingly.
"""

import argparse
import sys
import re
from pathlib import Path
from typing import Union
from code.wikidata_utils import extract_wd_id
import pandas as pd
import tomli
from rdflib import Graph, URIRef, Literal, Namespace
import logging



def to_rdf_node(val: str, namespace: Namespace = None) -> Union[URIRef, Literal, None]:
    """Convert a string value to an RDF node."""
    if pd.isna(val) or val == "":
        return None
    # Need fixing
    if namespace and (namespace != wd or extract_wd_id(str(val))):
        return URIRef(f"{namespace}{val}")
    return Literal(str(val))



def process_csv_file(
    df: pd.DataFrame, table_name: str, column_mapping: dict, graph: Graph, ns: dict
) -> None:
    """Convert a CSV DataFrame to RDF triples and add them to the graph."""
    subject_col = next(iter(column_mapping))
    for row in df.to_dict(orient="records"):
        subject_val = row.get(subject_col, "")
        subject_node = to_rdf_node(subject_val, namespace=wd)
        if subject_node is None:
            continue
        for col, prop in column_mapping.items():
            if col == subject_col or not prop:
                continue
            if prop.startswith("http://"):
                predicate = URIRef(prop)
            else:
                predicate = URIRef(f"{ns.get('wdt', '')}{prop}")
            object_node = to_rdf_node(row.get(col, ""), namespace=wd)
            if object_node:
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
    rel_path = Path(config["general"]["csv_folder"])
    script_dir = Path(__file__).parent.resolve()
    csv_folder = (script_dir / rel_path).resolve()

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

    # === Prepare Output ===
    output_dir = Path(config["general"]["rdf_output_path"])
    output_dir.mkdir(parents=True, exist_ok=True)
    # === Serialize RDF Output ===
    output_file = output_dir / "output.ttl"
    graph.serialize(destination=str(output_file), format="turtle")
    logger.info("RDF conversion completed. Output saved to: %s", output_file.resolve())

if __name__ == "__main__":
    main()
