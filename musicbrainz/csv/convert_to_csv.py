import json
import format_json

header = ["id"]
values = []

format_json.format()

with open("json_init.json", 'r') as json_file:
    json_data = json.load(json_file)
    # print(json_data)

def extract(data, first_level : bool=True, key : str="", value : dict={}):
    if key != "":
        first_level = False
                    
    if (isinstance(data, dict)):
        if first_level:
            global values
            first_level = False
            for k in data:
                extract(data[k], first_level, k, value)
            first_level = True
            values.append(value)
            value = {}

        else:
            for k in data:
                if k == "id":
                    extract(data["id"], first_level, key + "_id", value)
                
                if k == "name":
                    extract(data["name"], first_level, key + "_name", value)
                    
                if (isinstance(data[k], dict) or isinstance(data[k], list)):
                    extract(data[k], first_level, key + "_" + k, value)

                
    elif (isinstance(data, list)):
        rep_count = 0
        for element in data:
            rep_count += 1
            if (isinstance(element, dict)):
                if first_level:
                    rep_count = 0
                    extract(element, first_level, key, value)
                else:
                    extract(element, first_level, key + str(rep_count), value)

                
    else:
        global header
        if key not in header:
            header.append(key)
            
        value[key] = data
        return
                                

if __name__ == "__main__":
    extract(json_data)
    print(header[0:90])
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
            
                