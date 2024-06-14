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

filenames = sys.argv[1:]
output_name = "mapping.json"
dt = {}

for filename in filenames:
    with open(filename, "r") as csv_file:
        csv_reader = csv.reader(csv_file)
        header = next(csv_reader)
        
    header.append("entity_type")

    for item in header:
        dt[item] = ""
        
    dt["entity_type"] = []

        
with open(output_name, "w") as out_json:
    json.dump(dt, out_json, indent=4)