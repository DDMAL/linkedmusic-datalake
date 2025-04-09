"""
Script for retrieving the "genre" dumps from MusicBrainz.
"""

import time
import os
import argparse
import requests
import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm

# Constants
URL = "https://musicbrainz.org/ws/2/genre/all"
HEADERS = {
    "User-Agent": "DDMAL-LinkedData-Datalake/1.0 (yueqiao.zhang@mail.mcgill.ca)",
    "From": "yueqiao.zhang@mail.mcgill.ca",
}
MAX_REQUEST_RETRIES = 3
BATCH_SIZE = 50
RATE_LIMIT_DELAY = 1  # Default delay between requests (seconds)


def make_request(url, params=None, retries=MAX_REQUEST_RETRIES, timeout=60):
    """Make an HTTP request with retry logic."""
    for attempt in range(retries):
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
            print(f"Request error occurred: {exc}. Retry attempt {attempt+1}/{retries}")

            if response.status_code == 503:
                # Rate limiting - wait longer
                delay = 30
                print(f"Rate limited. Waiting {delay} seconds...")
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
    """Fetch Wikidata relations for each genre."""
    relations = []

    for genre_id in tqdm(genre_ids, desc="Fetching Wikidata relations"):
        response = make_request(genre_id, timeout=50)

        soup = BeautifulSoup(response.text, "html.parser")
        wikidata_row = soup.find("th", string="Wikidata:")

        if wikidata_row and wikidata_row.find_next_sibling("td").find("a"):
            wikidata_value = wikidata_row.find_next_sibling("td").find("a").text
            relations.append(f"http://www.wikidata.org/entity/{wikidata_value}")
        else:
            relations.append("")

        time.sleep(RATE_LIMIT_DELAY)

    return relations


def main(output_path="../data/output/genre.csv"):
    """Main function to run the genre data collection process."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Fetch genre data
    print("Fetching genre data from MusicBrainz...")
    genre_data = fetch_genres()

    # Create dataframe
    df = pd.DataFrame(genre_data)
    df = df[["id", "name"]]

    # Transform IDs
    df["genre_id"] = "https://musicbrainz.org/genre/" + df["id"].astype(str)
    df.drop("id", axis=1, inplace=True)

    # Fetch wiki relations
    print("Fetching Wikidata relations...")
    df["relations_wiki"] = fetch_wikidata_relations(df["genre_id"])

    # Save to CSV
    df.to_csv(output_path, index=False)
    print(f"Saved {len(df)} genres to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch genre data from MusicBrainz")
    parser.add_argument(
        "--output",
        default="../data/output/genre.csv",
        help="Path to save the output CSV file",
    )
    args = parser.parse_args()

    main(args.output)
