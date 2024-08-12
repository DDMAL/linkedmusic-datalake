import requests
import pandas
from bs4 import BeautifulSoup


artist_dict = {}

def get_artist_url(page_url, artist_name):
    response = requests.get(page_url)
    soup = BeautifulSoup(response.content, "html.parser")

    # Find the link with the specific artist name
    artist_section = soup.find(string=lambda text: text and artist_name in text)
    if artist_section:
        artist_link = artist_section.find_next("a", href=True)
        if artist_link:
            if artist_name not in artist_dict:
                artist_dict[artist_name] = "https://thesession.org/" + artist_link["href"]
            return artist_dict[artist_name]
    return None


df = pandas.read_csv("../data/raw/recordings.csv")

artist_name = "By "

# Get the URL of the artist
df["artist_url"] = df["recording_id"].apply(lambda x: get_artist_url(x, artist_name))
df.to_csv("../data/reconciled/recordings.csv", index=False)