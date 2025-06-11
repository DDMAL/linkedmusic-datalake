# Property Mappings for Relationships

In the DIAMM database, there are more complex reltionships between `people` and `sources` and between `organizations` and `sources`. They are modeled with a `related_sources` field in the `people` and `organizations` entity types, and with a `relationships` field in the `sources` entity type.

For both `related_sources` fields, they contain the type of relationship, as well as the url and name of the related source. For the `relationships` field, it contains the type of relationship, as well as the url and name of the related entity, and we can retrieve the entity type of the related entity from its url.

All relationships are bidirectional, which is to say that the relationship type and name is the same whether you're going from `sources` to `people` or vice-versa, and similarly for `organizations`. However, Wikidata's relationships are unidirectional and often don't have inverses. To give an example of this, the relationship "owner" between a person and a source is the same whether you're saying that the person owns the source or that the source is owned by the person, whereas Wikidata has an "owner" property to indicate who the owner of a source is, but does not have an inverse to indicate the sources that a person owns.

Furthermore, DIAMM distinguishes its relationships depending on the entity types that it links. As an example, the `source`-`person` "owner" relationship is different from the `organization`-`person` relationship, while in Wikidata, they are the same.

To handle this, the `code/diamm/extract_relation.py` script will extract all the relationship types and will output them to the `code/diamm/relations.json` file. Since all relationships are bidirectional and involve a source, and thus it is only the second entity type that can be different, relationships are classified on that second type, which can either be `people` or `organizations`.

The `relations.json` file contains a mapping of relations to properties. The properties are assumed to be from the source towards the other entity type. Properties that are the reverse have the property ID prefixed with `r` (lowercase). As an example, `rP86` would indicate that the relationship translates into P86 from the other entity type to the source, whereas `P86` would indicate that the relationship translates into P86 from the source to the other entity type.  
Relationships mapped to `null`/`None` are ignored by the RDF conversion script.

Non-trivial/obvious decisions made about that proeprty mapping are listed below:

- The "patron" relationship is mapped to P859 "sponsor" as it is for individuals/organizsations that have materially supported a work
- The "copied at" relationship is mapped to P1071 "location of creation", which is the property used to indicate the location at which an object was made
- The "mentioned in liminary text" relationship is not mapped to anything because there is no relevant property on Wikidata
- The "contemporary publisher" relationship is mapped to P123 "publisher" as there is not a distinction between contemporary or not in Wikidata
- The "used the MS" relationship is mapped to P1535 "used by" as it's an exact match
- The "commissioned/made for" and "commissioned by" relationships are mapped to P88 "commissioned by" as Wikidata does not distinguish between "commissioned by" and "commissioned for"
- The "decoration style model" relationship is mapped to P135 "movement" as it is the closest property to indicate the design style used by a work
