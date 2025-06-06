# General Reconciliation Notes

- For items like `culture`, where the culture may not exist in WikiData, it may be possible to reconcile with the location or language, if it exists in WikiData and is specific enough. This way, anyone searching for one of these items will still get a sense of the culture from the associated location or language.
	- For example: the people who speak `Big Nambas` do not have an entry in WikiData, but the language does.
	- For example: there is no WikiData entry for `Appalachians` as a culture, but there is an entry for the location of `Appalachia`.
	- The opposite case may also be true, where WikiData does not have an entry for the language but has an entry for the ethnic group or culture.
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

- "lyre" should be reconciled to `yoke lute (Q1814870)`
- "thumb lyre" should be reconciled to `mbira (Q1467960)`
- "bow" on its own should be reconciled to `musical bow (Q1630744)`
- "sticks" should be reconciled to `percussion sticks (Q55721717)`
- "gender" (as an instrument) should be reconciled to `metallophone (Q1165766)`
- "pot", "jug", "earthen pot" and similar articles should be reconciled to `musical jug (Q1342193)`
- "pandora" should be reconciled to `guitar (Q6607)`
- "trough" should be reconciled to `trough zithers (Q55724763)`
- "reed" should be reconciled to `reed instrument (Q42896320)`