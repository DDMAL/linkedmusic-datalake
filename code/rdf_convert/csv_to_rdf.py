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


# === Utility Functions ===



def to_rdf_node(val: str, namespace: Namespace = None) -> Union[URIRef, Literal, None]:
    """Convert a string value to an RDF node."""
    if pd.isna(val) or val == "":
        return None
    # Need fixing
    if namespace and (namespace != wd or extract_wd_id(str(val))):
        return URIRef(f"{namespace}{val}")
    return Literal(str(val))


def load_config(path: Path) -> dict:
    """Load TOML configuration file."""
    try:
        with open(path, "rb") as f:
            return tomli.load(f)
    except Exception as e:
        raise RuntimeError(f"Failed to load TOML config: {e}")



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
    # === Argument Parsing ===
    parser = argparse.ArgumentParser(
        description="General CSV to RDF converter driven by a TOML configuration file."
    )
    parser.add_argument('--config', type=str, default='rdf_config.toml', help='Path to the TOML configuration file')
    args = parser.parse_args()
    config_path = Path(args.config)

    # === Load Config ===
    config = load_config(config_path)
    general = config.get("general", {})
    rdf_ns = config.get("namespaces", {})

    # === Prepare Namespaces ===
    wd = rdf_ns.get("wd")

    # === Prepare Output ===
    output_dir = Path(general["rdf_output_path"])
    output_dir.mkdir(parents=True, exist_ok=True)

    # === Initialize RDF Graph ===
    graph = Graph()
    for prefix, ns in rdf_ns.items():
        graph.bind(prefix, Namespace(ns))

    # === Process CSV Tables ===
    base_csv_path = Path(general["csv_path"])
    for table_name, mapping in config.items():
        if table_name in ("general", "namespaces"):
            continue
        csv_file = base_csv_path / table_name.strip('"')
        if not csv_file.exists():
            print(f"Warning: CSV file '{csv_file}' not found. Skipping.")
            continue
        try:
            df = pd.read_csv(csv_file)
        except Exception as e:
            print(f"Error reading '{csv_file}': {e}")
            continue

        print(f"Processing {csv_file.name}...")
        process_csv_file(df, table_name, mapping, graph, rdf_ns)

    # === Serialize RDF Output ===
    output_file = output_dir / "output.ttl"
    graph.serialize(destination=str(output_file), format="turtle")
    print(f"RDF conversion completed. Output saved to: {output_file.resolve()}")

if __name__ == "__main__":
    main()
