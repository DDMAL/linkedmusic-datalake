# DIAMM Database CSV Layout

This file explains the layout of the CSV files produced by the CSV conversion script.

In addition to the fields described below, each table, except for `relations` will have an `id` column that will hold the ID (or primary key) for that entity type.

## Archives

Sources will be in relations

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
- `type` will be used to differentiate between relationship types between the same 2 entity types: for example for people-source relationships, where a person can have different types of relationships with a source (sources that they copied, sources that they are related to, etc)

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
