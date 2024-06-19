# Recordings:
-   Append the https://thesession.org/{entity_type}/{id} to the id and the tune_id to make them complete URIs
-   Rename the id to recording_id
-   Reconcile the recording column against the type "album" Q482994
-   Make a reconcile>facet>By judgement facet and a reconcile>facet>Best candidate's score facet.
-   In the best candidate's score facet, move the box to 99-101. In the judgement facet, choose none.
-   Match the cells using reconcile>actions>match each cell to its best candidate.
-   Move the best candidate's score facet to 0-98.
-   These cells are not present in Wikidata. Ignore them by reconcile>actions>create a new item for each cell.
-   Close both facets. Go to reconcile>add column with URLs of matched entities, name the new column recording_wiki.