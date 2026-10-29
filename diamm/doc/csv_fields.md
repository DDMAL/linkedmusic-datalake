# DIAMM Database CSV Layout

This file explains the layout of the CSV files produced by the CSV conversion script. It is simply a list of columns in the CSVs for each entity type, to explain how the data is translated from the downloaded JSON files (explained in [`data_layout.md`](./data_layout.md)) to CSV files for reconciliation.

As explained in the [Relations](#relations) section of this file, to handle relations between entity types, an additional CSV file is created to store relations between entity types. For each entity type, I list which relationships/fields will be put in the relations CSV.

In addition to the fields described below, each table, except for `relations`, will have an `id` column that will hold the ID (or primary key) for that entity type.

## Archives

Data in `sources` and `city` will be in the relations CSV

- `name`: original archive name, kept as text
- `siglum`: original archive siglum, kept as text
- `website`
- `rism_id`: exact string hint when one distinct nonblank RISM value is supplied
- `source_identifiers`: complete source identifier list serialized as JSON text;
  see the [identifier-list contract](external_identifier_selection.md)

Keep names and sigla unchanged through reconciliation under the
[archive text contract](archive_text.md). Nonempty cells become string literals;
empty cells emit no name/siglum statement. Extraction writes JSON null and empty
strings as empty CSV cells without retaining their distinction.

## Cities

Data in `archives`, `provenance`, `organizations`, and `country` will be in the relations CSV

- `name`: original city name, kept as text under the [geographic name contract](geographic_names.md)
- `country`: This is only here to help with reconciliation

## Compositions

Data in `composers` and `sources` will be put in the relations CSV

- `anonymous`: boolean indicating whether it's anonymous
- `title`
- `genres`: this is a list of genres separated by semicolons (to not interfere with the CSV)

## Country

Data in `cities`, `regions`, and `states` will be put in the relations CSV

- `name`: original country name, kept as text under the [geographic name contract](geographic_names.md)

## Organizations

Data in `related_sources`, `copied_sources`, `source_provenance`, and `location` will be put in the relations CSV. The relationships for `related_sources` will additionally keep track of the original relationship type.

- `name`
- `organization_type`
- `country`: The name of the country or region the organization is in, this is only here to help with reconciliation

## People

Data in `compositions`, `related_sources`, and `copied_sources` will be put in the relations CSV. The relationships for `related_sources` will additionally keep track of the original relationship type.

- `full_name`: cleaned display name used for reconciliation and the RDF label
- `variant_names`: this is a list of variant names separated by `", "`
- `earliest_year`: person birth year, under the [source-model interpretation](person_years.md)
- `latest_year`: person death year under the same interpretation
- `earliest_year_approximate`: source uncertainty flag for the birth year
- `latest_year_approximate`: source uncertainty flag for the death year
- `rism_id`: exact string hint when one distinct nonblank RISM value is supplied
- `viaf_id`: exact string hint when one distinct nonblank VIAF value is supplied
- `source_full_name`: exact original JSON display name, including date/floruit text
- `floruit`: optional separate JSON floruit text; not inferred from the display name
- `source_identifiers`: complete source identifier list serialized as JSON text

These person years are distinct from role dates and the upstream floruit field.
OpenRefine adds `earliest_year_@id` and `latest_year_@id` while retaining the
original year and flag cells. RDF conversion preserves all six cells and emits
direct birth/death years only when explicitly non-approximate. The two appended
text columns follow the [person-name preservation contract](person_name_preservation.md)
and must pass through reconciliation unchanged.
The two external identifier columns also require text-preserving import/export;
see the [external identifier contract](external_identifier_text.md).
The appended JSON column carries all identifier evidence and takes precedence
over scalar hints during RDF conversion; see the
[identifier-list contract](external_identifier_selection.md).

## Regions

Data in `organizations`, `cities`, and `provenance` will be put in the relations CSV

- `name`: original region name, kept as text under the [geographic name contract](geographic_names.md)
- `country`: source `parent` text, only a reconciliation hint; it does not create an RDF country link

For all three geographic tables, empty names emit no RDF label. Nonempty strings,
including whitespace and NA-like text, retain their spelling. JSON null and empty
strings share an empty CSV cell; extraction does not preserve that distinction.

## Relations

This will hold all relationships between objects. `key1` will contain the object whose type is alphabetically before the other (for example, `key1` will contain `author` and `key2` will contain `source`, but not vice-versa).

- `key1` and `key2` will have the format `type:pk` (for example `archive:1`) and denote the keys linked by the relationship
- `type` will be used to differentiate between relationship types between the same 2 entity types: for example for people-source relationships, where a person can have different types of relationships with a source (sources that they copied, sources that they are related to, etc). For the `people`-`sources` and `organizations`-`sources` relationships that have types, the value in the type field will be `f"related:{relationship_type}"`, to be able to conveniently store the relationship type

## Sets

Data in `relationships`, `holding_archives` and `sources` will put in the relations CSV. The relationships in `relationships` will additionally keep track of the original relationship type.

- `type`
- `cluster_shelfmark`
- `description`

## Sources

Data in `inventory`, `sets`, and `archive` will be put in the relations CSV

- `display_name`
- `shelfmark`
- `source_type`
