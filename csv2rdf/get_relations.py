"""
This script accepts a folder name as a commandline argument. 
It reads a mapping.json file and all .csv files in that folder.

For each CSV file provided as input, the script performs the following steps:

1.  Read folder: If a mapping file already exists, 
then the script reads that file and saves any predicate mappings that exist in that file.
2.  Extract Headers: The script extracts the headers from each CSV file.
3.  Write to JSON: If a column header extracted from a CSV file was mapped
in the existing mapping file, keep the existing mapping. If we find a header that
did not exist in the existing mapping file, create a key for that header with a blank
predicate value.  The script writes the resulting mapping to a JSON file,
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
    dt = {"entity_type": []}

dt_out = {"entity_type": dt["entity_type"]}

for filename in glob.glob(f"{FILEPATH}/{PATTERN}", recursive=False):
    with open(os.path.abspath(filename), "r", encoding="utf-8") as csv_file:
        csv_reader = csv.reader(csv_file)
        print(filename)
        header = next(csv_reader)[1:]

    for item in header:
        if item not in dt.keys():
            dt_out[item] = ""
        else:
            dt_out[item] = dt[item]

with open(OUTPUT_NAME, "w", encoding="utf-8") as out_json:
    json.dump(dt_out, out_json, indent=4, sort_keys=True)
