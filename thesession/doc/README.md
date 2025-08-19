# The Session Database

This document provides instructions for retrieving data dumps and additional guidelines for data reconciliation for The Session Database.

## Data Processing

### Getting the Data Dumps

- Navigate to the home folder for this repo: `/linkedmusic-datalake`
1. Execute:
    ```
    python3 thesession/src/fetch_data.py
    ```
2. This command downloads all data dumps from The Session Database into the `thesession/data/raw/` directory.
3. Verify that the following files are present:
    - `aliases.csv`
    - `events.csv`
    - `recordings.csv`
    - `sessions.csv`
    - `sets.csv`
    - `tune-popularity.csv`
    - `tunes.csv`

### Retrieving Artists

This step assigns a unique URI to each artist, even though these URIs are not currently sourced from Wikidata.

1. Execute:
    ```
    python3 thesession/src/find_artist.py
    ```
2. The script matches artist URLs to entries in `recordings.csv`.
3. Note: This process may take some time. Do not shut down your device until it completes.

### Data Reconciliation

Data reconciliation involves cleaning and standardizing raw data. Two methods are available:

- Use OpenRefine, following the instructions provided in the `/thesession/doc/reconcile_procedures.md` file.
- Alternatively, import the steps from the `thesession/openrefine/history/` folder into OpenRefine for reference.

> Be cautious when using this step, as changes to OpenRefine and The Session may affect the process. Review the data afterward to ensure its accuracy.

## Data Description

### aliases.csv
- Contains alias names for tunes.
- Core entity: `tune_id` (uses the alias name as an attribute).

### events.csv
- Contains details of musical events.
- Core entity: `events_id`.

### recordings.csv
- Contains recordings associated with tunes.
- Core entity: `recording_id`.

### sessions.csv
- Contains information about music sessions.
- Core entity: `sessions_id`.

### sets.csv
- Contains user-generated tune sets (playlists).
- Core entity: `tuneset_id` (linked to `members_id`).

### tune-popularity.csv
- Contains popularity scores for tunes.
- Core entity: `tune_id` (with the score stored as an attribute).

### tunes.csv
- Contains detailed information for all tunes.
- Core entity: `tune_id`.

## Missing Data Dumps

The following entities appear in the front-end search interface of The Session Database, but their data is not publicly available:
- Trips
- Discussions
- Members

## Abandoned Columns

- **abc:** This column may include illegal characters, which could prevent successful uploads into Virtuoso.

### Others
- AccountForReconciliation_updated.txt records the logs or comments for reconciliation of properties or types.