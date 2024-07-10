"""
This script does not take any commandline arguments. It parses all the .JSON files from the
../data folder into a single CSV file named output.csv.
"""

import os
import json
from fnmatch import fnmatch
import pandas as pd

# Load JSON data from a file
JSON_FILES_PATH = "../data"
PATTERN = "*.json"
df_list = []


# Function to convert lists to strings
def list_to_string(value):
    """
    This function takes a list as input argument and converts
    its first element into a string
    """
    if isinstance(value, list):
        return str(value[0])
    return value


for path, subdirs, json_files in os.walk(JSON_FILES_PATH):
    for json_file in json_files:
        with open(os.path.join(path, json_file), encoding="utf-8") as data_file:
            if fnmatch(json_file, PATTERN):
                data = json.load(data_file)

        df = pd.json_normalize(data, max_level=2)
        df_list.append(df)

# Convert to CSV
CSV_FILE = "output.csv"
df_merged = pd.concat(df_list)
df_merged = df_merged[
    ["metadata.tags.musicbrainz_recordingid"]
    + [
        col
        for col in df_merged.columns
        if col != "metadata.tags.musicbrainz_recordingid"
    ]
]

# Loop through columns and apply transformations
columns_to_drop = []

for column in df_merged.columns:
    if (
        df_merged[column].apply(lambda x: isinstance(x, dict)).any()
        or df_merged[column].apply(lambda x: isinstance(x, float)).any()
    ):
        # Mark column for dropping if any element is a dictionary or float
        columns_to_drop.append(column)
    elif df_merged[column].apply(lambda x: isinstance(x, list)).any():
        # Convert lists to strings
        df_merged[column] = df_merged[column].apply(list_to_string)

# Drop columns that contain dictionaries
df_merged.drop(columns=columns_to_drop, inplace=True)
for column in df_merged.columns:
    if column.endswith("id"):
        keyword = (column.split("_")[-1])[:-2]
        df_merged[column] = [
            "https://musicbrainz.org/" + keyword + "/" + l + " " for l in df_merged[column]
        ]
# print(df_merged)
df_merged.to_csv(CSV_FILE, index=False)

print(f"JSON data has been converted to CSV and saved as {CSV_FILE}")
