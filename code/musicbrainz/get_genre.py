"""
Script for retrieving the "genre" dumps.
"""

import time
import requests
import pandas as pd
from bs4 import BeautifulSoup

URL = "https://musicbrainz.org/ws/2/genre/all"
PARAMS = {"fmt": "json", "limit": "50"}
HEADERS = {
    "User-Agent": "DDMAL-LinkedData-Datalake/1.0 (yueqiao.zhang@mail.mcgill.ca)",
    "From": "yueqiao.zhang@mail.mcgill.ca",
}
MAX_REQUEST_RETRIES = 3

data = []
max_records = requests.get(url=URL, headers=HEADERS, params=PARAMS, timeout=50).json()[
    "genre-count"
]
time.sleep(1)

for i in range(0, max_records, 50):
    PARAMS["offset"] = str(i)
    for j in range(MAX_REQUEST_RETRIES):
        try:
            resp = requests.get(url=URL, headers=HEADERS, params=PARAMS, timeout=60)
            resp.raise_for_status()
            break

        except (requests.exceptions.HTTPError, requests.exceptions.ConnectTimeout, 
                requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as exc:
            print(f"Request error occurred: {exc}. Retry attempt {j+1}/{MAX_REQUEST_RETRIES}")

            # if code == 503:
            if j == MAX_REQUEST_RETRIES - 1:
                raise
            time.sleep(10)
            continue


    resp_json_dict = resp.json()
    data += resp_json_dict["genres"]
    time.sleep(5)
    # The max server request rate if we don't have an agreement with MusicBrainz is 1 req/sec.


df = pd.DataFrame(data)
df = df[["id", "name"]]

df["id"] = "https://musicbrainz.org/genre/" + df["id"].astype(str)
df.rename(columns={"id": "genre_id"}, inplace=True)
relations_wiki = []

for rec in df["genre_id"]:
    resp_wiki = requests.get(rec, timeout=50)

    soup = BeautifulSoup(resp_wiki.text, "html.parser")
    wikidata_row = soup.find("th", string="Wikidata:")
    wikidata_value = ""
    if wikidata_row:
        wikidata_value = wikidata_row.find_next_sibling("td").find("a").text
        relations_wiki.append("http://www.wikidata.org/entity/" + wikidata_value)
    else:
        relations_wiki.append(wikidata_value)

    time.sleep(1)
df["relations_wiki"] = relations_wiki

df.to_csv("../data/output/genre.csv", index=False)
