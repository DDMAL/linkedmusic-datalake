"""
for recording artists in The Session DB, since a large portion of them are not present on Wikidata,
we match them against their artist's webpage on The Session through API calls.
"""

import time
import requests
import pandas
from bs4 import BeautifulSoup


artist_dict = {}


def get_artist_url(page_url):
    """
    Defines a function that extracts an artist's URL from a recording's page.
    """
    response = requests.get(page_url, timeout=50)
    soup = BeautifulSoup(response.content, "html.parser")

    time.sleep(1)

    # Find the link with the specific artist name
    artist_section = soup.find(string=lambda text: text and "By " in text)
    if artist_section:
        artist_link = artist_section.find_next("a", href=True)
        if artist_link:
            return "https://thesession.org" + artist_link["href"]
    return None


df = pandas.read_csv("../data/reconciled/recordings-csv.csv")

# Get the URL of the artist
for i, artist in enumerate(df["artist"]):
    if artist not in artist_dict:
        artist_dict[artist] = get_artist_url(df["recording_id"][i])

df["artist_url"] = df["artist"].map(artist_dict)
df.to_csv("../data/reconciled/recordings-csv.csv", index=False)


# This script helps create more comprehensive linked data by connecting artists in The Session database to their profile pages when Wikidata entries are not available.