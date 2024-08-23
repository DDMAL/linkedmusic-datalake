# Applying Histories:
> Do this before reading further.
- In the `reconciliation_history` folder, JSON files are generated in OpenRefine via `Undo/Redo > Extract... > Export`.
- These files can be applied to a specific CSV in OpenRefine by using `Undo/Redo > Apply...` and selecting the corresponding JSON.
- This process might cause errors during reconciliation. If this happens, please check below for detailed reconciliation instructions.

# Recordings:
- Append `https://thesession.org/recordings/{id}` to the `id` and `https://thesession.org/tunes/{id}` to the `tune_id` to form complete URIs.
- Rename the `id` column to `recording_id`.
- Reconcile the `recording` column against the type "album" (Q482994).
- Create a `reconcile > facet > By judgment` facet and a `reconcile > facet > Best candidate's score` facet if they are not already present.
- In the `Best candidate's score` facet, move the slider to 99-101. In the `judgment` facet, choose "none."
- Match the cells using `reconcile > actions > match each cell to its best candidate`.
- Move the `Best candidate's score` facet to 0-98.
- These cells are not present in Wikidata. Ignore them by using `reconcile > actions > create a new item for each cell`.
- Close both facets. Go to `reconcile > add column with URLs of matched entities`, and name the new column `recording_wiki`.
- Run `find_artist.py` in the `/thesession/csv` folder to get the artist URL from The Session DB.
- Export the data to CSV.

# Sets:
- Append `https://thesession.org/members/{id}` to the `member_id`. Join the `member_id` column with the `tuneset` column.
- Write the result in a new column, in the name box enter `tuneset_id`, and use `"/sets/"` as the separator between the columns.
- Remove the `tuneset` column.
- Move the `tuneset_id` column to position 0.
- Transform the `tune_id` by appending `https://thesession.org/tunes/{id}` to the cells.
- Remove the columns `type`, `meter` and `mode` since they are duplicates from the `tunes` graph.
- *Remove the `abc` column since they cause error when uploading to Virtuoso Staging.

# Tunes:
- Transform the `tune_id` by appending `https://thesession.org/tunes/{id}` to the cells.
- Rename the `setting_id` column to a new name.
- Join the `tune_id` column with the new column in a new column called `setting_id`, with separator `"#setting"`.
- Delete the new column.
- Reconcile the `type` column against the type "music genre" (Q188451).
- Create a `reconcile > facet > By judgment` facet and a `reconcile > facet > Best candidate's score` facet if they are not already present.
- In the `judgment` facet, choose "none."
- Match the cells using `reconcile > actions > match each cell to its best candidate`.
- The remaining cells are not present in Wikidata. Ignore them by using `reconcile > actions > create a new item for each cell`.
- Close both facets. Go to `reconcile > add column with URLs of matched entities`, and name the new column `type_wiki`.
- Repeat the reconciliation steps for the `meter` column against "time signature" (Q155234) and the `mode` column against "tonality" (Q192822).
- All cells in the `meter` column should be matched. Use `reconcile > actions > match each cell to its best candidate`.
- The `mode` column should have approximately 73% of cells matched. Choose "none" in the `judgment` facet, and match them. Then ignore the remaining cells that are not present in Wikidata.
- Create `meter_wiki` and `mode_wiki` columns, respectively.
- *Remove the `abc` column since they cause error when uploading to Virtuoso Staging.

# Aliases and Tune Popularity:
- Transform the `tune_id` by appending `https://thesession.org/tunes/{id}` to the cells.
- For Tune Popularity, move the `tune_id` to the beginning.
- Rename `aliases-csv.csv` to `tune-aliases-csv.csv`.

# Events:
- Transform the `id` by appending `https://thesession.org/events/{id}` to the cells.
- Rename the `id` column to `events_id`.
- Join the `longitude` and `latitude` columns into a new column named `coordinate`.
- Text transform the cells to `return "Point(" + value + ")"`.
- Reconcile the `country` column against the type "country" (Q6256).
- Create a `reconcile > facet > By judgment` facet and a `reconcile > facet > Best candidate's score` facet if they are not already present.
- In the `judgment` facet, choose "none" and move the score to 54-101 in the score facet.
- Match each cell to its best candidate.
- Move the score facet to 38-53, and ignore those cells by using `create a new item for each cell`.
- Delete both facets.
- Add a column with URLs of matched entities, naming it `country_wiki`.
- Reconcile the `area` column against the type "administrative territorial entity" (Q56061). In the reconciliation window, choose "country" as the property `country` (P17).
- Move the score facet to 100-101, and match all entities to their best candidate.
- Move the score facet to 0-101, choose "none" in the `judgment` facet, and reconcile the `area` column again against the type "human settlement" (Q486972). In the reconciliation window, choose "country" as the property `country` (P17).
- Move the score facet to 100-101, and match all entities to their best candidate.
- Move the score facet to 71-72, and match all entities to their best candidate.
- Move the score facet to 0-101, choose "none" in the `judgment` facet, and reconcile the `area` column again against the type "territory" (Q4835091). In the reconciliation window, choose "country" as the property `country` (P17).
- Move the score facet to 100-101, and match all entities to their best candidate.
- Reconcile the `town` column against the type "human settlement" (Q486972).
- Move the score facet to 71-101, inspect, and match the reconciliation data.
- Move the score facet to 0-70, create a new item for each cell.
- Add a column with URLs of matched entities, and name it `town_wiki`.
- Reconcile the `venue` column against type Q77115 and the `town` column against type Q3957.
- Manually reconcile these columns since the rate of accurately reconciled cells is low.

# Sessions:
- Transform the `id` by appending `https://thesession.org/sessions/{id}` to the cells.
- Rename the `id` column to `sessions_id`.
- Join the `longitude` and `latitude` columns into a new column named `coordinate`.
- Text transform the cells to `return "Point(" + value + ")"`.
- Reconcile the `country` column against the type "country" (Q6256).
- Create a `reconcile > facet > By judgment` facet and a `reconcile > facet > Best candidate's score` facet if they are not already present.
- In the `judgment` facet, choose "none" and move the score to 60-101 in the score facet.
- Match each cell to its best candidate.
- Move the score facet to 34-59, and ignore those cells by using `create a new item for each cell`.
- Delete both facets.
- Add a column with URLs of matched entities, naming it `country_wiki`.
- Reconcile the `area` column against the type "administrative territorial entity" (Q56061). In the reconciliation window, choose "country" as the property `country` (P17).
- Move the score facet to 100-101, and match all entities to their best candidate.
- Move the score facet to 0-101, choose "none" in the `judgment` facet, and reconcile the `area` column again against the type "human settlement" (Q486972). In the reconciliation window, choose "country" as the property `country` (P17).
- Move the score facet to 100-101, and match all entities to their best candidate.
- Move the score facet to 71-72, and match all entities to their best candidate.
- Move the score facet to 0-101, choose "none" in the `judgment` facet, and reconcile the `area` column again against the type "territory" (Q4835091). In the reconciliation window, choose "country" as the property `country` (P17).
- Move the score facet to 100-101, and match all entities to their best candidate.
- Reconcile the `town` column against the type "human settlement" (Q486972).
- Move the score facet to 71-101, inspect, and match the reconciliation data.
- Move the score facet to 0-70, create a new item for each cell.
- Add a column with URLs of matched entities, and name it `town_wiki`.
