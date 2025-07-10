# Cantus Index

## 1. Getting Data dumps

The rest of the dataset is here: https://cantusindex.org/json-cids

Each cid can be used to fetch an item at https://cantusindex.org/json-cid-data/INSERT_CID, e.g. https://cantusindex.org/json-cid-data/001234
Use the script `fetch.py` in `code/cantus_index/fetch.py`, this gets the data and puts it all into one json file: `cantus_items.json`.


## 2. Reconciliation

- see `reconciliation_procedures.md`