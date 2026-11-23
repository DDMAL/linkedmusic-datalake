# MusicBrainz relationship-preservation pilot

## Scope and representation

The converter retains exact MusicBrainz roles for 33 artist relationships
previously mapped to `P767` and two release photography relationships
previously mapped to `P344`. The
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
limits, source-definition link, domain, range, and any configured `rdfs:subPropertyOf`
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

### Release photography

MusicBrainz credits an artist or an agency for photographs included with a
release. The release is the RDF subject. Each predicate identifies the type of
credit, including when the source relationship appears on the artist or label.
A credit named `photography` on either endpoint pair with a missing or
unrecognized type UUID is kept as an unresolved observation.
[Artist definition](https://musicbrainz.org/relationship/0b58dc9b-9c49-4b19-bb58-9c06d41c8fbf) · [Agency definition](https://musicbrainz.org/relationship/813919d5-a93d-4334-89df-ffa2f9b8ff43)

Run this query on the converted data graph to retrieve both credits. For
additional photography, also match an observation with the same `rdf:subject`,
`rdf:predicate` and `rdf:object` and the attribute `mbterm:attribute "additional"`.

```sparql
SELECT ?release ?creditType ?credited WHERE {
  VALUES ?creditType {
    <https://linkedmusic.ca/terms/musicbrainz/relationship/0b58dc9b-9c49-4b19-bb58-9c06d41c8fbf>
    <https://linkedmusic.ca/terms/musicbrainz/relationship/813919d5-a93d-4334-89df-ffa2f9b8ff43>
  }
  ?release ?creditType ?credited .
}
```

An artist whose photographs are included with a release contributed to that
release. With the matching schema, the [contributor query](queries/pilot_contributors.rq)
returns that artist, just as it returns a photographer credited on a recording.
The agency role has a MusicBrainz label endpoint and no P767 alignment in this
artist query. The photography query above returns both release roles.

Use `wdt:P344` for a video recording’s cinematographer. Wikidata’s photographer
property, `P14574`, takes an individual photograph as its subject.
[MusicBrainz cinematographer](https://musicbrainz.org/relationship/4b290951-ab5e-4605-a304-650aa1f35377) · [Wikidata photographer](https://www.wikidata.org/wiki/Property:P14574)

In exports made with the earlier mapping, select P344 on resources typed as
releases to retrieve the artist and agency credits. A release export can also
contain video recordings with their own P344 credits.

```sparql
PREFIX mb: <https://linkedmusic.ca/graphs/musicbrainz/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
SELECT ?release ?credited WHERE {
  ?release a mb:Release ;
           wdt:P344 ?credited .
}
```

The earlier mapping skipped the inverse artist and label entries. Its P344
triple omits the source UUID and qualifiers.
Use the export’s converter revision and configuration to interpret it. Recover
the exact source observations by converting the corresponding MusicBrainz records.

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

To find artists credited with adapting a recording or release, query `wdt:P5202`
on that version and restrict the result to MusicBrainz artist IRIs. The legacy
“arranged for” mapping also emits P5202 for the label that commissioned the
arrangement. That credit identifies the client. [Recording credit](https://musicbrainz.org/relationship/1a26bf37-1f34-4c9a-97d5-b96bc49e9153) · [Release credit](https://musicbrainz.org/relationship/c395de60-b84b-4a09-99b2-30b222fda04e)

This query runs against the sample converter’s `base.ttl`. For another version,
replace the recording IRI in `VALUES` with the recording or release IRI.

```sparql
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
SELECT DISTINCT ?agent WHERE {
  VALUES ?version { <https://musicbrainz.org/recording/00000000-0000-4000-8000-000000000001> }
  ?version wdt:P5202 ?agent .
  FILTER(STRSTARTS(STR(?agent), "https://musicbrainz.org/artist/"))
}
```

The artist results can include arrangers and remixers. To find remix credits
specifically, query the recording or release remixer UUID and inspect its
observation attributes. An artist who assisted on a remix and also arranged
the recording can qualify through the arrangement. MusicBrainz also credits
mash-ups and sample-based remixes under the remixer role. The P5202 triple
identifies the credited artist and leaves the original material unspecified.
[Wikidata property definition](https://www.wikidata.org/wiki/Property:P5202)

| Converter used for the graph | Output for a remixer credit on a recording or release |
| --- | --- |
| Before exact role preservation | A generic P767 contributor triple. The graph cannot distinguish that credit from other contributions. |
| With exact roles, before the remix-to-P5202 mapping | The remixer UUID and its observation, including any qualifiers. |
| With the remix-to-P5202 mapping | The exact role and observation, plus P5202 for a plain or additional remixer when the qualifiers support it. |

The exact-role revisions described here, including the release photography
mapping, all record `mapping/contributor-pilot-v1` as the `mbterm:mappingVersion`.
Identify the converter from the graph’s run record. For sample conversions,
match the `implementation_sha256` and
`configuration_sha256` entries in the accompanying `audit.json` to the source
revision. For a batch export, use the recorded converter revision and
configuration for that export. If those records are missing, its revision is unknown.

## Configuration and query compatibility

[`relations.json`](../src/rdf_conversion_config/relations.json) accepts:

- Existing Wikidata PID strings and `null` entries.
- Absolute HTTP(S) or URN predicate IRIs without a Wikidata prefix being added.
- Structured pilot entries specifying type UUID, predicate, direction through
  endpoint types, definition, source, and configured broader predicate.

Malformed configuration fails before batch conversion. Existing nonpilot null
inverse mappings remain null. The pilot explicitly recognizes either source
direction by UUID, including an inverse artist or label record.

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

This route covers the P767-aligned roles and explicit P767 assertions. For exact-role
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
contributor answers. Running the [adapted-by query](#remix-credits-and-adapted-by-queries)
on the default sample’s `base.ttl` returns the additional remixer,
`https://musicbrainz.org/artist/00000000-0000-4000-8000-000000000004`.
Tests additionally cover both source directions, different
endpoint-specific UUIDs, missing/conflicting evidence, partial dates, attributes,
stable observation IDs, embedded recordings, legacy mappings, and worker
serialization.

To convert one current API response saved as JSON:

```bash
poetry run python musicbrainz/src/convert_relationship_sample.py \
  --source-kind api --recording /tmp/recording-response.json \
  --output-dir /tmp/musicbrainz-api-pilot
```

Repeat `--recording`, `--release`, `--artist`, or `--label` for additional saved records.
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
