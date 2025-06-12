# Property Mappings for Relationships

In the DIAMM database, there are more complex reltionships between `people` and `sources` and between `organizations` and `sources`. They are modeled with a `related_sources` field in the `people` and `organizations` entity types, and with a `relationships` field in the `sources` entity type.

For both `related_sources` fields, they contain the type of relationship, as well as the url and name of the related source. For the `relationships` field, it contains the type of relationship, as well as the url and name of the related entity, and we can retrieve the entity type of the related entity from its url.

All relationships are bidirectional, which is to say that the relationship type and name is the same whether you're going from `sources` to `people` or vice-versa, and similarly for `organizations`. However, Wikidata's relationships are unidirectional and often don't have inverses. To give an example of this, the relationship "owner" between a person and a source is the same whether you're saying that the person owns the source or that the source is owned by the person, whereas Wikidata has an "owner" property to indicate who the owner of a source is, but does not have an inverse to indicate the sources that a person owns.

Furthermore, DIAMM distinguishes its relationships depending on the entity types that it links. As an example, the `source`-`person` "owner" relationship is different from the `organization`-`person` relationship, while in Wikidata, they are the same.

To handle this, the `code/diamm/extract_relation.py` script will extract all the relationship types and will output them to the `code/diamm/relations.json` file. Since all relationships are bidirectional and involve a source, and thus it is only the second entity type that can be different, relationships are classified on that second type, which can either be `people` or `organizations`.

The `relations.json` file contains a mapping of relations to properties. The properties are assumed to be from the source towards the other entity type. Properties that are the reverse have the property ID prefixed with `r` (lowercase). As an example, `rP86` would indicate that the relationship translates into P86 from the other entity type to the source, whereas `P86` would indicate that the relationship translates into P86 from the source to the other entity type.  
Relationships mapped to `null`/`None` are ignored by the RDF conversion script.

Non-trivial/obvious decisions made about that proeprty mapping are listed below:

- The "patron" relationship is mapped to P859 "sponsor" as it is for individuals/organizsations that have materially/financially supported a work. The "Establishment Patron" relationship is also mapped to this because there is no other property that can indicate this relationship
- The "copied at" and "scriptorium" relationships are mapped to P1071 "location of creation", which is the property used to indicate the location at which an object was made, as there isn't a more specific property to indicate that it was copied there
- All relationships that indicate that a person/organization was mentioned in a source are not mapped to anything because there are no relevant properties on Wikidata to indicate that something/someone was mentioned in a work/text
- The "contemporary publisher" relationship is mapped to P123 "publisher" as there is not a distinction between contemporary or not in Wikidata. The same principle is applied to "contemporary editor" being mapped to P98 "editor"
- The "used the MS" relationship is mapped to P1535 "used by" as it's an exact match. I also map the "Borrowed the MS" relationship to this as there is no specific property for borrowing
- The "commissioned/made for" and "commissioned by" relationships are mapped to P88 "commissioned by" as Wikidata does not distinguish between "commissioned by" and "commissioned for"
- The "decoration style model" relationship is mapped to P135 "movement" as it is the closest property to indicate the design style used by a work
- The "saw and described MS" relationship is mapped to P61 "discoverer or inventor" as it's the closest thing I could find to indicate that a person described the source, as there is nothing close to a "described by" property
- The "binder" relationship is mapped to P170 "creator" as it indicated that a person made an object, and there is no more precise property to indicate the fact that they just did the binding
- The "compiler" relationship is mapped to P98 "editor" as one of the alternate uses is to indicate that someone was the compiler
- The "copied at" relationship for people is mapped to P11603 "transcribed by" as that property can also cover copying
- The "transcribed music" proeprty is mapped to P9260 "music transcriber" as that appears to be an exact match
- The "dedicator", "reconstructed fragments", "completed the manuscript", and "flyleaves" properties are mapped to P767 "contributor to the creative work or subject", which is a form of catch-all property, as there are no specific properties for these relationships
- The "composition(s) in honour of" relationship is mapped to P825 "dedicated to" as there is no property to indicate that a source was made in honour of someone
- The "witnessed the document" relationship is not mapped to anything because I could not find any property on Wikidata to indicate this relationship
- The "author of liminary text" relationship is mapped to P2679 "author of foreword" as the liminary text is the foreword in this case
