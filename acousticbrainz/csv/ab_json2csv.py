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

# The floats are the percentages for the genre features extraction.
# Those data are too overwhelming and makes my inspection much more difficult.
# Sometimes python sees an ID as a float, so I want to keep those.
# If we normalize the higher level dictionaries, they makes the chart very large,
# and if we not normalize the higher level dictionaries,
# they will be left as dictionaries in the CSV, so not good as well.
# Therefore I decide to drop any dictionaries after level 2.

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
                if str(l) != "nan"
                else ""
            )
            for l in df_merged[column]
        ]
df_merged.to_csv(CSV_FILE, index=False)
