# Geographic relationships and organization locations

DIAMM gives an organization one optional location. The converter links the
organization to the city, region or country identified by the source using
`schema:location`. For example, if DIAMM identifies a city, the organization's
direct location is that city. A query can follow the city's own geographic
links to look for a wider area.

## Source evidence and decision

The upstream files below were inspected at revision
`052004f86960a5dc4d1e7446be8d5a6ac8594bd1`. This is definition evidence, not
confirmation of the historical snapshot or deployed API version.

| Source definition | Meaning and consequence |
| --- | --- |
| [Organization model](https://github.com/diamm/diamm/blob/052004f86960a5dc4d1e7446be8d5a6ac8594bd1/diamm/models/data/organization.py) | `location` is an optional foreign key to GeographicArea, with reverse name `organizations`. It is distinct from the organization's relationships to manuscripts. |
| [Region serializer](https://github.com/diamm/diamm/blob/052004f86960a5dc4d1e7446be8d5a6ac8594bd1/diamm/serializers/website/region.py) | `organizations` enumerates that reverse relation and supplies organization URLs. This supports an organization-to-region location assertion. |
| [Organization serializer](https://github.com/diamm/diamm/blob/052004f86960a5dc4d1e7446be8d5a6ac8594bd1/diamm/serializers/website/organization.py) | Its own `location.url` is supplied only for cities and countries; other geographic types yield null. The region's reverse listing is therefore meaningful evidence, even when the organization record has only location/parent text. |
| [Geographic-area model](https://github.com/diamm/diamm/blob/052004f86960a5dc4d1e7446be8d5a6ac8594bd1/diamm/models/data/geographic_area.py) | Types include states and regions/cultural areas/protectorates. A region endpoint does not by itself establish administrative status. |

Schema.org defines [location](https://schema.org/location) for organizations and
allows a place as its value. [Wikidata P131](https://www.wikidata.org/wiki/Property:P131)
asserts administrative territorial containment. DIAMM can place an organization
in a cultural region without making that administrative claim.

## RDF mapping

Each row below identifies the organization's direct place. The extractor records
these endpoints in `relations.csv`. The converter uses the same predicate and
points from the organization to the place regardless of the CSV column order.
See the [extractor](../src/to_csv.py) and [converter](../src/convert_rdf.py).

| Evidence in DIAMM | CSV keys in order | RDF subject → `https://schema.org/location` → object |
| --- | --- | --- |
| Organization's city URL or city's organization listing | `city:C,organization:O` | `organizations/O` → `cities/C` |
| Organization's country URL | `country:C,organization:O` | `organizations/O` → `countries/C` |
| Region's organization listing | `organization:O,region:R` | `organizations/O` → `regions/R` |

All endpoints use the base `https://www.diamm.ac.uk/`. A relation row is
sufficient even when the place has no detail record or Wikidata match.
Duplicate rows give one triple. If an export contains conflicting direct places,
each distinct supplied place survives. The converter never adds a broader
location from the place hierarchy or a reconciliation hint such as
`country_@id`. A shared P2888 match supplies no location evidence.

Run this query in the DIAMM graph to find the listed place, including places
whose detail record has no label.

```sparql
PREFIX schema: <https://schema.org/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?organization ?place ?name WHERE {
  ?organization schema:location ?place .
  OPTIONAL { ?place rdfs:label ?name }
}
```

An organization may appear in a separate manuscript relationship. Joining
through that organization retrieves its listed place. The join supplies no
evidence of where or when the manuscript was copied, held or performed.

## Parent and manuscript-provenance limits

The [city serializer](https://github.com/diamm/diamm/blob/052004f86960a5dc4d1e7446be8d5a6ac8594bd1/diamm/serializers/website/city.py)
gets `country` from a general geographic `parent`, then its nested serializer
constructs a `country-detail` URL without checking the parent's type. Local
extraction also assumes a country endpoint. Consequently, checking only the
URL path cannot recover the true type for this inspected serializer. A future
repair needs explicit source type/URL evidence or a snapshot-backed crosswalk;
names and reconciliation hints cannot supply that evidence. The current
country endpoint must not be silently relabelled as a region. Historical
occurrence and deployed serializer behavior remain unmeasured.

City-to-region rows use P131. A DIAMM region can be cultural, so check the
target region's type before interpreting a city-to-region link as
administrative containment.

The [source-provenance model](https://github.com/diamm/diamm/blob/052004f86960a5dc4d1e7446be8d5a6ac8594bd1/diamm/models/data/source_provenance.py)
links a manuscript to geographic areas, with separate uncertainty flags and
earliest/latest years. City/region serializers expose those qualifiers. The
[qualified provenance contract](source_provenance.md) retains both routes in
named observations with paired JSON, supported qualifiers and explicit legacy
behavior. It emits no direct source-to-city P131 for new or legacy inputs and
does not infer dates, creation, performance or current storage. This is separate
from the organization-location predicate described here.

The [region-history copy-step facet](geographic_names.md), other unprotected
text fields, source URL parsing outside this route and broader relationship
mapping remain separate limitations. No historical inputs, live DIAMM records,
production graphs or OpenRefine execution are established by pinned source code.

## Validation and regeneration

Four [regressions](../tests/test_geographic_relationships.py) use the actual CSV
loader and extraction/RDF CLIs, tracked export layouts, independently specified
graphs, Turtle round trips and SPARQL checks. They cover legacy relation rows,
duplicate/conflicting locations, identical numeric IDs in different local
namespaces, region reverse listings with null organization location URLs,
supplied name matches, hints/shared matches that must not create relationships,
and all three organization location routes. The query and exact graph checks
cover city parents, absence of additional organization links and independent
manuscript relationships. A negative query checks that manuscript
locations are not inferred through the organization. The tests do not replay
OpenRefine. Run from the repository root:

```sh
poetry run python scripts/check_offline.py
```

## Migrating organization-location queries and RDF

Older conversions used `wdt:P131` for an organization's city and `wdt:P17`
for its country. The earlier region mapping used
`https://linkedmusic.ca/graphs/diamm/organizationLocation`. In a regenerated
DIAMM graph, query all three direct place types with `schema:location`. To look
up the country recorded for a city, join the city's own `wdt:P17` edge and
observe the parent-type limitation above. P131 and P17 still have other uses in
this graph, so a global predicate replacement would corrupt unrelated links.

Regenerate from the matching `relations.csv` into a separate graph. Compare the
distinct organization/place pairs for each of the three row shapes against the
new graph, then check the location query before replacing the old graph.
Appending would retain duplicate legacy predicates. Region links omitted by an
older converter require the source relation rows. Record the input checksums
and converter revision for any comparison with historical RDF.
