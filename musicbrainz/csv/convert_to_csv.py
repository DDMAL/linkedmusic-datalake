import json
import csv
header = []
cnt = 0
values = []
    
with open("json_init.json", 'r') as json_file:
    json_data = json.load(json_file)
    # print(json_data)
    
    for element in json_data:
        for k, v in element:
            value_of_line = {}
            if (not (isinstance(v, dict) and isinstance(v, list))):
                if k not in header:
                    header += k
                value_of_line[k] = v
            values += value_of_line
            
    
with open("out.csv", "w") as out:
    # write header
    line = "id,"
    for column in header:
        if column != "id":
            line += column
        
        if column != header[-1]:
            line += ','
    out.writelines()
            
    line = ""
    for row in values:
        for column in header:
            line += row[column]
            
            if column != header[-1]:
                line += ','
    out.writelines()
        
            