# DIAMM Database Reconciliation Documentation

## 1. Fetching Data

The website supports content negotiation, either by adding `?format=json` to the end of the URL or by sending the HTTP header `Accept: application/json`. To retrieve the data, we use a web crawler, either `code/diamm/crawler.py` or `code/diamm/async_crawler.py` for a much faster one. The data is sent to `data/diamm/raw/<type>/<pk>.json`

The async crawler is rate limited to a maximum of 2 simultaneous connections, and up to 10 requests per second (globally, across all workers). This is a rate that was mentioned to be acceptable by Andrew Hankinson in [this comment on pull request #280](https://github.com/DDMAL/linkedmusic-datalake/pull/280#issuecomment-2898558404)

I chose to not download the pages for cities, countries and regions because we can easily reconcile against Wikidata for that. The only information that they contain is the list of archives, sources, and organizations in that city/country/region, which we already have because archives, sources, and organizations also have a field indicating which city/country they're in.

I also chose to not download the pages on authors because they do not contain anything of use at all in terms of classifying or adding data to the other data types in the database. The "author" data type seems to represent (modern) people who wrote papers that reference or mention various institutions or sources.

## 2. Processing Data

See `doc/diamm/data_layout.md` for a brief overview of the data downloaded by the scraper. The script `code/diamm/to_csv.py` parses the downloaded JSON data into CSVs, with columns described in `doc/diamm/csv_fields.md`. Relations, like the list of sources contained in an archive, is stored in the `relations.csv` file, to be reused when we turn the reconciled data into RDF. The CSV files are sent to the `data/diamm/csv/` folder.

## 3. Reconciling Data

All of the CSV files produced by `code/diamm/to_csv.py`, except for `relations.csv`, are reconciled in OpenRefine following the steps outlined in `reconciliation.md`. The folder `doc/diamm/reconciliation_files` contains the history and export template files for the reconciliation of each CSV.

## 4. Transforming to RDF (Turtle)

The `code/diamm/convert_rdf.py` will take the reconciled CSVs and the relations CSV and merge everything and will produce a Turtle file using Wikidata properties. All property mappings are contained in the `DIAMM_SCHEMA` dictionary to make changing mappings easier.

For all properties that were reconciled against Wikidata (e.g., city), if the reconciliation was successful, the Wikidata URI of the item is stored in the property, and if the reconciliation was unsuccessful, the literal name is stored instead.

Some properties of interest:

- P2888 (exact match) is used to indicate a Wikidata ID when the object itself (like an archive) has been reconciled against Wikidata
- P217 (inventory number) is used for shelfmarks, as it's the closest thing I could find and is what ChatGPT suggested to use
- P1449 (nickname) is used for the variant names, as it's the closest thing I could find and is what ChatGPT suggested to use
- P276 (location) is used for provenance organizations because the fact that an organization is the provenance organization of a source means that it most likely was its location at some point in time
- P767 (contributor to the creative work or subject) is used to indicate people that are related to a source, as it's the closest thing I could find for this relationship
- P170 (creator) is used to indicate people that copied a source
- P361 (part of) is used to indicate sets or compositions that are contained in sources

The JSON-LD approach was not followed for this database. However, the beginnings of a context file can be found in the `jsonld_approach/diamm` folder.
