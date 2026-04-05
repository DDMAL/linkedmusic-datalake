
## Summary of the Dataset to Reconcile
The University of Tennessee Song Index is contained within a single spreadsheet/csv

Here is a brief explanation of the columns in the CSV:

- id: I couldn't figure out what use it was, since there is no way to retrieve the entity webpage based on id. 
- reference: same issue as `id`
- sequence: position of the song in the anthology
- title: title of the song; this is also the column from which the URI is built
- composer: composer of the song
- author: author/lyricist/librettist of the song
- first_line: first line of the lyrics
- chorus_first_line: first line of the lyrics of the chorus section
- song_status: empty column
- song_type: genre of the song (e.g., "POPULAR", "SACRED")
- accompaniment: accompanying instrument in the song
- geography: the geographic location ("Africa") or the ethnic group ("Afro-American") from which the song originates
- language_1,language_2,language_3,language_4: language of the song
- call_number: call number of the anthology containing the song
- anthology_title: title of the anthology containing the song
- anthology_status: indicates whether an anthology is lost

## Summary of Cleaning and Reconciliation Operation on Each Column
Be sure to use `UTF-8` encoding. By default, OpenRefine will load the file using "`UTF-8-ROM`" encoding, which will not display many characters correctly

- **language_1/language_2 / language_3 / language_4**
  - Reconciled to Q1288568 (natural language)

- **geography**
  - Reconciled to Q6256 (country)
  - Manually reconciled around twenty entities which are not countries, for example, “AMERINDIAN”, or “AFRO-AMERICAN"

- **accompaniment**
  - Set UNACCOMPANIED to empty before reconciliation
  - Reconciled to Q110295396 (type of musical instrument)

- **song_status**
  - Removed since it contains no data

- **song_type**
  - Reconciled to Q188451 (music genre)

- **title -> uri**
  - No reconciliation was done this time, since almost no songs had a Wikidata entry.
  - Create a column named `uri` from the title. Use `urllib` to turn it into a URL-safe string (for example, `CHILDREN'S SONGS FROM JAPAN` becomes `CHILDREN'S%20SONGS%20FROM%20JAPAN`). There is no need to prepend any URL prefixes during reconciliation since that can be customized during RDF conversion.


- **composer**
  - Split value at the comma (for example, `McCartney P., Lennon J.` becomes two separate rows)
  - Consider reversing family and given name for better reconciliation (e.g., `McCartney P.` becomes `P McCartney`)
  - Create a column with only the value `composer`, using that column as the `occupation(P106)`. Reconciled to Q5 (human)

- **author**
  - Split value at the comma (for example, `McCartney P., Lennon J.` becomes two separate rows)
  - Consider reversing family and given name for better reconciliation (e.g., `McCartney P.` becomes `P McCartney`)
  - Create a column with only the value `lyricist`, using that column as the `occupation(P106)`. Reconciled to Q5 (human). Then, you may try reconciliation again with `poet`, `writer`, or `musician` as the occupation.


- **anthology_title -> anthology_uri**
  - No reconciliation was done this time, since almost no anthologies had a Wikidata entry.
  - Create a column named `uri` from the title. Use `urllib` to turn it into a URL-safe string (for example, `CHILDREN'S SONGS FROM JAPAN` becomes `CHILDREN'S%20SONGS%20FROM%20JAPAN`). There is no need to prepend any URL prefixes during reconciliation since that can be customized during RDF conversion.

- **anthology_status**
  - Clear any value that is not "LOST"
  - Reconcile the value "LOST" to the specific QID `Q63154570` (lost media)
