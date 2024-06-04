# This file converts a JSON Lines file from MusicBrainz to a CSV file
# For OpenRefine Reconciling
# Input file can be downloaded in
# https://data.metabrainz.org/pub/musicbrainz/data/json-dumps/20240522-001002/
# Output file can be imported to OpenRefine
# Both input and output files must be in data folder
# The input filename can be directly entered in second argument of the commandline
import json
import copy
import csv
import os
import sys

header = ["id"]
values = []

DIRNAME = os.path.dirname(__file__)

if len(sys.argv) != 3:
    raise ValueError("Invalid number of arguments")

inputpath = os.path.join(DIRNAME, "data", sys.argv[1])
outputpath = os.path.join(DIRNAME, "data", "out.csv")
entity_type = sys.argv[2]

# the file must be from MusicBrainz's JSON data dumps.
with open(inputpath, "r") as f:
    json_data = [json.loads(m) for m in f]

def extract(data, value: dict, first_level: bool = True, key: str = ""):
    '''
    (data, dict, bool, str) -> None
    
    Extract info from JSON Lines file and add a finite number of them into a list of dictionaries.
    Arguments:
        data : can be any type, parsed based on its type
        value : records the informations of the current dictionary
        first_level : records if the current level is the first level of the JSON file.
        key : the current key that will be added to a dictionary
    '''
    if key != "":
        first_level = False
        
    if "aliases" in key or "tags" in key:
        # ignore aliases and tags to make output simplier
        return

    if isinstance(data, dict):
        # the input JSON Lines format is lines of dictionaries, and the input data should be
        # a list of dictionaries.
        if first_level:
            # if this dictionary is not nested i.e. first level, then we extract every entry.
            global values
            # make a new entry for the value list, since each first level dictionary
            # in JSON file represents a new instance. This value dictionary is carried and 
            # preserved between each recursive call.
            value = {}
            for k in data:
                if k == 'id':
                    id = data[k]
                    extract(f"https://musicbrainz.org/{entity_type}/{id}", value, first_level, k)
                else:
                    extract(data[k], value, False, k)
            
            # after extracting every entry of the current line, append it to the list and empty it.
            values.append(copy.deepcopy(value))
            value = {}

        else:
            # if this dictionary is nested, then we do not extract all info,
            # we only need the id and the name of that dictionary.
            for k in data:
                if k == "id":
                    # extract its id
                    keywords = key.split("_")
                    word = keywords[-1]
                    id = data['id']
                    extract(f"https://musicbrainz.org/{word}/{id}", value, first_level, key + "_id")

                if k == "name":
                    # extract its name
                    extract(data["name"], value, first_level, key + "_name")

                if isinstance(data[k], dict) or isinstance(data[k], list):
                    # if there is still a nested instance, extract further
                    extract(data[k], value, first_level, key + "_" + k)

    elif isinstance(data, list):
        # extract each element of the list.
        if key == 'relations':
            for element in data:
                if 'type' in element and element['type'] == "wikidata":
                    extract((element['url'])['resource'], value, first_level, key + '_wiki')
        else:
            for element in data:
                extract(element, value, first_level, key)
                
    else:
        # if data is not a collection, we parse it and add to the current value dictionary.
        global header
        if key not in header:
            header.append(key)

        v = data
        if isinstance(data, str):
            v = v.replace(",", "\,")
            v = v.replace("\r\n", "")

        if data is None:
            v = ""

        if key in value:
            if isinstance(value[key], list): 
                value[key].append(v)
            else: 
                value[key] = [value[key]] + [v]
        else:
            value[key] = v
       
        return
    
def convert_dict_to_csv(dictionary_list: list, filename: str) -> None:
    """
    (list, str) -> None
    Writes a list of dictionaries into the given file. 
    If there are multiple values against a single key, a new column with only the 
    id and that value is created.
    
    Arguments: 
        dictionary_list: the list of dictionary that contains all the data
        filename: the destination filename
    """
    with open(filename, mode='w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(header)
        # Find the maximum length of lists in the dictionary
        
        for dictionary in dictionary_list:
            max_length = max(len(v) if isinstance(v, list) else 1 for v in dictionary.values())

            for i in range(max_length):
                row = [dictionary['id']]
                for key in header:
                    if key == 'id':
                        continue

                    if key in dictionary:
                        if isinstance(dictionary[key], list):
                            # Append the i-th element of the list, or an empty string if index is out of range
                            row.append((dictionary[key])[i] if i < len(dictionary[key]) else '')
                        else:
                            # Append the single value (for non-list entries, only on the first iteration)
                            row.append(dictionary[key] if i == 0 else '')
                    else:
                        row.append('')
                        
                writer.writerow(row)


if __name__ == "__main__":
    extract(json_data, {})
        
    convert_dict_to_csv(values, outputpath)