# MusicBrainz Reconciliation

Pretty much all the data is already reconciled by MusicBrainz against wikidata, the only thing that isn't is the `type` field for each data type

For each type file, both history and export settings JSON files are located in the `doc/musicbrainz/reconciliation_files` folder

Automatic reconciliation using Wikidata's API was attempted, but yielded poor results, so I went with manual reconciliation for most of the data due to its small nature. Relevant and/or important decisions are listed below:

- For most instances where more than 1 type are listed at once (like "Concert hall / Theatre"), I choose to not reconcile them
- Fields saying "other" or similar values were also not reconciled, due to there not being a good match on wikidata
- For area types, I matched indigenous territory / reserve to `lands inhabited by indigenous peoples` because it's the closest thing I could find on wikidata and encapsulates the concept well, and I matched subdivision to `administrative territorial entity` for the same reason
- For instrument types, I chose to match ensemble to nothing because it's unclear what type of ensemble it is
- For place types, festival stage was not reconciled because there is no match on wikidata
- For series types, run was not reconciled because no suitable match could be found on wikidata, some of the awards wer left unreconciled because it is unclear what they reference, and there is no match on wikidata
- For work types, Beijing opera was left unreconciled because there is no element on wikidata that would indicate a type of work, only the physical beijing opera, which not what we want to match
