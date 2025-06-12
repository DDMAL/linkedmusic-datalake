# MusicBrainz RDF Conversion

This documents any choices for properties in the RDF conversion process, as well as other information relating to the RDF conversion process

## Reducing Clutter

Due to the nature of the RDF conversion script, we need to store a fairly large amount of mapping data to properly convert the JSONL files to RDF.

In an effort to reduce the clutter of constant global variables containing mappings, the following dictionaries are stored separately in the `code/musicbrainz/rdf_conversion_config/` folder and loaded by [`code/musicbrainz/convert_to_rdf.py`](/code/musicbrainz/convert_to_rdf.py) at runtime:

- [`mappings.json`](/code/musicbrainz/rdf_conversion_config/mappings.json) : for the main fields
- [`relations.json`](/code/musicbrainz/rdf_conversion_config/relations.json): for relationships
- [`attribute_mapping.json`](/code/musicbrainz/rdf_conversion_config/attribute_mapping.json): for attributes

[`code/musicbrainz/convert_to_rdf.py`](/code/musicbrainz/convert_to_rdf.py) also imports two modules:

- [`code/musicbrainz/mapping_schema.py`](/code/musicbrainz/mapping_schema.py): it contains the class definition of `MappingSchema`  
- [`code/musicbrainz/url_patterns.py`](/code/musicbrainz/url_patterns.py): it contains regex patterns matching onto different urls.

## Rules for Literal Datatypes

The below rules are to conform with RDF standards and with Wikidata standards

- Any literal value not given an explicit type will default to `XSD:string`. This is part of the RDF standard.
- Dates are given the type `XSD:date`. If the value has both date and time, it will be in `XSD:datetime`
- Coordinates (latitude/longitude) are given the `GEO:wktLiteral` type in the format `f"Point({lon} {lat})"`.
- Durations (in seconds) are given the type `XSD:decimal` since they are numbers,
- All URLs that are stored as plain URLs in MusicBrainz dataset (instead of having their IDs extracted from the URI) kept as literals. This is because these URLs often lack the proper RDF URI formatting, or because they are links to personal websites (e.g. the link to a band's website).

## Miscellanous Notes on convert_to_rdf.py

- The script is optimized to be memory-efficient, but there's only so much you can do when one of the input files is >250GB.
- The script uses disk storage to store the graph as it builds it to save on memory space. By default, this folder is `./store`, from the working directory. The script automatically deletes the folder when it finishes. However, if the script crashes, it is recommended to delete the folder before running it again.
- The graph will not use disk storage if the input file is less than 1GB in size. This is a configurable limit in the script.
- By default, the script will ignore any data types that already have a corresponding file in the output directory. This is useful in the event that the program crashes and you only need to rerun the RDF conversion on the data that wasn't processed instead of the entire input directory.
- Settings for queue sizes, as well as the number of parallel processes are in global variables at the beginning of the script.
- For ease of reading, the fields are processed in alphabetical order in the `process_line` function.
- If you call `Literal(...)` with `XSD:date` as datatype, it will eventually call the `parse_date` isodate function to validate the format. However, `parse_date` is called after the construction of the `Literal`, making any exception it raises impossible to catch. This is why I call the `parse_date` function and pass its value to the constructor in the `convert_date` function, thus allowing any exceptions to be caught and dealt with.
- The same situation applies to the `convert_datetime` function with the `XSD:dateTime` datatype and the `parse_datetime` isodate function.
- The dictionary containing property mappings for the data fields and URLs was moved into a JSON file, located in [`code/musicbrainz/rdf_conversion_config/mappings.json`](/code/musicbrainz/rdf_conversion_config/mappings.json). The dictionary contains the internal dictionary of a `MappingSchema` object serialized into JSON by Python's built-in JSON module. As such, the outermost dictionary's are the properties, the innermost dictionary's keys are the source types (with `null` as a wildcard), and the values are the full URIs to the properties.
- To update this dictionary, either modify the JSON file, or modify the `MB_SCHEMA` and then use `json.dump(MB_SCHEMA.schema, file, indent=4)` to export it.

## Notes on Particularities in MusicBrainz Dataset

- The `release` entity type's `quality` field stands for "data quality". It indicates the credibility of the information MusicBrainz has on the release. See the [documentation page](https://musicbrainz.org/doc/Release#Data_quality) for more information. As it is effectively meta-metadata, there are no Wikidata entities or properties that we can use to store it. As such, for now, we will ignore this field. See [#336](https://github.com/DDMAL/linkedmusic-datalake/issues/336) for more information.
- The `release` entity type's `status` field does not neatly map onto a single Wikidata property: I use P1534 "end cause" for values like cancelled, withdrawn, etc, and I use P31 "instance of" for things like bootleg, official album, etc. Though we reconciled the predicate against a Wikidata property, the object (e.g. bootleg, official album) is left as literal because there is no Wikidata equivalent for all of them.
- The `event` entity type's `setlist` field seems to contain pre-rendered data about the setlist, which makes it difficult to parse. Furthermore, the same data is also located in the `relations` field, and as such, the `setlist` field is ignored during the RDF conversion process.
- The release group entity type is spelled `release-group` almost everywhere. Yet, in the `target-type` field under `relationships`, and as the name of a field under `relationships`, it is exceptionally spelled as `release_group`. The RDF conversion script's approach is to convert all underscores to dashes before processing.

## Attributes

The `work` entity type has an additional field `attributes` that contains a list of various attributes for that work:

- The vast majority of attribute types are IDs to other databases, but they can also contain a few other thing. For example:

  - the key (i.e. tonality) of the work (extracted and reconciled with OpenRefine, see [`doc/musicbrainz/miscellaneous_reconciliation.md`](/doc/musicbrainz/miscellaneous_reconciliation.md))
  - Non-Western musical concepts, such as the Tala, the musical meter of Indian classical music

- Unlike RISM, which has [P5504 "RISM ID"](https://www.wikidata.org/prop/direct/P5504) as a corresponding Wikidata property, the majority of these databases have no corresponding Wikidata property. Since the field contains only IDs, not full URLs/URIs, these IDs are not stored unless there is an corresponding Wikidata property.

- The file with all possible attribute values and Wikidata properties they map onto can be found in [`doc/musicbrainz/rdf_conversion_config/attribute_mapping.json`](/doc/musicbrainz/rdf_conversion_config/attribute_mapping.json). Attributes that are not present in `attribute_mapping.json` or that have the value `null`/`None` will be ignored by the RDF conversion script.

## URLS

For some databases, MusicBrainz decides to store number IDs (e.g. Discogs Artist ID 1000 ). For other databases, MusicBrainz decide to store the full url (e.g. <https://www.discogs.com/artist/25058>).

Whenever possible, we try to extract the ID from the url, and store the ID alone with the corresponding Wikidata property. For instance, we would extract 25058 from <https://www.discogs.com/artist/25058>, and store it with the predicate [Discogs artist ID (P1953)](https://www.wikidata.org/prop/direct/P1953).

The same database may have multiple Wikidata property. For example, Discogs has [Discogs artist ID (P1953)](https://www.wikidata.org/prop/direct/P1953) and [Discogs label ID (P1955)](https://www.wikidata.org/prop/direct/P1955) and [Discogs composition ID (P6080)](https://www.wikidata.org/prop/direct/P6080)...

To extract the IDs properly, a regex pattern, taken from the `URL match pattern` field of each Wikidata property (e.g. `^https?:\/\/(?:www\.)?discogs\.com\/(?:[a-z]+\/)?artist\/([1-9][0-9]*)` for [Discogs artist ID (P1953)](https://www.wikidata.org/prop/direct/P1953)) is stored in [`code/musicbrainz/url_patterns.py`](/code/musicbrainz/url_patterns.py).

If no Wikidata property exist, the url will be stored as [exact match (P2888)](https://www.wikidata.org/prop/direct/P2888). This means that when regex fail (and it does occasionally fail), the urls will still be linked to the entity.

Here is the mapping of databases onto their Wikidata property:

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

## Other Properties

For other properties in other fields:

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
- To store the packaging of a release, I use P9813 "container", as it seems to be the most appropriate, and because one of the example uses given for the property is to indicate the packaging of a musical release
