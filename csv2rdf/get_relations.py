"""
This script accepts an arbitrary number of input parameters, each representing a CSV file that needs to be converted. All converted files will be merged into a single RDF file.

For each CSV file provided as input, the script performs the following steps:

1. Extract Headers: The script extracts the headers from each CSV file.
2. Write to JSON: The script writes these headers to a JSON file, which will serve as the mapping file for the csv2rdf_single_subject.py script.
"""

import csv
import json
import sys
import os

filenames = sys.argv[1:]
OUTPUT_NAME = "mapping.json"
dt = {}
dt["entity_type"] = []

for filename in filenames:
    with open(os.path.abspath(filename), "r", encoding='utf-8') as csv_file:
        csv_reader = csv.reader(csv_file)
        header = next(csv_reader)

    for item in header:
        dt[item] = ""

with open(OUTPUT_NAME, "w", encoding='utf-8') as out_json:
    json.dump(dt, out_json, indent=4)
