# LinkedMusic data preservation and evaluation handoff

Prepared 20 October 2026. Updated after the first implementation session and
tracked with the staged implementation commits.

Liam confirmed on 20 October 2026 that he is the sole developer and does not
require PRs for this work. Keep topic-sized commits and merge directly into
`main`. This supersedes the older PR workflow in local guidance. Publishing
commits and deploying RDF to Virtuoso remain separate actions.

## Pending deployment — Liam must update Virtuoso

**The changes are to conversion code, mappings, tests, and documentation. The
stored dataset Turtle files and production Virtuoso graphs have not been
modified.** Only small test/sample Turtle files were generated under `/tmp`.
Committing or merging this code will not update the live data.

- [ ] Make the reviewed converter/configuration revisions available on the
  machine with the Arbutus/Montreal source snapshots; record snapshot and
  conversion versions.
- [ ] **RISM:** inspect the actual stored/live data for affected identifiers,
  then regenerate RDF from the reconciled CSVs into a new output directory or
  prepare the scoped identifier migration described in
  [the RISM procedure](rism/doc/identifier_normalization.md). The small live
  sample was already canonical, so establish whether a live migration is needed.
- [ ] **MusicBrainz:** validate the pilot against the stored JSON dump and
  regenerate RDF from that source after reviewing the representation. Specific
  roles and qualifiers cannot be reconstructed from the old P767-only Turtle.
  Export the matching schema/alignment RDF separately; use
  [the documented broad-contributor query](musicbrainz/doc/queries/pilot_contributors.rq)
  when querying the newly converted data.
- [ ] Back up the current named graphs and load candidate data/schema into
  separate staging graphs in Virtuoso. Check counts, canonical-ID joins,
  engineering-versus-photography answers, direction, qualifiers, and broad
  contributor answers.
- [ ] Replace the affected production graphs only after staging checks pass;
  load the MusicBrainz schema into its own named graph and adapt queries to the
  chosen graph IRIs. Do not simply append the new MusicBrainz data to the old
  graph: that would retain the old generic assertions alongside the new model.
- [ ] Re-run the checks against production and record the deployment date,
  source snapshot, conversion revision, graph IRIs, and rollback snapshot here.

Issue closure recommendation:

- **#462:** the converter defect is fixed on local `main`. Keep the issue open until
  the fix is published and the live-data disposition is recorded (migration and
  verification, or evidence that no migration is required). Alternatively, close
  the code issue after publishing only if deployment is tracked explicitly elsewhere.
- **#450:** keep open. The MusicBrainz contributor pilot addresses one concrete
  part of the broader source-meaning and cross-collection discussion; full-dump
  validation, deployment, and broader evaluation remain.
- **#419 / #432:** keep open; this work does not settle their identity/P2888
  modeling questions. No existing GitHub issue has been closed.

## Local commit stages

The four implementation/documentation commits from `data-preservation-pilot`
were merged into local `main` by fast-forward on 20 October 2026, preserving
their separate history. The wiki has a separate commit on its `master` branch.
None of these commits has been pushed, and none deploys data to Virtuoso.

| Stage | Repository | Commit |
| --- | --- | --- |
| RISM identifier conversion, tests, audit and migration procedure | linkedmusic-datalake | `4d58cdfd` |
| MusicBrainz role preservation, inventory, tests and sample conversion | linkedmusic-datalake | `412c3d66` |
| CKG role and date interpretation | linkedmusic-datalake | `60937e27` |
| Initial handoff and pending Virtuoso deployment checklist | linkedmusic-datalake | `38f9ef18` |
| Source-preserving RDF conversion policy | linkedmusic-datalake.wiki | `49ad0ad` |

Issues #462 and #450 were both confirmed open on
20 October 2026; neither was closed or commented on during this work.
The [three follow-up issues](#follow-up-issues) below were published on
20 October 2026: MusicBrainz validation/deployment
[#470](https://github.com/DDMAL/linkedmusic-datalake/issues/470), APSearch interval
preservation [#471](https://github.com/DDMAL/linkedmusic-datalake/issues/471), and
independent graph evaluation
[#472](https://github.com/DDMAL/linkedmusic-datalake/issues/472).

## Implementation status — 20 October 2026

Completed locally, with no production writes or full-dump regeneration:

- **RISM normalization:** reproduced the failed canonical-ID join, fixed full-match item-IRI normalization, and handled P2888 predicate aliases separately. Five offline tests pass. Added a read-only identifier audit and [separate migration procedure](rism/doc/identifier_normalization.md).
- **MusicBrainz pilot:** inventoried all 33 P767 role mappings against official definitions, retained specific roles using stable source UUIDs, and added named observations for direction, dates, attributes, and full source relationship JSON. Twelve offline tests pass, including inverse direction, negative role checks, named-graph scoping, and legacy mapping behavior. The normal multiprocessing JSONL converter also completed a two-record smoke test.
- **Current API validation:** six purposively selected official example records contained 18 artist relationships, including 10 pilot relationships. All 10 pilot roles and source payloads were checked against generated RDF. This is current API evidence, not a validation of the historical imported dump. See the [inventory](musicbrainz/doc/relationship_inventory.md) and [model, query compatibility, commands, and results](musicbrainz/doc/relationship_preservation.md).
- **Policy and descriptions:** updated the sibling wiki's RDF Conversion Guidelines and clarified CKG role-unspecified links and date meanings. SESEMMI remains unchanged.

The stored dumps are in Arbutus object storage and on the Montreal machine, not
in this checkout (confirmed by Liam). Current API examples were authorized as a
bounded alternative. Raw responses, manifests/checksums, and generated RDF/audits
are local under `/tmp/linkedmusic-preservation-2026-10-20/`; preserve that directory
outside Git if the session evidence needs long-term retention.

The live RISM check found 200/200 sampled P2888 objects already canonical and no
rows in a separate noncanonical-P2888 query. No affected live triples were
established by that bounded sample. This does not invalidate the reproduced
converter bug or establish that every stored file/predicate is canonical.

Next steps:

1. Review the pilot's predicate/observation representation and broad-query route.
   Newly converted pilot data requires the schema path query (or a later reviewed
   inference/materialization option) to recover broad contributor answers.
2. Validate actual dump field shapes and quantify unresolved observations, RDF
   expansion, and conversion cost when the stored snapshot is available.
3. Continue the independent manifest, fidelity/reconciliation audit and 10–15
   competency questions below; population-level evaluation has not been run.
4. Run the optional Virtuoso reasoning comparison only after the representation
   is settled. Installed rule sets and inference settings remain uninspected.
5. Compare the eventual paper scope with the final DLfM manuscript, still pending.

This phase focuses on LinkedMusic as an integrated data resource. Preserve source meanings during conversion, repair identifier inconsistencies, and evaluate the resulting graph using source comparisons and manually verified SPARQL. The original sequence below began with RISM issue #462 and the bounded MusicBrainz pilot; the status and deployment checklist above record what is now done and what remains.

## Scope agreed with Liam

Plan for two papers with distinct contributions:

| Paper | Central contribution | Evaluation |
| --- | --- | --- |
| LinkedMusic | Integration of heterogeneous music metadata, source-preserving mappings, entity reconciliation, provenance, and cross-collection discovery. | Conversion fidelity, linking coverage and correctness, reproducibility, and verified cross-source queries. |
| SESEMMI | Natural-language access, query generation, clarification, retrieval, repair, and communication of limitations. | Independent question answering, component comparisons, cost, latency, and potentially user studies. |

Work on LinkedMusic first. Its evaluation should run without SESEMMI or paid model calls. Compare the eventual paper scope with the final DLfM manuscript to establish the new contribution; the earlier review inspected presentation slides, not the final article.

Liam explicitly excludes repairing messy source databases and reconstructing distinctions absent from the supplied data. Preserve questionable source values and document relevant limitations. Source enrichment is a separate future project.

Conversion fidelity remains in scope: if the source distinguishes two roles or supplies a date interval, LinkedMusic should preserve that evidence. A wrong link or assertion introduced by our pipeline is also our responsibility. Classify findings as source limitations, conversion loss, conversion error, or reconciliation error before proposing a repair.

## Workspace and existing evidence

Repository: `/Users/Liam/Documents/Main/School/MasterDegree/DDMAL/GitHub/linkedmusic-datalake`

Wiki: `/Users/Liam/Documents/Main/School/MasterDegree/DDMAL/GitHub/linkedmusic-datalake.wiki`

Related application: sibling `SESEMMI/`. Use its existing findings as evidence; application changes belong to the later phase.

Read root `CLAUDE.md` and the relevant subproject README. The checkout was clean on `main` at `59b44485` before this handoff was added. Use Python 3.12 and the existing Poetry environment. Respect script-specific working directories. Keep large source dumps and generated RDF outside Git.

Useful evidence:

- [RISM #462](https://github.com/DDMAL/linkedmusic-datalake/issues/462): inconsistent Wikidata URI protocols.
- [Mapping discussion #450](https://github.com/DDMAL/linkedmusic-datalake/issues/450): loss of domain-specific relationships.
- [Identity lookup #419](https://github.com/DDMAL/linkedmusic-datalake/issues/419) and [P2888 discussion #432](https://github.com/DDMAL/linkedmusic-datalake/issues/432).
- `musicbrainz/doc/relationships_reconciliation.md`, `musicbrainz/doc/rdf_conversion.md`, and `musicbrainz/src/rdf_conversion_config/relations.json`.
- `ckg-musiconn/doc/data-model.md`, `ckg-detmold/doc/data-model.md`, and `ckg-apsearch/doc/data-model.md`.
- `../SESEMMI/eval/RELIABILITY_REVIEW.md`: dated September observations and reusable audit scripts, not a population-level quality estimate.
- `../linkedmusic-datalake.wiki/RDF-Conversion-Guidelines.md`: the local update replaces the former Wikidata-only policy with source-preserving mappings and reviewed alignments; the wiki has its own repository and commit.

Earlier chats: “Assess TISMIR Readiness” on 15 October, “Rank LinkedMusic improvements” on 1 October, and “Improve SESEMMI performance” on 15–17 September. This handoff supersedes their combined-paper scope and source-cleanup suggestions.

## First task Fix RISM identifier normalization

Relevant code:

- `rism/src/convert_to_rdf.py`, especially `WIKIDATA_PATTERN`, `convert_rdf_object`, and `process_triple`.
- `rism/src/mappings/property_mapping.json`.
- `rism/doc/rdf_conversion.md` and `rism/README.md`.

The converter declares the canonical `http://www.wikidata.org/entity/` namespace. However, its regex recognizes only `http(s)://www.wikidata.org/wiki/Q…`; an HTTPS `/entity/Q…` URI passes through unchanged. Confirm this behavior on a tiny fixture, then repair it.

1. Normalize recognized Wikidata item URI variants to `http://www.wikidata.org/entity/Q…`. Support observed `wiki` and `entity` forms and assess non-www variants against real inputs.
2. Keep normalization narrowly scoped to entity IRIs. Preserve literal text, typed `xsd:anyURI` literals, unrelated hosts, source-record URLs, and malformed identifiers. Require a full identifier match; avoid broad substring replacement.
3. Check intermediate lookups and predicate mappings separately. There is a noncanonical `https://wikidata.org/prop/direct/P2888` lookup in the `P921` handling. Canonicalization must not make an existing intermediate lookup stop matching.
4. Add focused tests for URI variants, idempotence, unchanged literals and unrelated URLs, and an end-to-end conversion fixture that successfully joins the output to a canonical Wikidata identifier.
5. Inspect a bounded sample of existing RISM RDF or the live graph to establish what is affected. A converter fix does not modify already loaded triples.
6. Prepare a separate reload or scoped migration procedure with before/after checks. Keep generated data local. Production replacement is a distinct deployment action, not part of writing this handoff.

Important stash correction: `CLAUDE.md` says `stash@{0}` contains a RISM regex fix. On 20 October, its file inventory contained CKG/documentation changes and no RISM converter diff. `stash@{1}` had no tracked-file diff in the inspection. Inspect actual stash contents if needed; do not blindly apply, pop, or drop either stash.

Deliverable: one focused RISM change with tests, documentation, and a clear distinction between fixed conversion code and migrated live data.

## Second task Preserve MusicBrainz relationship meanings

Preferred policy: preserve the source relationship and add reviewed alignments where meanings fit. Broad Wikidata relationships can remain useful for general queries, provided they do not replace more specific source evidence.

Unlike CKG, the current MusicBrainz input is JSON rather than an RDF vocabulary. “Preserve the original property” therefore means preserving the relationship type and its semantics in RDF, not assuming MusicBrainz already supplies an RDF predicate that can be copied unchanged.

Current implementation details:

- There are 33 mappings to `P767`: 16 recording-to-artist and 17 release-to-artist entries. These are configuration counts, not instance counts.
- `musicbrainz/src/convert_to_rdf.py` processes `relations` around line 502.
- Around line 1116, every non-null relationship mapping is converted using `WDT[v]`. Merely inserting a full source-property URI into `relations.json` would produce the wrong URI.
- Relationships use source and target entity types, and same-type relationships also use explicit direction. Existing null entries sometimes suppress duplicate inverse representations; they are not automatically evidence of missing relationships.
- Some instrument attributes are handled, but the direct relationship path does not generally preserve relationship qualifiers. Inspect the relevant raw records before deciding the pilot representation.

Pilot scope: recording-to-artist and release-to-artist roles currently collapsed to `P767`, including engineering, mastering, mixing, photography, and remixing.

1. Inventory each pilot relationship's stable source type ID, name, definition, permitted endpoints, direction, attributes, and any dates in the available dump. Use the stable type ID where available; identical labels can name different relationships.
2. Define stable RDF predicates representing those source types. Reuse an established RDF predicate only when its meaning and direction fit. Otherwise mint documented LinkedMusic terms tied to the source relationship IDs and official definitions. Do not label locally minted terms as an official MusicBrainz ontology.
3. Preserve relationship direction explicitly. If the chosen RDF predicate means “has recording engineer,” its subject is the recording and its object is the person. The source may express the same relationship in the opposite direction.
4. Extend mapping resolution to distinguish Wikidata PIDs from full IRIs or structured mapping entries. Validate the configuration and keep existing mappings working.
5. Preserve relevant qualifiers in a documented relationship representation when direct triples cannot carry them. Use stable named relationship nodes if needed to fit repository conventions. Avoid silently discarding them or expanding this pilot into a complete MusicBrainz remodel.
6. Retain a broader Wikidata assertion only where justified. A narrower predicate can be aligned using `rdfs:subPropertyOf` only when subject/object direction and meaning agree. Never declare a specific role equivalent to generic contribution.
7. Compare small source fixtures with generated RDF and run manually checked role queries. Confirm that engineers remain distinguishable from photographers, and that broad contributor queries still have a documented route.

Deliverables: mapping inventory, bounded converter changes, representative tests, updated data-model documentation, and a reproducible sample conversion. Defer full MusicBrainz regeneration until the representation and query behavior are reviewed.

## Ontology descriptions

For each retained or introduced predicate, provide a readable label, concise definition, source-definition link, direction, endpoint types, and examples of supported and unsupported interpretations. Where an RDF schema artifact is maintained, use `rdfs:label`, `rdfs:comment`, and source references alongside the machine-readable mappings.

Document CKG's generic related-person links as role-unspecified. Do not reinterpret them as composer or performer. Distinguish archive creation dates, work creation dates, and performance dates.

Ontology comments should explain distinctions preserved in the data. A comment cannot recover a role already collapsed to `P767`, and comments are not inference rules.

The later SESEMMI task must explicitly ingest the relevant schema descriptions. Adding `rdfs:comment` triples to Virtuoso alone does not guarantee they reach an LLM. Keep canonical LinkedMusic documentation independent of prompts, and record the later synchronization requirement without changing SESEMMI now.

## Third task Evaluate LinkedMusic independently

Start with a bounded pilot and expand sampling only as needed to support the paper's claims.

| Dimension | Method and output |
| --- | --- |
| Source coverage | A per-dataset manifest: source snapshot/date, entity counts, graph IRI, conversion version, licence references, selected field availability, and known exclusions. Date all counts. |
| Conversion fidelity | Trace selected roles, links, dates, and identifiers from source to RDF. Report preserved, deliberately generalized, omitted, and incorrectly transformed information with explicit denominators. |
| Reconciliation | Review an initial 50–100 links across selected sources, entity types, and matching methods. Include unlinked records to investigate missed opportunities. Distinguish identifier agreement from verified identity. |
| Cross-source usefulness | Define 10–15 competency questions with manually written SPARQL and independently checked expected answers or explicit reasons the imported data cannot answer them. Include both direct-QID and local-node/P2888 paths. |
| Repeatability | Record source checksums, conversion/configuration revisions, query text, result snapshots, and relevant external responses. |

Use probability-based sampling within stated strata if estimating error rates; report uncertainty and scope. Keep purposively selected problem examples separate. Do not claim population recall from a sample containing only accepted links, or claim an unmatched item is absent from Wikidata because one lookup failed.

Select two or three useful cross-collection tasks, such as jazz recordings across Weimar and MusicBrainz, and a source-supported person/source lookup across historical collections. Include a negative role test proving that generic CKG associations do not establish composition. Avoid choosing every case solely because it already succeeds.

Preserve and flag source anomalies without guessing corrections. The APSearch year `9009` is a source-tracing case; investigate where it first appears, then classify it. By contrast, dropping the end years of the 128 APSearch intervals is documented conversion loss and belongs in our fidelity backlog. The suspicious Detmold Person/opera cases likewise require tracing before attributing responsibility.

No universal source-database cleanup, new ingestion campaign, or new NLQ benchmark is required for this phase.

## Fourth task Test targeted Virtuoso reasoning

Recommendation: run a bounded experiment after the relationship representation is settled. Reasoning is useful when explicit, justified rules make preserved data easier to query.

First establish the installed Virtuoso version, currently registered rule sets, and endpoint settings. Current reasoning configuration was not inspected in this handoff.

The first experiment should use a small named rule set containing reviewed `rdfs:subPropertyOf` relationships, with optional well-justified class hierarchies. Virtuoso supports named inference contexts enabled by `DEFINE input:inference` or for individual query patterns.

Illustrative rule, using placeholder terms:

```turtle
@prefix ex: <https://example.org/linkedmusic-pilot/> .
@prefix wdt: <http://www.wikidata.org/prop/direct/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

ex:recording ex:hasRecordingEngineer ex:person .
ex:hasRecordingEngineer rdfs:subPropertyOf wdt:P767 .
```

Given that reviewed alignment, a contributor query can retrieve the engineer while an engineering query remains specific. The rule does not imply that every contributor is an engineer.

Compare three routes on the same fixture:

1. Explicit SPARQL over the source-specific predicates, without reasoning.
2. Per-query inference using the reviewed rule set.
3. Explicitly generated broader assertions, with derivation/version provenance, if compatibility or performance warrants comparison.

Check expected answers, unintended additional answers, duplicate counts, graph scoping, source provenance, query simplicity, and repeat-run latency. Include inverse-direction and negative tests. Keep base graphs distinct from schema/alignment graphs and any materialized derived data.

Treat identity reasoning as a separate decision. Do not automatically reinterpret every `wdt:P2888` link as `owl:sameAs`, declare P2888 transitive, or enable inverse-functional identity rules across all identifiers. `owl:sameAs` asserts identity; reconciliation mistakes or record-versus-entity confusion can then propagate statements across resources. Existing issue #419 contains a broad sameAs proposal that needs this review.

Likewise, neither comments nor ordinary Wikidata `P279`/`P1647` triples automatically become RDFS rules just because reasoning is enabled. Use explicit, reviewed alignments supported by the installed engine.

Deliverable: a small reproducible reasoning experiment and a recommendation based on correctness, provenance, and measured cost. Global production reasoning is not the first implementation step.

Primary references:

- [Virtuoso inference overview](https://docs.openlinksw.com/virtuoso/rdfsparqlrule/)
- [Virtuoso subclasses and subproperties](https://docs.openlinksw.com/virtuoso/rdfsparqlrulesubclassandsubprop/)
- [Enabling inference per query or pattern](https://docs.openlinksw.com/virtuoso/rdfsparqlruleenableinfr/)
- [RDF Schema subproperties](https://www.w3.org/TR/rdf-schema/#ch_subpropertyof)
- [OWL identity semantics](https://www.w3.org/TR/owl-ref/#sameAs-def)
- [MusicBrainz relationship schema](https://musicbrainz.org/doc/MusicBrainz_Database/Schema)
- [MusicBrainz API relationship attributes](https://musicbrainz.org/doc/MusicBrainz_API)

## Suggested implementation sequence

1. RISM normalization and focused regression tests.
2. MusicBrainz pilot mapping design and source-preserving conversion.
3. Consistent ontology policy and descriptions, including the outdated wiki guidance.
4. LinkedMusic data manifest, fidelity/link audit, and competency-query pilot.
5. Optional reasoning experiment, followed by a deployment recommendation.

Use one reviewable change per topic. Write the resource description and evaluation protocol alongside this work; results and conclusions follow the measurements. Keep small synthetic test fixtures in source control where appropriate, and generated audit reports/data outside it.

The RISM fixture/fix and MusicBrainz pilot are now implemented as described in the
status section above. The remaining roadmap starts with representation review
and stored-snapshot validation; do not repeat the completed conversion work.

## Follow-up issues

Drafted and published 20 October 2026 at Liam's request. The initial scopes and
acceptance criteria are retained below; use the linked GitHub issues for ongoing
tracking. The MusicBrainz and APSearch issues explicitly note that the associated
implementation/documentation commits remain local and Virtuoso is unchanged.
RISM deployment continues under existing issue #462, so no duplicate RISM issue
was created. Suggested work order: start the APSearch repair with offline
fixtures; prepare the evaluation protocol next; validate and deploy MusicBrainz
once its stored snapshot is available. Code changes can go directly to `main`;
the deployment checklist remains separate.

### [#470](https://github.com/DDMAL/linkedmusic-datalake/issues/470) — Validate and deploy the MusicBrainz relationship-preservation pilot

Labels: `musicbrainz`, `virtuoso`

Related: [#450](https://github.com/DDMAL/linkedmusic-datalake/issues/450),
[#401](https://github.com/DDMAL/linkedmusic-datalake/issues/401);
implementation commit `412c3d66`.

#### Problem

The converter now preserves 33 recording/release-to-artist relationship types
that previously collapsed to P767. It emits specific predicates and named
observations retaining source direction, dates, attributes, and relationship
JSON. The implementation has passed 12 offline tests and preserved all 10 pilot
relationships in six current API example records.

Those checks do not validate the historical dump or update the live graph.
Newly converted data also requires the documented schema route for broad
contributor queries. The stored source snapshots are in Arbutus object storage
and on the Montreal machine.

#### Work and acceptance criteria

- [ ] Identify the input snapshot, timestamp, checksums, licence references, and
  converter/configuration revision.
- [ ] Inspect a bounded sample spanning available pilot type IDs, recording and
  release records, recordings embedded in releases, and inverse artist records.
  Report which of the 33 mappings are exercised and which remain unobserved.
- [ ] Compare source relationships with generated RDF. Report input occurrences,
  distinct observations/assertions, unresolved mappings, and duplicate collapse
  with explicit denominators. Preserve and flag missing IDs or unexpected
  directions rather than guessing roles.
- [ ] Measure conversion time and RDF size on a fixed sample, including the
  overhead of observation nodes and retained JSON.
- [ ] Generate base RDF and its matching schema separately. In staging, verify
  exact-role queries, the broader P767 query route, relationship dates and
  attributes, source direction, and graph scoping. Include negative checks:
  photography does not imply engineering, and generic contribution does not
  imply a specific role.
- [ ] Back up the existing MusicBrainz graph, regenerate from the source JSON,
  and replace the affected data in Virtuoso after staging checks pass. Load the
  schema into a separate named graph; do not append the new model to old data.
- [ ] Repeat the queries against production and record graph IRIs, deployment
  date, source/conversion versions, results, and the rollback snapshot.

This issue is complete only when the validated representation is deployed and
the results are recorded. If deployment must be split out, create an explicit
linked follow-up before closing it. Do not infer population accuracy from the
purposive sample or reconstruct missing source roles. Global inference and
SESEMMI changes are outside this issue.

Implementation/model:
[relationship preservation](https://github.com/DDMAL/linkedmusic-datalake/blob/main/musicbrainz/doc/relationship_preservation.md).
Source type definitions:
[mapping inventory](https://github.com/DDMAL/linkedmusic-datalake/blob/main/musicbrainz/doc/relationship_inventory.md).

### [#471](https://github.com/DDMAL/linkedmusic-datalake/issues/471) — Preserve both endpoints of APSearch creation intervals

Label: `bug`

Related: [#450](https://github.com/DDMAL/linkedmusic-datalake/issues/450).

#### Problem

The APSearch branch of `coerce_date` converts every creation interval to the
start year. For example, `1909-01-01/1950-01-01` becomes only
`"1909"^^xsd:gYear`; the supplied end year is lost.

The documented `apsearch.ttl` snapshot contains 4,214 creation intervals,
including 128 spanning multiple years. These are existing snapshot observations,
not freshly measured production counts. Dropping their endpoints is conversion
loss. The Jan-01 placeholders also do not justify asserting precise calendar
days.

#### Work and acceptance criteria

- [ ] Document an RDF representation that preserves both year bounds and the
  original interval evidence, explicitly as a source creation period. Do not
  reinterpret it as a performance or field-recording date.
- [ ] Implement the APSearch conversion change. If the current P571 start-year
  assertion remains for compatibility, document it as a projection of the
  preserved period and provide a query for the complete interval.
- [ ] Add source-to-RDF fixtures covering single-year and multi-year intervals,
  unknown precision, and malformed or reversed values. Preserve and flag
  questionable source values; do not guess corrections or repair `9009`.
- [ ] Verify that the three intentionally shared CKG converter copies stay
  consistent and that musiconn and Detmold date behavior is unchanged.
- [ ] Run an overlap query against a fixture: an interval from 1909 through
  1950 should match a query for coverage during 1940 and should not match 1960.
- [ ] When the stored dump is available, report the number of source intervals,
  preserved bounds, and unresolved values with a dated denominator. Keep this
  measurement separate from the historical count of 128.
- [ ] Update the data-model documentation and regeneration/reload instructions.
  Record whether Virtuoso has been updated; if deployment remains pending,
  retain it explicitly in the deployment checklist or a linked follow-up.

The converter and offline query checks can be developed before the full dump
is available. Production migration is a separate operation. This issue does
not add information absent from the supplied data or redesign every CKG date.

Evidence:
[APSearch date model](https://github.com/DDMAL/linkedmusic-datalake/blob/main/ckg-apsearch/doc/data-model.md#4-dates--all-placeholder-gyear).
Implementation:
[`coerce_date`](https://github.com/DDMAL/linkedmusic-datalake/blob/main/ckg-apsearch/src/convert_to_rdf.py).

### [#472](https://github.com/DDMAL/linkedmusic-datalake/issues/472) — Build an independent LinkedMusic graph evaluation pilot

Label: `enhancement`

Related: [#450](https://github.com/DDMAL/linkedmusic-datalake/issues/450),
[#419](https://github.com/DDMAL/linkedmusic-datalake/issues/419),
[#432](https://github.com/DDMAL/linkedmusic-datalake/issues/432).

#### Problem

Converter tests and successful queries demonstrate bounded behavior, but they
do not establish the integrated graph's source fidelity, reconciliation quality,
or usefulness across collections. LinkedMusic needs reproducible evaluation
that runs independently of SESEMMI and paid model calls.

Start with two or three cross-collection tasks and a bounded set of sources.
Keep the evaluation protocol separate from measured results and paper claims.

#### Work and acceptance criteria

- [ ] Create a per-dataset manifest recording source snapshot/date and checksum
  when available, graph IRI, conversion/configuration revision, dated counts,
  licence references, selected field availability, and known exclusions. Mark
  unknown provenance explicitly rather than substituting an API retrieval date
  for the historical source snapshot.
- [ ] Trace selected roles, identifiers, links, and date intervals from source
  to RDF. Report preserved, deliberately generalized, omitted, and incorrectly
  transformed information with explicit denominators. Classify each finding as
  a source limitation, conversion loss, conversion error, or reconciliation
  error.
- [ ] Define and execute 10–15 competency questions using manually written
  SPARQL. Record source-backed expected answers or why the imported data cannot
  answer a question. Include direct-QID and local-node/P2888 paths, a meaningful
  cross-source join, and a negative test showing that a generic CKG related-person
  link does not establish composition.
- [ ] Review an initial 50–100 reconciliation cases across stated source,
  entity-type, and matching-method strata, including unlinked records. Use
  probability-based selection when estimating rates and keep purposively
  selected problem cases separate. Report identifier agreement separately from
  verified identity; do not estimate population recall from accepted links alone.
- [ ] Provide a reusable query/audit runner with query text, dated result
  snapshots, relevant external responses, and code/configuration hashes.
  Preserve timeout, partial-result, and endpoint-error status; a failed lookup
  is not proof that an entity or fact is absent.
- [ ] Produce a bounded findings report containing denominators, sampling
  limits, uncertainty where appropriate, unsupported questions, and the
  concrete conversion/reconciliation follow-ups supported by the evidence.

Protocol design and current-API/live-graph probes can begin now. Historical
source fidelity measurements require the corresponding stored snapshots.
Do not silently mix current API evidence with the imported snapshot.

Out of scope: a new NLQ benchmark, paid model calls, user studies, source-database
cleanup, new ingestion campaigns, and global identity inference. Review the
final DLfM manuscript before presenting this pilot as a new paper contribution.
