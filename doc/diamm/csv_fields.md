# DIAMM Database CSV Layout

Explain the layout of the CSV files produced by the CSV conversion script

For all tables except for relations, `id` will denote the pk

## Archives

Sources will be put in relations

- `name`
- `siglum`
- `website`
- `rism_id`
- `city`: the city name
- `country`: the country name

## Compositions

Composers and sources will be in relations

- `anonymous`
- `title`
- `genres`

## Organizations

All 3 source fields will be in relations

- `name`
- `organization_type`
- `city`
- `country`

## People

Compositions, and both source fields will be in relations

- `full_name`
- `variant_names`
- `earliest_year`
- `latest_year`
- `earliest_year_approximate`
- `latest_year_approximate`
- `rism_id`
- `viaf_id`

## Relations

This will hold all relationships between objects. `key1` will contain the object whose type is alphabetically before the other (per example, `key1` will contain `author` and `key2` will contain `source`, but not vice-versa).

- `key1` and `key2` will have the format `type:pk` (for example `archive:1`) and denote the keys linked by the relationship
- `type` will be used per example for people-source relationships, where a person can have different types of relationships with a source

## Sets

Archives and sources will be in relations

- `type`
- `cluster_shelfmark`
- `description`

## Sources

Inventory, archive and sets will be in relations

- `display_name`
- `shelfmark`
- `source_type`
