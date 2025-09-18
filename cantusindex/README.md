# Cantus Index

## 1. Fetching and Merging Data 

### 1.1 Fetching Data

- A list of all Cantus Index chant ids (`cid`) can be found at [https://cantusindex.org/json-cids](https://cantusindex.org/json-cids).
- Each `cid` can be used to fetch a JSON record at `https://cantusindex.org/json-cid-data/<cid>` (e.g. [https://cantusindex.org/json-cid-data/001234](https://cantusindex.org/json-cid-data/001234)).
- The script `cantusindex/src/fetch.py` fetches every `cid` record and saves it as a JSON file under `cantusindex/data/raw`

To run `fetch.py`:
1. Navigate to the home folder for `linkedmusic-datalake/`.
2. Run the following command:
   ```bash
   python3 cantusindex/src/fetch.py
   ```

### 1.2 Merging Data
- Once fetching is complete, `cantusindex/src/merge.py` can merge every JSON record under `cantusindex/data/raw` into a single CSV file

To run `merge.py`
1. Navigate to the home folder for `linkedmusic-datalake/`.
2. Run the following command:
   ```bash
   python3 cantusindex/src/merge.py
   ``` 

The output CSV file is saved as `cantusindex/data/merged/cantusindex.csv`: you should import this file into OpenRefine for Reconciliation 

## 2. Reconciliation

- See `reconciliation_procedures.md` in the `cantusindex/doc/` folder for details on reconciliation steps and procedures.

## 3. RDF Conversion

The merged JSON data can be converted to RDF using the General RDF Conversion script (see [General RDF Conversion Guide](/shared/rdf_conversion/using_rdfconv_script.md)).


The RDF config for Cantus Index is `shared/rdf_config/cantusindex.toml`. Follow the steps below in order to convert the database to RDF:

- Move your reconciled CSV file to `cantusindex/data/reconciled`. Make sure the file is named `cantusindex-reconciled.csv`.
- Ensure that column names in your reconciled CSV match those listed in the config.
- Change working directory to `/shared`
- Run the following command:
  ```bash
  python -m rdfconv.convert rdf_config/cantusindex.toml
  ```
- The output TTL file should be located at `cantusindex/data/rdf`
