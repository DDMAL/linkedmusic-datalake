# DIAMM Database Data Layout

Clarifies and explains the data layout of the DIAMM database, as it is received by the fetching script

All have `url` and `pk` fields

## Archives

- `sources` are the sources contained within
- `city` is the city that holds the archive
- `identifiers` has 3rd party identifies (RISM, sometimes WikiData)

## Authors

- `first_name` and `last_name` have the name
- it is unclear what the `pk` fields in the `bibliography` refer to

## Cities

- `archives` has the list of archives in that city
- `country` is the country that the city is located in
- `organizations` are organizations that are located in that city
- `provenance` is sources hat came from the city

## Compositions

- `composers` is a list of people
- `sources` is the list of sources that contain this composition
- it is unclear what the `pk` fields in the `bibliography` refer to

## Countries

- `cities` is a list of cities in that country
- `regions` is a list of regions in that country
- `states` is a list of states in that country

## Organizations

- `organization_type` is the type of organization
- `related_sources` is a list of related sources
- `copied_sources` is TBD
- `source_provenance` is yet more sources
- `location` is the city

## People

- `compositions` is the list of compositions that they wrote
- `related_sources`, `copied_sources` and `uninventoried_items` contain a list of sources
- `identifiers` has 3rd party identifiers (RISM, VIAF, GNS, Wikidata)

## Regions

- `cities` is a list of cities
- `provenance` is a list of sources

## Sets

- `cluster_chelfmark` seems to be its name
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
- `identifiers` is 3rd party identifiers
- `notes` are a list of notes, pks are unclear
