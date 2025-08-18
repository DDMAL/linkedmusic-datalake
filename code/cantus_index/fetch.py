import requests
import time
import json

CIDS_URL = "https://cantusindex.org/json-cids"
CID_DATA_URL = "https://cantusindex.org/json-cid-data/{}"
OUTPUT_FILE = "cantus_items.json"
DELAY = 0.05  # seconds between requests, if it breaks, increase the delay
MAX_RETRIES = 5  # Maximum number of retries for a single CID
TIMEOUT = 10  # Timeout for network requests in seconds

def fetch_cids():
    try:
        resp = requests.get(CIDS_URL, timeout=TIMEOUT)  # Added timeout
        resp.raise_for_status()
        return json.loads(resp.content.decode("utf-8-sig"))
    except Exception as e:
        print(f"Error fetching CIDs: {e}")
        return []  # Return an empty list if fetching fails

def fetch_cid_data(cid):
    url = CID_DATA_URL.format(cid)
    resp = requests.get(url, timeout=TIMEOUT)  # Added timeout
    resp.raise_for_status()
    return json.loads(resp.content.decode("utf-8-sig"))

def main():
    cids = fetch_cids()
    if not cids:  # Check for empty or corrupted input
        print("No CIDs found. Exiting.")
        return

    print(f"Found {len(cids)} CIDs.")
    results = []
    for i, cid in enumerate(cids, 1):
        cid = cid['cid']
        retries = 0
        had_error = False
        while retries < MAX_RETRIES:
            try:
                data = fetch_cid_data(cid)
                results.append(data)
                if i % 50 == 0:
                    print(f"[{i}/{len(cids)}] Fetched CID {cid}")
                time.sleep(DELAY)
                if had_error:
                    print(f"Recovered after error, successfully fetched CID {cid}")
                    had_error = False
                break
            except Exception as e:
                had_error = True
                retries += 1
                print(f"Error fetching CID {cid} (attempt {retries}/{MAX_RETRIES}): {e}")
                if retries == MAX_RETRIES:
                    print(f"Failed to fetch CID {cid} after {MAX_RETRIES} attempts. Skipping.")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Saved all results to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()