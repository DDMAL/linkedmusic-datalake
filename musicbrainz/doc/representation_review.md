# MusicBrainz relationship representation decision

Reviewed 20 October 2026 for #450/#470. **Retain the 33 specific role
predicates, named source observations and explicit broad-contributor query
over a separately scoped schema graph.** No converter or mapping change is
justified by the evidence reviewed. This completes the local representation
review, not historical-dump validation or deployment.

## Reviewed versions and evidence

Repository HEAD was `c468e94794da4bf0ae6d2f543c242414cb6f56ce` on `main`.
The MusicBrainz implementation/configuration and contributor query are unchanged
from `412c3d66af392e5c6a6508dddbb865c6c4f1ad1b`. The mapping identifier remains
`https://linkedmusic.ca/terms/musicbrainz/mapping/contributor-pilot-v1`.
At review time, the APSearch/evaluation work and this review were uncommitted;
that HEAD alone does not identify the reviewed working tree. Subsequent commit
status is recorded in the [handoff](../../LINKEDMUSIC-HANDOFF.md#local-commit-stages).

Exact SHA-256 values of the principal reviewed files:

| File | SHA-256 |
| --- | --- |
| `src/relationship_mapping.py` | `679ac0fb5c1b55836e175f9cb9855734544bae9e3bfa60979ffb2dd300b6b02b` |
| `src/convert_to_rdf.py` | `aa76ba8735ba7eb5e0c9d465e9921a1f5dc07ce8acc0b8155be28b0307747639` |
| `src/convert_relationship_sample.py` | `d418e6572ffd254327521979c80399edc040e7251617c73fecdfb81d2845501c` |
| `src/rdf_conversion_config/relations.json` | `ea842339835b6e95ea741696e2570f3d7416eed16839067461a8acd3eeefafd9` |
| `src/rdf_conversion_config/mappings.json` | `f8a785e1530a88ce41ba98953ab115cabf1d7d757a317acd74568df1a307272e` |
| `src/rdf_conversion_config/attribute_mapping.json` | `61259f615fec177c0dc2d40cd68b54fd25d66df2182e12a917028da48f0bef05` |
| `doc/queries/pilot_contributors.rq` | `e3a1050adefae6ad47749007e468d55ed962a94cb67159cbd296fe7b0e6a5a4f` |
| `../evaluation/cases.json` | `504775361ef2654b90d103bc0dff6c78f198be5b2d0930f2cccb1929a06e0dad` |
| `../evaluation/queries/cq07.rq` | `9555d9dc5c726c2a6a38718df01368337c2e9686c2ca37a3d3190407c90676b0` |
| `../evaluation/queries/cq08.rq` | `d6464c1e1d1b03647d7ebdba0241f3b8c15c7a1a92608b7e3c8856219d66e2b7` |
| `../evaluation/queries/cq09.rq` | `5593ba97d6d8f7e4247ef666b86697ea45668454efadb3fa25bf56cc32434201` |

Evidence read from the retained workspace copy:

- All 33 official relationship-definition HTML pages, their manifests and the
  [inventory](relationship_inventory.md). Each configured UUID, endpoint pair,
  local definition, permitted attribute list and start/end-date support was
  checked against the archived page. The semantic alignment judgment below is
  a local review decision, not an official MusicBrainz endorsement.
- Six archived API responses: two recording and four release records, with
  18 top-level artist relationships, 10 pilot relationships and seven distinct
  pilot type UUIDs. These are the previously selected current-API examples,
  not new fetches or historical-dump samples.
- Converter integration, schema generation, sample conversion, existing tests
  and evaluation cases CQ07–CQ09. Synthetic controls cover behavior absent
  from the API selection, including inverse artist records and photography.

All 340 files in `evaluation/audits/handoff-2026-10-20/manifest.json` matched
their recorded checksums. The manifest SHA-256 is
`ea551d83175d6ab8b26ccf1ce9b758383ebf7987dd84575f2c712517270df005`.
New local results are under
`evaluation/audits/representation-review-2026-10-20/`: `review-evidence.json`
records the per-type checks and file hashes; `api-conversion/` contains the
reproduced base/schema/audit; `fixture-queries/` contains all 14 evaluation
queries and results. These ignored artifacts are local evidence, not a remote
backup. The repository tests and decision remain usable without them.

## Mapping and source-meaning findings

All **16 recording and 17 release mappings** retain their documented source
meanings. The inventory contains the individual UUIDs and source links; the
groups below account for all 33 reviewed entries.

| Source types | Entries | Interpretation retained |
| --- | ---: | --- |
| Field recordist; recording engineer, on recording and release | 4 | Explicit field work is distinct from general capture of a performance. Neither credit establishes performance or composition. |
| Balance; mix; sound; audio, on both endpoints | 8 | Preserve separate engineering disciplines; acoustic sound work differs from equipment work, and mixing differs from remixing. |
| Mastering, on both endpoints | 2 | Preserve endpoint-specific credits, including deprecated recording mastering; do not relocate them to a release. |
| Booking, on both endpoints | 2 | Studio/venue arrangements constitute a contribution without implying performance. |
| DJ mix; audio director, on both endpoints | 4 | DJ assembly and creative audio direction remain distinct from recording engineering. |
| Instrument technician, on both endpoints | 2 | Instrument preparation/tuning does not establish playing it. |
| Remixer, on both endpoints | 2 | Substantial reworking remains separate from ordinary mixing. |
| Recording misc; artists and repertoire; photography; engineer | 4 | Preserve unspecified tasks, artist development/liaison, photographs and general engineering separately. Recording photography is also deprecated in the archived source definitions. |
| Release transfer; lacquer cut | 2 | Transfer does not establish remastering; lacquer cutting does not establish other mastering work. |
| Release liner notes; booklet editor; production coordinator | 3 | Text, booklet editing and production coordination contribute to the release without establishing music authorship; liner-note translation requires its qualifier. |

The reviewed broader alignment is defensible for each group: an artist
credited in one of these roles contributes to the identified recording or
release. This uses P767's broad person-or-organization contribution meaning,
not a claim that every credit is a musical performance or that every artist
is a person. [Wikidata P767](https://www.wikidata.org/wiki/Property:P767).

Each alignment goes **from the specific predicate to P767**, with no reverse
or equivalence assertion. This preserves the subset meaning of
[`rdfs:subPropertyOf`](https://www.w3.org/TR/rdf-schema/#ch_subpropertyof).
No additional role hierarchy is introduced: generic engineering alone cannot
answer recording-engineer questions. Domain/range describe the intended RDF
endpoints; they are not a substitute for validating source field shapes.

The source pairs are artist-first. A recording/release supplies `backward`;
an artist supplies `forward`. The converter deliberately normalizes both to
recording/release → artist, rejecting unexpected directions for recognized
pilot evidence. Recording and release types with the same name have distinct
UUIDs. UUIDs, rather than current labels, select the role. A synthetic check
now exercises all 33 UUIDs from both endpoints: 66 mapped observations and
33 direct role assertions. It verifies implementation behavior, not occurrence
of all these roles in the unavailable dump.

## Observations, qualifiers and preservation boundaries

The direct triple is a useful summary of a source credit. Its named observation
retains the qualifiers and reifies the same subject/predicate/object. The
converter emits the direct triple explicitly; evidence nodes alone are not
being treated as assertions of a role.

Begin/end remain source text, including partial dates and empty strings.
`ended: false` survives; null and absent values remain distinguishable in the
JSON. Relationship dates do not establish recording, release or performance
dates. Assistant/additional/translator/instrument/medium qualifiers apply to
the credit. An assistant credit does not establish lead responsibility; a
liner-note translator does not thereby become its original author. Attribute
ID/value/credit maps retain their associations in JSON, and unrecognized
payload fields remain available for later interpretation.

The SHA-256 observation IRI identifies **source record IRI + relationship
payload**, with sorted object keys. The checks establish that:

- Identical duplicate entries on one source record coalesce. They are not
  separately countable occurrences after conversion.
- Different qualifiers or embedded target metadata create different nodes,
  even when the direct role triple is unchanged. JSON array order participates;
  object-key order does not.
- Inverse observations retain their own source/direction and have separate
  nodes, while producing the same normalized direct triple.
- Parent title/metadata, input filename, snapshot date and mapping version are
  outside the digest. Repeated snapshots may reuse an observation IRI. Keep
  snapshot and conversion provenance in graph/run manifests; do not append
  outputs from different mapping revisions and assume the IRI separates them.

The complete retained payload is the **relationship object supplied to the
converter**, including embedded target details. It is not the entire parent
record, response envelope or original JSON whitespace. Nonpilot relationships
do not get these observations. Entities missing their own ID are skipped by
the existing converter. This is bounded relationship preservation, not a
lossless archive of the MusicBrainz dump.

The earlier unresolved-evidence description was too broad. A known pilot UUID
is retained even with invalid endpoints/direction or a missing target. An
unknown/missing UUID is retained only when an endpoint-specific pilot label
identifies a candidate, including the inverse lookup. If both UUID and label
are unrecognized, ordinary nonpilot handling applies. A label never assigns a
role to an unknown UUID. One regression check now makes this boundary explicit.
Zero unresolved observations therefore does **not** prove complete coverage of
all input relationships.

Unexpected JSON shapes are another limit: the code assumes objects for
relationships and usual scalar/list field shapes. For example, the attribute
iteration expects a list, not null. This review does not claim arbitrary
malformed inputs are accepted, or that those shapes occur in the stored dump.
No speculative parser redesign was made.

## Query decision and alternatives

Use [`pilot_contributors.rq`](queries/pilot_contributors.rq), also expressed in
[CQ08](../../evaluation/queries/cq08.rq): union explicit P767 assertions in the
chosen data graph with role assertions whose predicates have a nonempty
`rdfs:subPropertyOf` path to P767 in the chosen schema graph. `DISTINCT` gives
record/artist pairs, independent of the number of roles or source observations.
The schema graph must match the conversion version and contain reviewed rules.

| Route | Correctness and provenance | Compatibility decision |
| --- | --- | --- |
| Explicit schema query | Uses only the named data/schema scopes; no extra base assertions. Qualifier-sensitive queries can join the retained observations. | **Chosen now.** Requires changing P767-only queries and configuring the matching schema graph. |
| Separate derived P767 graph | Could supply the same broad pairs if generated only from reviewed rules. Needs source-observation links, rule/configuration versions, refresh/retraction policy and distinct-pair handling. | Consider only for a concrete legacy-query or measured performance need. Old queries would still need to include the derived graph; merely creating it does not change a query pinned to the base graph. |
| Per-query inference | Could derive broader answers while retaining specific base data. Rule-set scope and answer provenance must be established in the target engine. | Optional later experiment in an isolated Virtuoso instance. Neither portability nor latency has been measured here. |

Local checks supporting the choice:

- In the archived API conversion, ordinary base-graph P767 returns zero
  contributor pairs; the scoped schema query returns the expected ten.
  All ten payloads and direct role assertions were checked, and the reproduced
  base and schema RDF match the earlier archived graphs.
- The expanded synthetic named-graph control returns five distinct broad pairs
  versus three explicit-P767 pairs. A pair with two roles and explicit P767
  appears once. Role data in an unrelated graph, and alignments in either the
  data graph or an unrelated schema graph, contribute no extra pairs.
- Exact recording-engineer queries exclude photographers, generic P767
  contributors and other role UUIDs. They make no claim to enumerate every
  engineering discipline. CQ07's intent is specifically recording engineering.
- CQ09 was also run over freshly converted synthetic observations: four input
  occurrences (one repeated payload, one changed qualifier, one inverse)
  produce three observations, one role assertion and six result rows for two
  attributes per observation. Every row retains the correct observation IRI,
  source, direction, dates and full payload. Row counts are not credit counts.

CQ08 intentionally projects away provenance; use CQ09's observation pattern
when the question depends on the credit's qualifications or source. For a
broad evidence query, bind the observation's `rdf:predicate` to the reviewed
schema path while retaining its IRI and source fields. Existing generic P767
triples need their own evidence route; this pilot cannot manufacture discarded
qualifiers for them. The evaluation queries' 25-row limits are inspection
bounds, not completeness guarantees.

No derived assertions or Virtuoso inference experiment were implemented.
The explicit route is sufficient for the reviewed questions; a future engine
comparison should be driven by a compatibility or performance requirement.

## Changes and verification

Changes are limited to this decision, model/inventory/README/handoff
documentation, four new MusicBrainz regression tests and a stronger existing
graph-scope test. Documentation now states the candidate-recognition and JSON
boundaries, observation-ID limits, qualifier-sensitive counting, and recording
photography's deprecation. Converter code, mapping definitions and query files
are unchanged.

Python 3.12.11 / RDFLib 7.6.0 verification on 20 October 2026:

```bash
poetry run python -m unittest discover -s musicbrainz/tests -v
poetry run python -m unittest discover -s evaluation/tests -v
poetry run python -m unittest discover -s rism/tests -v
poetry run python -m unittest discover -s ckg-apsearch/tests -v
poetry run python evaluation/run_queries.py --fixture --output-dir /tmp/representation-review-fixture
poetry run black --check musicbrainz/tests/test_relationship_preservation.py
git diff --check
```

Results: **48 passing tests** (16 MusicBrainz, 16 evaluation, five RISM,
11 APSearch) and **14 passing fixture queries**. RDFLib emitted deprecation
warnings about its dataset/context API; there were no test failures. Replaying
the six saved API files through `convert_relationship_sample.py --source-kind
api` produced ten mapped observations, ten role assertions, one
recording-engineer answer and ten broad contributor pairs. No source API or
production SPARQL probe was repeated; only P767/RDFS reference documentation
was consulted online.

## Deferred questions and next available task

Resume source work only when Liam confirms access to the historical snapshots.
It must establish actual field shapes and role coverage; unknown/nonpilot
relationship denominators; repeated/inverse/embedded occurrences; unresolved
evidence; source/conversion versions; and RDF expansion/runtime at scale.
Historical reconciliation and independently verified live answers also remain
pending. These synthetic/current-API results are not population-quality rates.

The next available optional task is to scope the isolated Virtuoso comparison:
read the local operations guidance and inspect an available local/test instance
before proposing exact graph IRIs, rule-set names, queries and cleanup. If no
isolated instance is available, record that limitation. Do not use the public
production endpoint as an assumed test environment or change its rules.
The explicit schema query remains the default while that comparison is pending.

Production source/schema graphs, inference settings and SESEMMI were unchanged.
During the review, no commit, push, deployment or GitHub issue update was
performed. Subsequent local commits are recorded in the handoff. Keep #470 and
#472 open: their source-based validation and deployment/evaluation criteria
remain outstanding.
