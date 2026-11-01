# Qualified city/region source provenance

Implemented locally on 29 October 2026. City and region `provenance` entries
now survive extraction and RDF conversion with their uncertainty and year
bounds paired. The former city/source P131 projection is removed, including
for legacy CSVs; the formerly omitted region/source route now emits observations.
This is a query compatibility change. Stored RDF has not been regenerated.

## Definition evidence and scope

The retained upstream files were inspected and their Git blob hashes verified
against the existing manifests at revision
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

This review used retained definition evidence, not live records or historical
snapshots. It does not confirm the deployed serializer or input snapshot version.
Other model fields (country, protectorate, note, person/organization links and
their uncertainty) are not recovered when absent from these serialized entries.
Other provenance routes and geographic parent routing remain separate work.

## Extraction and CSV boundary

[`to_csv.py`](../src/to_csv.py), using
[`source_provenance.py`](../src/source_provenance.py), appends the
`source_provenance` column to `relations.csv`. City/source and region/source
rows use `type=provenance`; the evidence cell contains the complete parsed
entry as sorted, compact JSON. Unknown fields, strings, explicit nulls and
absent keys remain distinguishable. String whitespace, Unicode, quotes and
newlines survive JSON/CSV escaping. This preserves parsed JSON values, not
the original file's whitespace, numeric token spelling or duplicate object keys.

The complete evidence participates in relation deduplication. Identical entries
collapse; differing qualifiers or metadata survive as distinct rows, even for
the same source/place pair. List order and multiplicity are not retained.
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
conversion with relation context. Unexpected nonempty relation types are rejected.
Invalid qualifier values within a valid object are retained and flagged instead.

## RDF contract

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

The [shared preservation schema](../../shared/ontology/preservation.ttl) now
provides labels, definitions and conservative alignments for these terms.
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

## Query compatibility

City/source P131 was an unqualified administrative-containment claim. It is
not retained even when uncertainty is explicitly false: provenance alone
does not establish that meaning. No replacement direct P131/P276/P1071/P571
assertion is emitted for either geographic route. Existing archive locations,
organization provenance/location mappings and city/region/country parent
links retain their behavior and separate limitations. P2888 matches and country
hints cannot create a provenance entry.

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

## Query and answer contract

Added 1 November 2026 under the [shared contract](../../shared/ontology/README.md).
The executable templates scope every data pattern to the DIAMM named graph:

- [Broad discovery and uncertainty selection](queries/source_provenance.rq)
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

### Design review — 29 October 2026

Historical review: the shared-contract prerequisite below was implemented on
1 November in [shared/ontology](../../shared/ontology/README.md), including
machine-readable definitions, executable shapes and query controls. The
optional lineage profile is specified but not emitted by existing converters;
application deployment and real-data evaluation remain pending.

Liam requested a critical review of the observation pattern, uncertainty
ontology and NLQ implications. The implementation is a candidate preservation
model, not a completed shared ontology or an NLQ-ready deployment. Its bounded
conversion tests establish retention of synthetic evidence, not the quality of
generated natural-language answers or query performance.

The intermediate resource is a named IRI, not a blank node. It serves the
qualification role described by the [W3C n-ary relation pattern](https://www.w3.org/TR/swbp-n-aryRelations/).
SPARQL can bind either kind of resource to a variable; switching to blank nodes
would not remove the joins or the need to interpret qualifiers. The current
hash is deterministic for identical evidence but changes with JSON formatting
or display-name metadata, and does not distinguish identical entries retrieved
in different snapshots. Its identity is not an independently identified event.

The `diamm:` terms are locally defined. There is no shared provenance/uncertainty
schema across this model, DIAMM person-year observations, MusicBrainz statements
and APSearch creation periods. A source uncertainty flag, date approximation,
parsing status, reconciliation quality and model-generated answer confidence
are different quantities. They must not be merged into one confidence score.
In particular, an unflagged DIAMM association does not establish verification.

Historical manuscript provenance and provenance of the RDF assertion are also
different. The current `dcterms:source` link points to the same geographic
resource used as the place endpoint; it is too coarse to identify the exact
source document/snapshot or conversion activity. A proposed shared lineage
layer should identify the source record version and conversion, using reviewed
[PROV-O](https://www.w3.org/TR/prov-o/) terms where appropriate. That layer is
not implemented. [CRMinf](https://cidoc-crm.org/extensions/crminf/html/CRMinf_v1.2.1.html)
is a candidate for a future requirement to represent attributed scholarly
beliefs and argumentation; it is not adopted here, and the boolean flags do
not provide the missing actors, arguments or calibrated belief values.

Read-only inspection of sibling SESEMMI at `fix/clara-starter-role-agnostic`
found its `llm-service/app/graph/schema_corpus.py` still describes
`diamm:Source wdt:P131 diamm:City` and contains neither the provenance observation
class nor its uncertainty terms. Retrieval reads that static corpus. Loading
schema triples into Virtuoso does not automatically update this context.
An in-memory candidate class block passed through the actual ontology parser
and slicer with its qualifiers intact when selected; selecting only Source
omitted those definitions. This was a deterministic structural check, not an
NLQ model evaluation. No SESEMMI files or production services were changed.

Before deployment or extending this modeling pattern, agree a small shared
assertion/lineage vocabulary with labels, definitions, shapes and explicit
source-specific qualifier meanings. Provide query templates for broad discovery,
explicitly uncertain, source-unflagged, unknown and conflicting evidence, with
counts defined over manuscripts versus observations. The later SESEMMI update
must keep qualifier classes and query notes in retrieved context, synchronize
examples with the deployed graph version, and verify that the returned columns
and answer wording retain uncertainty. No accuracy or latency effect has yet
been measured. This review does not change the current RDF representation.

### Conversion checks and deployment boundary

Six new [regressions](../tests/test_source_provenance.py) exercise actual
extraction/CSV/RDF loading and CLIs, full independently specified graphs,
Turtle round trips and SPARQL. They cover both geographic routes, explicit
false/true flags, missing/null/invalid qualifiers, unusual strings and extra
fields, short/unsupported/reversed years, legacy and blank evidence cells,
duplicate/conflicting/reordered rows, typed endpoints with shared numeric IDs,
invalid/mismatched evidence, and preservation of unrelated relationships.
All six failed before implementation (14 failures including subtests); the
additional JSON ambiguity and relation-type controls were added during review.
The existing geographic-name extraction/query test now uses the observation
route while keeping its full graph and string checks.

The full offline command passes **134 tests and 14 competency fixture queries**,
including 51 DIAMM tests. These are synthetic checks. No OpenRefine replay,
independent agent review or historical population measurement was performed.
Self-review added duplicate-key/non-JSON constant rejection and a relation-type
guard, including text loading of NA-like relation types. Both documented queries
were executed against a synthetic graph with independently checked expected
results; Black and repository/wiki diff checks pass. Retained source copies,
verified hashes and test logs are in ignored
`evaluation/audits/diamm-source-provenance-2026-10-29/`; tests do not depend on them.

When snapshot access resumes, identify the matching raw city/region records,
checksums and serializer version. Count original entries, distinct evidence
observations, duplicates, missing/unsupported qualifiers and changed assertions
with explicit denominators. Re-extract `relations.csv` to recover qualifiers;
old relation rows or RDF cannot supply lost years/certainty. Other tables still
need their matching reconciled exports. Regenerate into a separate directory,
check exact and uncertain queries in staging, and back up before replacement.
Do not append to old RDF: obsolete city/source P131 statements would remain.
Record deployment version, graph and rollback snapshot before claiming live
behavior. Historical prevalence, real export compatibility and RDF-size cost
remain unmeasured. This repair is local and uncommitted; nothing was deployed.
