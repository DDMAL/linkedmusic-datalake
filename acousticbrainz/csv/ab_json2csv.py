import pandas as pd
import os
import json

# Load JSON data from a file
json_files_path = "../data"
json_files_dir = os.listdir(json_files_path)
df_list = []

# Function to convert lists to strings
def list_to_string(value):
    if isinstance(value, list):
        return str(value[0])
    return value
    
for json_file in json_files_dir:
    with open(os.path.join(json_files_path, json_file)) as data_file:
        data = json.load(data_file)
        
    df = pd.json_normalize(data, max_level=2)
    df_list.append(df)
    
# Convert to CSV
csv_file = 'output.csv'
df_merged = pd.concat(df_list)
df_merged = df_merged[
    ['metadata.tags.musicbrainz_recordingid'] +
    [col for col in df_merged.columns if col != 'metadata.tags.musicbrainz_recordingid']
]

# Loop through columns and apply transformations
columns_to_drop = []

for column in df_merged.columns:
    if df_merged[column].apply(lambda x: isinstance(x, dict)).any() or df_merged[column].apply(lambda x: isinstance(x, float)).any():
        # Mark column for dropping if any element is a dictionary
        columns_to_drop.append(column)
    elif df_merged[column].apply(lambda x: isinstance(x, list)).any():
        # Convert lists to strings
        df_merged[column] = df_merged[column].apply(list_to_string)    
    
# Drop columns that contain dictionaries
df_merged.drop(columns=columns_to_drop, inplace=True)
for column in df_merged.columns:
    if column.endswith("id"):
        df_merged[column] = df_merged[column].apply(lambda x: "https://musicbrainz.org/" + (column.split("_")[-1])[:-2] + "/" + str(x))
# print(df_merged)
df_merged.to_csv(csv_file, index=False)

print(f"JSON data has been converted to CSV and saved as {csv_file}")
