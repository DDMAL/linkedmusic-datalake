"""
fetch the latest test data dump files
"""

import os
import time
import requests

def get_latest_json_dump_url():
    """
    get the latest repo
    """
    resp = requests.get(URL, timeout=50)
    resp.raise_for_status()
    return "https://data.metabrainz.org/pub/musicbrainz/data/json-dumps/" + resp.text.strip()


def fetch_api_call(url):
    """
    API calls to fetch all .tar.xz files
    """

    for file in tar_xz_files:
        file_path = os.path.join(url, file)
        local_path = os.path.join(RAW_PATH, file)
        with requests.get(file_path, stream=True, timeout=50) as r:
            r.raise_for_status()
            with open(local_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        print(f"downloaded {local_path}")
        time.sleep(1)


# Check if data/raw folder exists.
tar_xz_files = [
    "area.tar.xz",
    "artist.tar.xz",
    "event.tar.xz",
    "instrument.tar.xz",
    "label.tar.xz",
    "place.tar.xz",
    "recording.tar.xz",
    "release-group.tar.xz",
    "release.tar.xz",
    "series.tar.xz",
    "work.tar.xz"
]
URL = "https://data.metabrainz.org/pub/musicbrainz/data/json-dumps/LATEST"
RAW_PATH = "./data/musicbrainz/raw/archived/"
if not os.path.exists(RAW_PATH):
    os.makedirs(RAW_PATH)
latest_url = get_latest_json_dump_url()
fetch_api_call(latest_url)
