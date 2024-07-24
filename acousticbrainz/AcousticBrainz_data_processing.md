AcousticBrainz Raw JSON to CSV Procedure:

1.  Download data in https://data.metabrainz.org/pub/musicbrainz/acousticbrainz/dumps/. Unzip it and move it into the data/ folder.
2.  Run ab_json2csv.py for the CSV folder. An output.csv should be generated.
3.  Reconcile any necessary cells in this CSV using OpenRefine.
4.  See reconciliation details at /linkedmusic-datalake/csv2rdf/acousticbrainz/ab_reconciliation_details.md