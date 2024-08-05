"""
fetch the test files
"""

import os
import time
import requests
from bs4 import BeautifulSoup


def get_latest_json_dump_url():
    """
    get the latest repo
    """
    url = "https://data.metabrainz.org/pub/musicbrainz/data/json-dumps/"
    response = requests.get(url, timeout=500)
    soup = BeautifulSoup(response.text, "html.parser")

    # Extract all directories
    dirs = [a.text for a in soup.find_all("a") if a.text.startswith("latest-is-")]

    latest_dir = dirs[-1]
    latest_dir = latest_dir[10:]
    resp_url = url + latest_dir + "/"
    return resp_url


def fetch_api_call(url):
    """
    API calls to fetch all .tar.xz files
    """
    response = requests.get(url, timeout=500)
    soup = BeautifulSoup(response.content, "html.parser")

    # Find all links ending with .tar.xz
    tar_xz_files = [
        url + a["href"] for a in soup.find_all("a") if a["href"].endswith(".tar.xz")
    ]

    for src_url in tar_xz_files:
        response = requests.get(src_url, timeout=500)

        local_filename = os.path.join(DEST_FOLDER, src_url.split("/")[-1])
        with requests.get(src_url, stream=True, timeout=500) as r:
            r.raise_for_status()
            with open(local_filename, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        print(f"downloading {src_url}")
        time.sleep(0.1)

DEST_FOLDER = "../data/raw"
latest_url = get_latest_json_dump_url()
fetch_api_call(latest_url)
