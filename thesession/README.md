#   The Session DB

##  Get the data dumps
1.  Run ```python3 fetch_data.py``` in the ```thesession/csv``` folder.
2.  This will download all data dumps of The Session database into ```thesession/data/raw``` folder.

##  Get the artists
1.  Run ```python3 find_artist.py``` in the ```thesession/csv``` folder.
2.  This will match the artists URL to the recordings.csv.

##  Reconciliation
-   Using OpenRefine, follow the ```thesession/data/reconciled/reconcile_procedures.md```
-   Optionally, use the files in ```reconciliation_history``` folder as import steps in Openrefine.