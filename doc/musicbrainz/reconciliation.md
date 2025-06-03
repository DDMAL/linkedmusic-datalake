# MusicBrainz Reconciliation

Pretty much all the data is already reconciled by MusicBrainz against wikidata, only the values for a few fields aren't:

- The `type` field for all entity types that have it
- The values for the `key` attribute type for works
- The values for the `gender` field for artists
- The values for the `language`/`languages` field for works

Ichiro confirmed this, stating that we won't reconcile on our end the MusicBrainz data, only data in specific fields.

For each reconciliation, both history and export settings JSON files are located in the `doc/musicbrainz/reconciliation_files` folder

## Types

Automatic reconciliation using Wikidata's API was attempted, but yielded poor results, so I went with manual reconciliation for most of the data due to its small nature. Relevant and/or important decisions are listed below:

- For most instances where more than 1 type are listed at once (like "Concert hall / Theatre"), I choose to not reconcile them because it is impossible to choose between the options.
- Fields saying "other" or similar values were also not reconciled, due to there not being a good match on wikidata
- For area types, I matched indigenous territory / reserve to `lands inhabited by indigenous peoples` because it's the closest thing I could find on wikidata and encapsulates the concept well, and I matched subdivision to `administrative territorial entity` for the same reason
- For instrument types, I chose to match ensemble to nothing because it's unclear what type of ensemble it is
- For place types, festival stage was not reconciled because there is no match on wikidata
- For series types, run was not reconciled because no suitable match could be found on wikidata, some of the awards wer left unreconciled because it is unclear what they reference, and there is no match on wikidata
- For work types, Beijing opera was left unreconciled because there is no element on wikidata that would indicate a type of work, only the physical beijing opera, which not what we want to match

## Keys

The "keys" that were extracted (in the format of "A major", "B mixolydian", etc) were reconciled against Q192822 "tonality". Every major and minor tonality was successfully reconciled with this, but the other modes (mixolydian, lydian, etc) were not. I left them unreconciled after validating that there are no "A mixolydian"-style entries on Wikidata for modes other than major and minor.

## Genders

The genders that were extracted were reconciled against Q48264 "gender identity". The "other" gender was reconciled to "non-binary gender", and the "not applicable" gender not reconciled.

## Languages

The languages that were extracted had their full names reconciled against Q34770 "language", using the ISO 639-3 column as P220 "ISO 639-3 code". A few cases would not get automatically reconciled. For those, I used the SPARQL query below on the [Wikidata Query Service](https://query.wikidata.org/) to find the entities that had the ISO 639-3 code for the language I was looking for, and when there were multiple hits, I would take the one with the most references for the P220 statement.

```SPARQL
SELECT ?language ?languageLabel WHERE {
  ?language wdt:P220 "ksh".
  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
}
```

I chose to not reconcile syr "Syriac" because there is no entity on Wikidata with syr as the value in P220. There is an [entity](https://www.wikidata.org/wiki/Q33538) in Wikidata with syc "Classical Syriac", but since it is a different language then the one represented by syr I did not reconcile it

For qaa, this is a language code reserved for internal use of the database; MusicBrainz uses it to indicate "Artificial (Other)". As such, I have reconciled it to Q3247505 "artificial language", which is meant to represent languages that were constructed for a purpose
