#   1: The procedure:
*   Since all ids and Wikidata links are already reconciled in the conversion process, there's no need to turn to OpenRefine.
-   Steps:
1.  Navigate to ```linkedmusic-datalake/musicbrainz/csv``` folder.
1.  Run ```python3 fetch.py``` to get the latest tar.xz files from the MusicBrainz public data dumps into the local ```data/raw/``` folder.
2.  Run ```python3 untar.py``` to unzip the files and extract the jsonl files needed into the local ```data/raw/extracted_jsonl/mbdump/``` folder.
2.  Run convert_to_csv.py.
    *   Example command line: 
        ```python3 convert_to_csv.py```
3.  A CSV file named by its entity type will be generated in ```data/output/``` folder. It can be used for further operations.

#   2: The data details:
-   In the link provided as below(It provides 2 versions, we usually choose the latest such as 20240626-001001/), we can download archived files which end with suffix ".tar.xz". If we unzip any of them, we will see a "mbdump" folder with a file named by its entity type and without extension. This is the dump in "JSON Lines" format. Each line represents one record in the dump. 
-   The name of the file is just the type of the entity(the class of an instance) in the database. For example, there are types such as area, artist, event, instrument, label, place etc.
-   In every line, there must be an attribute named "id", which is the primary key of each record. When converted into CSV, we rename the id according to "{entity_type}_id" format to be more precise of which entity type we are working with.
-   During the conversion process, for all ids of different entity type (genre_id, artist_id, area_id, etc.), we add the MusicBrainz reference to the id in the format: "https://musicbrainz.org/{entity_type}/{id}". It automatically converts the id to a URI reference.
-   For any record, if it is reconciled with Wikidata link by MusicBrainz bots, then it should have an object in "relations" > "resources" > "url", with the Wikidata link as the value. If it exists, then it is extracted to the CSV file.

# 3: Mapping
- Made-up predicate URLs:
    "packaging": "https://musicbrainz.org/packaging",
    "packaging-id": "https://musicbrainz.org/packaging",
    "media_pregap_id": "https://musicbrainz.org/pregap",
    "media_discs_id": "https://musicbrainz.org/disc",


#   DEPRECATED
#   3: As an experiment data sets:
-   For experiment purposes, you had better only use a small portion of each data dump:
-   So, use the command of bash(for example, extract 3000 entries of an entity), please find the "mbdump" folder and open the terminal at the folder, then exectute:
        head -n 3000 "area">"test_area"
    to get the first 3000 lines from the area data dumps.
-   All other data dumps perform the same procedure.


