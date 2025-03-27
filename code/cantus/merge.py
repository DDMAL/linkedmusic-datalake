"""
Merge all raw Cantus CSV into one Dataframe and export to a new CSV
"""

import os
import glob
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
for filename in glob.glob(f"{INPUT_PATH}/*.csv", recursive=False):
    # Read the CSV file into a DataFrame
    df = pd.read_csv(filename)
    entity_id = (filename.split("/")[-1])[0:-4] # get the source id
    df["source_id"] = f"https://cantusdatabase.org/source/{entity_id}"

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
