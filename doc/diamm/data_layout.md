# DIAMM Database Data Layout

This file clarifies and explains the data layout of the DIAMM database, as it is received by the fetching script. Each individual object is received as a JSON file describing it. Each entity type has its own JSON structure and different fields, which are described below.

In addition to the fields described below, all entity types have `url` and `pk` fields, which respectively indicate the URL/URI of that entity, and its DIAMM ID (or primary key).

The `related_source` field for both `organizations` and `people` contains relationships between those entities and `sources` (e.g. owner, discovered by, etc). Each relationship contains the entity it links to, as well as the type of relationship it is.  
The `relationships` field for `sources` is very similar, containing relationships between the set and `organizations` and `people`. Each relationship contains the entity it links to (and its type), as well as the type of relationship.

## Archives

- `sources` are the sources contained within
- `city` is the city that holds the archive
- `identifiers` has 3rd party identifies (RISM, sometimes Wikidata)

## Authors

- `first_name` and `last_name` have the name
- it is unclear what the `pk` fields in the `bibliography` refer to

## Cities

- `archives` has the list of archives in that city
- `country` is the country that the city is located in
- `organizations` are organizations that are located in that city
- `provenance` is a list of sources that came from the city

## Compositions

- `composers` is a list of people
- `sources` is the list of sources that contain this composition
- it is unclear what the `pk` fields in the `bibliography` refer to

## Countries

- `cities` is a list of cities in that country
- `regions` and `states` are a list of regions in that country

## Organizations

- `organization_type` is the type of organization
- `related_sources` is a list of related sources, that also contains information about the relationship type
- `copied_sources` is a list of sources that were copied at that organization
- `source_provenance` is a list of sources whose provenance is this organization
- `location` is the city in which the organization is located

## People

- `compositions` is the list of compositions that they wrote
- `related_sources`, `copied_sources` and `uninventoried_items` contain a list of sources. `uninventoried_items` seems to be a catch-all for sources that don't fit in the other 2 lists. `related_sources` also contains information about the relationship type
- `identifiers` has 3rd party identifiers (RISM, VIAF, GNS, Wikidata)

## Regions

This designates administrative regions between cities and countries (think provinces). It does not always seem to be used.

- `organizations` is a list of organizations in that region
- `cities` is a list of cities in the region
- `provenance` is a list of sources that came from this region

## Sets

- `cluster_shelfmark` seems to be its name
- `holding_archives` are the archives that hold the set
- `sources` are the sources contained within the set
- `description` is a text field
- `bibliography` is unclear

## Sources

- `inventory` is a list of compositions
- `composer_inventory` is a list of composers that list some of their compositions
- `archive` is the archive that contains it
- `sets` are sets that contain this source
- `bibliography` is unclear
- `identifiers` is 3rd-party identifiers
- `notes` are a list of notes, the pks here are unclear
- `relationships` is a list of relationships to `people` and `organizations`, they are the complement of those entity types' `related_sources` fields
