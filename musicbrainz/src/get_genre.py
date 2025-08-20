"""
Script for retrieving the "genre" dumps from MusicBrainz and outputting RDF.
"""

import time
import os
import argparse
import requests
import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDFS, RDF

# Constants
URL = "https://musicbrainz.org/ws/2/genre/all"
HEADERS = {
    "User-Agent": "DDMAL-LinkedData-Datalake/1.0 (yueqiao.zhang@mail.mcgill.ca)",
    "From": "yueqiao.zhang@mail.mcgill.ca",
}
MAX_REQUEST_RETRIES = 3
BATCH_SIZE = 50
RATE_LIMIT_DELAY = 1.375  # Default delay between requests (seconds)

WDT = Namespace("http://www.wikidata.org/prop/direct/")
WD = Namespace("http://www.wikidata.org/entity/")
LMMB = Namespace("https://linkedmusic.ca/graphs/musicbrainz/")
MB = Namespace("https://musicbrainz.org/")
MBGE = Namespace(f"{MB}genre/")


def make_request(url, params=None, retries=MAX_REQUEST_RETRIES, timeout=60):
    """Make an HTTP request with retry logic."""
    for attempt in range(retries):
        response = None
        try:
            response = requests.get(
                url=url, headers=HEADERS, params=params, timeout=timeout
            )
            response.raise_for_status()
            return response
        except (
            requests.exceptions.HTTPError,
            requests.exceptions.ConnectTimeout,
            requests.exceptions.ReadTimeout,
            requests.exceptions.ConnectionError,
        ) as exc:
            tqdm.write(
                f"Request error occurred: {exc}. Retry attempt {attempt+1}/{retries}"
            )

            if response and response.status_code == 503:
                # Rate limiting - wait longer
                delay = 30
                tqdm.write(f"Rate limited. Waiting {delay} seconds...")
            else:
                delay = 10

            if attempt == retries - 1:
                raise
            time.sleep(delay)


def fetch_genres():
    """Fetch all genre data from MusicBrainz."""
    params = {"fmt": "json", "limit": str(BATCH_SIZE)}

    # Get total count
    initial_response = make_request(URL, params=params)
    max_records = initial_response.json()["genre-count"]
    time.sleep(RATE_LIMIT_DELAY)

    data = []
    # Use tqdm for progress tracking
    for offset in tqdm(range(0, max_records, BATCH_SIZE), desc="Fetching genres"):
        params["offset"] = str(offset)
        response = make_request(URL, params=params)
        data.extend(response.json()["genres"])
        time.sleep(RATE_LIMIT_DELAY)

    return data


def fetch_wikidata_relations(genre_ids):
    """Using web-scraping technique to fetch Wikidata relations for each genre."""
    relations = []

    for genre_id in tqdm(genre_ids, desc="Fetching Wikidata relations"):
        response = make_request(genre_id, timeout=50)
        soup = BeautifulSoup(response.text, "html.parser")
        wikidata_row = soup.find("th", string="Wikidata:")

        if wikidata_row and wikidata_row.find_next_sibling("td").find("a"):
            wikidata_value = wikidata_row.find_next_sibling("td").find("a").text
            relations.append(f"{WD}{wikidata_value}")
        else:
            relations.append("")

        time.sleep(RATE_LIMIT_DELAY)

    return relations


def main(output_path="../data/rdf/"):
    """Main function to run the genre data collection process and save RDF."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Fetch genre data
    print("Fetching genre data from MusicBrainz...")
    genre_data = fetch_genres()

    # Create dataframe and select needed columns
    df = pd.DataFrame(genre_data)
    df = df[["id", "name"]]

    # Transform IDs into full URLs
    df["genre_id"] = "https://musicbrainz.org/genre/" + df["id"].astype(str)
    df.drop("id", axis=1, inplace=True)

    # Fetch wiki relations
    print("Fetching Wikidata relations...")
    df["relations_wiki"] = fetch_wikidata_relations(df["genre_id"])

    # Create RDF graph
    g = Graph()
    g.bind("wdt", WDT)
    g.bind("wd", WD)
    g.bind("mb", LMMB)
    g.bind("mbge", MBGE)

    for _, row in df.iterrows():
        genre_uri = URIRef(row["genre_id"])
        g.add((genre_uri, RDF.type, LMMB["Genre"]))
        g.add((genre_uri, RDFS.label, Literal(row["name"])))
        if row["relations_wiki"]:
            g.add((genre_uri, URIRef(f"{WDT}P2888"), URIRef(row["relations_wiki"])))

    # Serialize RDF graph to output file (RDF/XML format)
    g.serialize(destination=f"{output_path}/genre.ttl", format="turtle")
    print(f"Saved {len(df)} genres to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch genre data from MusicBrainz")
    parser.add_argument(
        "--output",
        default="../data/rdf/",
        help="Path to save the output RDF file",
    )
    args = parser.parse_args()

    main(args.output)
