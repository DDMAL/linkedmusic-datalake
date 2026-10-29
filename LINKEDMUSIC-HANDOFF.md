# LinkedMusic data preservation and evaluation handoff

Prepared 20 October 2026. Updated **29 October 2026** after reconciling the
repository documentation and sibling wiki with the completed preservation work,
most recently DIAMM archive name/siglum text preservation. The
[root status and contract index](README.md#preservation-and-evaluation-status)
provides a shorter entry point. This handoff retains the dated task evidence;
historical test counts are not the current baseline.

Local validation remains **117 tests and 14 competency fixture queries**, rerun
on 29 October. At Liam's subsequent request, the later repairs and documentation
were committed and pushed to draft PR #473, and the wiki updates were published.
The PR remains open, draft and unmerged. Publishing code does not deploy RDF.
Publication statements in the dated task sections describe the status at those
tasks; the 29 October publication section below supersedes earlier local-only
status. Historical validation results retain their original scope.

## Working agreement — update the handoff after every task

Liam explicitly requested this on 26 October 2026. Before reporting a task
finished, update this handoff with the changes, validation actually performed,
review findings and their disposition, relevant commits, publication/deployment
status, remaining limitations and the next concrete task. Keep historical test
results distinct from the current baseline. Updating the handoff is part of
finishing the work.

## Completed task — documentation reconciliation

Completed 29 October 2026 against datalake code through `319cdcb7` and the
sibling wiki based on `49ad0ad`. The repository README now indexes every
preservation contract and states the validation/publication/deployment boundary.
Contributor notes describe the actual SIMSSA Turtle route, MusicBrainz auxiliary
lookups, DIAMM contracts, CKG intervals and the common offline command.

Shared conversion and property-mapping guides now reflect whole-ID handling,
literal/local-prefix precedence, existing CSV missing-value limits and
definition-based source preservation. The identifier review includes the later
DIAMM repairs; old test counts are dated. MusicBrainz runtime/path guidance and
obsolete external-ID sections were corrected, broken local links repaired, and
evidence references point to the retained ignored audit copies as well as their
original temporary locations. Historical findings keep their measured results.

The sibling wiki has a new **Preservation and Evaluation** entry point linked
from Home, Project Status and the sidebar. CKG interval/role/date descriptions,
reconciliation policy, source-preserving query guidance, ingestion and loading
steps are synchronized. Ontology diagrams and counts are explicitly historical
pending validated deployment. Unresolved authority lookups no longer claim
proven absence from Wikidata or independently verified identity. The ignored
`CLAUDE.local.md` mirror was synchronized, and the two older local CKG working
documents were marked historical rather than treated as current instructions.

Validation: `poetry run python scripts/check_offline.py` passed **117 tests and
14 competency fixture queries** (shared 14, RISM 5, MusicBrainz 31, DIAMM 34,
APSearch 11, evaluation 22). This was a documentation-only refresh; no converter,
mapping, fixture or source data changed. The documentation check covered 77
repository Markdown files and 32 wiki pages: 655 local/repository links,
anchors and wiki-navigation references passed after repairing stale targets.
Four wiki SPARQL examples parsed with RDFLib without remote execution.
Diff whitespace checks passed in both repositories. Self-review also corrected
the wiki's claim that the CKG converter stops on unknown predicates: the code
reports and drops them, so output review must inspect those omissions. musiconn
residue claims and historical MusicBrainz coverage/qualifier notes were aligned
with the documented evidence limits. The PR metadata check confirmed that
draft PR #473 still has 20 commits through `0b508a76`; its prior hosted CI
result does not validate later repairs.

No independent agent review, OpenRefine replay, snapshot inspection, new source
API retrieval or production SPARQL probe was performed. At completion of this
documentation task, changes were uncommitted in both repositories, with three
local context files ignored. The subsequent authorized publication is recorded
below; no merge, issue update, data regeneration or deployment occurred.
The next bounded implementation task remains **DIAMM geographic names** below;
historical validation and deployment still await confirmed snapshot access.

## Publication status — 29 October 2026

Liam explicitly authorized committing and pushing after the documentation
review. Remote heads matched the recorded publication state, so normal
fast-forward pushes were used; no force push or branch-protection change was
needed.

- Datalake documentation commit `de1b8379` (`docs: synchronize preservation and
  evaluation guidance`) updates 31 Markdown files. Pushing
  `preservation-repairs-2026-10-21` also publishes the 19 already-committed
  DIAMM/SIMSSA/MusicBrainz repair and handoff commits after `0b508a76`.
  GitHub confirmed draft PR #473 at `de1b8379` with 40 commits, open and unmerged.
- Wiki documentation commit `5575645` (`docs: synchronize preservation models
  and evaluation guidance`) updates 16 files, including the new preservation
  overview. The push to wiki `master` also publishes the earlier policy commit
  `49ad0ad`; the remote advanced from `295e751` to `5575645`.
- Follow-up documentation commits record publication in this handoff, the
  repository overview/contributor notes, identifier review and wiki status pages.
  The three ignored local context files remain outside Git.

The earlier same-day validation remains **117 tests and 14 competency fixture
queries**. The 655-link documentation check and diff checks passed again before
the first commits. Only documentation changed after that test run.
[Hosted offline run 40862669774](https://github.com/DDMAL/linkedmusic-datalake/actions/runs/40862669774)
completed successfully for `de1b8379`. This verifies the published documentation
and repair revision; CI on subsequent status commits is recorded separately by
GitHub. The PR description was synchronized with the published repair scope and
validation. The 655-link and diff checks also passed after the status updates.
No snapshot validation, RDF regeneration, merge or deployment was performed.
The next bounded implementation task remains DIAMM geographic names.

## Completed task — MusicBrainz URL recognition

Completed 21 October 2026 in local commit `5d5e18ae`. The
[URL contract](musicbrainz/doc/url_recognition.md) records the input boundary,
evidence, test scope and deferred validation. Complete HTTP/HTTPS Wikidata item
URLs on `www.wikidata.org` or `wikidata.org`, using `/wiki/` or `/entity/`, now
normalize to canonical HTTP entity IRIs. Full matching requires positive ASCII
QID digits without leading zeros. Malformed URLs and unrelated values remain
original literals. MusicBrainz source nodes, ordinary name literals, multiple
supplied matches and the existing URL-to-P2888 policy are preserved.

Four new tests use the actual entity converter and tracked mappings. They cover
all eight URL variants, idempotence, malformed/external values, name literals,
multiple targets, exact triples, a Turtle round trip and a canonical-QID SPARQL
join. They reported 13 failing subtests before the repair and now pass.
`poetry run python scripts/check_offline.py` passes **69 tests and 14 competency
fixture queries**; Black and diff checks pass. No historical inputs or production
graphs were inspected or changed, and nothing was pushed or deployed.

## Completed task — DIAMM identifier validation

Completed locally in `db00b71d` on 21 October 2026, after publication of the
prior work described below. The [DIAMM contract](diamm/doc/identifier_validation.md)
records the export evidence, strict bare-QID boundary and remaining limits.
The helper rejects partial/ambiguous IDs and returns false for missing or
non-string values. Original names remain labels, and unmatched field values
use the original genre/type text. Full URLs remain outside this export contract.

The converter is now safe to import: explicit `build_rdf_graph` reads inputs,
and guarded `main()` retains the existing script paths and writes Turtle.
Five tests cover all nine CSV layouts and all ten helper call sites, negative
ID controls, names and source relationships, exact triples, a Turtle round trip,
safe imports and the real script entry point. The common offline command now
includes DIAMM and passes **74 tests and 14 competency fixture queries**. Black
and diff checks pass. No historical CSVs or production graphs were touched.

At that repair, the separate people earliest/latest year-ID branches remained
uncovered. They were repaired on 26 October as recorded below. Neither change
establishes complete DIAMM source fidelity.

## Publication status — 21 October 2026

At Liam's request, all 20 existing datalake commits through `0b508a76` were
pushed to `origin/preservation-repairs-2026-10-21`. A direct `main` push was
rejected by GitHub's protected-branch rule requiring a pull request.
[Draft PR #473](https://github.com/DDMAL/linkedmusic-datalake/pull/473) publishes
that history for review; it has not been merged and remote `main` is unchanged.
The connector lacked PR-creation permission, so the local GitHub CLI created it.
The [hosted offline CI run](https://github.com/DDMAL/linkedmusic-datalake/actions/runs/39602976457)
passed for the published head (69 tests and 14 fixture queries); CodeRabbit
was still pending when checked. This does not cover the later DIAMM commit.
No branch protection was changed. The subsequent DIAMM and SIMSSA commits and updated handoffs
remain local, outside that PR. The sibling wiki was not pushed. Nothing was
deployed, and issues remain open.

## Completed task — SIMSSA P2888 literal handling

Completed locally in `ea716132` on 21 October 2026. The
[person mapping contract](simssa/doc/person_identifier_mapping.md) records the
history evidence, required export settings and limitations. Person P2888 now
requires a canonical Wikidata item IRI; arbitrary URLs, property IDs, malformed
item URLs and unmatched text do not create exact-match links. Original names
are explicit `xsd:string` labels, including whole QIDs and URLs. Local subjects
and work author/composer links are preserved. No shared-converter changes were
needed; work-title mappings and the JSON-LD route remain unchanged.

Three synthetic CSV tests use the actual person/work mappings and independently
specified expected triples, including all ten accepted ID/URL forms, negative
controls, blanks, original-name text and Turtle round trips. All three failed
against the old mapping and now pass. The common offline command passes
**77 tests and 14 competency fixture queries**; all nine configs validate.
Black and diff checks pass.

There is no checked-in SIMSSA export template. The history copies original
names without facets; actual historical export fidelity remains unverified.
Named records must retain their original-name cell: this mapping does not
reconstruct missing original text from reconciliation values. Snapshot work,
affected counts and production regeneration remain deferred. This commit is
local, outside draft PR #473, and has not been pushed or deployed.

## Completed task — MusicBrainz auxiliary CSV identifier validation

Completed locally in `fe196861` on 26 October 2026 on
`preservation-repairs-2026-10-21`.
The [auxiliary identifier contract](musicbrainz/doc/auxiliary_identifier_validation.md)
records the review of all 14 export/history pairs. Only complete bare QIDs with
positive ASCII digits and no leading zero qualify. Full URLs, suffixes,
ambiguous values and missing/non-string cells do not create item IRIs.

All six helper call sites handle missing candidates without crashing. Missing
type mappings now retain the original type, including primary/secondary types.
Unmatched language exports keep their full-name literal; blank or non-string
language matches fall back to the original source code. Other auxiliary fields
retain their original JSON text. Source nodes, entity links, URL recognition
and role mappings are preserved.

Seven new tests use the production converter and tracked mappings, including
all 14 export layouts parsed with pandas, independently specified triples and
Turtle round trips. The cases reproduced failures before the fix and now pass.
The common offline command passes **84 tests and 14 competency fixture queries**;
Black and diff checks pass. No snapshots were read or regenerated. This work
has local validation only; no push, merge or deployment was performed for it.

## Completed task — MusicBrainz CSV loading and lookup isolation

Completed locally in `60ebf3b9` on 26 October 2026 following Claude's review of
`fe196861`/`1a089373`. The review found no introduced defects, but identified
two older loader problems; both were reproduced before this follow-up.
The [updated contract](musicbrainz/doc/auxiliary_identifier_validation.md)
records the evidence, internal mapping format and remaining limits.

All auxiliary/type CSVs now preserve text with `dtype=str` and
`keep_default_na=False`: `nan`, `None`, `NA`, `null` and numeric-looking strings
remain available as lookup keys and candidate text. Empty candidates retain
source fallbacks; empty lookup keys are ignored. Each of the five auxiliary
fields has its own dictionary, and type matches are scoped by entity kind.
Missing tables cannot borrow another field's match for a label such as `Other`.

Four new tests exercise real CSV loaders and per-file `main`, missing tables,
and the complete asynchronous CLI with worker processes and Turtle output.
The CLI regression reproduced cross-field QIDs and lost text keys against the
old code, then passed after the fix. The original 14-layout test now uses the
production loader and includes packaging `None` in CSV input.
The common offline command passes **88 tests and 14 competency fixture queries**;
Black and diff checks pass. All new input files are synthetic and temporary.
Claude's follow-up static review found no actionable bugs in either fix or its
CLI/worker wiring. Its documentation suggestion about recursive lookups was
addressed in the RDF conversion guide; the reviewer did not rerun tests.
Historical affected counts, snapshot validation and deployment remain deferred.
This follow-up has not been pushed or deployed.

## Completed task — DIAMM person years and approximation

Completed 26 October 2026 in local commit `fe53b415` on
`preservation-repairs-2026-10-21`. The
[person-year contract](diamm/doc/person_years.md) records the upstream model
evidence pinned to `diamm/diamm` revision
`052004f86960a5dc4d1e7446be8d5a6ac8594bd1`, the tracked export/history boundary,
RDF vocabulary, query compatibility and regeneration procedure. The upstream
model distinguishes lifespan years from a separate floruit field, supporting
retention of the birth/death interpretation. No historical API snapshot was read.

Both year-ID branches now use complete bare-QID validation. The six related CSV
cells preserve text during parsing. Each source year, ID and approximation flag
stays together in a deterministic observation, including rejected/missing cells.
Supported years use `xsd:gYear`; direct P569/P570 triples require an explicit
false approximation flag. Approximate/unknown values remain queryable evidence.
Year IDs never replace source year values, and conflicting rows retain their
own qualifiers. Date objects therefore change from year-item IRIs to literals;
validated year-item links are on observations. Existing queries must account
for this change. Names and source relationships retain their existing behavior.

Seven new tests failed against the old converter (65 failed assertions/subtests)
and now pass, alongside the five existing DIAMM tests. They exercise actual CSV
loading and CLI output, independently specified triples, raw text, both year
fields, malformed/ambiguous IDs, missing/invalid flags, exact/approximate values,
stable observation identity, duplicate/conflicting rows, Turtle and SPARQL.
`poetry run python scripts/check_offline.py` passes **95 tests and 14 competency
fixture queries**. Black and diff checks pass. Claude's read-only review found
no converter correctness defects and did not independently rerun tests. Its
stale-handoff finding was addressed by the concurrent handoff update. Optional
short-year Turtle and near-miss year controls were added within the seven tests;
the contract now notes datatype-sensitive literal matching, cross-graph date
comparison and unmeasured observation volume. Its pre-existing extraction and
other-column parsing findings remain outside this repair, as documented below.
All 12 DIAMM tests passed again after the review additions.

No stored data was regenerated, no production graph changed, and this repair
has not been pushed or deployed. Historical affected counts, real export shapes
and source-version confirmation still await snapshot access. QID syntax alone
does not verify that a reconciliation is correct. Other CSV columns retain
their existing pandas behavior at that stage. Original-name/floruit preservation
was addressed in the subsequent task below.

## Completed task — DIAMM original person names and floruit text

Completed 26 October 2026 in local commit `becc8734` on
`preservation-repairs-2026-10-21`. The
[preservation contract](diamm/doc/person_name_preservation.md) records the pinned
upstream model/serializer, input boundary, RDF properties, query example and
compatibility limits. The reviewed detail serializer exposes floruit through
`full_name`, with no separate floruit field. This explains why removing the
parenthesized suffix discarded source information.

Extraction now retains the exact original `source_full_name` alongside the
existing cleaned `full_name`, plus optional separate source `floruit` text when
supplied. Both columns are appended to the tracked export and left untouched
by the existing history. Import instructions require text preservation.
The RDF loader protects all three name/text columns from pandas type inference;
nonempty original values become `diamm:sourceFullName`/`diamm:floruit` strings.
Floruit within a display name remains in that full string; no independent
field, date bounds or birth/death statements are inferred from it. Legacy
exports without the new fields still load, without claiming to recover lost
text. Source nodes, cleaned labels and relationships retain their roles.

Four tests reproduced seven failed assertions/subtests before the change and
now pass. They run the actual extraction and RDF CLIs around a synthetic export
projection using the tracked columns; expected full graphs and text-query
results are independently specified. Cases cover suffixes, ordinary parentheses,
NA-like/numeric text, optional missing/null cells, Unicode/quotes/newlines,
legacy exports and composition/copyist/owner relationships. The complete offline
command passes **99 tests and 14 competency fixture queries**; Black and diff
checks pass. Claude's read-only review found no introduced correctness defects;
it did not rerun tests or independently fetch the upstream evidence. Its three
optional suggestions were addressed: test/document an empty cleaned name,
guard against future history removal/reordering, and explain project-wide
import trimming. These strengthen the same four tests; all 16 DIAMM tests
passed again after those additions.

No OpenRefine GUI/service replay or historical snapshot validation was performed.
No source data was regenerated or deployed, and this work has not been pushed.
Old outputs still need their matching raw snapshots to recover lost text.
Other source fields and external-ID parsing remain outside this repair.

## Completed task — DIAMM RISM/VIAF identifier text

Completed 27 October 2026 in local commit `406c868e` on
`preservation-repairs-2026-10-21`. The
[external identifier contract](diamm/doc/external_identifier_text.md) traces the
three columns through extraction, the tracked export/history pairs and RDF.
Pinned upstream archive/person models and serializers at
`052004f86960a5dc4d1e7446be8d5a6ac8594bd1` define string identifiers. No historical
snapshot or live DIAMM API was inspected.

Archive `rism_id` and person `rism_id`/`viaf_id` now load as text. Nonempty cells
remain literals under P5504/P214; empty cells emit no identifier statement.
Leading zeros, long digits, NA-like strings, punctuation and whitespace survive.
ID-like strings and URLs do not create matches. Local subjects, labels, supplied
name matches and source relationships retain their existing behavior. Previously
numeric RDF objects now become strings; already-coerced exports need their
matching source evidence for recovery. Reconciliation instructions now explicitly
require text-preserving import for all three columns.

Five new tests reported six failures, including subtests, against the old
converter: zeros were stripped, `9007199254740993` rounded to
`9007199254740992.0`, and NA-like strings disappeared. All pass after the repair.
They cover actual CSV parsing, extraction/RDF CLIs, tracked export selection,
full expected graphs, Turtle round trips, an exact-string SPARQL query,
duplicate/conflicting rows, blanks/nulls and source relationships. The complete
offline command passes **104 tests and 14 competency fixture queries**, including
all 21 DIAMM tests. Black and diff checks pass.

Self-review found no introduced correctness defects. It identified the existing
one-value extraction boundary: archives choose the first RISM-labelled entry,
while people choose the last RISM/VIAF-labelled entries. That was addressed by
the subsequent list-preservation repair below; this earlier repair claims
preservation only of selected cells. No independent agent review or OpenRefine GUI/service replay
was performed. All test data is synthetic. Other CSV columns retain their prior
parsing. Historical affected counts, actual source shapes and source-version
confirmation await snapshot access. No stored data was regenerated, and this
repair has not been pushed or deployed.

## Completed task — DIAMM external identifier selection

Completed 27 October 2026 in local commit `ae26d383` on
`preservation-repairs-2026-10-21`. The
[identifier-list contract](diamm/doc/external_identifier_selection.md) records
the pinned upstream models/serializers and label definitions, representation,
reconciliation behavior, legacy compatibility, query examples and regeneration
procedure. The upstream serializers return all identifier rows without defining
a preferred entry. Synthetic records reproduce loss from first/last selection,
blank entries hiding values and substring label classification.

Archive/person extraction now appends `source_identifiers`, retaining the complete
parsed JSON list, including duplicate entries, order, labels, URLs and unexpected
values. Full `RISM Online`/`VIAF` labels are recognized case-insensitively. Scalar
RISM/VIAF columns contain a hint only for one distinct nonblank supplied string;
different values leave the hint empty. Existing histories retain their name
reconciliation operations; updated export templates carry the JSON unchanged.
Matching results can change where the old arbitrary hint is no longer supplied.

RDF retains the JSON as `diamm:sourceIdentifiersJson` and projects every supported
nonempty string under archive/person P5504 and person P214. The list takes
precedence over scalar hints, including explicit empty/null lists. Missing/empty
evidence cells retain the legacy scalar route. Invalid JSON or an unexpected
top-level value stops conversion with the subject identified; unexpected list
entries remain evidence without invented assertions. Other schemes survive only
inside JSON. No new exact-match links or authority URLs are inferred. Local
subjects, labels, supplied name matches and source relationships retain their roles.

Seven new tests reproduced 11 failures (including subtests) before implementation
and now pass. They exercise actual extraction/export projection/RDF CLIs, full
expected graphs, Turtle and SPARQL, repeated/conflicting values, blanks/nulls,
label near misses, unexpected entry shapes, text fidelity, legacy CSVs, malformed
JSON and stale hints. Existing name/text regressions now include the new evidence.
The complete offline command passes **111 tests and 14 competency fixture queries**,
including all 28 DIAMM tests; Black and diff checks pass. Self-review found no
introduced correctness defects and added absent-list and whitespace-label
controls; all seven selection tests passed again after those additions.
No independent agent review or OpenRefine GUI/service replay was performed.

All test inputs are synthetic. Historical prevalence, actual source-version and
export compatibility, changed reconciliation results and RDF size remain
unmeasured. Old scalar exports cannot recover omitted entries. Other entity
identifier lists, mappings for other schemes and other CSV parsing remain
outside this repair. Nothing was pushed, merged, regenerated or deployed.

## Completed task — DIAMM archive names and sigla

Completed 28 October 2026 in local commit `5460e18a` on
`preservation-repairs-2026-10-21`.
The [archive text contract](diamm/doc/archive_text.md) traces the fields through
extraction, the tracked history/export and RDF. The upstream archive model and
detail serializer were inspected at pinned revision
`052004f86960a5dc4d1e7446be8d5a6ac8594bd1`; both define name/siglum text.
No live DIAMM records or historical snapshots were read.

The RDF loader now protects archive `name` and `siglum` from pandas inference.
Nonempty cells remain strings under `rdfs:label` and P11550, preserving leading
zeros, long digits, NA-like values, Unicode and whitespace. Empty cells emit no
corresponding statement; empty names no longer fabricate `"None"` labels.
Literal `"None"` and whitespace-only text survive. No defaults are inferred from
matches or identifiers. Source subjects, supplied name matches and archive
location/source links retain their behavior. Extraction/history/export changes
were unnecessary; import instructions now explicitly protect both text columns.

Six new tests reported nine failures, including subtests, against the old
converter and now pass. They cover numeric-only CSVs, full extraction/export
projection/RDF CLIs, independently specified graphs, Turtle round trips,
exact-string SPARQL joins, blanks/nulls, invalid match candidates and conflicting
rows. The complete offline command passes **117 tests and 14 competency fixture
queries**, including all 34 DIAMM tests. Black and diff checks pass. Self-review
found no introduced correctness defects and added an extraction row-count check;
all six archive tests passed again. No independent agent review or OpenRefine
GUI/service replay was performed.

The existing export retains unmatched text in `name_@id`: an unmatched whole
`Q42` there still passes the existing syntax-only match check. That ambiguity
is documented and tested, not repaired by this task. JSON null/empty strings
share an empty CSV cell; conflicting direct triples do not preserve row pairing.
Other tables/fields and historical prevalence remain unverified. Previously
numeric RDF objects now become strings; old damaged exports require matching
source evidence for recovery. Nothing was pushed, merged, regenerated or deployed.

## Next task — DIAMM geographic names

1. Review `name` in cities, countries and regions from extraction through their
   tracked histories/exports to RDF. These tables still use default pandas
   parsing and unconditional name literals. Reproduce any loss with synthetic
   records, including numeric-looking, NA-like and empty names.
2. If supported, make a bounded text-preservation repair while retaining supplied
   matches, local subjects and geographic/source links. Keep country matching
   hints distinct from source relationships, and review blank behavior before
   changing it. Do not infer missing names or alter reconciliation semantics.
3. Run actual extraction/CSV/RDF regressions and offline checks, document evidence
   and compatibility, and update this handoff. Other tables, the existing
   unmatched-QID export ambiguity and historical prevalence remain separate.
   Do not repeat completed archive or identifier-list work.

Do not restart completed MusicBrainz URL, role or auxiliary work, or SIMSSA
mapping work. Publishing remains separate; respect protected remote `main`.
Historical validation and deployment still await confirmed snapshot access.

## Completed task — Global Jukebox mapping repair

Completed 21 October 2026 in local commit `93f23953`. The
[decision record](theglobaljukebox/doc/alternative_names_mapping.md) documents
source/export contracts, authoritative definitions and the Git history.
Commit `781beaf5` introduced duplicate declarations while partially applying
the earlier SKOS mapping change. All 19 social-factors society alternative-name
columns now use `skos:altLabel` with explicit `xsd:string`, preserving whole
`Q42` values and URLs as names attached to the local society resource.
The converter and other table mappings are unchanged.

The complete Global Jukebox configuration parses and passes
`rdf_process_predicates` for all 17 tables; no further configuration errors
were exposed. The compatibility test now covers all nine tracked configs.
A new synthetic CSV-to-RDF test uses the actual table and independently
specified expected triples. It exercises every repaired column, multiple
names, blanks, sparse records, ID-like strings, Unicode, punctuation and
whitespace, plus local subjects and a Turtle round trip. A whole `Q42` is
also tested in every name column to enforce literal handling throughout.

`poetry run python scripts/check_offline.py` passes **65 tests and 14 competency
fixture queries** (previous baseline: 64 and 14). Black and `git diff --check`
pass. Shared identifier documentation and the dataset README now link the
mapping decision and remove the obsolete config exclusion.

Historical exports, affected counts, full-dump fidelity and stored/live RDF
remain unverified and unchanged. Snapshot work is deferred until Liam confirms
access; no production probes, push, deployment or issue updates were performed.


## Start here — next agent

**Liam deferred the stored-snapshot work for a couple of weeks on 20 October
2026. Resume that work when he confirms access is available, not automatically
on an estimated date.** This defers historical fidelity measurements, the real
50–100-case reconciliation review, full-dump validation/regeneration and the
associated deployment work. Do not request the dumps as a prerequisite for the
task below or repeat live probes to substitute for the unavailable snapshots.

**The MusicBrainz representation review is complete.** Read the
[decision record](musicbrainz/doc/representation_review.md), after root
`CLAUDE.md` and `musicbrainz/README.md`. It retains all 33 specific predicates,
named source observations, and the
[explicit schema query](musicbrainz/doc/queries/pilot_contributors.rq) for broad
contributors. Ordinary P767-only queries omit the new roles. Exact-role and
qualifier-sensitive queries retain their distinct purposes; CQ09 preserves
observation IDs and source evidence.

All 33 archived definitions were reviewed. The six saved API examples reproduce
ten mapped observations and ten role assertions spanning seven type UUIDs.
No converter or mapping defect was established. Documentation now states the
bounded recognition of unresolved relationships, the scope of retained JSON,
observation-ID/counting limits, and recording photography's deprecation. Four
new regression tests and a stronger graph-scope test cover the previously
unchecked cases. That review passed 48 tests and 14 fixture queries on
20 October. The completed additions below bring the current baseline to **117 passing
tests and 14 passing competency fixture queries**; neither result establishes
population quality. Do not repeat completed reviews or restart the tooling.

**The requested snapshot-independent improvements are complete (21 October).**
Run `poetry run python scripts/check_offline.py` for the preservation suites and
all 14 competency fixture queries. The new
[GitHub Actions workflow](.github/workflows/offline-checks.yml) runs the same
command on pushes to `main`, pull requests and manual dispatches with Python
3.12 and locked dependencies. It requires no snapshots, credentials, running
triplestore or source API calls after dependency installation. The workflow is
published in draft PR #473. Hosted offline CI passed for the original
`0b508a76` publication; the later repairs and docs were published on 29 October
and triggered a new run, recorded in that publication section above.

The [identifier review](evaluation/identifier_review.md) retains source nodes
and explicit, scoped QID/P2888 joins, with three query examples and six new
synthetic tests. It records differences in normalization and match handling
across converters. No global node replacement or identity inference was added.

**The next requested local repair is also complete (21 October).** The
[shared CSV identifier contract](shared/rdf_conversion/identifier_preservation.md)
records the export review and fix. Conversion now recognizes complete Wikidata
IDs/URLs, preserves external URLs and prose, honors literal declarations and
local prefixes, and stops extracting PIDs from unrelated predicate URLs/text.
The general-purpose search helper and dataset mappings are unchanged. Ten new
tests bring the total to **64 tests and 14 competency fixture queries**; they
include actual DTL mapping conversion and Turtle round-trip checks.

**The Global Jukebox mapping repair is also complete (21 October).** See the
completed-task section above and commit `93f23953`. It added the 65th test and
restored validation of all nine configs. The subsequent MusicBrainz URL repair
(`5d5e18ae`) brought validation to 69 tests. DIAMM validation (`db00b71d`)
brought the total to 74 tests. SIMSSA person mapping (`ea716132`) brought the
total to 77. MusicBrainz auxiliary CSV validation on 26 October brought it to 84;
the loader follow-up brought it to 88. DIAMM person-year preservation brought
the total to 95. DIAMM original-name/floruit preservation brought the
total to 99 tests. DIAMM RISM/VIAF identifier text preservation brought it to 104.
DIAMM external identifier-list preservation brought the total to 111.
Archive name/siglum text preservation brings the current total to
**117 tests and 14 competency fixture queries**. Geographic name text parsing
is the next bounded review.
These are code/config findings, not measured historical-data defects. Snapshot
validation and regeneration remain deferred until Liam confirms access.

The Virtuoso comparison remains optional and lower priority until a concrete
compatibility/performance need arises. Inspect an isolated local/test environment
before preparing graph/rule-set names, fixtures, queries, provenance and cleanup.
Do not assume the public production endpoint is a test instance. Keep the
explicit schema query as the default while no alternative is justified.

Keep production source/schema graphs, inference settings and SESEMMI unchanged.
Do not close #470 or #472 on the strength of fixtures. Historical validation,
reconciliation review and deployment remain deferred until Liam confirms
snapshot access; this local design decision does not remove those requirements.

**Evidence retained for the wait:** both former `/tmp` evidence directories were
copied and checksum-verified into the ignored workspace directory
`evaluation/audits/handoff-2026-10-20/` (340 files, about 3.1 MB). Its
`manifest.json` records original paths, copy paths and SHA-256 values.
`preservation/` holds converter/API evidence; `evaluation/` holds query runs,
current-source responses and source snapshots. Prefer these copies if `/tmp`
has been cleared. This is local retention, not a remote backup, and Git does
not transfer it to another checkout. The code, docs and synthetic fixtures
remain sufficient for offline checks if these optional artifacts are absent;
record missing evidence rather than claiming it was inspected. The representation
review reverified all 340 checksums. Its new local evidence is under
`evaluation/audits/representation-review-2026-10-20/` (review metadata, archived-API
conversion and 14 fixture-query outputs), also ignored by Git.

The 21 October synthetic conversion probes are retained in
`evaluation/audits/identifier-review-2026-10-21/conversion-probes.json`.
Offline-run evidence, including the clean committed-tree check, is under
`evaluation/audits/offline-ci-2026-10-21-verified/`. These are also local,
ignored artifacts; the tests do not depend on their presence.

Liam confirmed on 20 October 2026 that he is the sole developer and does not
require PRs for local work; the original work used topic-sized commits on local
`main`. The 21 October publication established that remote `main` requires PRs.
The active local branch is now `preservation-repairs-2026-10-21`; keep the later
work there and respect the protected workflow for publication. Publishing,
merging and deploying RDF to Virtuoso remain separate actions.

## Pending deployment — Liam must update Virtuoso

Deferred with the stored-snapshot work as described in **Start here** above.
This checklist records later deployment requirements, not the next agent's task.

**The changes are to conversion code, mappings, tests, and documentation. The
stored dataset Turtle files and production Virtuoso graphs have not been
modified.** Only small test/sample Turtle files were generated under `/tmp`
and the ignored `evaluation/audits/` workspace directory.
Committing or merging this code will not update the live data.

- [ ] Make the reviewed converter/configuration revisions available on the
  machine with the Arbutus/Montreal source snapshots; record snapshot and
  conversion versions.
- [ ] **Shared CSV converter:** review source cells affected by stricter identifier
  recognition and explicit literal/local-prefix precedence. Regenerate into a
  separate directory and check source keys, labels and canonical joins, including
  triples excluded by existing conditional mappings. Follow the
  [shared identifier procedure](shared/rdf_conversion/identifier_preservation.md).
  Global Jukebox's TOML mapping conflict is repaired locally; validate its
  alternative-name exports against the documented contract before regeneration.
  Never repair collapsed old QIDs without their source values.
- [ ] **RISM:** inspect the actual stored/live data for affected identifiers,
  then regenerate RDF from the reconciled CSVs into a new output directory or
  prepare the scoped identifier migration described in
  [the RISM procedure](rism/doc/identifier_normalization.md). The small live
  sample was already canonical, so establish whether a live migration is needed.
- [ ] **MusicBrainz:** validate the pilot against the stored JSON dump and
  regenerate RDF from that source using the reviewed representation. Specific
  roles and qualifiers cannot be reconstructed from the old P767-only Turtle.
  Export the matching schema/alignment RDF separately; use
  [the documented broad-contributor query](musicbrainz/doc/queries/pilot_contributors.rq)
  when querying the newly converted data. Also audit source URL forms under the
  [URL contract](musicbrainz/doc/url_recognition.md), comparing canonical joins
  and preserved literal targets before staging/replacement.
- [ ] **DIAMM:** review actual exported identifier cells under the
  [contract](diamm/doc/identifier_validation.md), verify preserved names and
  source relationships, and regenerate separately. Apply the
  [person-year contract](diamm/doc/person_years.md) to actual date/flag cells and
  query compatibility, plus the [original-name/floruit contract](diamm/doc/person_name_preservation.md)
  across extraction and OpenRefine. Follow the
  [external identifier text contract](diamm/doc/external_identifier_text.md) for
  RISM/VIAF strings and query datatypes. Apply the
  [identifier-list contract](diamm/doc/external_identifier_selection.md) to
  complete archive/person lists, supported labels, ambiguous hints and changed
  reconciliation results. Apply the [archive text contract](diamm/doc/archive_text.md)
  to names and sigla, including empty-cell behavior, string query compatibility
  and matching hints. Review remaining column parsing before asserting full
  source fidelity.
- [ ] **SIMSSA TOML route:** verify actual person exports and completeness of
  original names under the [contract](simssa/doc/person_identifier_mapping.md),
  record which conversion route produced stored RDF, and regenerate separately.
  Test canonical item links and retained names before replacing any graph.
- [ ] **APSearch:** review the
  [creation-period representation and regeneration procedure](ckg-apsearch/doc/creation-period-preservation.md),
  regenerate from the stored E6304 snapshot into a new directory, and inspect
  the generated audit of both bounds, unresolved values and source anomalies.
  Verify original CTO values and interval-overlap answers in staging before
  replacing the APSearch production graph. Do not append to old data and leave
  obsolete P571 projections in place. Record actual snapshot counts separately
  from the historical 4,214 intervals / 128 multi-year ranges.
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
- **#471:** keep open. The APSearch converter repair and offline validation are
  published in draft PR #473 but not merged or deployed. Stored-snapshot validation and
  the deployment disposition remain pending.
- **#472:** keep open. The six-dataset manifest inventory, audit protocol,
  14 competency queries, query runner and stratified sampler are implemented.
  Synthetic checks and bounded live probes are recorded; matched-snapshot
  fidelity, real reconciliation reviews and independent live expected answers
  remain pending. See [the evaluation findings](evaluation/findings-2026-10-20.md).
- **#419 / #432:** keep open. The local identifier review now recommends
  retaining source nodes and using scoped direct-QID/P2888 joins. Actual entity
  identity, affected-source prevalence and performance remain unverified;
  concrete converter follow-ups are documented. No GitHub issue was updated
  or closed by the review.

## Local commit stages

The four implementation/documentation commits from `data-preservation-pilot`
were merged into local `main` by fast-forward on 20 October 2026, preserving
their separate history. The wiki has a separate commit on its `master` branch.
The datalake commits through the documentation refresh `de1b8379` are published
in draft PR #473, including the later DIAMM, SIMSSA and MusicBrainz work. Wiki
commits `49ad0ad` and `5575645` were published to wiki `master` on 29 October.
The follow-up status commits document that publication. None deploys RDF data
to Virtuoso.

| Stage | Repository | Commit |
| --- | --- | --- |
| RISM identifier conversion, tests, audit and migration procedure | linkedmusic-datalake | `4d58cdfd` |
| MusicBrainz role preservation, inventory, tests and sample conversion | linkedmusic-datalake | `412c3d66` |
| CKG role and date interpretation | linkedmusic-datalake | `60937e27` |
| Initial handoff and pending Virtuoso deployment checklist | linkedmusic-datalake | `38f9ef18` |
| Source-preserving RDF conversion policy | linkedmusic-datalake.wiki | `49ad0ad` |
| APSearch creation-period preservation, shared CKG copies, tests and procedure | linkedmusic-datalake | `89b9e768` |
| Independent evaluation manifests, protocol, query/sampling tools and fixtures | linkedmusic-datalake | `4d82f03b` |
| MusicBrainz representation decision, documentation and regression coverage | linkedmusic-datalake | `bf3491fa` |
| Consolidated preservation handoff and commit status | linkedmusic-datalake | `9bbb4c7d` |
| Offline validation command and GitHub Actions workflow | linkedmusic-datalake | `df9f785f` |
| Identifier design review, scoped queries and synthetic controls | linkedmusic-datalake | `6c680314` |
| Offline CI and identifier-review handoff | linkedmusic-datalake | `93642c26` |
| Shared CSV identifier preservation, tests and export contract | linkedmusic-datalake | `a928a19d` |
| Global Jukebox alternative-name mapping, regression and decision record | linkedmusic-datalake | `93f23953` |
| MusicBrainz complete item-URL normalization, tests and contract | linkedmusic-datalake | `5d5e18ae` |
| DIAMM complete bare-ID validation, import-safe conversion and tests | linkedmusic-datalake | `db00b71d` |
| SIMSSA person exact-match guard, original labels and regression tests | linkedmusic-datalake | `ea716132` |
| MusicBrainz auxiliary CSV item validation, source fallbacks and tests | linkedmusic-datalake | `fe196861` |
| MusicBrainz CSV text preservation, field/type lookup isolation and CLI regressions | linkedmusic-datalake | `60ebf3b9` |
| DIAMM person-year evidence, approximation-aware dates, ID validation and regressions | linkedmusic-datalake | `fe53b415` |
| DIAMM original person names/floruit text, export compatibility and CLI regressions | linkedmusic-datalake | `becc8734` |
| DIAMM RISM/VIAF identifier text, export contract and extraction/CSV/RDF regressions | linkedmusic-datalake | `406c868e` |
| DIAMM complete identifier lists, conservative hints, RDF projection and regressions | linkedmusic-datalake | `ae26d383` |
| DIAMM archive name/siglum text, empty-cell behavior and extraction/CSV/RDF regressions | linkedmusic-datalake | `5460e18a` |

The earlier continuation implemented the APSearch repair directly in the working
tree on `main`, based on `c468e947`. An earlier commit attempt was rejected by
automatic approval review because that conversation did not explicitly
authorize committing. Liam subsequently requested topic-sized commits on
20 October 2026; that workflow blocker was resolved by the three topic commits
from that date above. The 21 October additions also have separate topic commits.

The APSearch commit keeps all three shared CKG converter/configuration copies
together with its tests, overlap query and regeneration procedure. The evaluation
commit adds `evaluation/`, its root README link and the ignore rule for local
audit outputs. The MusicBrainz review commit adds the decision record, clarified
documentation and four tests plus stronger graph-scope checks; its converter,
configuration and query files are unchanged. The consolidated handoff is a
separate documentation commit after those topics.

The 20 October code passed 48 tests and 14 fixture queries. The 21 October
CI/review additions brought the total to 54 tests and the same 14 competency
queries. The subsequent shared CSV repair adds ten tests for a total of 64.
The Global Jukebox mapping regression adds one more, bringing the total to 65.
The MusicBrainz URL repair adds four tests for 69. DIAMM adds five for the
total of 74. SIMSSA adds three for 77, and MusicBrainz auxiliary CSV validation
adds seven to reach 84. The CSV loader/lookup follow-up adds four to reach 88;
DIAMM person-year preservation adds seven to reach 95. Original-name/floruit
preservation adds four to reach 99. RISM/VIAF identifier text preservation adds
five to reach 104. Complete archive/person identifier-list preservation adds
seven to reach 111. Archive name/siglum text preservation adds six for the
current total of 117.
Earlier validation also passed from a clean `git archive` of committed code,
invoked outside that checkout using the existing Python environment. The
26 October auxiliary and DIAMM year/name results and the 27 October external-ID
results and the 28 October archive-text results were verified in the working
checkout.
The earlier archive check confirms independence from ignored evidence and source
dumps, not a fresh Linux dependency installation or hosted Actions run.
Changed Python files passed Black's check, and each staged change passed
`git diff --cached --check`. Generated audit/source evidence remains ignored.
No push, deployment or GitHub issue update was performed.

Issues #462 and #450 were both confirmed open on
20 October 2026; neither was closed or commented on during this work.
The [three follow-up issues](#follow-up-issues) below were published on
20 October 2026: MusicBrainz validation/deployment
[#470](https://github.com/DDMAL/linkedmusic-datalake/issues/470), APSearch interval
preservation [#471](https://github.com/DDMAL/linkedmusic-datalake/issues/471), and
independent graph evaluation
[#472](https://github.com/DDMAL/linkedmusic-datalake/issues/472).

## Implementation status — 20–21 October 2026

Completed locally, with no production writes or full-dump regeneration:

- **Offline validation and CI (21 October):** one command runs isolated test
  processes and all competency fixture queries. The workflow uses Python 3.12,
  Poetry 2.1.4 and the lockfile. Output-directory protection, nonzero failure
  propagation, YAML settings and formatting were checked locally. Hosted CI
  subsequently passed for the published `0b508a76` revision, as recorded in
  the 21 October publication section. The later repairs were published on
  29 October and triggered another hosted run; see the newer publication section.
- **Identifier design review (21 October):** reviewed converter/configuration
  paths for direct QIDs, source nodes and P2888. Added three query examples and
  six synthetic controls, preserving source/graph evidence and exposing
  competing targets. That review baseline passed **54 tests and 14 competency
  fixture queries**. Converter/configuration behavior remains unchanged;
  source-impact measurements and focused repair follow-ups are separate.

- **RISM normalization:** reproduced the failed canonical-ID join, fixed full-match item-IRI normalization, and handled P2888 predicate aliases separately. Five offline tests pass. Added a read-only identifier audit and [separate migration procedure](rism/doc/identifier_normalization.md).
- **MusicBrainz pilot:** inventoried all 33 P767 role mappings against official definitions, retained specific roles using stable source UUIDs, and added named observations for direction, dates, attributes, and full source relationship JSON. Sixteen offline tests now pass, including inverse direction, negative role checks, named-graph scoping, and legacy mapping behavior. The earlier normal multiprocessing JSONL converter smoke test also completed on two records.
- **MusicBrainz representation decision:** completed the
  [bounded review](musicbrainz/doc/representation_review.md), retaining all 33
  role predicates and the separate-schema query. Six archived API records
  reproduced all ten pilot observations/payloads; all 33 roles passed synthetic
  checks from both source endpoints. Documentation and regression coverage were
  improved without changing the converter/configuration. That review's combined
  baseline was 48 passing tests plus 14 fixture queries; dump validation remains pending.
- **Current API validation:** six purposively selected official example records contained 18 artist relationships, including 10 pilot relationships. All 10 pilot roles and source payloads were checked against generated RDF. This is current API evidence, not a validation of the historical imported dump. See the [inventory](musicbrainz/doc/relationship_inventory.md) and [model, query compatibility, commands, and results](musicbrainz/doc/relationship_preservation.md).
- **Policy and descriptions:** updated the sibling wiki's RDF Conversion Guidelines and clarified CKG role-unspecified links and date meanings. SESEMMI remains unchanged.
- **APSearch interval repair:** preserves the original `CTO_0001073` assertion
  and named observations with paired `xsd:gYear` bounds. Parsed, ordered periods
  retain a P571 start-year projection; unresolved values retain evidence and
  review flags without a projection. `9009` is preserved and flagged, not
  corrected. All three CKG converter/configuration copies remain identical.
  Eleven offline tests pass, including named-graph overlap (1909–1950 matches
  1940, excludes 1960), malformed/reversed/unknown values, duplicate collapse
  and legacy feed behavior. The normal CLI smoke test also passed.
  See [the model, audit and reload procedure](ckg-apsearch/doc/creation-period-preservation.md).
- **Independent evaluation foundation (#472):** added six dataset manifests
  with explicit unknown provenance/counts, a fidelity/reconciliation protocol,
  a 60-case review design and reproducible stratified sampler, and 14 manually
  written competency queries with hand-authored synthetic expected answers.
  All 14 fixture queries and 16 evaluation tests pass; the 32 current converter
  tests also pass. The read-only runner records exact queries, raw responses,
  timestamps, file hashes and failure/partial status. The initial live batch
  returned 11 valid responses, one timeout and one HTTP error; one case required
  an unconfigured schema graph and sent no request. One Weimar/MusicBrainz
  identifier join was observed, with current source corroboration only on the
  MusicBrainz side. This is not a population-quality measurement. See
  [the evaluation package](evaluation/README.md) and
  [the bounded findings](evaluation/findings-2026-10-20.md).

The APSearch CLI fixture contained **9 input occurrences / 8 distinct
observations**, including 1 duplicate: 4 parsed, 4 unresolved, 6 retained start
bounds, 6 retained end bounds and 5 flagged observations, producing 78 RDF
triples. These are deliberately selected synthetic cases, not accuracy estimates
or snapshot measurements. Five musiconn and six Detmold synthetic records
produced byte-identical Turtle under the previous converter at `c468e947`.
Formatting, diff whitespace and local documentation-link checks passed.
Inputs, output, CLI logs, checksums and the comparison report are under
`/tmp/linkedmusic-preservation-2026-10-20/apsearch/`.

The stored dumps are in Arbutus object storage and on the Montreal machine, not
in this checkout (confirmed by Liam). Current API examples were authorized as a
bounded alternative. Raw responses, manifests/checksums, and generated RDF/audits
were initially saved under `/tmp/linkedmusic-preservation-2026-10-20/` and are now
also retained in `evaluation/audits/handoff-2026-10-20/preservation/` outside Git.

Evaluation query runs and current-source responses are separately archived under
`/tmp/linkedmusic-evaluation-2026-10-20/`, with a verified local copy in
`evaluation/audits/handoff-2026-10-20/evaluation/` outside Git. The historical
snapshots were not substituted with current API
retrievals. No real 50–100-case reconciliation review has been performed.

The live RISM check found 200/200 sampled P2888 objects already canonical and no
rows in a separate noncanonical-P2888 query. No affected live triples were
established by that bounded sample. This does not invalidate the reproduced
converter bug or establish that every stored file/predicate is canonical.

Current queue (the **Start here** section is the next-agent brief):

1. **Local requested work complete:** offline CI, the identifier review and
   shared CSV identifier preservation and Global Jukebox mapping repair are
   implemented and tested, as are MusicBrainz URL recognition and DIAMM ID
   validation and SIMSSA person P2888 handling. MusicBrainz auxiliary CSV ID
   validation, its CSV loader/lookup follow-up and DIAMM person-year preservation
   are also complete (26 October), as is DIAMM original-name/floruit preservation.
   DIAMM RISM/VIAF identifier text preservation is complete (27 October).
   DIAMM external identifier-list preservation is also complete (27 October).
   Archive name/siglum text preservation is complete (28 October).
   Geographic name text parsing is the next bounded review.
   The Virtuoso comparison remains optional; none is a prerequisite to waiting
   for snapshots.
2. **Deferred until snapshot access resumes:** populate the prepared
   [evaluation manifests](evaluation/manifests.json) from
   the actual snapshots and conversion/deployment records. Use the
   [protocol](evaluation/protocol.md) to trace source occurrences, freeze complete
   reconciliation frames and select the planned 60-case review. Independently
   establish expected live answers; the 14 synthetic query controls and bounded
   endpoint probes do not replace these measurements.
3. **Deferred with those snapshots:** validate MusicBrainz and APSearch dump
   field shapes, unresolved observations,
   RDF expansion and conversion cost when their stored snapshots are available.
   The APSearch converter now emits an audit with explicit denominators and
   normalized-input/converter/mapping/output hashes; the historical source
   snapshot date remains unknown until supplied in a run manifest.
4. **When the final DLfM manuscript is available:** compare the eventual paper
   scope with it. Slides alone do not settle the new contribution.

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

Preserve and flag source anomalies without guessing corrections. The APSearch
year `9009` remains a source-tracing case; investigate where it first appears,
then classify it. Dropping the end years of the historical 128 APSearch
multi-year intervals was documented conversion loss: the local converter repair
now preserves both bounds, but stored/live data remains unchanged pending
validation and reload. The suspicious Detmold Person/opera cases likewise
require tracing before attributing responsibility.

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

The numbered sequence below records the original roadmap. For current priority
and the snapshot-work deferral, follow **Start here** and **Current queue** above.

1. RISM normalization and focused regression tests.
2. MusicBrainz pilot mapping design and source-preserving conversion.
3. Consistent ontology policy and descriptions, including the outdated wiki guidance.
4. LinkedMusic data manifest, fidelity/link audit, and competency-query pilot.
5. Optional reasoning experiment, followed by a deployment recommendation.

Use one reviewable change per topic. Write the resource description and evaluation protocol alongside this work; results and conclusions follow the measurements. Keep small synthetic test fixtures in source control where appropriate, and generated audit reports/data outside it.

The RISM fixture/fix, MusicBrainz pilot, APSearch interval repair and independent
evaluation foundation are now implemented, and the MusicBrainz representation
review is complete. Offline CI and the separate identifier review are now
complete too, as is the shared CSV identifier repair; remaining local follow-ups
are recorded in **Start here**.
Resume #472's matched-source measurements and
actual reconciliation review when Liam confirms snapshot access is available.
Stored-snapshot validation remains necessary before deployment. Do not repeat
completed conversion or protocol work.

## Follow-up issues

Drafted and published 20 October 2026 at Liam's request. The initial scopes and
acceptance criteria are retained below; use the linked GitHub issues for ongoing
tracking. The MusicBrainz and APSearch issues explicitly note that the associated
implementation/documentation commits remain local and Virtuoso is unchanged.
RISM deployment continues under existing issue #462, so no duplicate RISM issue
was created. The APSearch repair/offline fixtures and MusicBrainz representation
review are complete locally. Resume source-based evaluation and converter
validation/deployment when snapshot access is available. The local
#471 checklist below reflects
this continuation; the GitHub issue has not been edited, commented on or closed.
The deployment checklist remains separate.

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

Local status, 20 October 2026: implementation and offline validation complete,
committed locally as `89b9e768`; stored-snapshot checks and deployment remain
pending. Details:
[creation-period preservation](ckg-apsearch/doc/creation-period-preservation.md).

#### Problem

The previous APSearch branch of `coerce_date` converted every creation interval to the
start year. For example, `1909-01-01/1950-01-01` becomes only
`"1909"^^xsd:gYear`; the supplied end year is lost.

The documented `apsearch.ttl` snapshot contains 4,214 creation intervals,
including 128 spanning multiple years. These are existing snapshot observations,
not freshly measured production counts. Dropping their endpoints is conversion
loss. The Jan-01 placeholders also do not justify asserting precise calendar
days.

#### Work and acceptance criteria

- [x] Document an RDF representation that preserves both year bounds and the
  original interval evidence, explicitly as a source creation period. Do not
  reinterpret it as a performance or field-recording date.
- [x] Implement the APSearch conversion change. If the current P571 start-year
  assertion remains for compatibility, document it as a projection of the
  preserved period and provide a query for the complete interval.
- [x] Add source-to-RDF fixtures covering single-year and multi-year intervals,
  unknown precision, and malformed or reversed values. Preserve and flag
  questionable source values; do not guess corrections or repair `9009`.
- [x] Verify that the three intentionally shared CKG converter copies stay
  consistent and that musiconn and Detmold date behavior is unchanged.
- [x] Run an overlap query against a fixture: an interval from 1909 through
  1950 should match a query for coverage during 1940 and should not match 1960.
- [ ] When the stored dump is available, report the number of source intervals,
  preserved bounds, and unresolved values with a dated denominator. Keep this
  measurement separate from the historical count of 128.
- [x] Update the data-model documentation and regeneration/reload instructions.
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

Local status, 20 October 2026: the [evaluation foundation](evaluation/README.md)
is committed locally as `4d82f03b`. Six manifests and the query/audit tools are
ready; 14 fixture questions pass and bounded live probes are documented in the
[preliminary findings](evaluation/findings-2026-10-20.md). The source-based
acceptance criteria remain pending where noted below. The GitHub issue itself
has not been edited, commented on or closed in this continuation.

Liam has deferred the historical-source measurements and real reconciliation
review for a couple of weeks. Resume them when he confirms snapshot access;
the MusicBrainz and identifier reviews and offline CI are complete. Optional
local follow-ups are described above; source-based evaluation remains deferred.

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

- [x] Create a per-dataset manifest recording source snapshot/date and checksum
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
- [x] Provide a reusable query/audit runner with query text, dated result
  snapshots, relevant external responses, and code/configuration hashes.
  Preserve timeout, partial-result, and endpoint-error status; a failed lookup
  is not proof that an entity or fact is absent.
- [ ] Produce a bounded findings report containing denominators, sampling
  limits, uncertainty where appropriate, unsupported questions, and the
  concrete conversion/reconciliation follow-ups supported by the evidence.

The manifests explicitly mark unavailable snapshot/deployment provenance and
population counts unknown. The question criterion is partly implemented:
14 manual queries, synthetic expected bindings and initial live execution are
complete, but independent source-backed live expectations remain pending.
A preliminary report exists for those checks; the final source-based report
and real 50–100-case reconciliation review are not complete.

Protocol design and current-API/live-graph probes can begin now. Historical
source fidelity measurements require the corresponding stored snapshots.
Do not silently mix current API evidence with the imported snapshot.

Out of scope: a new NLQ benchmark, paid model calls, user studies, source-database
cleanup, new ingestion campaigns, and global identity inference. Review the
final DLfM manuscript before presenting this pilot as a new paper contribution.
