import json
from collections import defaultdict

with open('../data/flatt_from_openre.json', 'r') as file:
    data = json.load(file)

def remove_empty_dicts(data):
    if isinstance(data, dict):
        # Create a copy of the dictionary to avoid modifying it while iterating
        data_copy = data.copy()

        for key, value in data_copy.items():
            # Recursively call the function to handle nested dictionaries
            if isinstance(value, dict):
                data_copy[key] = remove_empty_dicts(value)

        # Remove keys with empty dictionaries
        return {key: value for key, value in data_copy.items() if value != {}}
    else:
        # For non-dictionary data types, return the value as is
        return data

final_doc = []

grouped_data = defaultdict(list)
for i in data:
    nested_json = {}  # Create a new dictionary for each record
    for key, value in i.items():
        if value is not None:
            key = key.replace('_ - ', '')
            keys = key.split(" - ")  # Split the key into nested levels
            current_level = nested_json
            for k in keys[:-1]:
                current_level = current_level.setdefault(k, {})
            if value is not None:
                if value != {}:
                    current_level[keys[-1]] = value
    grouped_data[nested_json.get('@id')].append(nested_json)
def merge(grouped_data):
    merged_data = []
    for id_group in grouped_data.values():
        merged_doc = {}
        for doc in id_group:
            for key, value in doc.items():
                if key not in merged_doc:
                    # Key does not exist in merged_doc, add it
                    merged_doc[key] = value
                elif merged_doc[key] != value:
                    # Key exists but with different values, convert to a list
                    if not isinstance(merged_doc[key], list):
                        merged_doc[key] = [merged_doc[key]]
                    merged_doc[key].append(value)
        merged_data.append(merged_doc)
    return merged_data
merged_data = merge(grouped_data)

# Convert the nested JSON structure to a JSON string and write it to a file
with open('restructure_from_flat.json', 'w') as file:
    json.dump(merged_data, file, indent=2)
