"""
Script for retrieving the "genre" dumps since they are not available online.
"""
import time
import requests
import pandas as pd

URL = "https://musicbrainz.org/ws/2/genre/all"
PARAMS = dict(fmt="json", limit="50")

data = []
max_records = dict(requests.get(url=URL, params=PARAMS, timeout=500).json())["genre-count"]

for i in range(0, max_records, 50):
    PARAMS["offset"] = i
    resp = requests.get(url=URL, params=PARAMS, timeout=500)
    temp = resp.json()

    try:
        data += dict(temp)["genres"]
    except KeyError:
        print(dict(temp))

    time.sleep(0.1)

df = pd.DataFrame(data)
df = df[["id", "name", "disambiguation"]]

df["id"] = "https://musicbrainz.org/genre/" + df["id"].astype(str)
df.rename(columns={"id":"genre_id"})

df.to_csv("data/genre.csv", index=False)
