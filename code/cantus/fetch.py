"""
Fetch the CSV exports from Cantus DB sources data dumps.
Set TESTING to True to use sources_short.json, which contains only a few sources,
otherwise keep it False to get the full database.
"""

import json
import os
import time
import requests

# Set this to True to use sources_short.json, which contains only a few sources
TESTING = False

# Retrieve the newest sources list, skip this if you're only loading the short list
if not TESTING:
    resp = requests.get("https://cantusdatabase.org/json-sources/", timeout=50)
    with open("./data/cantus/mappings/sources.json", "w", encoding="utf-8") as sources_json:
        sources_json.write(json.dumps(resp.json(), indent=4))

# Read the sources to download
SOURCE_PATH = os.path.abspath(
    f"./data/cantus/mappings/sources{"_short" if TESTING else ""}.json"
)
with open(SOURCE_PATH, mode="r", encoding="utf-8") as f:
    source_list = json.load(f)

# Check if data/raw folder exists.
RAW_PATH = "./data/cantus/raw"
if not os.path.exists(RAW_PATH):
    os.makedirs(RAW_PATH)

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

    time.sleep(0.025)  # Sleep for 25ms to avoid overwhelming the server
