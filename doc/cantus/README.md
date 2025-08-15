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

### To work on

Modes are also written in abbreviated form ([guidelines here](https://cantusdatabase.org/description/#Mode)). We need to figure out a way to store all relevant information in mode fields (e.g. transposing, simple polyphony).

## 3. Reconciliation with OpenRefine

### Reconciliation

- The `doc/cantus/openrefine/sources_history.json` can be imported directly into OpenRefine by Undo/Redo > Apply > choose the file to skip the following process. However, if the datasets are updated, since the `sources_history.json` file is specific against a particular test, mistakes are likely to happen.

1. Create new column `source_label` by going to column `holding_institution` then `Edit column > Add column based on this column...` and using the following GREL expression:
```
value + "," + cells["shelfmark"].value
```
2. Create `feast_original`, `service_original`, `mode_original` and `genre_original` columns as copies of the respective columns.
3. Reconcile the `feast` column against "Christian Holy Day" instance Q60075825.
4. Move the best candidate's score facet box to 99-101, match all of them to their best candidate.
5. Reset the best candidate's score facet, choose none in the judgement facet and create new items for all of them.
6. Reconcile the `service` column against "Prayer in the Catholic Church" instance Q3406098.
7. Move the best candidate's score facet box to 99-101, match all of them to their best candidate.
8. Reset the best candidate's score facet, choose none in the judgement facet and create new items for all of them.
9. Reconcile the `genre` column against "music genre" instance Q188451.
10. Move the best candidate's score facet box to 99-101, match all of them to their best candidate.
11. Reset the best candidate's score facet, choose none in the judgement facet, and create new items for all of them.
12. Reconcile the `mode` column against "mode" instance Q731978.
13. Since the mode are numbers, we have to search for the mode names manually, I used the [Wikipedia list of western church modes](https://en.wikipedia.org/wiki/Mode_(music)#Western_Church) for tis.
14. For example, if it's mode 1, then search for a new match > "mode 1" > "dorian mode".
15. For all uncertain modes, create a new item for each.
16. Go to `Export > custom tabular`, then for the column `feast` under `For reconciled cells, output`, select `Matched entity's ID`. Do the same for the columns `service`, `genre` and `mode`.
17. Download as CSV.

TODO: think about what to do for the "*" in the mode column.

## 4. Convert to TTL 

The downloaded CSV can be converted to RDF using the General RDF Conversion script (see [General RDF Conversion Guide](../rdf_conversion/using_rdfconv_script.md)). 

The RDF config of CantusDB is in `code/rdf_config/cantusdb.toml`. Please ensure that the column names of your CSV match the ones listed in the config before following the steps below:

- Move the reconciled CSV to `data/cantus/reconciled`. Make sure the reconciled CSV is named `cantus-reconciled.csv`.
- Change working directory to `/code`
- Run the following command 
```bash
python -m rdfconv.convert rdf_config/cantusdb.toml
```
- The output TTL file should be located at `data/cantus/rdf`