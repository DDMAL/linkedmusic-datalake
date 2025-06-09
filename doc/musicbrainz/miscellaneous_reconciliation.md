# MusicBrainz Reconciliation

Please read the section **4. Extracting and Reconciling Unreconciled Fields** in README.md before reading this document.

Pretty much all MusicBrainz data are already reconciled with Wikidata (Ichiro confirmed that MusicBrainz entities don't need additional reconciliation), only the values in the following fields are not:

- The `type` field for all entity types that have it
- The values for the `key` attribute type for works
- The values for the `gender` field for artists
- The values for the `language`/`languages` field for works
- The values for the `packaging` field for works

There is also the field `relationship` that is unreconciled. This field is treated separately in `relations.md`.

For each reconciliation, both OpenRefine history and export settings JSON files are located in the `doc/musicbrainz/reconciliation_files` folder

## Types

`types` are subclasses of a given `entity-type`. For example, `municipality` is a possible `type` of `area`.

Automatic reconciliation using Wikidata's API was attempted, but yielded poor results, so I went with manual reconciliation for most of the data due to its small nature. Relevant and important decisions are listed below:

- For most instances where more than 1 types are listed at once (e.g. "Concert hall / Theatre"), I choose to not reconcile at all because it is impossible to choose between the options.
- Fields saying "other" or similar values were also not reconciled, due to there not being a good match on Wikidata.
- For area types, I matched `indigenous territory / reserve` to `lands inhabited by indigenous peoples` because it's the closest thing I could find on Wikidata that encapsulates both concepts. I matched `subdivision` to `administrative territorial entity` for the same reason.
- For instrument types, I chose to leave `ensemble` unreconciled because it's unclear what type of ensemble it is.
- For place types, `festival stage` was not reconciled because there is no match on Wikidata.
- For series types, `run` was not reconciled because no suitable match could be found on Wikidata. Some of the awards were left unreconciled because they are unclear and have no match on Wikidata.
- For work types, Beijing opera was matched to [Q335101](https://www.wikidata.org/entity/Q335101) "Peking opera" as it seems to match exactly what this is

## Keys

`key` is the tonality of the musical work

The "keys" that were extracted (in the format of "A major", "B mixolydian", etc.) were reconciled against Q192822 "tonality". Every major and minor tonality was successfully reconciled with this, but for the other modes, it was decided to reconcile them against the musical note of the tonic (e.g. [Q744346 "A"](https://www.wikidata.org/wiki/Q744346)) until we can create a new property for the mode (see [#339](https://github.com/DDMAL/linkedmusic-datalake/issues/339) for more information). However, this is a clear violation of the range of [P826 "tonality"](https://www.wikidata.org/wiki/Property:P826), as instances of musical notes are not included in the property constraint.

However, modes without tonic (e.g. [lydian mode(Q686115)](https://www.wikidata.org/entity/Q686115)) do exist as Wikidata entities. We may consider, for example, specifying the mode as [lydian mode(Q686115)](https://www.wikidata.org/entity/Q686115) and the tonic (Wikidata property to be created) as [A(Q744346)](https://www.wikidata.org/wiki/Q744346).

Alternatively, we may consider creating these modes ourselves since they are referenced often across databases (e.g. in The Session).

## Genders

The genders that were extracted were reconciled against Q48264 "gender identity". The "other" gender was reconciled to "non-binary gender", and the "not applicable" gender is not reconciled.

## Languages

The languages that were extracted had their full names reconciled against Q34770 "language", using the ISO 639-3 column as P220 "ISO 639-3 code". A few cases would not get automatically reconciled. For those, I used the SPARQL query below on the [Wikidata Query Service](https://query.wikidata.org/) to find the entities that had the ISO 639-3 code for the language I was looking for, and when there were multiple hits, I would take the one with the most references for the P220 statement.

```SPARQL
SELECT ?language ?languageLabel WHERE {
  ?language wdt:P220 "ksh".
  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
}
```

(Replace "ksh" with the language code you want)

I chose to not reconcile `syr`, which is supposed to be "Syriac", because there is no entity on Wikidata with syr as the value in P220. There is [Classical Syriac](https://www.wikidata.org/wiki/Q33538) in Wikidata, which has a language code of `syc`. But since it is a different language then the one represented by `syr`, I did not reconcile it.

`qaa` is a language code reserved for internal use of the database; MusicBrainz uses it to indicate "Artificial (Other)". As such, I have reconciled it to Q3247505 "artificial language", which is meant to represent languages that were constructed for a specific purpose (in this case for a song).

## Packagings

Reconciliation using OpenRefine's API was attempted against Q66157003 "packing material" and Q207822 "product packaging", both yielding very poor results. As a result of this and due to the small size of the dataset, I performed manual reconciliation for the packagings. Relevant and important decisions are listed below:

- For quite a few packaging types (paper sleeve, digifile, to name a few), when using Wikidata's search bar, I would get redirected to [Q63367831 "optical disc packaging"](https://www.wikidata.org/wiki/Q63367831), despite that page making no references to that packaging type, and as such I left them unreconciled
- I did not reconcile the "None" or "Other" types to anything
- I reconciled the "Book" type to Q571 "book" (your standard book) because I could not find a more suitable choice, and I feel like reconciling to this is better than not reconciling it, same thing for the "Box" type with Q188075 "box"
- I reconciled "slim jewel case" to Q1023101 "jewel case" as there is no slim variant on Wikidata, and I like doing this is more useful than not reconciling it
- For "Metal tin", I reconciled it to Q15706035 "tin" as it's the closest thing I could find
- For "Snap case", there is [Q7547268 "snap case"](https://www.wikidata.org/wiki/Q7547268), but at the time of writing this, that entity has no descriptions or statements, so I have no clue what it's supposed to be, and as such didn't reconcile this entry
