# DIAMM Database Reconciliation Documentation

Before starting, you should change your directory to `code/diamm/` as all scripts are written with the expectation that the working directory will be the script's directory.

## 1. Fetching Data

The website supports content negotiation, either by adding `?format=json` to the end of the URL or by sending the HTTP header `Accept: application/json`. Additionally, this content negotiation works on the search interface, and you can query it for data across all data types. The search page will paginate results 50 at a time, and will specify how many pages are left and will give an URL to the next (and previous) page. To retrieve the data, we load the search page for all data types `https://www.diamm.ac.uk/search/?type=all`, iterate through the search results, and the move on to the next page.

Additionally, each page that will be saved is scanned to find URLs corresponding to `cities`, `countries`, or `regions` to load and save those as well.

There are 2 scripts that can achieve this, `code/diamm/fetch.py` is a synchronous script, and `code/diamm/async_fetch.py` is asynchronous, and thus much faster.

The synchronous script is limited to a request every 100ms, but so far has never reached this limit. The async script is rate limited to a maximum of 2 simultaneous connections across 3 workers, 1 of which is for querying the search page and the other 2 are for downloading the item pages. It is also limited to 10 requests per second (globally, across all workers). In addition to this, the searching worker is further limited to 1 request per second. This rate is pending review by Andrew Hankinson in [#285](https://github.com/DDMAL/linkedmusic-datalake/issues/285)

As per discussion in [#288](https://github.com/DDMAL/linkedmusic-datalake/issues/288), we will store pages for cities, countries, and regions to reconcile them, to better handle disambiguations.

As per discussion in [#287](https://github.com/DDMAL/linkedmusic-datalake/issues/287), we will not be storing the bibliographic data as it is a pre-rendered HTML field, and is incredibly difficult to parse. We will still be able to point people to the bibliography on the DIAMM website because we still store DIAMM URLs. As such, there is no need to download the pages on authors because they onl contain bibliographic links, we will only store the links to them.

## 2. Processing Data

See `doc/diamm/data_layout.md` for a brief overview of the data downloaded by the scraper. The script `code/diamm/to_csv.py` parses the downloaded JSON data into CSVs, with columns described in `doc/diamm/csv_fields.md`. Relations, like the list of sources contained in an archive, is stored in the `relations.csv` file, to be reused when we turn the reconciled data into RDF. This includes both one-to-many and many-to-many relations. The CSV files are sent to the `data/diamm/csv/` folder.

## 3. Reconciling Data

All of the CSV files produced by `code/diamm/to_csv.py`, except for `relations.csv`, are reconciled in OpenRefine following the steps outlined in `reconciliation.md`. The folder `doc/diamm/reconciliation_files` contains the history and export template files for the reconciliation of each CSV.

## 4. Transforming to RDF (Turtle)

The `code/diamm/convert_rdf.py` will take the reconciled CSVs and the relations CSV, and will merge everything to produce a Turtle file using Wikidata properties. All property mappings are contained in the `DIAMM_SCHEMA` dictionary to make changing mappings easier.

For all properties that were reconciled against Wikidata (e.g., city), if the reconciliation was successful, the Wikidata URI of the item is stored in the property, and if the reconciliation was unsuccessful, the literal name is stored instead. When the items themselves were reconciled against wikidata (archives, organizations, cities, etc), a triple is created with P2888 linking to the reconciled Q-ID.

The `related_sources` field in the `organizations` and `people` entity types, as well as the `relationships` field for the `sources` entity type are handled separately, and that is detailed in `relationships_properties.md`.

Some properties of interest:

- RDFS:label is used instead of P2561 to indicte the ame of places/objects, as that's what Wikidata uses for the primary label for items
- P2888 (exact match) is used to indicate a Wikidata ID when the object itself (like an archive) has been reconciled against Wikidata
- P131 is used to indicate the city or region an entity is in, and p17 is used for the country
- P217 (inventory number) is used for shelfmarks, as it's the closest thing I could find and is what ChatGPT suggested to use
- P1449 (nickname) is used for the variant names, as it's the closest thing I could find and is what ChatGPT suggested to use
- P276 (location) is used for provenance organizations because the fact that an organization is the provenance organization of a source means that it most likely was its location at some point in time
- P767 (contributor to the creative work or subject) is used to indicate people that are related to a source, as it's the closest thing I could find for this relationship
- P11603 (transcribed by) is used to indicate people that copied a source as one of the alternate uses is to indicate copying
- P361 (part of) is used to indicate sets or compositions that are contained in sources

### JSON-LD

The JSON-LD approach was not followed for this database. However, the beginnings of a context file can be found in the `jsonld_approach/diamm` folder.
