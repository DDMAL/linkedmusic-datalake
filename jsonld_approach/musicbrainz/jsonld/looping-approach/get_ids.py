import json
import csv

# Function to recursively extract @id values from nested JSON
def extract_ids(data, valid_formats, ids=set()):
    if isinstance(data, dict):
        for key, value in data.items():
            if key == '@id' and any(value.startswith(format) for format in valid_formats):
                ids.add(value)
            if key == 'genre':
                ids |= set(value)
            else:
                extract_ids(value, valid_formats, ids)  # Pass valid_formats as well
    elif isinstance(data, list):
        for item in data:
            extract_ids(item, valid_formats, ids)  # Pass valid_formats as well
    return ids

# Load the JSON-LD file
with open("./../../code/initial_compact.jsonld", 'r') as json_file:
    data = json.load(json_file)

valid_formats = [
    "http://musicbrainz.org/artist",
    "http://musicbrainz.org/label",
    "http://musicbrainz.org/area"
]

# Extract @id values
id_values = extract_ids(data, valid_formats)

# Write the @id values to a CSV file
with open('ids.csv', 'w', newline='') as csv_file:
    writer = csv.writer(csv_file)
    writer.writerow(['@id'])  # Write the header
    for id_value in id_values:
        writer.writerow([id_value])

print('CSV file created with @id values.')
