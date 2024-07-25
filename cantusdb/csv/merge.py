"""
Merge all raw Cantus CSV into one Dataframe and export to a new CSV
"""

import os
import pandas as pd

INPUT_PATH = os.path.join(os.path.dirname(__file__), "../data/raw")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "../data/cantus.csv")
MAPPING_PATH = os.path.join(os.path.dirname(__file__), "../data/mappings")

# Create an empty list to store individual DataFrames
dfs = []
genre_mappings = pd.read_csv(
    os.path.join(MAPPING_PATH, "genres.tsv"), sep="\t", header=0, index_col=False
)
service_mappings = pd.read_csv(
    os.path.join(MAPPING_PATH, "services.tsv"), sep="\t", header=0, index_col=False
)
genre_mappings = dict(zip(genre_mappings["Genre"], genre_mappings["Description"]))
service_mappings = dict(zip(service_mappings["Service"], service_mappings["Description"]))

# Iterate over all files in the directory
for filename in os.listdir(INPUT_PATH):
    # Construct the full file path
    file_path = os.path.join(INPUT_PATH, filename)

    # Check if the file is a CSV file
    if filename.endswith(".csv"):
        # Read the CSV file into a DataFrame
        df = pd.read_csv(file_path)
        df["source_id"] = "https://cantusdatabase.org/sources/" + str(filename.split(".")[0])

        # Append the DataFrame to the list
        dfs.append(df)

# Concatenate all DataFrames in the list into a single DataFrame
merged_df = pd.concat(dfs, ignore_index=True)
merged_df["genre"] = merged_df["genre"].map(genre_mappings)
merged_df["office"] = merged_df["office"].map(service_mappings)
merged_df["node_id"] = "https://cantusdatabase.org/chant/" + merged_df["node_id"].astype(str)
merged_df["cantus_id"] = "https://cantusindex.org/id/" + merged_df["cantus_id"].astype(str)
merged_df.insert(0, "source_id", merged_df.pop("source_id"))
merged_df.insert(0, "chant_id", merged_df.pop("node_id"))

merged_df.to_csv(OUTPUT_PATH, index=False)
