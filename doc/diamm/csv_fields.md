# DIAMM Database CSV Layout

This file explains the layout of the CSV files produced by the CSV conversion script. It is simply a list of columns in the CSVs for each entity type, to explain how the data is translated from the downloaded JSON files (explained in `doc/diamm/data_layout.md`) to CSV files for reconciliation.

As explained in the [Relations](#relations) section of this file, to handle relations between entity types, an additional CSV file is created to store relations between entity types. For each entity type, I list which relationships/fields will be put in the relations CSV.

In addition to the fields described below, each table, except for `relations`, will have an `id` column that will hold the ID (or primary key) for that entity type.

## Archives

Data in `sources` will be in the relations CSV

- `name`
- `siglum`
- `website`
- `rism_id`
- `city`: the name of the city the archive is located in
- `country`: the name of the country the archive is located in

## Compositions

Data in `composers` and `sources` will be put in the relations CSV

- `anonymous`: boolean indicating whether it's anonymous
- `title`
- `genres`: this is a list of genres separated by semicolons (to not interfere with the CSV)

## Organizations

Data in `related_sources`, `copied_sources`, and `source_provenance` will be put in the relations CSV

- `name`
- `organization_type`
- `city`: the name of the city the organization is located in
- `country`: the name of the country the organization is located in

## People

Data in `compositions`, `related_sources`, and `copied_sources` will be put in the relations CSV

- `full_name`
- `variant_names`: this is a list of variant names separated by `", "`
- `earliest_year`
- `latest_year`
- `earliest_year_approximate`
- `latest_year_approximate`
- `rism_id`
- `viaf_id`

## Relations

This will hold all relationships between objects. `key1` will contain the object whose type is alphabetically before the other (for example, `key1` will contain `author` and `key2` will contain `source`, but not vice-versa).

- `key1` and `key2` will have the format `type:pk` (for example `archive:1`) and denote the keys linked by the relationship
- `type` will be used to differentiate between relationship types between the same 2 entity types: for example for people-source relationships, where a person can have different types of relationships with a source (sources that they copied, sources that they are related to, etc)

## Sets

Data in `holding_archives` and `sources` will put in the relations CSV

- `type`
- `cluster_shelfmark`
- `description`

## Sources

Data in `inventory`, `sets`, and `archive` will be put in the relations CSV

- `display_name`
- `shelfmark`
- `source_type`
