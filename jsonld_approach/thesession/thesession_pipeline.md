# thesession.org flattening and json-ld structures

> Summary:  
>   1. run script `thesession/flattening/data/fetch_data.py` to download the csv dumps from [adactio/TheSession-data](https://github.com/adactio/TheSession-data). Currently only extracting data from `aliases.csv`, `recordings.csv`, `tune_popularity.csv`, and `tunes.csv`.
>   2. Run script `thesession/flattening/flatten.py` to flatten the data
>   3. Run script `thesession/jsonld/generate_jsonld.py` to generate the compact json-ld


## 1. Extracting columns and feature flattening
The flattening scripts flatten and merge data from the provided source CSV files. These scripts merge data on tune_id and merge with `tunes.csv` to get tune as the main entity for this database.
TODO: the flattening process for `recordings.csv` is hard to understand, should be cleaned.  

## 2. Reconciliation with OpenRefine
Currently thesession.org data is not reconciled with Wikidata objects.

## 3. Reconcile column names and generating json-ld
Currently the json-ld is generated as follow:  
In `generate_naive_json.py`: generate the naive json structure and clean up indexes

In `generate_jsonld.py`:
- Call the generating functions from `generate_naive_json.py`.
- Import the file `naive_json`, add `@context` and other json-ld components as necessary.

## 4. Future Todos:
1. Cleanup recordings flattening code. 