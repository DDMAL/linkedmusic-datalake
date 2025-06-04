# MusicBrainz: Relationships between Entities


## Understanding MusicBrainz Relationships

MusicBrainz Relationships ([Official Definition](https://musicbrainz.org/doc/Relationships)) can exist between _almost_ any two entities of any given of the given 13 entity-types. For example, an artist may be the `"owner"` of a label, just as well as a label can be the `"owner"` of a place. However, MusicBrainz, unlike Wikidata, is extremely rigid about what entity-type is connected by a particular relationship. In our previous example, the two `"owner"` relationships are in fact distinct: the [first](https://musicbrainz.org/relationship/610fa594-eeaa-407b-a9f1-49f509ab5559) can only be between an artist and a label, while the [second](https://musicbrainz.org/relationship/06829429-0f20-4c00-aa3d-871fde07d8c4) can only be between a label and a place.




However, the vast majority of relationships between entities are listed in the `relationships` field. 


Given that across all entity types, there are roughly 800 different relation types that all need to be mapped, storing the mappings inside the script would make it very messy. As such, the script `code/musicbrainz/extract_relations.py` will parse all the JSONL data files and will extract every relationship type between all entities. Importantly, the script will only add new relationships, preserving pre-existing mappings.

In the MusicBrainz dataset, a few relationships between entities are kept in their own fields, like how `artist-credit` is the field that contains that contains the artists who made the recording.

The output file is located in `doc/musicbrainz/rdf_conversion_config/` and is structured in a subject -> object -> relationship format (i.e. the outermost dictionary key indicates the subject's entity type, the second dictionary key indicates the object's dictionary type, and the keys of the third dictionary are the relationships). The values associated with each relationship are the Wikidata Property ID (P###) that the relationship maps to, in string format (i.e. `"P2888"`). If a relationship is to be ignored (or not mapped), then it should either be removed or left as `null`/`None`, and the RDF conversion script will ignore it.

## Homogeneous Relationships

Some relationships are homogeneous (same source and target type), like for example the area-to-area property `part of`, that indicates that an area is apart of the other. Directionality is important, because different Wikidata properties represent the fact that Québec is in Canada and the fact that Canada contains Québec. To solve this problem, both the relationship extraction and RDF conversion scripts are configured to suffix any homogeneous relationship with its direction (either `forward` or `backward`) to be able to differentiate between the directions.

## Decisions made regarding property mappings

- To be filled once work on mapping relations starts

## A note on inverse properties (or the lack thereof)

The majority of Wikidata properties that are meant to link 2 entities together do not have inverse properties. This is intentional. Instead of (for example) having a property saying that a recording was made in an area, and another property saying that an area was where a specific recording was made, Wikidata only has the property saying that a recording was made in a particular area, and SPARQL can handle the reverse lookup.

The following properties/relationships were ignored because they are duplicates of their inverse:

- To be filled once work on mapping relations starts
