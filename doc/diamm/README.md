# DIAMM Database Reconciliation

## 1. Fecthing Data

The website supports content negotiation, either by adding `?format=json` to the end of the URL or by sending the HTTP header `Accept: application/json`. To retrieve the data, we use a web crawler, either `code/diamm/crawler.py` or `code/diamm/async_crawler.py` for a much faster one. The data is sent to `data/diamm/raw/<type>/<pk>.json`

## 2. Processing Data

See `doc/diamm/data_layout.md` for a brief overview of the data downloaded by the scraper. The script `code/diamm/to_csv.py` parses the downloaded JSON data is parsed into CSVs, with columns described in `doc/diamm/csv_fields.md`. Relations, like the list of sources contained in an archive, is stored in the `relations.csv` file, to be reused when we turn the reconciled data into RDF. The CSV files are sent to the `data/diamm/csv/` folder.

## 3. Reconciling Data

All of the CSV files produced by `code/diamm/to_csv.py`, except for `relations.csv`, are reconciled in OpenRefine following the steps outlined in `reconciliation.md`. The folder `doc/diamm/reconciliation_files` contains the history and export template files for each CSV.

## 4. Transforming to RDF (JSON-LD)

TODO
