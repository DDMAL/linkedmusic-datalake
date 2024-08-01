"""
This script accepts a folder name as a commandline argument. 
It reads a mapping.json file and all .csv files in that folder.

For each CSV file provided as input, the script performs the following steps:

1.  Read folder: If a mapping file already exists, 
then the script reads that file and append any additional predicates.
2.  Extract Headers: The script extracts the headers from each CSV file.
3.  Write to JSON: The script writes these headers to a JSON file,
which will serve as the mapping file for the csv2rdf_single_subject.py script.
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
