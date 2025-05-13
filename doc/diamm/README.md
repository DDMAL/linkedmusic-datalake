# DIAMM Database Reconciliation

## 1. Fecthing Data

The website supports content negotiation, either by adding `?format=json` to the end of the URL or by sending the HTTP header `Accept: application/json`. To retrieve the data, we use a web crawler, either `code/diamm/crawler.py` or `code/diamm/async_crawler.py` for a much faster one.

## 2. Processing Data

See `doc/diamm/data_layout.md` for a brief overview of the data downloaded by the scraper.

## 3. Reconciling Data

TODO

## 4. Transforming to RDF (JSON-LD)

TODO
