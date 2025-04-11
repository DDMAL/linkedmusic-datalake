"""
fetch the CSV exports from Cantus DB sources data dumps
"""

import json
import os
import time
import requests

# Retrieve the newest sources list
resp = requests.get("https://cantusdatabase.org/json-sources/", timeout=50)
with open("./data/cantus/mappings/sources.json", "w", encoding="utf-8") as sources_json:
    sources_json.write(str((resp.json()).keys()))

# Check if data/raw folder exists.
RAW_PATH = "./data/cantus/raw"
if not os.path.exists(RAW_PATH):
    os.makedirs(RAW_PATH)

# Read the sources to download
SOURCE_PATH = os.path.abspath(
    "./data/cantus/mappings/sources_short.json"
)
with open(SOURCE_PATH, mode="r", encoding="utf-8") as f:
    source_list = json.load(f)

# Send a GET request to the URL
for source_id in source_list:
    src_url = f"https://cantusdatabase.org/source/{source_id}/csv"
    response = requests.get(src_url,  timeout=50)

    # Check if the request was successful
    if response.status_code == 200:
        # Open the file in write-binary mode and write the content
        with open(f"./data/cantus/raw/{source_id}.csv", "wb") as file:
            file.write(response.content)

        print(f"File has been downloaded and saved as {source_id}.csv")
    else:
        print(f"Failed to retrieve the file. Status code: {response.status_code}")

    time.sleep(1)
