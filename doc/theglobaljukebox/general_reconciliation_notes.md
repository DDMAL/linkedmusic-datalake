# General Reconciliation Notes

- Some vocalizations and items used as instruments are not typically classified in musical categories on WikiData, but can still be reconciled.
  - E.g. "audience interjections" may be reconciled to `interjection (Q83034)`; "stamping" may be reconciled to `stomping (Q104787204)`; "sound of creaking hammock" may be reconciled to `hammock (Q193823)`
- Some instruments may not be found in WikiData, but their family may have an entry. In this case, reconcile the item with the family of instruments. This way, people can still find these items when searching for a more general category.
  - E.g. specific drums, percussion, and bells not found in WikiData may be reconciled to the more general family categories of `drum (Q11404)`, `percussion instrument (Q133163)`, and `bell (Q101401)`.
  - E.g. "urghul" is not in WikiData, but `viol (Q40125)` is

# Commonly used WikiData items and properties

## `human settlement (Q486972)` and `sovereign state (Q3624078)`

- Useful for reconciling against locations
- Items like `city (Q515)` and `town (Q3957)` are more strictly defined, but fall within the category of `human settlement` and so using the broader category can match more entries

## `ethnic group (Q41710)`

- Denotes people who identify with each other based on shared traits such as culture, language, ancestors, and history.
- Not to be exchanged for `human race (Q3254959)`, which refers to the physical traits, ancestry, genetics, or social relations of a group of people and is inaccurate.
- Also differing from `culture (Q11042)`, which does not refer to the people themselves, but instead denotes their practices, beliefs, and material traits.
- Also differing from `civilization (Q8432)`, which may encompass many cultures and ethnic groups, and refers to a complex society including its urban development, social stratification, governments, and symbolic systems of communication.

## `modern language (Q1288568)`

- While there are multiple WikiData entries for language, (including `language (Q34770)` and `language (Q315)`), `modern language` only includes currently spoken languages.
  - constructed languages, ancient languages, proto-languages, and fictional languages would all fall under "language" but not "modern language".
- Some datasets may include dead languages such as Old English or Latin and in these cases, another entry may be more useful to reconcile against, such as `dead language (Q45762)`.

## `song type (Q107356781)` and `music genre (Q188451)`

- "Song type" refers to the function, context, or structural form of a song.
  E.g. lullaby, anthem, ballad, hymn, dirge, etc.
- "Music genre" refers to the musical style or tradition a song belongs to
  - E.g. pop, rock, jazz, blues, folk, etc
- Both of these WikiData items can be useful for columns labeled "genre"
- Some song types may not have WikiData entries, but their corresponding dances do, such as "war dance" and "social dance"

## `voice type (Q1063547)`

- Useful for reconciling human voices as instruments.

## `ISO 639-3 code (P220)`

- Useful for accurately identifying languages.

## `Köppen climate classification (P2564)` and `category in the Köppen climate classification systems (Q23702033)`

- Established classification for region climates.

# Specific Reconciliation Instances

## Instruments

- "lyre" should be reconciled to `yoke lute (Q1814870)`
- "thumb lyre" should be reconciled to `mbira (Q1467960)`
- "bow" on its own should be reconciled to `musical bow (Q1630744)`
- "sticks" should be reconciled to `percussion sticks (Q55721717)`
- "gender" (as an instrument) should be reconciled to `metallophone (Q1165766)`
- "pot", "jug", "earthen pot" and similar articles should be reconciled to `musical jug (Q1342193)`
- "pandora" should be reconciled to `guitar (Q6607)`
- "trough" should be reconciled to `trough zithers (Q55724763)`
- "reed" should be reconciled to `reed instrument (Q42896320)`

## Miscellaneous

- "[US state] Black" will often have a WikiData entry of the form "African Americans in [U.S. State]"
- "Tibet" should be reconciled to `Tibet` (Q17252).
- "Indochinese Peninsula" should be reconciled to `Mainland Southeast Asia` (Q43467)
- "Western Isles" should be reconciled to `Outer Hebrides` (Q80967)
- "Urals Dist" should be reconciled to `Ural` (Q1322976)
- "Persia" should be reconciled to `Iran` (Q794)
- "E England" should be reconciled to `East of England` (Q48006)
- "Northwestern Dist" (of Russia) should be reconciled to `Northwestern Federal District` (Q383093)

# Missing data

## Humans/Musical Groups

- Most of the humans and musical groups in this database (specifically the metadata file of the Urban Strain dataset) are straightforward to match. However, there are some that do not contain WikiData entries, including:

  - James Lowe of The Electric Prunes
  - George Chambers of The Chambers Brothers
  - Volde Faut of The Stomp Six (which also does not have an entry)
  - Bob Gilette of The Wolverines
  - Earl Bolick of The Blue Sky Boys
  - Bea Lilly of The Lilly Brothers
  - Billy Hicks of Eubie Blake and the Shuffle Along Orchestra (also no entry)
  - Joe Schenk of Van & Schenk
  - Jerry Joyce and his orchestra
  - Jack Taylor (bassist active in the 1930s)
  - Simeon Hatch (pianist active in the 1930s/40s)
  - Joe Dupars (1960s trumpet)
  - Louis Blackburn (The Ronettes trombonist)
  - The Paragon Ragtime Orchestra
  - LaForest Dent (Bennie Moten's Kansas City Orchestra saxophonist)
  - The Raelettes (associated with Ray Charles)
  - Frank Rodriguez (? & the Mysterians organist)
  - Uncle Dane Macon (1920s banjoist/singer/entertainer)
  - Kirk McGee (fiddler for Uncle Dane Macon)
  - Jesse Simpkins (Louis Jordan & His Tympany Five bassist)
  - Millard J. Thomas (1950s bassist)
  - Billy Carter (1960s organist)
  - Tommy Lindsey (1930s trumpeter)
  - The Cotton Pickers
  - Bennie Kreuger (The Cotton Pickers clarinetist)
  - Bob Cusumano (Tommy Dorsey band trumpeter)
  - Gene Traxler (Tommy Dorsey band bassist)
  - Charles Smith (Kool & The Gang guitarist)
  - Clyde Baum (1940s mandolinist)
  - Larry Wellborn (1950s bassist)
  - Uncle John Turner (percussionist)
  - Fred Whiting (Al Dexter and his Troopers bassist)
  - Hezzie Bryant (Cliff Bruner's Texas Wanderers bassist)
  - Cincinnati's University Singers and Theater Orchestra
  - Marlin Greene (1960s guitarist)
  - Darryl Jones (guitarist who played with Lionel Richie)
  - Peewee Lambert (The Stanley Brothers mandolinist)
  - Francis Vigneau (pianist associated with Guy Lombardo)
  - Clifton White (1950s guitarist)
  - Leroy Harris (Earl Hines and his Orchestra saxophonist and clarinetist)
  - Marvin Saxbe (The Stomp Six guitarist)
  - Ron Tooley (trumpeter for James Brown)
  - John Williams (saxophonist for Andy Kirk & his Twelve Clouds of Joy)
  - Andy Kirk & his Twelve Clouds of Joy
  - Ray Charles Orchestra
  - Chuck Lowry (singer for The Pied Pipers)

## Instruments

- Farfisa organ
