"""
fetch the CSV exports
"""

import json
import os
import time
import requests

# URL of the file to download
SOURCE_PATH = os.path.join(
    os.path.dirname(__file__), "../data/mappings/sources_short.json"
)
with open(SOURCE_PATH, mode="r", encoding="utf-8") as f:
    SOURCE_LIST = json.load(f)

# Send a GET request to the URL
for src in SOURCE_LIST:
    SRC_URL = "https://cantusdatabase.org/source/" + str(src) + "/csv"
    response = requests.get(SRC_URL,  timeout=500)

    # Check if the request was successful
    if response.status_code == 200:
        # Open the file in write-binary mode and write the content
        with open(f"../data/raw/{src}.csv", "wb") as file:
            file.write(response.content)

        print(f"File has been downloaded and saved as {src}.csv")
    else:
        print(f"Failed to retrieve the file. Status code: {response.status_code}")

    time.sleep(0.1)
