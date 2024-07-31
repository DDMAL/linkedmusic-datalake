"""
This script takes as many as input parameters as needed.
All the parameters will be the CSV files that need to be converted 
and merged into one single RDF file.
For all the CSV files, this script extracts their headers and write them
to a JSON file, which is used as the mapping file for the 
csv2rdf_single_subject.py script.
"""

import csv
import json
import sys
import os
import glob

FILEPATH = sys.argv[1]
OUTPUT_NAME = os.path.join(FILEPATH, "mapping.json")
PATTERN = "*.csv"

try:
    with open(OUTPUT_NAME, "r", encoding="utf-8") as mapping:
        dt = json.load(mapping)
except FileNotFoundError:
    dt = {}
    dt["entity_type"] = []

for filename in glob.glob(f"{FILEPATH}/{PATTERN}", recursive=False):
    with open(os.path.abspath(filename), "r", encoding="utf-8") as csv_file:
        csv_reader = csv.reader(csv_file)
        header = next(csv_reader)

    for item in header:
        if item not in dt.keys():
            dt[item] = ""

with open(OUTPUT_NAME, "w", encoding="utf-8") as out_json:
    json.dump(dt, out_json, indent=4)
