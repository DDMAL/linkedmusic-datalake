# Applying Histories:
> Do this before reading further.
- In the `reconciliation_history` folder, JSON files are generated in OpenRefine via `Undo/Redo > Extract... > Export`.
- These files can be applied to a specific CSV in OpenRefine by using `Undo/Redo > Apply...` and selecting the corresponding JSON.
- This process might cause errors during reconciliation. If this happens, please check below for detailed reconciliation instructions.

# Recordings:
- Transform the `id` column cells into the form `https://thesession.org/recordings/{id}` and the `tune_id` column cells into the form `https://thesession.org/tunes/{id}` to create complete URIs. To do so, selecting the `id` (`tune_id`) column and `edit cells > transform`. Use the regex `"https://thesession.org/recordings/" + value` (`"https://thesession.org/tunes/" + value`).
- Rename the `id` column to `recording_id`.
- Reconcile the `recording` column against the type "album" (Q482994).
- Create a `reconcile > facet > By judgment` facet and a `reconcile > facet > Best candidate's score` facet if they are not already present.
- In the `Best candidate's score` facet, move the slider to 99-101. In the `judgment` facet, choose "none."
- Match the cells using `reconcile > actions > match each cell to its best candidate`.
- Move the `Best candidate's score` facet to 0-98.
- These cells are not present in Wikidata. Ignore them by using `reconcile > actions > create one new item for similar cells`. This operation creates a new item for each unique value in the selected cells, grouping identical values together.
- Close both facets. Go to `reconcile > add column with URLs of matched entities`, and name the new column `recording_wiki`.
- Reconcile artist column against type null. (Currently, we only reconcile the artists which have higher frequency of appearence in the Recordings spreadsheet.) 
- Run `find_artist.py` in the `/thesession/csv` folder to get the artist URL from The Session DB.
- Export the data to CSV.

# Sets:
- Transform the `member_id` column cells into the form `https://thesession.org/members/{id}` by selecting the `member_id` column and `edit cells > transform`. Use the regex `"https://thesession.org/members/" + value`.
- Join the `member_id` column with the `tuneset` column using `"/sets/"` as the separator and write the result in a new column named `tuneset_id`. You can do this in two ways: 1. select the `member_id` column and then `edit column > join columns...`, selecting `tuneset_id` as the second column and specifying `"/sets/"` as the separator, or 2. select the `member_id` column and `edit column > add column based on this column...`, then use the regex `join ([coalesce(cells['member_id'].value,''),coalesce(cells['tuneset'].value,'')],'/sets/')`.
- Remove the `tuneset` column.
- Move the `tuneset_id` column to position 0.
- Transform the `tune_id` column cells into the form `https://thesession.org/tunes/{id}` by selecting the `tune_id` column and `edit cells > transform`. Use the regex `"https://thesession.org/tunes/" + value`.
- Remove the columns `type`, `meter` and `mode` since they are duplicates from the `tunes` graph.
- *Remove the `abc` column since they cause error when uploading to Virtuoso Staging.

# Tunes:
- Transform the `tune_id` column cells into the form `https://thesession.org/tunes/{id}`. To do so, select the `tune_id` column and `edit cells > transform`. Use the regex `"https://thesession.org/tunes/" + value`.
- Rename the `setting_id` column to `temp`.
- Join the `tune_id` column with the `temp` column in a new column called `setting_id`, with separator `"#setting"`. You can do this in two ways: 1. select the `tune_id` column and then `edit column > join columns...`, selecting `temp` as the second column and specifying `"#setting"` as the separator, or 2. select the `tune_id` column and `edit column > add column based on this column...`, then use the regex `join ([coalesce(cells['tune_id'].value,''),coalesce(cells['temp'].value,'')],'#setting')`.
- Delete the `temp` column.
- Reconcile the `type` column against the type "music genre" (Q188451).
- Create a `reconcile > facet > By judgment` facet and a `reconcile > facet > Best candidate's score` facet if they are not already present.
- In the `judgment` facet, choose "none."
- Match the cells using `reconcile > actions > match each cell to its best candidate`.
- The remaining cells are not present in Wikidata. Ignore them by using `reconcile > actions > create one new item for similar cells`.
- Close both facets. Go to `reconcile > add column with URLs of matched entities`, and name the new column `type_wiki`.
- Repeat the reconciliation steps for the `meter` column against "time signature" (Q155234).
- All cells in the `meter` column should be matched. Use `reconcile > actions > match each cell to its best candidate`.
- Transform the `mode` column to add a space between the tonic and the mode. To do so, select the `mode` column and `edit cells > transform`. Use the regex `value.length() > 1 ? value.substring(0,1) + " " + value.substring(1) : value`.
- Repeat the reconciliation steps for the `mode` column against "tonality" (Q192822).
- The `mode` column should have approximately 73% of cells matched. Choose "none" in the `judgment` facet, and match them. Then ignore the remaining cells that are not present in Wikidata with `reconcile > actions > create one new item for similar cells`.
- Create `meter_wiki` and `mode_wiki` columns, respectively.
- *Remove the `abc` column since they cause error when uploading to Virtuoso Staging.

# Aliases and Tune Popularity:
- Transform the `tune_id` column cells into the form `https://thesession.org/tunes/{id}`. To do so, select the `tune_id` column and `edit cells > transform`. Use the regex `"https://thesession.org/tunes/" + value`.
- For Tune Popularity, move the `tune_id` to the beginning.
- Rename `aliases-csv.csv` to `tune-aliases-csv.csv`.

# Events:
- Transform the `id` column cells into the form `https://thesession.org/events/{id}`. To do so, select the `id` column and `edit cells > transform`. Use the regex `"https://thesession.org/events/" + value`.
- Rename the `id` column to `events_id`.
- Join the `longitude` and `latitude` columns into a new column named `coordinate`. To do so, select the `longitude` column and then `edit column > join columns...`, selecting `latitude` as the second column and specifying `" "` as the separator.
- Text transform the cells with Jython to 
```
if str(value)=="": return None 
else: return "Point(" + value + ")"
```
- Text transform the cells with Jython in column `dtstart` and `dtend` to
```
if value is not None: return value[0:10] + "T" + value[11:]
else: return None
```
- Reconcile the `country` column against the type "country" (Q6256).
- Create a `reconcile > facet > By judgment` facet and a `reconcile > facet > Best candidate's score` facet if they are not already present.
- In the `judgment` facet, choose "none" and move the score to 54-101 in the score facet.
- Match each cell to its best candidate.
- Move the score facet to 38-53, and ignore those cells by using `create one new item for similar cells`.
- Delete both facets.
- Add a column with URLs of matched entities, naming it `country_wiki`.
- Reconcile the `area` column against the type "administrative territorial entity" (Q56061). In the reconciliation window, choose "country" as the property `country` (P17).
- Move the score facet to 100-101, and match all entities to their best candidate.
- Move the score facet to 0-101, choose "none" in the `judgment` facet, and reconcile the `area` column again against the type "human settlement" (Q486972). In the reconciliation window, choose "country" as the property `country` (P17).
- Move the score facet to 100-101, and match all entities to their best candidate.
- Move the score facet to 71-72, and match all entities to their best candidate.
- Move the score facet to 0-101, choose "none" in the `judgment` facet, and reconcile the `area` column again against the type "territory" (Q4835091). In the reconciliation window, choose "country" as the property `country` (P17).
- Move the score facet to 100-101, and match all entities to their best candidate.
- Add a column URLs of matched entities, naming it `area_wiki`.
- Reconcile the `town` column against the type "human settlement" (Q486972) and choose "country" as the property `country` (P17).
- Move the score facet to 71-101, inspect, and match the reconciliation data.
- Move the score facet to 0-70, create a new item for each cell.
- Add a column with URLs of matched entities, and name it `town_wiki`.
- Reconcile the `venue` column against type Q77115 and choose "town" as the property `location` (P276).
- Manually reconcile these columns since the rate of accurately reconciled cells is low.
- Add a column URLs of matched entities, naming it `venue_wiki`.

# Sessions:
- Transform the `id` column cells to the form `https://thesession.org/sessions/{id}`. To do so, select the `id` column and `edit cells > transform`. Use the regex `"https://thesession.org/sessions/" + value`.
- Rename the `id` column to `sessions_id`.
- Join the `longitude` and `latitude` columns into a new column named `coordinate`. To do so, select the `longitude` column and then `edit column > join columns...`, selecting `latitude` as the second column and specifying `" "` as the separator.
- Text transform the cells using Jython to 
```
if str(value)=="": return None 
else: return "Point(" + value + ")"
```
- Text transform the cells in column `date` using Jython to
```
if value is not None: return value[0:10] + "T" + value[11:]
else: return None
```
- Reconcile the `country` column against the type "country" (Q6256).
- Create a `reconcile > facet > By judgment` facet and a `reconcile > facet > Best candidate's score` facet if they are not already present.
- In the `judgment` facet, choose "none" and move the score to 60-101 in the score facet.
- Match each cell to its best candidate.
- Move the score facet to 34-59, and ignore those cells by using `create one new item for similar cells`.
- Delete both facets.
- Add a column with URLs of matched entities, naming it `country_wiki`.
- Reconcile the `area` column against the type "administrative territorial entity" (Q56061). In the reconciliation window, choose "country" as the property `country` (P17).
- Move the score facet to 100-101, and match all entities to their best candidate.
- Move the score facet to 0-101, choose "none" in the `judgment` facet, and reconcile the `area` column again against the type "human settlement" (Q486972). In the reconciliation window, choose "country" as the property `country` (P17).
- Move the score facet to 100-101, and match all entities to their best candidate.
- Move the score facet to 71-72, and match all entities to their best candidate.
- Move the score facet to 0-101, choose "none" in the `judgment` facet, and reconcile the `area` column again against the type "territory" (Q4835091). In the reconciliation window, choose "country" as the property `country` (P17).
- Move the score facet to 100-101, and match all entities to their best candidate.
- Add a column with URLs of matched entities, and name it `area_wiki`.
- Reconcile the `town` column against the type "human settlement" (Q486972).
- Move the score facet to 71-101, inspect, and match the reconciliation data.
- Move the score facet to 0-70, create a new item for each cell.
- Add a column with URLs of matched entities, and name it `town_wiki`.
