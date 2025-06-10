"""
This script is a synchronous web crawler that fetches JSON data from the DIAMM website.
It is highly recommended to use the async version of the crawler instead of the sync version.
It is set up with the assumption that you will pipe stdout to a logfile.
If you want to revisit pages that have already been visited by previous executions of the crawler,
set the REVISIT variable to True.
The script is rate limited to 10 requests per second, or 1 request every 100ms on average,
to avoid overwhelming the server.
"""

import os
import json
import re
from time import sleep, time
import requests

# Regex pattern to match DIAMM URLs, and capture the type and ID
REGEX_MATCH = re.compile(r"https:\/\/www\.diamm\.ac\.uk\/([a-z]+)\/([0-9]+)\/?")
# Regex pattern to match DIAMM URLs for cities and countries only
REGEX_CITY_COUNTRY_REGION = re.compile(
    r"https:\/\/www\.diamm\.ac\.uk\/(cities|countries|regions)\/([0-9]+)\/?"
)

BASE_URL = "https://www.diamm.ac.uk/"
BASE_PATH = "../../data/diamm/raw/"

REVISIT = False  # Set to True if you want to revisit pages visited during previous executions of the crawler

# Minimum time between requests in seconds (10 requests per second)
TIME_BETWEEN_REQUESTS = 0.1

# These pages will be saved, and the rest will be ignored
SAVED_TYPES = [
    "archives",
    "compositions",
    "organizations",
    "people",
    "sets",
    "sources",
    "cities",
    "countries",
    "regions",
]

time_since_last_request = 0


def make_request(url):
    """
    Make a GET request to the given URL and return the JSON response.
    Handles errors and checks for the correct content type.
    If the request fails or the content type is not JSON, it returns None.
    Catch all exceptions to avoid crashing the crawler.
    """
    global time_since_last_request
    # Implement the rate limiting
    sleep(max(0, TIME_BETWEEN_REQUESTS - (time() - time_since_last_request)))
    time_since_last_request = time()

    try:
        response = requests.get(url, timeout=10, headers={"Accept": "application/json"})
        if response.status_code != 200:
            print(f"Failed to fetch {url}: {response.status_code}")
            return None
        if response.headers["Content-Type"] != "application/json":
            print(
                f"Unexpected content type for {url}: {response.headers['Content-Type']}"
            )
            return None
        return response.json()
    except Exception:
        return None


visited = set()

to_visit = []

search_url = f"{BASE_URL}search/?type=all"

while search_url is not None:
    search_data = make_request(search_url)
    print(f"Fetched search data from {search_url}")

    if search_data is None:
        print(f"Failed to fetch or parse search data from {search_url}")
        break

    search_url = search_data["pagination"].get("next")

    if to_visit:
        search_data["results"].extend({"url": v} for v in to_visit)
    to_visit = []

    for res in search_data["results"]:
        if match := REGEX_MATCH.match(res["url"]):
            visit_url = match.group(0)
            page = match.group(1), match.group(2)
            if page[0] not in SAVED_TYPES:
                continue
            if page in visited:
                continue
            visited.add(page)
            if not REVISIT and os.path.exists(
                os.path.join(BASE_PATH, page[0], f"{page[1]}.json")
            ):
                continue
            data = make_request(visit_url)
            print(f"Fetched data from {visit_url}")

            if data is None:
                print(f"Failed to fetch or parse data for {visit_url}")
                continue

            text = json.dumps(data, ensure_ascii=False, indent=4)
            os.makedirs(os.path.join(BASE_PATH, page[0]), exist_ok=True)
            with open(
                os.path.join(BASE_PATH, page[0], f"{page[1]}.json"),
                "w",
                encoding="utf-8",
            ) as f:
                f.write(text)

            for match in REGEX_CITY_COUNTRY_REGION.finditer(text):
                new_page = (match.group(1), match.group(2))
                if not REVISIT and os.path.exists(
                    os.path.join(BASE_PATH, new_page[0], f"{new_page[1]}.json")
                ):
                    continue
                if new_page not in visited:
                    to_visit.append(match.group(0))
