# Cantus Index

## 1. Fetching Data dumps

A list of all Cantus Index chant id (cid) can be found at https://cantusindex.org/json-cids

Each cid can be used to fetch an JSON recordat `https://cantusindex.org/json-cid-data/\<cid\>` (e.g. https://cantusindex.org/json-cid-data/001234)

The script `cantus_index/src/fetch.py` fetches every cid record and merge them into a single file: `cantus_items.json`.

To run `fetch.py`:
1. Navigate to the home folder for `linkedmusic-datalake/`.
2. Run the following command
```bash
python3 cantus_index/src/fetch.py
```


## 2. Reconciliation

- see `reconciliation_procedures.md` in the `cantus_index/doc/` folder

## TODO

- Refine property mappings
- Upload to virtuoso