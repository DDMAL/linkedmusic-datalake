# MusicBrainz contributor representation

## Specific assertions and explicit schema joins

Retain specific source role predicates in the base graph and their configured
broader P767 alignment in a separate schema graph. The
[contributor query](queries/pilot_contributors.rq) unions explicit P767 data
with roles having a nonempty schema path to P767. It returns distinct
record/artist pairs and does not materialize generic assertions. A generic
contributor, photographer or generic engineer does not establish recording
engineering; use the exact recording-engineer UUID for that question.

This model covers the 33 configured recording/release contributor mappings.
Their [inventory](relationship_inventory.md) links source definitions; it is
not a population measurement or a fresh verification of an unavailable dump.
The [model contract](relationship_preservation.md) defines endpoints, retained
qualifiers and unresolved evidence. Source references need snapshot validation.

## Source observations and counting units

Each observation IRI hashes the source record IRI plus the complete supplied
relationship JSON with sorted object keys. Identical repeated payloads on one
source record coalesce. Qualifier changes, embedded target metadata and array
order can create separate observations; object-key order does not. Inverse
source records retain their own source/direction observations while producing
the same normalized role assertion.

Parent-record metadata, file paths, snapshot dates and mapping versions are
outside the digest. Do not append different conversions and assume observation
IRIs distinguish their snapshots. Preserve run-level input/code/configuration
identity and separate graph populations. The retained payload is the supplied
relationship object, not the whole entity response or original whitespace.
The sample CLI separately archives the exact supplied input file bytes.

Count distinct role triples for assertions, observation IRIs for distinct
source payload observations, and record/artist pairs for contributors. Query
rows can multiply when an observation has several attributes. Identical input
occurrences are not recoverable as distinct occurrences from coalesced nodes.

A known pilot UUID is retained even with invalid endpoints/direction or a
missing target. An unknown/missing UUID is retained only when the endpoint-
specific pilot label recognizes a candidate, including the inverse route.
Otherwise ordinary nonpilot conversion applies. A label never assigns a
specific role to an unknown UUID. Zero unresolved observations therefore does
not prove that every input relationship was covered.

Assistant and translator attributes qualify the observed credit. A direct role
triple does not establish lead responsibility or original authorship. Use
[CQ09's observation pattern](../../evaluation/queries/cq09.rq) and retain the
source, direction, payload and observation IRI when qualifiers matter.

## Alternatives and compatibility

| Route | Evidence and compatibility requirements |
| --- | --- |
| Explicit schema query (current) | Separate named data/schema scopes; matching configuration; no additional base assertions. Ordinary P767-only queries need adaptation. |
| Derived contributor graph | Requires a concrete compatibility need, reviewed rules, source-observation links, rule/version provenance and retraction policy. Existing queries must include the derived graph. |
| Engine inference | Requires an isolated engine experiment with explicit rule scope, answer provenance and measured performance. No production inference is configured by these tools. |

Synthetic tests exercise exact-role exclusions, inverse/duplicate observations,
qualifiers and graph-scope controls. The sample CLI runs the same scoped
contributor query against separate local named graphs. These checks establish
bounded code behavior; they do not validate historical source coverage, link
identity or production performance. Unknown inputs and arbitrary malformed JSON
shapes require separate validation before regeneration.

## Reproduce and validate a population

From the repository root, using locked Python 3.12 dependencies:

```sh
poetry run python -m unittest discover -s musicbrainz/tests -v
poetry run python musicbrainz/src/convert_relationship_sample.py --output-dir path/to/new-role-sample
poetry run python scripts/check_offline.py
```

Keep source snapshots, configuration, raw input copies, base/schema outputs and
the audit report together. Identify unrecognized/nonpilot relationships as well
as unresolved pilot observations before claiming coverage. Validate the exact
source/schema graphs and application queries in staging before a separately
approved deployment. Installing this representation does not update stored RDF,
Virtuoso inference settings or application schema context.
