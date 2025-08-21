import json
def get_all_keys(data, keys=None):
    if keys is None:
        keys = set()
    if isinstance(data, dict):
        for key, value in data.items():
            keys.add(key)
            get_all_keys(value, keys)
    elif isinstance(data, list):
        for item in data:
            get_all_keys(item, keys)
    return keys

# Your JSON data as a string (replace this with your actual JSON data)
# with open('compact.jsonld','r') as f:
#     json_data = json.load(f)

with open('compact.jsonld', 'r') as file:
    json_data = json.load(file)

# Parse the JSON data
# data = json.loads(json_data)

# Get and print all keys
keys = get_all_keys(json_data)
result_dict = {key: None for key in keys}
# Write the dictionary to the output file as JSON
with open("key_names.jsonld", 'w') as output_file:
    json.dump(result_dict, output_file, indent=4)
