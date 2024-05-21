import json
import csv

with open("json_init.json", 'r') as json_file:
    json_data = json.load(json_file)
    # print(json_data)
    
    for element in json_data:
        print()