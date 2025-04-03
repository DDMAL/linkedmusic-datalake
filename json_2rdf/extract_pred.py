"""
This module reads a JSON Lines (JSONL) file, extracts unique predicates from the data, 
and appends them to an existing `mapping.json` file without modifying any pre-existing mappings. 
The `mapping.json` file is structured as a dictionary where each unique predicate serves as a key 
with an empty string as its value, unless a value already exists.

This script is designed to incrementally build and maintain a mapping of predicates 
encountered across multiple JSON objects in a JSON Lines file, allowing for dynamic 
data schema updates without overwriting previous mappings.

Usage:
    - Place a JSON Lines file named "input.jsonl" in the same directory.
    - Run the script. If `mapping.json` exists, new predicates will be appended to it;
      if not, a new `mapping.json` file will be created with all unique predicates from
      `input.jsonl`.

Dependencies:
    - json: Required for reading, parsing, and writing JSON data.
    - os: Used to check for the existence of `mapping.json`.

Functions:
    - extract_predicates(data, predicates): Recursively extracts unique predicates 
      from a dictionary. If a predicate is nested within a dictionary or list, it 
      is added to the set of predicates.

File I/O:
    - `input.jsonl`: The JSON Lines input file, where each line is a JSON object.
    - `mapping.json`: The output mapping file, which stores unique predicates as keys 
      with their associated values. New predicates are added with an empty string as 
      their value unless already present.

Example:
    If `mapping.json` contains:
    {
        "pred1": "existing value"
    }
    and `input.jsonl` has a new predicate "pred2", then after running the script, 
    `mapping.json` will contain:
    {
        "pred1": "existing value",
        "pred2": ""
    }
"""

import json
import os


# Function to recursively extract predicates
def extract_predicates(d, p):
    """
    Recursively extracts unique predicate names from a JSON object and adds them to a set.

    This function traverses the JSON structure to find all keys (predicates) in 
    the provided `data` dictionary. It handles nested dictionaries and lists by 
    recursively searching through each level, ensuring that all unique predicates 
    are added to the provided set. The "id" field is ignored, as it is assumed 
    to represent the main subject rather than a predicate.

    Parameters:
    data (dict): A JSON object represented as a dictionary, which may contain 
                 nested dictionaries or lists.
    predicates (set): A set to store unique predicate names (keys) found in the 
                      JSON object.

    Returns:
    None. The function modifies the `predicates` set in place, adding any new 
          unique predicate names it encounters.

    Example:
    If `data` is:
    {
        "id": "http://example.org/id",
        "pred1": "value1",
        "pred2": {
            "pred2_1": "value2"
        },
        "pred3": [
            {"pred3_1": "value3"},
            "simple_value"
        ]
    }
    
    Then after calling `extract_predicates(data, predicates)`, the `predicates` set 
    will contain:
    {"pred1", "pred2", "pred2_1", "pred3", "pred3_1"}
    """
    for key, value in d.items():
        if key != "id":  # Ignore the "id" field, as it represents the main subject
            p.add(key)
            if isinstance(value, dict):
                extract_predicates(value, p)  # Recurse for nested dictionaries
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        # Recurse for dictionaries within lists
                        extract_predicates(item, p)


# Load the JSON Lines (JSONL) file and extract unique predicates
predicates = set()
with open("recording", "r", encoding="utf-8") as f:
    for line in f:
        data = json.loads(line)
        extract_predicates(data, predicates)

# Load existing mapping.json if it exists
if os.path.exists("pred_mapping.json"):
    with open("pred_mapping.json", "r", encoding="utf-8") as infile:
        predicate_mapping = json.load(infile)
else:
    predicate_mapping = {}

# Add new predicates to the mapping without modifying old entries
for predicate in predicates:
    if predicate not in predicate_mapping:
        predicate_mapping[predicate] = {"": ""}

# Write the updated mapping back to mapping.json
with open("pred_mapping.json", "w", encoding="utf-8") as outfile:
    json.dump(predicate_mapping, outfile, indent=4)

print("New predicates appended to mapping.json without modifying old mappings.")
