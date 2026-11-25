# Qualified manuscript provenance

City and region `provenance` entries survive extraction and RDF conversion with
their uncertainty and year bounds paired. Both routes emit named observations;
neither emits a direct source-to-city P131 assertion, including for legacy CSVs.
Organization `source_provenance` entries use a separate [organization observation](#organization-provenance)
that keeps each co-listed place name and its own uncertainty flag.
Check the [graph version](#checking-the-graph-version) before using the observation queries.

## Definition evidence and scope

The upstream source definitions below are pinned to revision
`052004f86960a5dc4d1e7446be8d5a6ac8594bd1`:

- [SourceProvenance model](https://github.com/diamm/diamm/blob/052004f86960a5dc4d1e7446be8d5a6ac8594bd1/diamm/models/data/source_provenance.py): links a manuscript source to geographic areas, with separate `city_uncertain` and `region_uncertain` booleans and optional integer `earliest_year`/`latest_year` fields.
- [City serializer](https://github.com/diamm/diamm/blob/052004f86960a5dc4d1e7446be8d5a6ac8594bd1/diamm/serializers/website/city.py): `city_sources` supplies `url`, display `name`, `city_uncertain` and both years.
- [Region serializer](https://github.com/diamm/diamm/blob/052004f86960a5dc4d1e7446be8d5a6ac8594bd1/diamm/serializers/website/region.py): `region_sources` supplies the corresponding region flag and years.

These definitions support a provenance association and the supplied bounds.
They do not establish administrative containment, place of creation, a
performance, continuous residence throughout an interval, or current storage.
An explicit false flag means DIAMM does not mark that geographic association
uncertain; it is not independent verification or day-level date precision.
The model's default false does not justify filling an absent serialized flag.
City and region entries do not expose the provenance row's primary key, so
entries across the two listings cannot be identified as the same source event.

Pinned definition evidence does not establish live records, historical
snapshots, the deployed serializer or the input snapshot version.
Other model fields (country, protectorate, note, person/organization links and
their uncertainty) are not recovered when absent from these serialized entries.
The organization listing exposes a different set of fields, described below.

## Extraction and CSV boundary

[`to_csv.py`](../src/to_csv.py), using
[`source_provenance.py`](../src/source_provenance.py), appends the
`source_provenance` column to `relations.csv`. City/source, region/source and organization/source provenance
rows use `type=provenance`; the evidence cell contains the complete parsed
entry as sorted, compact JSON. Unknown fields, strings, explicit nulls and
absent keys remain distinguishable. String whitespace, Unicode, quotes and
newlines survive JSON/CSV escaping. This preserves parsed JSON values, not
the original file's whitespace, numeric token spelling or duplicate object keys.

The complete evidence participates in relation deduplication. Identical entries
collapse; differing qualifiers or metadata survive as distinct rows, even for
the same source and listing record. List order and multiplicity are not retained.
The fixed four-column header is written even for an empty relation table.
Unrelated relation rows have an empty evidence cell and retain their mappings.

This file bypasses OpenRefine. No reconciliation history/export changes are
needed. The RDF loader reads the evidence and relation-type columns as text,
avoiding pandas missing-value inference (including NA-like type strings that
must not masquerade as an empty legacy type). Existing three-column relation
files still load.

Both extraction and conversion validate entry URLs against
`http[s]://www.diamm.ac.uk/sources/{positive ASCII integer}` with an optional
trailing slash. The RDF converter also checks agreement with `key2`. Other
URL forms require source-backed review; they stop conversion rather than being
interpreted as another endpoint. Non-object entries, malformed evidence JSON,
duplicate JSON keys and non-JSON numeric constants in CSV evidence also stop
conversion with relation context. City/source and region/source rows reject unexpected relation types. For
organization/source rows, only `type=provenance` selects this mapping.
Unsupported qualifier values survive in the raw JSON.

## RDF contract

### City and region provenance

`diamm:` below is `https://linkedmusic.ca/graphs/diamm/`. Local endpoints remain
`https://www.diamm.ac.uk/sources/{id}` and `/cities/{id}` or `/regions/{id}`.
The place does not need a detail-table row; no name, type or match is invented.

| Term | Meaning and direction |
| --- | --- |
| `diamm:sourceProvenance` | Manuscript source → named observation of a supplied geographic provenance association. This edge does not assert certainty. |
| `diamm:SourceProvenanceObservation` | Class of observations retaining one source/place entry and its qualifiers. |
| `diamm:place` | Observation → local city/region mentioned by this provenance entry. |
| `dcterms:source` | Observation → local geographic resource whose provenance listing supplied the entry. |
| `diamm:sourceField` | Observation → `"city"` or `"region"` (`xsd:string`), the geographic field in the provenance model. |
| `diamm:sourceProvenanceJson` | Observation → exact nonempty CSV evidence cell (`xsd:string`). Includes the original source URL and display name without promoting them to names or matches. |
| `diamm:uncertain` | Observation → `xsd:boolean`, emitted only for a JSON boolean in the corresponding geographic flag. |
| `diamm:earliestYear`, `diamm:latestYear` | Observation → supplied bound as `xsd:gYear`, for JSON integers 1–9999 only. Short years are padded; booleans, strings and floats are not coerced. |
| `diamm:validationFlag` | Observation → string identifying an unresolved qualifier, legacy input or reversed bounds. |

The [shared preservation schema](../../shared/ontology/preservation.ttl) provides labels, definitions and conservative alignments for these terms.
Its [contract and shapes](../../shared/ontology/README.md) distinguish source
uncertainty, date approximation and processing flags. The schema is separate
from converter instance output and is not deployed automatically. No Wikidata
alignment or direct-location inference rule is asserted for these properties.
The existing `dcterms:source` link is coarse origin context, including on legacy
rows; it does not identify an exact document version, snapshot or conversion.

Observation IRIs are `diamm:source-provenance/{sha256}`, hashing the compact
JSON array `[source IRI, place IRI, exact evidence cell]`. A missing/empty cell
uses an empty string. Input row order does not affect identity. Different
typed endpoints or evidence produce separate observations. Manually changing
JSON formatting in CSV evidence can change identity, as can a display-name
change. These are evidence identities, not stable upstream event identifiers.

Flags are `missing-uncertainty`, `null-uncertainty`, `invalid-uncertainty`, and
the same three prefixes on `earliest-year` and `latest-year`. Null or missing
bounds do not establish open-ended intervals. Values outside the supported
year range remain in JSON; a flag indicates an unsupported projection, not
proof that the source is erroneous. Supported but reversed bounds are both
retained with `reversed-year-bounds`; interval queries must exclude that flag.

Legacy rows with no evidence column or an empty evidence cell get only
`legacy-unqualified-provenance`, with no JSON, certainty or year assertions.
This records unavailable qualifiers without guessing their original values.
Fresh entries with absent qualifier keys instead retain their JSON and the
individual missing-field flags. Mixed legacy/qualified rows remain separate;
the converter does not infer that one supersedes another.

## Organization provenance

Each manuscript links through `diamm:organizationProvenance` to a named
`diamm:OrganizationProvenanceObservation`. Its `dcterms:source` identifies
the local `/organizations/{id}` that supplied the listing. The observation
IRI uses the same hash rule as the geographic routes, with the organization
IRI as the second endpoint. The complete entry, including the manuscript
display text and any additional fields, is available as `diamm:sourceProvenanceJson`.

| Source fields | RDF properties on this observation |
| --- | --- |
| `entity_uncertain` | `diamm:entityUncertain` qualifies the association with the listing organization. |
| `city`, `city_uncertain` | `diamm:cityName`, `diamm:cityUncertain` |
| `region`, `region_uncertain` | `diamm:regionName`, `diamm:regionUncertain` |
| `country`, `country_uncertain` | `diamm:countryName`, `diamm:countryUncertain` |
| `protectorate` | `diamm:protectorateName` |

Each nonempty string keeps its exact spelling as an `xsd:string`. Each JSON
boolean becomes an `xsd:boolean` for that field, including when the place
name is absent. False means the source left that field unflagged. A missing,
null or unsupported flag leaves the query variable unbound. Inspect the JSON
to distinguish these cases. The organization listing supplies neither a
protectorate uncertainty flag nor year bounds. Its place names supply text
only. Joining on equal names cannot identify a geographic record or establish
a shared event with a city or region listing. [Organization serializer](https://github.com/diamm/diamm/blob/052004f86960a5dc4d1e7446be8d5a6ac8594bd1/diamm/serializers/website/organization.py#L25-L40)

Use the [organization provenance query](queries/organization_provenance.rq)
to retrieve one row per observation. For an institution listed in Florence,
a manuscript entry naming Siena with `city_uncertain=false` and
`entity_uncertain=true` returns Siena with its explicit false flag.
A second entry naming Bologna with reversed flags returns its own row.
The organization's own listed place remains available through `schema:location`.

An older three-column `organization:O,source:S,provenance` row or an empty
evidence cell yields a named observation with the organization endpoint and
`legacy-unqualified-provenance`. Its names, booleans and JSON are absent.
Re-extraction from the matching raw organization records is needed to recover
the original entries. A fresh entry containing only the manuscript URL still
has JSON and can be distinguished from a legacy row.

Earlier converters emitted manuscript-to-organization `wdt:P276` for this
route. In those graphs, following `wdt:P276/schema:location` can retrieve
the organization's listed place. The path supplies no manuscript place or
certainty. In newly converted graphs, query the observation to identify the
organization and read its entry. Check the export revision and graph IRI
before interpreting an empty result. A P276 edge alone cannot identify a
converter version because archive holdings also use P276. Copyist rows use
P1071 and typed related-source rows follow their own [relationship mappings](relationships.md).

## Query compatibility

For organization listings, use the [organization provenance query](queries/organization_provenance.rq).

City/source P131 was an unqualified administrative-containment claim. It is
not retained even when uncertainty is explicitly false: provenance alone
does not establish that meaning. No replacement direct P131/P276/P1071/P571
assertion is emitted for either geographic route. Existing archive holdings,
organization locations and city/region/country parent
links retain their behavior and separate limitations. P2888 matches and country
hints cannot create a provenance entry.

For example, suppose DIAMM lists an organization in Florence and separately
associates a manuscript with Florence, marked uncertain for 1400–1450. The
organization links directly to the city with `https://schema.org/location`.
Follow the manuscript's `diamm:sourceProvenance` link to find an observation
with Florence as its place, `diamm:uncertain true`, both years and the parsed
entry. A second manuscript linked only to the organization has no geographic
provenance observation from that link.

To retrieve supplied provenance together with its available qualifiers:

```sparql
PREFIX diamm: <https://linkedmusic.ca/graphs/diamm/>
SELECT ?source ?observation ?place ?uncertain ?earliest ?latest ?flag WHERE {
  ?source diamm:sourceProvenance ?observation .
  ?observation diamm:place ?place .
  OPTIONAL { ?observation diamm:uncertain ?uncertain }
  OPTIONAL { ?observation diamm:earliestYear ?earliest }
  OPTIONAL { ?observation diamm:latestYear ?latest }
  OPTIONAL { ?observation diamm:validationFlag ?flag }
}
```

For an explicitly non-uncertain association with the supplied bounds 1400–1450:

```sparql
PREFIX diamm: <https://linkedmusic.ca/graphs/diamm/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT ?source ?observation ?place WHERE {
  ?source diamm:sourceProvenance ?observation .
  ?observation diamm:place ?place; diamm:uncertain false;
               diamm:earliestYear "1400"^^xsd:gYear;
               diamm:latestYear "1450"^^xsd:gYear .
  FILTER NOT EXISTS { ?observation diamm:validationFlag "reversed-year-bounds" }
}
```

Scope these queries to the DIAMM graph in a shared endpoint. Always join
qualifiers on the observation, rather than combining them across a source/place
pair. The path `diamm:sourceProvenance/diamm:place` is useful for broad discovery
but includes uncertain and legacy entries. Count distinct observations or pairs
explicitly: multiple flags can multiply result rows. Neither query establishes
independently verified identity, manuscript creation or uninterrupted presence.

To select city observations, bind `?observation diamm:sourceField ?field`
and apply `FILTER(STR(?field) = "city")`. Use `"region"` for region observations.
This compares the text of the stored `xsd:string` on both RDFLib and Oxigraph.

### Checking the graph version

Before running the observation queries, check the export's converter revision
and run both probes on the DIAMM named graph. The first detects the older
direct P131 pattern on typed manuscripts.

```sparql
PREFIX diamm: <https://linkedmusic.ca/graphs/diamm/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
ASK { GRAPH diamm: { ?source a diamm:Source ; wdt:P131 ?place . } }
```

The second detects city and region manuscript provenance observations.

```sparql
PREFIX diamm: <https://linkedmusic.ca/graphs/diamm/>
ASK { GRAPH diamm: { ?source diamm:sourceProvenance ?observation . } }
```

| Direct P131 | Observation | Interpretation |
| --- | --- | --- |
| true | false | The old path is present. Observation queries miss those associations. |
| false | true | Observations are present. Use the observation queries with the matching export. |
| true | true | Both patterns are present. Check which exports were loaded before interpreting counts. |
| false | false | The probes cannot identify the version. Check the graph IRI, export revision and source relation rows before interpreting an empty result. |

## Query and answer contract

The [shared contract](../../shared/ontology/README.md) supplies the evidence vocabulary.
The executable templates scope every data pattern to the DIAMM named graph:

- [Organization provenance](queries/organization_provenance.rq) returns the listing organization,
  entry names, field-specific flags and raw evidence, including rows with unknowns.
- [City and region discovery and uncertainty selection](queries/source_provenance.rq)
  returns source, place, observation identity, uncertainty state, supported
  bounds, validation flags and a qualifier-disagreement indicator. Its `VALUES`
  list selects all three states; restrict it to `"uncertain"`,
  `"source-unflagged"` or `"unknown"` as needed. Repeated validation flags can
  create multiple result rows per observation; use distinct identities to count.
- [Qualifier disagreements](queries/source_provenance_disagreements.rq)
  returns pairs of observations and differing supported values for the same
  manuscript/place. Missing values, metadata-only changes and different places
  do not establish a conflict. Different years may describe different events;
  the query identifies evidence to review, not proven historical contradictions.
- [Counts](queries/source_provenance_counts.rq) returns distinct manuscripts
  and observations per uncertainty state. Manuscripts can occur in several
  groups; their subtotals must not be summed or described as event counts.

| Evidence | Required answer wording/behavior |
| --- | --- |
| Explicit true | Attribute uncertainty to DIAMM; retain the place and observation. |
| Explicit false | Say the source does not flag the association as uncertain; do not say verified or independently certain. |
| Missing, null, invalid or legacy flag | Say uncertainty information is unavailable/unsupported. Do not infer false from absence. Retain validation flags. |
| Differing supported qualifiers for one pair | Present both observations and their qualifiers; do not select a preferred value without further evidence. |
| Missing/reversed bounds | Do not invent an open interval, swap bounds or imply continuous presence. |

The [candidate NLQ context](source_provenance_nlq.txt) prepares a later SESEMMI
migration. Its observation block and surrounding notes must accompany relevant
Source context. These query controls establish deterministic RDF behavior, not
LLM accuracy or production latency. Existing SESEMMI configuration is unchanged.

## Validation and regeneration

### Observation identity and lineage

A named observation keeps a relationship and its qualifiers together, following
the [W3C n-ary relation pattern](https://www.w3.org/TR/swbp-n-aryRelations/).
Its deterministic content hash does not identify a historical event, retrieval
occurrence or source-document version. Switching to blank nodes would still
require joins and qualifier interpretation.

The [shared evidence contract](../../shared/ontology/README.md) supplies labels,
definitions, conservative source-specific alignments and executable shapes.
It distinguishes geographic uncertainty, person-date approximation and
conversion flags. None of these fields measures reconciliation quality or
model-generated answer confidence. A source-unflagged association is not
independent verification.

Historical manuscript provenance is separate from RDF lineage. The coarse
`dcterms:source` link to a place or listing organization does not identify a snapshot or conversion execution.
The optional PROV-O profile requires actual retained artifacts, source-record
selectors and run manifests; converters do not fabricate or currently emit it.
Shape validation cannot prove that the external artifacts exist or that their
checksums and contents are correct.

Application context must include the observation class and qualifier notes
whenever provenance is selected. Coordinate complete corpus/examples and graph
version before rollout; loading schema triples does not update a static NLQ
corpus. Deterministic query checks do not measure answer accuracy or latency.

### Conversion checks and deployment boundary

Six new [regressions](../tests/test_source_provenance.py) exercise actual
extraction/CSV/RDF loading and CLIs, full independently specified graphs,
Turtle round trips and SPARQL. They cover both geographic routes, explicit
false/true flags, missing/null/invalid qualifiers, unusual strings and extra
fields, short/unsupported/reversed years, legacy and blank evidence cells,
duplicate/conflicting/reordered rows, typed endpoints with shared numeric IDs,
invalid/mismatched evidence, and preservation of unrelated relationships.
The geographic-name extraction/query test uses the observation route while
retaining its full graph and string assertions. The
[provenance contract tests](../tests/test_provenance_contract.py) check real
converter output against the shapes and exercise graph isolation, unknown
qualifiers, disagreements and counts. The
[shared tests](../../shared/tests/test_preservation_contract.py) distinguish
uncertainty, approximation and processing status and validate synthetic lineage
with positive and malformed cases.

Run from the repository root after installing locked development dependencies:

```sh
poetry install --no-interaction --no-root
poetry run python scripts/check_offline.py
```

These tests use synthetic evidence and do not replay OpenRefine or establish
historical population measurements. The dependency lock includes RDFLib 7.6.0;
see the [dependency validation contract](../../shared/ontology/README.md#dependencies-and-converter-compatibility)
before regenerating output from a different runtime.

When snapshot access resumes, identify the matching raw city, region and organization records,
checksums and serializer version. Count original entries, distinct evidence
observations, duplicates, missing/unsupported qualifiers and changed assertions
with explicit denominators. Re-extract `relations.csv` to recover qualifiers;
old relation rows or RDF cannot supply lost names or qualifiers. Other tables still
need their matching reconciled exports. Regenerate into a separate directory,
check exact and uncertain queries in staging, and back up before replacement.
Appending would retain obsolete city/source P131 and manuscript/organization
P276 statements. Confirm that independently supported archive P276 links survive.
Record deployment version, graph and rollback snapshot before claiming live
behavior. Historical prevalence, real export compatibility and RDF-size cost
require matching snapshots and separate deployment evidence.
