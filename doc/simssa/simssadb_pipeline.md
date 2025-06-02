# SimssaDB flattening and json-ld structures

> Summary:

> 1. Upload SQL dump to local postgreSQL database
> 2. With output run `jsonld_approach/simssadb/flattening/SQL_query.py`
> 3. Reconcile `initial_flattened.csv` with OpenRefine
> 4. Reconcile `files.csv` with OpenRefine
> 5. With output run `jsonld_approach/simssadb/flattening/restructure.py`
> 6. With output run `jsonld_approach/simssadb/jsonld/generate_jsonld.py` (which also takes `jsonld/context.jsonld` as the initial context)

## 1. Extracting columns and feature flattening

After uploading the database dump to the local PostgreSQL database, we first select relevant columns and perform initial feature flattening with `psycopg` in `SQL_query.py`

When extracting the files, I found that since there often was more than one file per work, the SQL query would create rows where each data field was duplicated, except for the fields relating to the files, due to the behaviour of the `FULL OUTER JOIN` SQL command.
As such, I decided to instead create a second CSV file that would only contain the files, and there would be a field indicating the musical work that the file corresponded to, allowing us to merge that CSV file with the main CSV file during RDF conversion.
Furthermore, some files aren't linked to any musical works. I chose to simply ignore them when exporting the list of files because files without musical works aren't useful at all for the datalake.

## 2. Reconciliation with OpenRefine

OpenRefine reconciliation was performed on `initial_flattened.csv` and on `files.csv`. You can see the reconciled files `reconciled_wikiID.csv` and `reconciled_files_WikiID.csv`. You can use `jsonld_approach/simssadb/openrefine/history_flattened.json` and `jsonld_approach/simssadb/openrefine/history_files.json` to facilitate reconciliation and `jsonld_approach/simssadb/openrefine/export_template_flattened.json` and `jsonld_approach/simssadb/openrefine/export_template_files.json` to export to the desired csv format.

## 3. Reconcile column names and generating json-ld

Currently the json-ld is generated as follows:

In `generate_jsonld.py`:

1. Convert csv to json documents
2. Loop through each json document and edit each entry, creating the compact jsonld. Also parse the files csv to extract and files associated with each entry.
3. Generate the jsonld file at `compact.jsonld`
4. The contexts used in the `compact.jsonld` file is imported from `context.jsonld`

### TODO: Make the RDF conversion convert to Turtle
