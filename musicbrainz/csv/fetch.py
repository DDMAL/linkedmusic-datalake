"""
fetch the latest test data dump files
"""

import os
import time
import requests
from bs4 import BeautifulSoup


def get_latest_json_dump_url():
    """
    get the latest repo
    """
    url = "https://data.metabrainz.org/pub/musicbrainz/data/json-dumps/LATEST"
    resp = requests.get(url, timeout=50).text.strip()
    return resp


def fetch_api_call(url):
    """
    API calls to fetch all .tar.xz files
    """
    response = requests.get(url, timeout=50)
    soup = BeautifulSoup(response.content, "html.parser")

    # Find all links ending with .tar.xz
    tar_xz_files = [
        url + a["href"] for a in soup.find_all("a") if a["href"].endswith(".tar.xz")
    ]

    for src_url in tar_xz_files:
        response = requests.get(src_url, timeout=50)

        local_filename = os.path.join(RAW_PATH, src_url.split("/")[-1])
        with requests.get(src_url, stream=True, timeout=50) as r:
            r.raise_for_status()
            with open(local_filename, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        print(f"downloaded {local_filename}")
        time.sleep(1)


# Check if data/raw folder exists.
RAW_PATH = "../data/raw"
if not os.path.exists(RAW_PATH):
    os.makedirs(RAW_PATH)
latest_url = get_latest_json_dump_url()
fetch_api_call(latest_url)
