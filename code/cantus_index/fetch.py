import requests
import time
import json

CIDS_URL = "https://cantusindex.org/json-cids"
CID_DATA_URL = "https://cantusindex.org/json-cid-data/{}"
OUTPUT_FILE = "cantus_items.json"
DELAY = 0.2  # seconds between requests chose .2 as .1 would suddenly top working, and have errors

def fetch_cids():
    resp = requests.get(CIDS_URL)
    resp.raise_for_status()
    return json.loads(resp.content.decode("utf-8-sig"))

def fetch_cid_data(cid):
    url = CID_DATA_URL.format(cid)
    resp = requests.get(url)
    resp.raise_for_status()
    return json.loads(resp.content.decode("utf-8-sig"))

def main():
    cids = fetch_cids()
    print(f"Found {len(cids)} CIDs.")
    results = []
    for i, cid in enumerate(cids, 1):
        cid = cid['cid']
        #if i == 5000:
          #  print("Stopping after 10000 CIDs for testing purposes.")
          #  break
        try:
            data = fetch_cid_data(cid)
            results.append(data)
            if i % 50 == 0:
                print(f"[{i}/{len(cids)}] Fetched CID {cid}")
            #print(f"[{i}/{len(cids)}] Fetched CID {cid}")
            time.sleep(DELAY)
        except Exception as e:
            print(f"Error fetching CID {cid}: {e}")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Saved all results to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()