# LinkedMusic data preservation and evaluation handoff

Prepared 20 October 2026. Updated after the first implementation session and
tracked with the staged implementation commits.

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

- **#462:** the converter defect is fixed locally. Keep the issue open until
  the fix is merged and the live-data disposition is recorded (migration and
  verification, or evidence that no migration is required). Alternatively, close
  the code issue after merge only if deployment is tracked explicitly elsewhere.
- **#450:** keep open. The MusicBrainz contributor pilot addresses one concrete
  part of the broader source-meaning and cross-collection discussion; full-dump
  validation, deployment, and broader evaluation remain.
- **#419 / #432:** keep open; this work does not settle their identity/P2888
  modeling questions. No GitHub issue status has been changed.

## Local commit stages

Implementation commits are on branch `data-preservation-pilot`; the wiki has a
separate commit on its `master` branch. None of these commits has been pushed,
and none deploys data to Virtuoso.

| Stage | Repository | Commit |
| --- | --- | --- |
| RISM identifier conversion, tests, audit and migration procedure | linkedmusic-datalake | `4d58cdfd` |
| MusicBrainz role preservation, inventory, tests and sample conversion | linkedmusic-datalake | `412c3d66` |
| CKG role and date interpretation | linkedmusic-datalake | `60937e27` |
| Source-preserving RDF conversion policy | linkedmusic-datalake.wiki | `49ad0ad` |

The handoff and deployment checklist are committed as a final documentation
stage after these changes. Issues #462 and #450 were both confirmed open on
20 October 2026; neither was closed or commented on during this work.

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
