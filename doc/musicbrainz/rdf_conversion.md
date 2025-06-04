# MusicBrainz RDF Conversion

This documents any choices for properties in the RDF conversion process

## Reducing clutter

Due to the nature of the script, we need to store a fairly large amount of mapping data to properly convert the JSONL files to RDF. In an effort to reduce the clutter of constant global variables containing mappings, the mapping dictionaries for the main fields, the relations, and the attributes have been separated to their own JSON files, respectively `mappings.json`, `relations.json`, and `attribute_mapping.json`, all located in the `code/musicbrainz/rdf_conversion_config/` folder, and are loaded by the script. They were separated due to the size of the mappings, they would create too much clutter in the main script otherwise.

Furthermore, the dictionary containing the regex patterns to match URLs and the class definition for `MappingSchema` have also been moved to their own modules, respectively `code/musicbrainz/url_patterns.py` and `code/musicbrainz/mapping_schema.py`, to further reduce clutter at the top of the script.

## A note on data types

- Any literal value not given an explicit type will default to `XSD:string`. This is expected behaviour of the RDF standard.
- Dates are given the type `XSD:date`, this is what wikidata uses, if something has a date and time, it will be in `XSD:datetime`
- Coordinates (lat/lon) are given the `GEO:wktLiteral` type in the format `f"Point({lat} {lon})"`; this is what wikidata uses
- Durations (in seconds) are stored in `XSD:decimal`, as they are numbers, this is also what wikidata does
- Any and all URLs that are stored as plain URLs (instead of having IDs extracted if they links to other databases) kept as Literals. This is because these URLs aren't always URIs and lack the proper RDF URI formatting.

## Miscellaneous notes

- For the `release` entity type, `quality` does not indicate the quality of the release, it is an internal marker for musicbrainz that indicates how good the information about the release is. See the [documentation page](https://musicbrainz.org/doc/Release#Data_quality) for more information.
- For the `release` entity type, `packaging` does not have any property that could fill the purpose, so that field is ignored
- For the `release` entity type, `status` does not neatly map onto a Wikidata property. Instead, I use P1534 "end cause" for values like cancelled, withdrawn, etc, and I use P31 "instance of" for things like bootleg, official album, etc. Additionally, I attempted to reconcile the values of the fields against wikidata, but there are no equivalent entities on Wikidata so I would end up reconciling against improper entities, thus I chose to leave the statuses entirely unreconciled.

## Attributes

The `work` entity type has an additional field `attributes` that contains a list of various attributes for that work. The vast majority of attribute types are more IDs to other databases, but there are a few other things like the key that the work is in, as well as non-Western things like the tala for example, which is the musical meter for Indian music.
The vast majority of the databases don't have a property on Wikidata, and since the field only contains IDs, not full URLs/URIs, I don't store the IDs for which there is no Wikidata ID. The file with all the attributes and the properties they map to can be found in `doc/musicbrainz/rdf_conversion_config/attribute_mapping.json`. Attributes not present or that get mapped to `null`/`None` will be ignored by the RDF conversion script.

Additionally, one of the attribute types is `key`, which represents the tonality of the work (e.g. A major). Since these aren't reconciled against wikidata by MusicBrainz, I reconciled them using OpenRefine, and use the reconciled values in the RDF conversion script. The `doc/musicbrainz/reconciliation.md` file has more details on the reconciliation process.

## Properties

URLs linking to the following databases will be processed with their relevant wikidata property, and every other URL will be put as P2888 "exact match". Matching for the URLs is done with regex because despite there being properties for quite a few of these databases, there will be errors and some will end up listed as "other databases" anyways. Most of the regex patterns are taken from the wikidata pages for the properties, in the section where they list regex patterns to match URLs and extract the relevant IDs for the properties.

To match the URLs, every url is matched against the entire regex list, stopping if a match is found. If a match is found, the relevant ID for the property will be extracted, then the property corresponding to that match will be used, and otherwise, the default (P2888) will be used.

Some databases have multiple properties, differentiating between entity types (like MusicBrainz), while others only have 1 property for all datatypes (like RISM). This is handled by the script because the regex patterns have been customized to properly match what the Wikidata property expects.

- Wikidata: P2888 (there is no other for this), convert from `https://wikidata.org/wiki/...` to `https://wikidata.org/entity/...`
- Geonames: P1566
- Soundcloud: P3040
- Youtube & Youtube Music: P2397 for channels, P1651 for videos, and P4300 for playlists
- Discogs: P1953 for artists, P1954 for works, P1955 for labels
- VGMDB: P3483 for singled/albums (releases), P3511 for organizations (labels)
- BookBrainz: P2607 for authors, P8063 for publishers (labels)
- IMSLP: P839
- IMDb: P345
- Apple Music: P2850 for artists, P2281 for albums, P9550 for labels, P10110 for tracks
- VIAF: P214
- last.fm: P3192
- Rate Your Music: P8392 for releases, P7313 for labels, P5404 for artists, P11622 for concerts, P11600 for venues, P11665 for works, P13056 for tracks
- Metal Archives (Encyclopaedia Metallum): P1952 for bands, P2721 for releases, P8166 for labels, P1989 for artists
- Musik Sammler: P9965 for artists
- Worldcat.org: P10832
- BNF: P268
- RISM: P5504
- Deutschen Nationalbibliothek: P227
- LoC: P244

Now for the other properties:

- To indicate the "main" name, I use RDFS:label instead of P2561 as that's what wikidata does
- To indicate alternate names (possible in other languages), I use P4970 "alternative name" and put a language tag when I can
- To indicate start and end dates, I use P571 "inception" and P576 "dissolved, abolished or demolished" for most things, as that's the property that matches
- To store barcodes, I use P3962 "Global Trade Item Number", which is the catch-all property for barcodes, and the barcode is stored as a string
- To store ASINs (Amazon Standard Identification Number), I use P5749 "Amazon Standard Identification Number", as it is an exact match
- To store IPI (Interested Parties Information) numbers, I use P1828 "IPI name number" as what's in the database is the name number, not the base code
- Label codes are codes issued by the GVL, and they map to P7320 "labelcode"
- To indicate that a release contains a specific disc, I use P527 "has part", which is the inverse of P361 "part of"
- To indicate that a release contains a recording, I use P658 "tracklist"
- To indicate titles of albums, songs, releases, etc I use P1476 "title", which applies to any creative work
- To indicate release/publication dates for songs/albums/releases, I use P577 "publication date", which applies to all works
- To indicate that a release was released by a label, P264 "record label" is used as it's an exact match for the property we need
- To indicate that a release is a part of a release group, I use P361 "part of", because release groups are just groups of releases
- To attribute a release, release group or recording to an artist, I use P175 "performer"
- To indicate that a release was released in a country (this is what release events are), I use P495 "country of origin" as it is used to indicate where a work is from
- For other people related to a release (engineers, art directors, etc), I use P767 "contributor to the creative work or subject" as it's a catch-all for people that contributed in some way to the work
- To indicate musical genres, I use P136 "genre", as it is an exact match for what we want
- To indicate types, I use P31 "instance of" instead of RDF:type because our goal is to mach against wikidata, so we should use its properties as much as possible
- To indicate the area for artists, I use P27 "country of citizenship", as it is already used for this purpose on wikidata
- For people, to indicate place of birth/death I use P19/P20, respectively, and P569/P570 for date of birth/death
- For groups, I use P571/P576 for date of foundation/dissolution and P740 for location of formation, and nothing for location of dissolution, as there is no wikidata property for that
- To indicate start and end dates for events, I use P580 and P582 as that's what they're for
- To indicate start and end dates for labels themselves, I also use P571 and P576
- To indicate the location of a label, I use P17 "country" all the locations I could find are countries, and furthermore, that's the property that Wikidata uses for them
- To indicate the location of a place, I use P131 "located in the administrative territorial entity" as it matches the information we want to convey
- To indicate coordinates for a place, I use P625 "coordinate location", and I represent them as a GEO:wktLiteral, which is what Wikidata does
- To indicate start/end dates for a place, I also use P571/P576
- To indicate the duration of a recording, I use P2047 "duration", the time in the database is in milliseconds, but I convert them to seconds and store it as a XSD:decimal
- To indicate the first release date of a release group, I use P577 "publication date", as the property is an exact match for what we want
- To store the time (and date) that an event took place, I use P585 "point in time"
- The event `setlist` field is ignored as it is difficult to parse and the same data is also located in the `relations` field
