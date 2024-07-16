AcousticBrainz Raw JSON to CSV Procedure:

1.  Get data in https://data.metabrainz.org/pub/musicbrainz/acousticbrainz/dumps/.
2.  Run ab_json2csv.py for the CSV folder. An output.csv should be generated.
3.  Reconcile any necessary cells in this CSV using OpenRefine.
4.  For testing, the gender and genres are reconciled against Wikidata, and albums, artists, etc are reconciled to their MusicBrainz links.