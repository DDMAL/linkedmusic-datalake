# The Session Database

This document provides instructions for retrieving data dumps and additional information regarding data reconciliation for The Session Database.

## Data processing

### Getting the Data Dumps

> All folders are based on the linkedmusic-datalake repository.
1. In the `code/thesession/` folder, run:
    ```
    python3 fetch_data.py
    ```
2. This command will download all data dumps from The Session Database into the `data/thesession/raw/` folder.
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

1. In the `code/thesession/` folder, run:
    ```
    python3 find_artist.py
    ```
2. The script matches artist URLs to entries in `recordings.csv`.
3. Please note: This process may take some time. Do not shut down your device until it completes.

### Data Reconciliation

Data reconciliation involves cleaning and standardizing raw data. Two methods are available:

- Use OpenRefine and follow the instructions in the `thesession/data/reconciled/reconcile_procedures.md` file.
- Alternatively, import the steps listed in the `reconciliation_history` folder into OpenRefine for reference.

## Data Description

### aliases.csv
- Contains alias names for tunes.
- Core entity: `tune_id` (used as the subject, with alias name as an attribute).

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
- Core entity: `tune_id` (the score is stored as an attribute of the tune).

### tunes.csv
- Contains details for all tunes.
- Core entity: `tune_id`.

## Missing Data Dumps

The following entities are visible in the front-end search interface of The Session Database, but their data is not publicly available:
- Trips
- Discussions
- Members

## Abandoned Columns

- **abc:** This column may include illegal characters, which could prevent successful upload into Virtuoso.

