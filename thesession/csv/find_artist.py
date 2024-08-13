import requests
import pandas
import time
from bs4 import BeautifulSoup


artist_dict = {}

def get_artist_url(page_url):
    response = requests.get(page_url)
    soup = BeautifulSoup(response.content, "html.parser")

    time.sleep(1)

    # Find the link with the specific artist name
    artist_section = soup.find(string=lambda text: text and "By " in text)
    if artist_section:
        artist_link = artist_section.find_next("a", href=True)
        if artist_link:
            return "https://thesession.org" + artist_link["href"]
    return None

df = pandas.read_csv("../data/reconciled/recordings.csv")

# Get the URL of the artist
for i, artist in enumerate(df["artist"]):
    if artist not in artist_dict:
        artist_dict[artist] = get_artist_url(df["recording_id"][i])

df["artist_url"] = df["artist"].map(artist_dict)
df.to_csv("../data/reconciled/recordings.csv", index=False)