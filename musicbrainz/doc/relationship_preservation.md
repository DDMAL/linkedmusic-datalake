# MusicBrainz relationship-preservation pilot

## Scope and representation

The 33 configured recording/release-to-artist mappings retain their distinct
MusicBrainz relationship types instead of emitting only `P767`. This addresses
**conversion loss**, not source-data cleanup. The
[inventory](relationship_inventory.md) records UUIDs, endpoint pairs, source
attribute leads, definition references, and the limits of available evidence.
Other mappings retain their existing behavior; this is not a complete
MusicBrainz remodel.

The [representation rationale](representation_review.md) explains this model
and the explicit, separately scoped schema query below. Source-definition
references must be checked against the snapshot being converted; this document
does not establish fidelity of an unavailable historical dump.

Each role uses a local predicate:

```text
https://linkedmusic.ca/terms/musicbrainz/relationship/{MusicBrainz type UUID}
```

These are **LinkedMusic predicates**, not official MusicBrainz RDF terms.
The schema generator supplies a readable label, definition with interpretation
limits, source-definition link, domain, range, and configured `rdfs:subPropertyOf`
alignment to `wdt:P767`. A generic contributor never implies a specific role.
No `owl:equivalentProperty`, `owl:sameAs`, or automatic identity rule is added.

For example, the recording-engineer UUID
`a01ee869-80a8-45ef-9447-c59e91aa7926` means:

```turtle
@prefix mbrel: <https://linkedmusic.ca/terms/musicbrainz/relationship/> .
@prefix ex: <https://example.org/synthetic/> .

ex:recording mbrel:a01ee869-80a8-45ef-9447-c59e91aa7926 ex:artist .
```

The RDF subject is the recording; the object is the artist. MusicBrainz uses
artist-first endpoint order, so the source record may describe the same credit
as artist → recording (`forward`) or recording → artist (`backward`). Both
produce the RDF direction above. Release recording-engineer credits use a
different UUID. The UUID is authoritative even if a source label changes.

## Relationship observations and qualifiers

Every pilot relationship also gets a named observation:

```text
https://linkedmusic.ca/graphs/musicbrainz/relationship/{sha256}
```

The digest covers the source record IRI and its entire relationship JSON,
serialized with sorted object keys. Repeated identical input produces the same
IRI; different qualifiers produce distinct observations. The node identifies
an observed source payload, **not** a MusicBrainz relationship instance.
Inverse observations may produce different nodes and the same direct triple.
Embedded target metadata and array order participate in the digest; a change
to an embedded artist name can therefore create a new observation without
changing the role assertion. Parent-record metadata, snapshot identity and
mapping version do not participate. Keep snapshot/conversion provenance in the
run manifest and graph scope; the node is not a globally unique occurrence ID.
Count direct role triples for distinct role assertions; count observation nodes
for source occurrences with distinct payloads. Identical duplicate JSON entries
on one source record intentionally coalesce.

A mapped observation is an `rdf:Statement` with `rdf:subject`, `rdf:predicate`,
and `rdf:object`. Its `dcterms:source` points to the source record.
The `https://linkedmusic.ca/terms/musicbrainz/` vocabulary records:

| Fields | Representation and limits |
| --- | --- |
| Type ID, label, direction | Original supplied values; the definition URI is added only after validation. |
| Begin/end | Exact text, including year-only, year-month, or empty strings. These are dates of the relationship, not release dates or performance dates. |
| Ended | Original boolean, including `false`; missing/null stays distinguishable in the JSON. |
| Attributes | Supplied attribute labels, including assistant, translator, instrument or medium details. These qualify this role, not the artist generally. |
| Attribute IDs, values, credit strings | Separate JSON literals preserve key/value association. |
| Full source payload | `rdf:JSON` retains all fields, embedded target details, null values, and unrecognized qualifiers. This is semantic JSON preservation, not byte-for-byte whitespace preservation. |
| Mapping version/status | The local mapping version and either `mapped` or a reason a direct assertion was withheld. Audit artifacts also hash the exact code/configuration. |

Direct predicates summarize a role without its qualifiers. An assistant
engineering credit supports an engineering-role query, but does not establish
that the artist was the lead engineer. A liner-note translator is a liner-note
contributor, not necessarily its original author. Use the observation when the
question depends on such distinctions.

Within the recognized pilot, missing/unknown type IDs, unexpected
endpoints/direction, and missing targets retain source evidence as unresolved
observations. Recognition requires a known pilot UUID, or a pilot label in the
expected endpoint pair (including its inverse). If neither identifies a pilot
candidate, existing nonpilot conversion applies; this is not an audit of every
unknown relationship. A coincident label can trigger evidence retention but
cannot assign a specific role. The sample command exits unsuccessfully after
writing its audit if any retained observation is unresolved. Full-batch users
must inspect `mbterm:mappingStatus` and separately account for unrecognized
relationships before publishing data. A recognized pilot UUID with inconsistent
endpoints withholds both the role assertion and the legacy relation edge; its
unresolved payload remains available rather than asserting either interpretation.

The retained JSON is the complete relationship object supplied to the converter,
not the complete parent entity, response envelope or dump line. A source entity
without an ID is skipped by the existing converter. This pilot assumes the
usual JSON field shapes. A null attribute list is retained in the payload and
produces no convenience attribute triples; other arbitrary malformed shapes
are not promised support. Validate those shapes against the stored dump before regeneration.

This pilot does not preserve qualifiers on nonpilot mappings. It does not move
recording-level mastering or photography credits onto releases, infer
unsupplied roles, or reconcile new people.

### Remix credits and adapted-by queries

For a mapped recording or release remixer credit, the base graph also contains
`?version wdt:P5202 ?artist` when the credit identifies a plain or additional
remixer. The assertion points from the credited version to the artist in
either source direction. A credit on a recording inside a release applies to
that recording. A release-level assertion requires its own credit.

The [MusicBrainz JSON serializer](https://github.com/metabrainz/musicbrainz-server/blob/42caf9ae663cef43ec489853786b866f3dbe6316/lib/MusicBrainz/Server/WebService/Serializer/JSON/2/Relationship.pm#L27-L50)
represents unqualified credits with an empty `attributes` list. The converter
also accepts `["additional"]`, including its matching attribute UUID when
supplied. An assistant, a missing or unknown qualifier list, conflicting IDs,
or extra attribute values or credit text leaves only the exact remix role and
its source observation. The [role inventory](relationship_inventory.md) links
the recording and release definitions and their attributes.

For “who adapted this version?”, query `wdt:P5202` on that version. The results
can include arrangers. For “who received a remix credit?”, query the
recording or release remixer UUID and read the attributes on its observation.
Even when one artist has both an arrangement and an assistant remix credit
on the same recording, the adaptation triple alone cannot identify which
credit supplied it. Older conversions may retain a remix observation without
the direct adaptation triple. Check the converter revision when comparing
graphs. [Wikidata property definition](https://www.wikidata.org/wiki/Property:P5202)

## Configuration and query compatibility

[`relations.json`](../src/rdf_conversion_config/relations.json) accepts:

- Existing Wikidata PID strings and `null` entries.
- Absolute HTTP(S) or URN predicate IRIs without a Wikidata prefix being added.
- Structured pilot entries specifying type UUID, predicate, direction through
  endpoint types, definition, source, and configured broader predicate.

Malformed configuration fails before batch conversion. Existing nonpilot null
inverse mappings remain null. The pilot explicitly recognizes either source
direction by UUID, including an inverse artist record.

New pilot conversion outputs **specific role triples**. It does not materialize
the former generic P767 triples. An old P767-only query against newly converted
base data will therefore omit these roles. For broader queries without
reasoning, keep the generated schema in a separate graph and use:

```sparql
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
SELECT DISTINCT ?record ?artist WHERE {
  {
    GRAPH <urn:linkedmusic:pilot:data> { ?record wdt:P767 ?artist }
  } UNION {
    GRAPH <urn:linkedmusic:pilot:data> { ?record ?role ?artist }
    GRAPH <urn:linkedmusic:pilot:schema> {
      ?role rdfs:subPropertyOf+ wdt:P767
    }
  }
}
```

The checked query is also available as
[`pilot_contributors.rq`](queries/pilot_contributors.rq).

This returns distinct record/artist pairs and deliberately omits evidence
columns. For qualifier-sensitive answers, use the observation pattern in
[CQ09](../../evaluation/queries/cq09.rq), retaining the observation IRI, source
record, direction and payload. Multiple attributes can create several result
rows for one observation. Count distinct observation IRIs for observations,
and distinct record/artist pairs for contributors. CQ07–CQ09 are bounded to
25 rows in the evaluation runner; they do not certify complete live results.

This route covers the configured pilot roles and explicit P767 assertions, not
every conceivable contribution in all MusicBrainz mappings. For exact-role
queries, name the desired role predicate directly; photography is never a
recording-engineering answer.

The sample command evaluates separate named data/schema graphs locally using
the same explicit contributor query above. Production graph scoping, named inference rules, and
materialized P767 assertions remain a separate experiment. Ordinary
`rdfs:comment` triples are descriptions, not inference rules.

## Reproduce offline

From the repository root, with Python 3.12 and the existing Poetry environment:

```bash
poetry run python -m unittest discover -s musicbrainz/tests -v
poetry run python musicbrainz/src/convert_relationship_sample.py \
  --output-dir /tmp/musicbrainz-role-pilot
```

The default input is a small synthetic recording with an engineer, photographer
and remixer. Expected results: three observations, three distinct role
assertions, one engineering answer, one photography answer, and three distinct
contributor answers. Tests additionally cover both source directions, different
endpoint-specific UUIDs, missing/conflicting evidence, partial dates, attributes,
stable observation IDs, embedded recordings, legacy mappings, and worker
serialization.

To convert one current API response saved as JSON:

```bash
poetry run python musicbrainz/src/convert_relationship_sample.py \
  --source-kind api --recording /tmp/recording-response.json \
  --output-dir /tmp/musicbrainz-api-pilot
```

Repeat `--recording`, `--release`, or `--artist` for additional saved records.
The command makes **no network or model calls**. It requires a new output
directory and writes `base.ttl`, `schema.ttl`, `audit.json` and exact input copies
separately. Explicit input paths require `--source-kind synthetic`, `api` or
`dump`; only the built-in fixture defaults to synthetic. The audit records
runtime versions, output hashes, source and code/configuration checksums, query text, result snapshots and observation
status counts. Auxiliary reconciliation tables are empty in this bounded
runner; use the normal converter and its reconciliation tables for a complete
dataset conversion.

## Population validation and rollout

The included fixture is synthetic. Historical MusicBrainz source snapshots and
matching archived definition/API evidence are not supplied with this model.
No fixture or fresh API response can establish fidelity of an older stored dump.
Before regeneration, identify matching inputs and compare endpoint/type UUIDs,
directions, qualifier keys, unknown/nonpilot relationships and date precision.
Keep separate denominators for input occurrences, distinct payload observations,
role assertions and contributor pairs.

Generate into separate candidate outputs with source/code/configuration hashes.
Load base data and matching schema into distinct staging graphs; verify
source-backed exact-role and qualifier queries and scoped broad queries. Check
application schema compatibility, backups and rollback before a separately
approved replacement. Installing this code does not change stored or deployed
RDF or configure application context.

## Emit a matching schema for a batch conversion

Generate schema from the exact `relations.json` used by the batch converter:

```sh
poetry run python musicbrainz/src/emit_relationship_schema.py \
  --relations musicbrainz/src/rdf_conversion_config/relations.json \
  --output-dir /absolute/path/to/new-role-schema
```

The output directory must be new. It contains `schema.ttl`, a byte-for-byte copy
of the mapping configuration and `audit.json` with configuration, schema, code,
lock-file and runtime identity. Match the recorded configuration hash with the
batch run, load data and schema into distinct graphs, then run the
[scoped contributor query](queries/pilot_contributors.rq). Without the schema,
queries following broader P767 paths cannot discover the specific-role edges.
This command does not load data or configure inference.

Internal callers need `RelationshipMappings` for role evidence; plain mapping
dictionaries retain the legacy conversion path and do not implement this contract.
