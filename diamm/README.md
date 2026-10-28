# DIAMM Database Documentation

This file details the entire process for the DIAMM database, from fetching the data all the way to converting it into RDF.

Before starting, you should change your directory to `diamm/src/` as all scripts are written with the expectation that the working directory will be the script's directory.

## 1. Fetching Data

The website supports content negotiation, either by adding `?format=json` to the end of the URL or by sending the HTTP header `Accept: application/json`. Additionally, this content negotiation works on the search interface, and you can query it for data across all data types. The search page will paginate results 50 at a time, and will specify how many pages are left and will give an URL to the next (and previous) page. To retrieve the data, we load the search page for all data types <https://www.diamm.ac.uk/search/?type=all>, iterate through the search results, and the move on to the next page.

Additionally, each page that will be saved is scanned to find URLs corresponding to `cities`, `countries`, or `regions` to load and save those as well.

There are 2 scripts that can achieve this, [`diamm/src/fetch.py`](/diamm/src/fetch.py) is a synchronous script, and [`diamm/src/async_fetch.py`](/diamm/src/async_fetch.py) is asynchronous, and thus much faster.

The synchronous script is limited to a request every 100ms, but so far has never reached this limit. The async script is rate limited to a maximum of 2 simultaneous connections across 3 workers, 1 of which is for querying the search page and the other 2 are for downloading the item pages. It is also limited to 10 requests per second (globally, across all workers). In addition to this, the searching worker is further limited to 1 request per second. This rate has been approved by Andrew Hankinson in [#368](https://github.com/DDMAL/linkedmusic-datalake/pull/368#issuecomment-2972496886).

Additionally, the async script has a maximum queue size for the queue of pages to be downloaded that will pause the searching worker if the queue gets too full to help even the load on the search endpoint.

Furthermore, to help with legibility, utility classes for the async script have been moved to the [`diamm/src/utils.py`](/diamm/src/utils.py) module.

As per discussion in [#288](https://github.com/DDMAL/linkedmusic-datalake/issues/288), we will store pages for cities, countries, and regions to reconcile them, to better handle disambiguations.

As per discussion in [#287](https://github.com/DDMAL/linkedmusic-datalake/issues/287), we will not be handling the bibliographic data as it is a pre-rendered HTML field, and is incredibly difficult to parse. We will still be able to point people to the bibliography on the DIAMM website because we still store DIAMM URLs. As such, there is no need to download the pages on authors because they only contain bibliographic links, we will only store the links to them.

## 2. Processing Data

See [`data_layout.md`](./doc/data_layout.md) for a brief overview of the data downloaded by the scraper. The script [`diamm/src/to_csv.py`](/diamm/src/to_csv.py) parses the downloaded JSON data into CSVs, with columns described in [`csv_fields.md`](./doc/csv_fields.md). Relations, like the list of sources contained in an archive, are stored in the `relations.csv` file, to be reused when we turn the reconciled data into RDF. This includes both one-to-many and many-to-many relations. The CSV files are sent to the `diamm/data/csv/` folder.

Additionally, a utility class for the `to_csv.py` script is located in the `diamm/src/utils.py` module.

Person extraction keeps `source_full_name` alongside the cleaned `full_name`,
so parenthesized lifespan/floruit text survives. An optional separate source
`floruit` field is also retained. Follow the
[person-name preservation contract](doc/person_name_preservation.md) when
importing and exporting these columns through OpenRefine.

Archive and person extraction also retains the complete identifier list in
`source_identifiers`. RISM/VIAF scalar columns provide reconciliation hints only
when one distinct nonblank string is available. The
[identifier-list contract](doc/external_identifier_selection.md) describes
classification, multiple values, evidence retention and legacy compatibility.

## 3. Reconciling Data

All of the CSV files produced by [`diamm/src/to_csv.py`](/diamm/src/to_csv.py), except for `relations.csv`, are reconciled in OpenRefine following the steps outlined in [`reconciliation.md`](./doc/reconciliation.md). The `diamm/openrefine/` folder contains the history and export template files for the reconciliation of each CSV.

## 4. Transforming to RDF (Turtle)

The [`diamm/src/convert_rdf.py`](/diamm/src/convert_rdf.py) will take the reconciled CSVs and the relations CSV, and will merge everything to produce a Turtle file using Wikidata properties. Main field mappings are in `DIAMM_SCHEMA`; the preservation contracts below describe additional source-evidence properties.

For reconciled descriptive fields such as genre and type, a successful match supplies a Wikidata URI; otherwise the original literal text remains. When the items themselves were reconciled against Wikidata (archives, organizations, cities, etc), a triple is created with P2888 linking to the reconciled Q-ID.

Person years follow the [year and approximation contract](doc/person_years.md).
Original year, candidate ID and approximation flag stay together in a source
observation. P569/P570 contain year literals only when the source explicitly
marks the year as non-approximate; approximate or unknown values remain
queryable through observations. Year-item IRIs are retained only as validated
reconciliation evidence on those observations. See the contract for query
examples and the change from the older date-object representation.

Original person display names and separate floruit text are string values on
`diamm:sourceFullName` and `diamm:floruit`. They do not supply birth/death dates.
Older CSVs without those optional columns still load; their lost text requires
the matching raw snapshot to recover.

Archive RISM and person RISM/VIAF identifiers follow the
[external identifier text contract](doc/external_identifier_text.md): nonempty
cells remain string literals, preserving leading zeros and long digits. Import
them as text in OpenRefine too. Previously numeric RDF objects now become strings;
the converter cannot recover text already lost from old exports.

New exports use the complete `source_identifiers` JSON cell to emit all supported
RISM/VIAF strings and retain the list on `diamm:sourceIdentifiersJson`. This cell
takes precedence over scalar hints; absent/empty cells use the legacy behavior.
Other schemes remain JSON evidence only. See the identifier-list contract above.

Archive names and sigla follow the [archive text contract](doc/archive_text.md):
nonempty strings retain their exact text under `rdfs:label` and P11550, including
leading zeros and NA-like values. Empty cells emit no corresponding statement;
empty names no longer become `"None"` labels. Import both columns as text in
OpenRefine. Existing name matches and source/location links remain independent.

The [identifier validation contract](doc/identifier_validation.md) documents
complete bare-QID matching, preserved unmatched names, import-safe conversion
and offline regression coverage. Run `poetry run python scripts/check_offline.py`
from the repository root to include the DIAMM tests.

The `related_sources` field in the `organizations` and `people` entity types, as well as the `relationships` field for the `sources` entity type are handled separately, and that is detailed in [`relationships.md`](./doc/relationships.md).

Some properties of interest:

- RDFS:label is used instead of P2561 to indicate the name of places/objects, as that's what Wikidata uses for the primary label for items, including for the title of compositions
- P2888 (exact match) is used to indicate a Wikidata ID when the object itself (like an archive) has been reconciled against Wikidata
- P131 is used to indicate the city an entity is in, and P17 is used for the country. P131 is only used to point to the most specific point (city), and the city will point to the region.
- RDFS:label is used for shelfmarks for sets, as it essentially is the name/label for the set
- skos:altLabel is used for the variant names, as it's what Wikidata uses
- P276 (location) is used for provenance organizations because the fact that an organization is the provenance organization of a source means that it most likely was its location at some point in time
- P11603 (transcribed by) is used to indicate people that copied a source as one of the alternate uses is to indicate copying
- P361 (part of) is used to indicate sets or compositions that are contained in sources

### JSON-LD

The JSON-LD approach was not followed for this database. However, the beginnings of a context file can be found in the `diamm/jsonld_approach/` folder.
