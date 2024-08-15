#   The Session DB

##  Get the data dumps

1.  Run ```python3 fetch_data.py``` in the ```thesession/csv``` folder.
2.  This will download all data dumps of The Session database into ```thesession/data/raw``` folder.
3.  Make sure you have "aliases.csv", "events.csv", "recordings.csv", "sessions.csv", "sets.csv", "tune-popularity.csv", "tunes.csv". (7 in total)

##  Get the artists

1.  Run ```python3 find_artist.py``` in the ```thesession/csv``` folder.
2.  This will match the artists URL to the recordings.csv.
3.  This is slow, please do not close the device during this process.

##  Reconciliation

-   Using OpenRefine, follow the ```thesession/data/reconciled/reconcile_procedures.md``` manual for reconciliation.
-   Optionally, use the files in ```reconciliation_history``` folder as import steps in Openrefine.

#   Description of the Data Dumps

##  aliases.csv

-   Contains all aliase names of a specific tune.
-   The core entity is tune_id.
-   The core entity is not the alias. It uses tune_id as the subject and the alias name as an attribute.

##  events.csv

-   Contains musical events and their associated attributes
-   The core entity is events_id

##  recordings.csv

-   Contains the recordings related to the tunes
-   The core entity is recording_id

##  sessions.csv

-   Contains music sessions and their associated attributes
-   The core entity is sessions_id

##  sets.csv

-   Contains user-made tunesets (playlists)
-   The core entity is tuneset_id, it's associated with the members_id.

##  tune-popularity.csv

-   Contains tunes with their popularity number
-   The core entity is tune_id
-   The core entity is not the popularity. It uses tune_id as the subject and the popularity as an attribute.

##  tunes.csv

-   Contains all the tunes
-   The core entity is tune_id.

#   Missing Data Dumps

The "Trips", "Discussions", and "Members" entity appears in the search box of The Session DB front end, but it is not in the public data dumps that we can retrieve. They are not public to us.