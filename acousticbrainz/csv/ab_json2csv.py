"""
This script does not take any commandline arguments. It parses all the .JSON files from the
../data folder into a single CSV file named output.csv.
"""

import json
import glob
import pandas as pd

# Load JSON data from a file
JSON_FILES_PATH = "../data"
PATTERN = "*.json"
CSV_FILE = "output.csv"
df_list = []


def expand_lists(dataframe, list_columns):
    """
    Expand each column containing lists
    """
    for col in list_columns:
        dataframe = dataframe.explode(col)
    return dataframe


for json_file in glob.glob(f"{JSON_FILES_PATH}/**/{PATTERN}", recursive=True):
    with open(json_file, encoding="utf-8") as data_file:
        data = json.load(data_file)
        df = pd.json_normalize(data, max_level=2)
        df_list.append(df)

# Convert to CSV
df_merged = pd.concat(df_list)
# Reording columns
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
columns_with_lists = []

for column in df_merged.columns:
    if (
        df_merged[column].apply(lambda x: isinstance(x, dict)).any()
        or df_merged[column].apply(lambda x: isinstance(x, float)).any()
    ) and not column.endswith("id"):
        # Mark column for dropping if any element is a dictionary or float
        columns_to_drop.append(column)
    elif df_merged[column].apply(lambda x: isinstance(x, list)).any():
        # Convert lists to strings
        columns_with_lists.append(column)

# Drop columns that contain dictionaries
df_merged.drop(columns=columns_to_drop, inplace=True)
df_merged = expand_lists(df_merged, columns_with_lists)
for column in df_merged.columns:
    if column.endswith("id"):
        keyword = (column.split("_")[-1])[:-2]
        df_merged[column] = [
            (
                "https://musicbrainz.org/" + keyword + "/" + str(l)
                if str(l) != 'nan'
                else ""
            )
            for l in df_merged[column]
        ]
df_merged.to_csv(CSV_FILE, index=False)
