import csv
import json
import sys

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