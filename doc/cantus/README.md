#   CantusDB CSV

**This workflow needs to be updated as Cantus has changed**

##  How to Get Data Dumps
- /linkedmusic-datalake/data/cantus/mappings/sources.json is a file which contains a list of source ids in Cantus DB that is automatically updated. 
- /linkedmusic-datalake/code/cantus/fetch.py makes API calls to Cantus DB and fetchs all the source CSV into the /linkedmusic-datalake/data/cantus/raw/ folder. 
- /linkedmusic-datalake/code/cantus/merge.py merges all the CSVs into one large cantus.csv that contains all the sources.
*   For testing: a sources_short.json is used. It uses the first 10 sources as samples.

- Navigate to the home folder for linkedmusic-datalake/.
- ```python3 ./code/cantus/fetch.py``` -> download all sources CSV
- ```python3 ./code/cantus/merge.py``` -> merge all sources CSV
The ```cantus.csv``` should be imported into OpenRefine for further operations.

##  2. Reconciliation with OpenRefine

### Reconciliation

*   The sources_history.json can be imported directly into OpenRefine by Undo/Redo > Apply > choose the file to skip the following process. However, if the datasets are updated, since the history.json file is specific against a particular test, mistakes are likely to happen.

1.  Reconcile the "office" column against "Prayer in the Catholic Church" instance Q3406098.
2.  Move the best candidate's score facet box to 99-101, match all of them to their best candidate.
3.  Reset the best candidate's score facet, choose none in the judgement facet. Create new item for all of them.
4.  Create new item for all of them.
5.  Reconcile the "genre" column against "music genre" instance Q188451.
6.  Move the best candidate's score facet box to 99-101, match all of them to their best candidate.
7.  Reset the best candidate's score facet, choose none in the judgement facet, create new item for all of them.
8.  Reconcile the "mode" column against "mode" instance Q731978.
9.  Since the mode are numbers, we have to search for the mode names manually.
10. For example, if it's mode 1, then search for a new match > "mode 1" > "dorian mode".
11. For all uncertain modes, create a new item for each.
12. For the two reconciled columns, add column with URLs of matched entities.

*   Made-up URIs of Properties:
https://cantusdatabase.org/marginalia
https://cantusdatabase.org/sequence
https://cantusdatabase.org/office
https://cantusindex.org/id
https://cantusdatabase.org/finalis
https://cantusdatabase.org/extra

##  3. Abbreviation mappings

Some cells in the original CSV export are in abbreviations. Two TSV files in the data/mappings folder contains the official mappings for the abbreviations in Cantus DB. They are used to map the abbreviations in genres column and services colum to their real literals. This process ease reconciliation. 
genres.tsv: "https://cantusdatabase.org/genres/", since the Mass/office column have no importance here, it's removed.
services.tsv: "https://cantusdatabase.org/offices/"

##  4. Export and process after

# DEPRECATED

##  2. Reconcile column names and generating json-ld 
Currently the json-ld is generated as follow:
In `jsonld/generate_jsonld.py`
- Load the reconciled csv as a dataframe in pandas and convert them to json documents (each corresponds to an entry/line in the csv)
- Loop through each json document and edit each entry, creating the compact jsonld. More information can be found in `generate_jsonld.py`
- Generate the jsonld file at `compact.jsonld`
- The contexts used in the compact.jsonld file is imported from `context.jsonld`
