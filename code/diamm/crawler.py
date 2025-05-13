import os
import requests
import json
import re

BASE_URL = "https://www.diamm.ac.uk/"
BASE_PATH = "../../data/diamm/"

REGEX_MATCH = re.compile(r"https:\/\/www\.diamm\.ac\.uk\/([a-z]+)\/([0-9]+)\/?")

REVISIT = False

BAD_PAGES = [
    "documents",
    "cover",
    "admin",
    "cms"
]

visited = set() # tuple (str, str) representing (type, id), example is ("compositions", "117")

to_visit = [("sources", "117")]  # Starting point

while len(to_visit) != 0:
    page = to_visit.pop()
    if page in visited:
        continue
    visited.add(page)
    
    if not REVISIT:
        if os.path.exists(os.path.join(BASE_PATH, page[0], f"{page[1]}.json")):
            visited.add(page)
            continue

    url = f"{BASE_URL}{page[0]}/{page[1]}/"
    response = requests.get(url, timeout=10, headers={"Accept": "application/json"})
    if response.status_code != 200:
        print(f"Failed to fetch {url}: {response.status_code}")
        continue
    if response.headers["Content-Type"] != "application/json":
        print(f"Unexpected content type for {url}: {response.headers['Content-Type']}")
        continue
    print(f"Fetched {url}")

    try:
        data = json.loads(response.text)
    except json.JSONDecodeError:
        print(f"Failed to parse JSON for {url}")
        continue

    os.makedirs(os.path.join(BASE_PATH, page[0]), exist_ok=True)
    with open(os.path.join(BASE_PATH, page[0], f"{page[1]}.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    matches = REGEX_MATCH.findall(json.dumps(data))
    for match in matches:
        if match[0] in BAD_PAGES:
            continue
        if (match[0], match[1]) not in visited:
            to_visit.insert(0, (match[0], match[1]))