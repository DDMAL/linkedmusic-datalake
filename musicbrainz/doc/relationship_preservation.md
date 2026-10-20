# MusicBrainz relationship-preservation pilot

## Scope and representation

The 33 recording/release-to-artist mappings previously collapsed into `P767`
now retain their distinct MusicBrainz relationship types. This addresses
**conversion loss**, not source-data cleanup. The
[inventory](relationship_inventory.md) records UUIDs, endpoint pairs, permitted
attributes, source definitions, and the limits of the evidence inspected.
Other mappings retain their existing behavior; this is not a complete
MusicBrainz remodel.

Each role uses a local predicate:

```text
https://linkedmusic.ca/terms/musicbrainz/relationship/{MusicBrainz type UUID}
```

These are **LinkedMusic predicates**, not official MusicBrainz RDF terms.
The schema generator supplies a readable label, definition with interpretation
limits, source-definition link, domain, range, and reviewed `rdfs:subPropertyOf`
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

Missing/unknown type IDs, unexpected endpoints/direction, and missing targets
retain source evidence as unresolved observations. They do not acquire a role
from a coincident label. The sample command exits unsuccessfully after writing
its audit if any observation is unresolved. Full-batch users must inspect
`mbterm:mappingStatus` before publishing data.

This pilot does not preserve qualifiers on nonpilot mappings. It does not move
deprecated recording mastering credits onto releases, infer unsupplied roles,
or reconcile new people.

## Configuration and query compatibility

[`relations.json`](../src/rdf_conversion_config/relations.json) accepts:

- Existing Wikidata PID strings and `null` entries.
- Absolute HTTP(S) or URN predicate IRIs without a Wikidata prefix being added.
- Structured pilot entries specifying type UUID, predicate, direction through
  endpoint types, definition, source, and reviewed broader predicate.

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

This route covers the reviewed pilot roles and explicit P767 assertions, not
every conceivable contribution in all MusicBrainz mappings. For exact-role
queries, name the desired role predicate directly; photography is never a
recording-engineering answer.

The sample command uses a local union of base/schema graphs for its portable
offline queries. Production graph scoping, named inference rules, and
materialized broader assertions remain a separate experiment. Ordinary
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
The command makes **no network or model calls**. It produces `base.ttl`,
`schema.ttl`, and `audit.json` separately. The audit records source and
code/configuration checksums, query text, result snapshots and observation
status counts. Auxiliary reconciliation tables are empty in this bounded
runner; use the normal converter and its reconciliation tables for a complete
dataset conversion.

## Current API check, 20 October 2026

Six records were selected from examples on the official relationship-definition
pages and fetched with `inc=artist-rels`. They contained 18 top-level artist
relationships, of which **10 fall within the pilot**. All 10 yielded the expected
specific role assertions and mapped observations; none was unresolved.

| Official record | Manually checked pilot evidence |
| --- | --- |
| [Song of the Black Swan](https://musicbrainz.org/recording/532c89f0-0788-497f-a05e-a287209528d4) | Mike Hatch: recording engineer, 1997-06-01 through 1997-06-03; Tom Lazarus: mixing. |
| [Let My Fish Loose (Aphex Twin remix)](https://musicbrainz.org/recording/91dad391-5033-45c6-8a1e-1cc502ddd393) | Aphex Twin: remixer. |
| [A Huge Ever Growing Pulsating Brain…](https://musicbrainz.org/release/6ceab0eb-8ade-4747-a038-c5ba050311b9) | George Peckham: mastering. |
| [Perfecto Fluoro](https://musicbrainz.org/release/63677dab-e665-4893-92de-16750c31776a) | Paul Oakenfold: DJ mix; source attributes distinguish medium 1 and medium 2. |
| [String Concertos, Volume 2](https://musicbrainz.org/release/8ea41a35-b261-4082-b914-29c3bf06c168) | Michael Talbot: liner notes, begin/end both `2001`, retained without inventing month/day. |
| [Seven Last Words from the Cross](https://musicbrainz.org/release/521f9863-1a19-4022-a4ee-28a3122743fb) | Tim Parry: booklet editor; Elke Hockings and Hyperion: liner notes with translator attributes; Paul Spicer: liner notes. |

The API query results contain one recording-engineer answer, no recording
photographers, and 10 distinct record/artist contributor pairs. Photography's
positive and negative checks use the synthetic fixture. The current API sample
does not exercise every one of the 33 mappings and cannot establish population
accuracy or fidelity of the historical dump. Raw responses, their retrieval
URLs/timestamps/checksums, and generated results are local artifacts under
`/tmp/linkedmusic-preservation-2026-10-20/`.

Before full regeneration, inspect the Arbutus/Montreal snapshot, validate its
field shapes (including embedded recordings and inverse artist records), and
measure RDF size/runtime overhead from observation nodes. Review query
compatibility and schema graph placement before loading. No full MusicBrainz
regeneration, live graph replacement, or production inference was performed.

**Deployment is still required:** regenerate from the source JSON, validate the
new RDF in staging, then replace the affected MusicBrainz graph in Virtuoso and
load the matching schema into a separate named graph. Old P767-only Turtle
cannot recover the discarded roles or qualifiers. Merging the converter change
does not update Virtuoso, and appending new RDF to the old graph would leave the
old generic assertions in place.

The later SESEMMI phase must explicitly ingest these definitions, qualifier
semantics, and query patterns. Merely loading schema comments into Virtuoso
does not synchronize application context; no SESEMMI code is changed here.
