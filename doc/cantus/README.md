# CantusDB CSV

## 1. Getting Data Dumps

- `data/cantus/mappings/sources.json` is a file which contains a list of source ids in Cantus DB that is automatically updated when the fetching script is run.
- `code/cantus/fetch.py` updates the above sources file and makes API calls to Cantus DB and fetches all the source CSVs into the `data/cantus/raw/` folder.
- `code/cantus/merge.py` merges all the CSVs into one large cantus.csv that contains all the sources.
  - For testing, a `sources_short.json` is used. It uses the first 10 sources as samples. Set `TESTING` to `True` in `fetch.py` to use this.

1. Navigate to the home folder for linkedmusic-datalake/.
2. ```python3 ./code/cantus/fetch.py``` -> download all sources CSV
3. ```python3 ./code/cantus/merge.py``` -> merge all sources CSV

## 2. Abbreviation mappings

Some cells in the original CSV export are in abbreviations. Two TSV files in the data/mappings folder contains the official mappings for the abbreviations in Cantus DB. They are used to map the abbreviations in genres column and services column to their real literals. This process eases reconciliation.

- [genres.tsv](https://cantusdatabase.org/genres/)
- [services.tsv](https://cantusdatabase.org/offices/)

The `code/cantus/merge.py` script takes care of implementing both abbreviation mappings.

The ```cantus.csv``` file should be imported into OpenRefine for further operations.

## 3. Reconciliation with OpenRefine

### Reconciliation

- The `jsonld_approach/cantusdb/openrefine/sources_history.json` can be imported directly into OpenRefine by Undo/Redo > Apply > choose the file to skip the following process. However, if the datasets are updated, since the `sources_history.json` file is specific against a particular test, mistakes are likely to happen.

1. Create `service_@id`, `mode_@id` and `genre_@id` columns as copies of the respective columns.
2. Reconcile the `service_@id` column against "Prayer in the Catholic Church" instance Q3406098.
3. Move the best candidate's score facet box to 99-101, match all of them to their best candidate.
4. Reset the best candidate's score facet, choose none in the judgement facet and create new items for all of them.
5. Reconcile the `genre_@id` column against "music genre" instance Q188451.
6. Move the best candidate's score facet box to 99-101, match all of them to their best candidate.
7. Reset the best candidate's score facet, choose none in the judgement facet, and create new items for all of them.
8. Reconcile the `mode_@id` column against "mode" instance Q731978.
9. Since the mode are numbers, we have to search for the mode names manually, I used the [Wikipedia list of western church modes](https://en.wikipedia.org/wiki/Mode_(music)#Western_Church) for this.
10. For example, if it's mode 1, then search for a new match > "mode 1" > "dorian mode".
11. For all uncertain modes, create a new item for each.

Made-up URIs of Properties:

- https://cantusdatabase.org/marginalia
- https://cantusdatabase.org/sequence
- https://cantusdatabase.org/office
- https://cantusindex.org/id
- https://cantusdatabase.org/finalis
- https://cantusdatabase.org/extra

These are currently used in the JSON-LD context file, and will be changed to Wikidata properties when the Turtle conversion is implemented.

## 4. Reconcile column names and generating json-ld

Currently the json-ld is generated as follows in `jsonld_approach/cantusdb/jsonld/generate_jsonld.py`:

- Load the reconciled csv as a dataframe in pandas and convert them to json documents (each corresponds to an entry/line in the csv)
- Loop through each json document and edit each entry, creating the compact jsonld. More information can be found in `jsonld_approach/cantusdb/jsonld/generate_jsonld.py`
- Generate the jsonld file at `jsonld_approach/cantusdb/jsonld/compact.jsonld`
- The contexts used in the compact.jsonld file is imported from `jsonld_approach/cantusdb/jsonld/context.jsonld`

The `generate_jsonld.py` script should also be run from the repository root directory.

### TODO: Convert to Turtle instead
