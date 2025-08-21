# Cantus Index

## 1. Getting Data dumps

The dataset is here: https://cantusindex.org/json-cids

Each cid can be used to fetch an item at https://cantusindex.org/json-cid-data/INSERT_CID, e.g. https://cantusindex.org/json-cid-data/001234
Use the script `fetch.py` in `cantus_index/src/fetch.py`, this gets the data and puts it all into one json file: `cantus_items.json`.

1. Navigate to the home folder for `linkedmusic-datalake/`.
2. ```python3 cantus_index/src/fetch.py``` -> download all data and merge into single file

There may be some errors when fetching the data, but the code automatically retries them so no need to worry


## 2. Reconciliation

- see `reconciliation_procedures.md` in the `cantus_index/doc/` folder