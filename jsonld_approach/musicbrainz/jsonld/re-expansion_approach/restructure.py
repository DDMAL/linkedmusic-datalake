import json

# Read the JSON data
with open('../data/template_openre.json', 'r') as file:
    data = json.load(file)

# def grouping(data, property):
# # Create a dictionary to store grouped data
#     grouped_data = {}

#     # Group the data by "id"
#     for item in data:
#         id_value = item['@id']
#         if id_value not in grouped_data:
#             grouped_data[id_value] = {'@id': id_value, property: []}
#         grouped_data[id_value][property].append(item[property])

#     # Convert the grouped data back to a list
#     return list(grouped_data.values())


# a = grouping(data,'track')


# # Save the result as JSON


def remove_nulls(obj):
    if isinstance(obj, list):
        # If the object is a list, iterate through its elements
        return [remove_nulls(item) for item in obj if item is not None]
    elif isinstance(obj, dict):
        # If the object is a dictionary, iterate through its key-value pairs
        return {key: remove_nulls(value) for key, value in obj.items() if value is not None}
    else:
        # For other data types, simply return the value
        return obj

def remove_empty_dicts(obj):
    if isinstance(obj, list):
        # If the object is a list, filter out empty dictionaries and recursively call the function
        return [remove_empty_dicts(item) for item in obj if not (isinstance(item, dict) and not bool(item))]
    elif isinstance(obj, dict):
        # If the object is a dictionary, recursively call the function on its values and filter out empty dictionaries
        return {key: remove_empty_dicts(value) for key, value in obj.items() if not (isinstance(value, dict) and not bool(value))}
    else:
        # For other data types, simply return the value
        return obj

    
cleaned_json = remove_empty_dicts(remove_nulls(data))
with open('restructure.json', 'w') as output_file:
    json.dump(cleaned_json, output_file, indent=2)