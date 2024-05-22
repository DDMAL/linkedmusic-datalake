import json
import csv

with open("json_init.json", 'r') as json_file:
    json_data = json.load(json_file)
    # print(json_data)
    
    header = []
    cnt = 0
    values = []
    for element in json_data:
        for k, v in element:
            value_of_line = {}
            if (not (isinstance(v, dict) and isinstance(v, list))):
                if k not in header:
                    header += k
                value_of_line[k] = v
            values += value_of_line
            
            
            
            