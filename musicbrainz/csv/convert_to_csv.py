import json
import format_json

header = ["id"]
cnt = 0
values = []

format_json.format()
    
with open("json_init.json", 'r') as json_file:
    json_data = json.load(json_file)
    # print(json_data)
    
for element in json_data:
    value = {}
    for k in element:
        if (not (isinstance(element[k], dict) or isinstance(element[k], list))):
            if k not in header:
                header.append(k)
            temp = str(element[k]).replace("\r\n", "")
            temp = temp.replace(",", "`")
            value[k] = temp
    values.append(value)
                
# print(header)
# print(values)

with open("out.csv", "w") as out:
    # write header
    line = "id,"
    for column in header:
        if column == "id":
            continue
            
        line += column
        
        if column != header[-1]:
            line += ','
    out.writelines(line)
    out.writelines("\n")
            
    line = ""
    for row in values:
        for column in header:
            if column in row:
                line += str(row[column])
            
            if column != header[-1]:
                line += ','
            else:
                line += "\n"
    out.writelines(line)
        
            