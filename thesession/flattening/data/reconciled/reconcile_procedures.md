# Recordings:
-   Append the https://thesession.org/{entity_type}/{id} to the id and the tune_id to make them complete URIs
-   Rename the id to recording_id
-   Reconcile the recording column against the type "album" Q482994
-   Make a reconcile>facet>By judgement facet and a reconcile>facet>Best candidate's score facet if they are not present.
-   In the best candidate's score facet, move the box to 99-101. In the judgement facet, choose none.
-   Match the cells using reconcile>actions>match each cell to its best candidate.
-   Move the best candidate's score facet to 0-98.
-   These cells are not present in Wikidata. Ignore them by reconcile>actions>create a new item for each cell.
-   Close both facets. Go to reconcile>add column with URLs of matched entities, name the new column recording_wiki.
-   Export to CSV.

# Sets:
-   Append the https://thesession.org/members/{id} to the member_id. Join the member_id column with the tuneset column. 
-   Check the Delete joined columns box, the Write result in new column named box and enter 'tuneset_id', and enter '/sets/' in the Separator between the content of each column box.
-   Move the column tuneset_id to position 0.
-   Transform the tune_id by appending https://thesession.org/tunes/{id} to the cells.
-   Reconcile the column 'type' against the type "music genre" Q188451.
-   Make a reconcile>facet>By judgement facet and a reconcile>facet>Best candidate's score facet if they are not present.
-   In the best candidate's score facet, move the box to 40-101. In the judgement facet, choose none.
-   Match the cells using reconcile>actions>match each cell to its best candidate.
-   Move the best candidate's score facet to 0-39.
-   These cells are not present in Wikidata. Ignore them by reconcile>actions>create a new item for each cell.
-   Close both facets. Go to reconcile>add column with URLs of matched entities, name the new column type_wiki.
-   Repeat the reconciliation steps for meter column against "time signature" Q155234 and mode column against "tonality" Q192822. 
-   The meter column should all be matched. We use reconcile>actions>match each cell to its best candidate.
-   The mode column should have ~73% percent matched. Move the best candidate's score facet to 50-101, and match them. Then move the facet to 17-50, and ignore them.
-   Create meter_wiki column and mode_wiki column respectively.
-   *Remove column abc, date, and setting order for experiment's convenience.

# Tunes:
-   Transform the tune_id by appending https://thesession.org/tunes/{id} to the cells.
-   Reconcile the column 'type' against the type "music genre" Q188451.
-   Make a reconcile>facet>By judgement facet and a reconcile>facet>Best candidate's score facet if they are not present.
-   In the judgement facet, choose none.
-   Match the cells using reconcile>actions>match each cell to its best candidate.
-   These rest cells are not present in Wikidata. Ignore them by reconcile>actions>create a new item for each cell.
-   Close both facets. Go to reconcile>add column with URLs of matched entities, name the new column type_wiki.
-   Repeat the reconciliation steps for meter column against "time signature" Q155234 and mode column against "tonality" Q192822. 
-   The meter column should all be matched. We use reconcile>actions>match each cell to its best candidate.
-   The mode column should have ~73% percent matched. Choose none in the judgement facet, and match them. Then ignore the rest cells that are not present in Wikidata.
-   Create meter_wiki column and mode_wiki column respectively.
-   *Remove column setting_id and username for experiment's convenience.

# Aliases and Tune Popularity:
-   Transform the tune_id by appending https://thesession.org/tunes/{id} to the cells.
-   For Tune Popularity, move the tune_id to the beginning.
