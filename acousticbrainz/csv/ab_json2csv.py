import pandas as pd
import os
import json

# Load JSON data from a file
json_files_path = "../data"
json_files_dir = os.listdir(json_files_path)
df_list = []

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
df_merged.to_csv(csv_file, index=False)

print(f"JSON data has been converted to CSV and saved as {csv_file}")
