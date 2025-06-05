"""
Script to extract relationships from DIAMM data files.
This script reads JSON files from the DIAMM dataset, extracts relationships between entities,
and saves the relationships in a structured JSON format.

The `organizations` and `people` entities
"""

import os
import json
from pathlib import Path

BASE_PATH = "../../data/diamm/raw/"
OUTPUT_PATH = "."

relations = {}
for entity_type in ("organizations", "people"):
    print(f"Processing {entity_type}")
    relations[entity_type] = {}
    for filename in (Path(BASE_PATH) / entity_type).glob("*.json"):
        with open(filename, "r", encoding="utf-8") as file:
            data = json.load(file)
            for relation in data.get("related_sources", []):
                if rtype := relation.get("relationship"):
                    relations[entity_type][rtype] = None

with open(
    os.path.join(OUTPUT_PATH, "relations.json"), "w", encoding="utf-8"
) as output_file:
    json.dump(relations, output_file, indent=4, ensure_ascii=False)
