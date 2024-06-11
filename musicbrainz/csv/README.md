# MusicBrainz JSON -> CSV
Steps:
1.  Get the latest JSON files from https://data.metabrainz.org/pub/musicbrainz/data/json-dumps
    *  Examples in data folder.
2.  Run convert_to_csv.py, specify the entity type in the second argument.
    *  Example command line: 
            cd musicbrainz/csv
            python3 convert_to_csv.py data/test_area area
3.  A out.csv should be generated. Rename it and save it.
4.  This should go to OpenRefine to further reconcile. (?)