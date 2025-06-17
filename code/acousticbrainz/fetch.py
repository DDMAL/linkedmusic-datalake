"""
Fetch all highlevel data and the partial lowlevel dumps from AcousticBrainz.
"""

import os
import requests

# Hardcode the URLs since they're not getting updated
HIGHLEVEL_URL = "https://data.metabrainz.org/pub/musicbrainz/acousticbrainz/dumps/acousticbrainz-highlevel-json-20220623/"
FEATURES_URL = "https://data.metabrainz.org/pub/musicbrainz/acousticbrainz/dumps/acousticbrainz-lowlevel-features-20220623/"
NUM_FILES = 30  # The dumps are split into 30 files each

HIGHLEVEL_FILES = [
    f"{HIGHLEVEL_URL}acousticbrainz-highlevel-json-20220623-{i}.tar.zst"
    for i in range(NUM_FILES)
]
FEATURE_FILES = [
    f"{FEATURES_URL}acousticbrainz-lowlevel-features-20220623-{k}.tar.zst"
    for k in ("lowlevel", "rhythm", "tonal")
]

OUTPUT_PATH = "../../data/acousticbrainz/raw/"
HIGHLEVEL_OUTPUT_PATH = os.path.join(OUTPUT_PATH, "highlevel")


def fetch_files(file_urls, output_path):
    """
    Fetch files from the given URLs and save them to the specified output path.
    """
    os.makedirs(output_path, exist_ok=True)

    for file_url in file_urls:
        local_path = os.path.join(output_path, os.path.basename(file_url))
        if not os.path.exists(local_path):
            print(f"Downloading {file_url} to {local_path}")
            response = requests.get(file_url, timeout=10, stream=True)
            response.raise_for_status()
            with open(local_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
        else:
            print(f"{local_path} already exists, skipping download.")


if __name__ == "__main__":
    fetch_files(HIGHLEVEL_FILES, HIGHLEVEL_OUTPUT_PATH)
    fetch_files(FEATURE_FILES, OUTPUT_PATH)
    print("All files downloaded successfully.")
