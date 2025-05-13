# DIAMM Database CSV Layout

For all except for relations, `id` will denote the pk

## Archives

Sources and city will be put in relations

- `name`
- `siglum`
- `website`
- `rism_id`
- `wd_id`

## Authors

If I can figure out what bibliography is, I'll add it to the relations

- `full_name`

## Cities

Archives, country, organizations and provenance will be put in relations

- `name`

## Compositions

Composers and sources will be in relations

- `anonymous`
- `title`
- Genres and cycles need to be figured out

## Countries

-

## Organizations

-

## People

-

## Regions

-

## Relationships

This will hold all relationships between objects. `key1` will contain the object whose type is alphabetically before the other (per example, `key1` will contain `author` and `key2` will contain `source`).

- `key1` and `key2` will have the format `type:pk` (for example `archive:1`) and denote the keys linked by the relationship
- `note` will be used per example for people-source relationships, where a person can have different types of relationships with a source

## Sets

-

## Sources

-
