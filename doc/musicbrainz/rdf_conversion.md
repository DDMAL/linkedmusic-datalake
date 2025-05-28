# MusicBrainz RDF Conversion

This documents any choices for properties in the RDF conversion process

A note on data types:

- Any literal value not given an explicit type will default to XSD:string. This is expected behaviour of the RDF standard.
- Dates are given the type XSD:date, this is what wikidata uses, if something has a date and time, it will be in XSD:datetime
- Coordinates (lat/lon) are given the GEO: wktLiteral, this is what wikidata uses
- Durations (in seconds) are stored in XSD:decimal, as they are numbers

Now for the properties:

- To indicate the "main" name, I use RDFS:label instead of P2561 as that's what wikidata does
- To indicate alternate names (possible in other languages), I use P4970 "alternative name" and put a language tag when I can
- To indicate start and end dates, I use P571 "inception" and P576 "dissolved, abolished or demolished" for most things, as that's the property that matches
- To indicate that a release contains a specific disc, I use P527 "has part", which is the inverse of P361 "has part"
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
