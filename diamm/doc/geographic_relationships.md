# Geographic relationship review and organization locations

Reviewed 29 October 2026. The bounded repair preserves the organization/region
rows already extracted into `relations.csv`. Previously those rows had no RDF
branch and disappeared. Parent routing and qualified source provenance remain
separate problems; this change does not establish complete geographic fidelity.

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

The [P131 definition](https://www.wikidata.org/wiki/Property:P131) is specific
to administrative territorial containment. The broader
[P276 definition](https://www.wikidata.org/wiki/Property:P276) also distinguishes
other location predicates by use. Both definitions were checked on 29 October.
This repair retains the exact source relationship under a DIAMM predicate;
it does not declare an exact Wikidata alignment or a subproperty rule. This
avoids choosing geographic semantics absent from the exported region type.

## RDF contract

| Item | Contract |
| --- | --- |
| Predicate | `https://linkedmusic.ca/graphs/diamm/organizationLocation` |
| Readable label | DIAMM organization location |
| Definition | Geographic area supplied as the organization's `location`, exposed by the inverse `Region.organizations` listing. |
| Direction | Organization → geographic area; the repaired input route has a local region endpoint. |
| Endpoint resources | `https://www.diamm.ac.uk/organizations/{id}` → `https://www.diamm.ac.uk/regions/{id}` |
| Input | Existing `relations.csv` row `organization:{id},region:{id},` from region extraction. No reconciliation is needed to assert it. |
| Supported interpretation | DIAMM assigns this organization to this geographic location. |
| Unsupported interpretations | The region is administrative; a manuscript was copied, held or performed there; the organization was there during a particular year; a country hint verifies the link. |

[`to_csv.py`](../src/to_csv.py) already records this relation with organization
as `key1` and region as `key2`. The added branch in
[`convert_rdf.py`](../src/convert_rdf.py) preserves those endpoints and direction.
No extraction, OpenRefine history, export, label or match changes are required.
As with other relation rows, RDF can contain endpoints whose detail table is
absent; this does not fabricate a label, type or Wikidata match for that endpoint.
Duplicate rows collapse to one triple. Distinct supplied regions survive;
the converter does not choose a preferred location or resolve conflicting rows.

Organization/city P131 and organization/country P17 retain their existing
behavior. The new predicate currently covers the previously omitted region
route only, so queries for all organization locations must include those older
routes too. This is a compatibility boundary, not a uniform remapping of every
location field. `country`/`country_@id` are matching hints; shared P2888 matches
also do not create a location. No transitivity or identity rules are enabled.

Example query for the repaired route:

```sparql
PREFIX diamm: <https://linkedmusic.ca/graphs/diamm/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?organization ?region ?name WHERE {
  ?organization diamm:organizationLocation ?region .
  OPTIONAL { ?region rdfs:label ?name }
}
```

Scope it to the DIAMM graph in a shared endpoint. A P131-only or P276-only query
will not retrieve these new location assertions. An explicit join through an
organization can expose its stated region alongside manuscript relationships,
but does not establish a direct manuscript/region relationship or its dates.

## Other review findings and their disposition

The [city serializer](https://github.com/diamm/diamm/blob/052004f86960a5dc4d1e7446be8d5a6ac8594bd1/diamm/serializers/website/city.py)
gets `country` from a general geographic `parent`, then its nested serializer
constructs a `country-detail` URL without checking the parent's type. Local
extraction also assumes a country endpoint. Consequently, checking only the
URL path cannot recover the true type for this inspected serializer. A future
repair needs explicit source type/URL evidence or a snapshot-backed crosswalk;
names and reconciliation hints cannot supply that evidence. The current
country endpoint must not be silently relabelled as a region. Historical
occurrence and deployed serializer behavior remain unmeasured.

The [source-provenance model](https://github.com/diamm/diamm/blob/052004f86960a5dc4d1e7446be8d5a6ac8594bd1/diamm/models/data/source_provenance.py)
links a manuscript to geographic areas, with separate uncertainty flags and
earliest/latest years. City/region serializers expose those qualifiers. Local
extraction discards them: city/source rows become unqualified P131, while
region/source rows currently have no RDF branch. Simply adding an unqualified
region/source location assertion would discard uncertainty and conflate source
provenance with the organization's own location. The next bounded task is a
source-preserving city/region provenance representation, including paired raw
qualifiers and explicit legacy-input behavior. It must not invent dates or
interpret provenance as manuscript creation, performance or current storage.

The [region-history copy-step facet](geographic_names.md), other unprotected
text fields, source URL parsing outside this route and broader relationship
mapping remain separate limitations. No historical inputs, live DIAMM records,
production graphs or OpenRefine service were inspected in this review.

## Validation and regeneration

Four [regressions](../tests/test_geographic_relationships.py) use the actual CSV
loader and extraction/RDF CLIs, tracked export layouts, independently specified
graphs, Turtle round trips and SPARQL checks. They cover legacy relation rows,
duplicate/conflicting locations, identical numeric IDs in different local
namespaces, region reverse listings with null organization location URLs,
supplied name matches, hints/shared matches that must not create relationships,
and existing city/country/source links. A negative query checks that manuscript
locations are not inferred through the organization. Three tests failed before
the repair; all four pass after it. No OpenRefine replay is claimed.

The full offline command, `poetry run python scripts/check_offline.py`, passes
**128 tests and 14 competency fixture queries**, including 45 DIAMM tests.
Black and diff checks pass. Self-review found no introduced correctness defects;
parent type ambiguity and provenance qualifier loss remain documented above.
No independent agent review was performed. Pinned upstream files and before/after
test logs are retained in the ignored
`evaluation/audits/diamm-geographic-relationships-2026-10-29/` directory; tests
do not depend on those local evidence copies.

When snapshot access resumes, count organization/region relation rows and
distinct pairs with explicit denominators. Check them against the source region
listings and record input checksums and conversion revision. Legacy relation
CSVs can supply this repair without re-reconciliation when that source evidence
is verified; old RDF alone cannot recover the omitted links. Regenerate into a
separate directory, compare the new triples alongside labels and existing
relationships, then stage the query before backed-up graph replacement.
Historical frequency, actual export compatibility and production behavior
remain unverified. No stored RDF was regenerated or deployed by this repair.
