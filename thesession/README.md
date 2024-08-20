# The Session DB

## Getting the Data Dumps

1. Run `python3 fetch_data.py` in the `thesession/csv` folder.
2. This will download all data dumps from The Session database into the `thesession/data/raw` folder.
3. Ensure you have the following files: `aliases.csv`, `events.csv`, `recordings.csv`, `sessions.csv`, `sets.csv`, `tune-popularity.csv`, and `tunes.csv` (7 in total).

## Retrieving Artists

1. Run `python3 find_artist.py` in the `thesession/csv` folder.
2. This script will match artist URLs to the `recordings.csv` file.
3. Please note, this process is slow; do not close your device while it is running.

## Reconciliation

- Using OpenRefine, follow the instructions in the `thesession/data/reconciled/reconcile_procedures.md` manual for reconciliation.
- Optionally, you can use the files in the `reconciliation_history` folder as import steps in OpenRefine.

# Description of the Data Dumps

## `aliases.csv`

- Contains all alias names for specific tunes.
- The core entity is `tune_id`.
- Note: The core entity is not the alias; it uses `tune_id` as the subject and the alias name as an attribute.

## `events.csv`

- Contains musical events and their associated attributes.
- The core entity is `events_id`.

## `recordings.csv`

- Contains recordings related to the tunes.
- The core entity is `recording_id`.

## `sessions.csv`

- Contains music sessions and their associated attributes.
- The core entity is `sessions_id`.

## `sets.csv`

- Contains user-made tune sets (playlists).
- The core entity is `tuneset_id`, which is associated with `members_id`.

## `tune-popularity.csv`

- Contains tunes along with their popularity scores.
- The core entity is `tune_id`.
- Note: The core entity is not the popularity; it uses `tune_id` as the subject and the popularity score as an attribute.

## `tunes.csv`

- Contains all the tunes.
- The core entity is `tune_id`.

# Missing Data Dumps

The "Trips," "Discussions," and "Members" entities appear in the search box of The Session DB front end, but they are not included in the public data dumps that we can access. These entities are not publicly available.

# Abandoned Columns

- `abc`: This column may contain illegal characters that prevent it from being uploaded to Virtuoso.
