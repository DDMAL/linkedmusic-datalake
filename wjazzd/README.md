# About Weimar Jazz Database
The Weimar Jazz Database was created as part of the Jazzomat project. Much of the information can be found on the [official website](https://jazzomat.hfm-weimar.de/dbformat/dboverview.html). 

For an even more in depth dive into the project, you can read chapters in the [following book](https://d1wqtxts1xzle7.cloudfront.net/55243585/inside_the_jazzomat_final_rev_oa4-libre.pdf?1512809734=&response-content-disposition=inline%3B+filename%3DInside_the_Jazzomat_New_Perspectives_for.pdf&Expires=1767825454&Signature=GuXygFuslUrc9TcEqJTsp-NZWtGMvTtDvm8-4uvCqWHFW5Fd2OXsNfHIwj6Y1PN4wGxoWO2ielG8fTfp2ZX9viXent09q7LTbipArwkMq0J~U6nfwg8DNakUtaG5i902N5Mc3Pq5jpjOFjFCt5yKVvOZxj0QV2Nap1c84YcV3aj1kZ7WPJY4iKRcGZwasLaWUqn0WJIEj3fne0DfZ5G~ygytq3ySiyJhH726cwSO4yRuocTuq80BXfMH1xoc6ZqzOcamy2~xwr3EOQw0oWt0ytvq7yr6J2hNBNhYRGmLT7ggOcPVZIrE0D5B3CStzZgA~dMWcBrWGva22c4Dz4WNaA__&Key-Pair-Id=APKAJLOHF5GGSLRBV4ZA), starting on page 19.

The official abbreviation of `Weimar Jazz Database` is `WjazzD` (occasionally referred to as `WJD` as well), we will be using the lowercase string `wjazzd` to as a naming convention.

[Jazztube](http://mir.audiolabs.uni-erlangen.de/jazztube/) is a related project by the team behind the Weimar Jazz Database, aiming to help visualize `WjazzD`. Since [Jazztube](http://mir.audiolabs.uni-erlangen.de/jazztube/) webpages are more informative, our URI will point to `http://mir.audiolabs.uni-erlangen.de/jazztube/` instead of `https://jazzomat.hfm-weimar.de/`. 

# How to Obtain The Database
The database can be downloaded at the [official download page](https://jazzomat.hfm-weimar.de/download/download.html) in the form of a SQLite3 database.

# Ingestion Workflow
- Change Directory to Repository Root
- Obtain a copy of the Weimar Jazz Database SQLite file and store it at the path `/wjazzd/data//sql/wjazzd.db`
- Install `sqlite3` if not done already
```bash
sudo apt install sqlite3  # Or 'brew install sqlite' on macOS
```
- Export all tables of SQLite file to CSV
```bash
mkdir -p ./wjazzd/data/raw && \
for t in $(sqlite3 ./wjazzd/data/sql/wjazzd.db ".tables"); do
  echo "Exporting $t"
  sqlite3 -header -csv ./wjazzd/data/sql/wjazzd.db "SELECT * FROM $t;" \
  > ./wjazzd/data/raw/$t.csv
done
```
- Copy relevant CSV to a separate `data/processed` folder (some CSVs, like `melody.csv`, are not worth being converted to Linked Data form) 
```bash
mkdir -p wjazzd/data/processed && cp wjazzd/data/raw/{composition_info.csv,record_info.csv,solo_info.csv,track_info.csv,transcription_info.csv} wjazzd/data/processed/
```
- Reconcile processed CSV using OpenRefine: refer to [reconciliation guideline](./doc/reconciliation_procedures.md)
- After reconciliation, review `shared/rdf_config/wjazzd.toml` to make sure that it matches your reconciled CSV. For more information on how the General RDF Conversion script works, please consult [its documentation](../shared/rdf_conversion/using_rdfconv_script.md)
- After having reviewed the TOML file, run the general rdf conversion script using the following command from the `/shared` directory:
```bash
python -m rdfconv.convert rdf_config/wjazzd.toml
```

# Content of the Database
The [official database homepage](https://jazzomat.hfm-weimar.de/dbformat/dboverview.html) provides a provides a comprehensive overview of each table and field in the database. Below will be provided a quick overview of the entities that are ingested into the LinkedMusic Datalake

## Ingested Entity Types
- solo: a section in a recorded song where a musician is soloing. A solo is part of a song
- track: a song. A track is part of a record (i.e. album) and contains one or more solos
- record: an album. A record contains tracks.
- composition: the jazz composition underlying a solo or a track. Both a solo and the track containing it are linked to the composition.

