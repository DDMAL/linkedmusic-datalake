"""
Script for retrieving the "genre" dumps since they are not available online.
"""

import time
import requests
from requests.exceptions import HTTPError
import pandas as pd
from bs4 import BeautifulSoup

URL = "https://musicbrainz.org/ws/2/genre/all"
PARAMS = dict(fmt="json", limit="50")
MAX_REQUEST_RETRIES = 3

data = []
max_records = requests.get(url=URL, params=PARAMS, timeout=50).json()["genre-count"]

for i in range(0, max_records, 50):
    PARAMS["offset"] = i
    for j in range(MAX_REQUEST_RETRIES):
        try:
            resp = requests.get(url=URL, params=PARAMS, timeout=50)
            resp.raise_for_status()
            break

        except HTTPError as exc:
            code = exc.response.status_code

            if code == 503:
                if j == 2:
                    raise
                time.sleep(j + 1)
                continue

            raise

    temp = resp.json()
    data += temp["genres"]
    time.sleep(0.02)


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
        relations_wiki.append("")

    time.sleep(0.1)
df["relations_wiki"] = relations_wiki

df.to_csv("data/genre.csv", index=False)
