# LinkedMusic roadmap and current checkpoint

Updated 11 November 2026. This is the current queue and restart point. Detailed
requirements live in linked issues and PRs; historical implementation evidence
remains in the existing preservation handoff.

## Current checkpoint

- **Task:** LM-WF01, establish the cross-session development/review workflow.
- **Status:** awaiting independent Claude review.
- **Repository/branch:** DDMAL/linkedmusic-datalake,
  `docs/review-workflow-2026-11-11`, based on main `59b44485`.
- **PR:** [#474](https://github.com/DDMAL/linkedmusic-datalake/pull/474), open for
  review. Resolve its live head SHA before starting a review or resuming work.
- **Completed:** workflow, agent entry instructions, roadmap, PR template and
  reusable Claude review brief published.
- **Validation:** seven Markdown files and 22 relative links checked against
  the pinned base plus proposed files; entry import, whitespace, final newlines,
  code fences and Git diff checks passed. No converter tests or Claude model
  session run for this task. The PR records the revision-specific review packet.
- **Evidence:** reviewable Markdown in this PR; initial data observations below
  are file-availability observations, not integrity or completeness measurements.
- **Open decision:** Claude review and Liam's acceptance of the workflow.
- **Publication:** code/wiki/RDF behavior unchanged; this task requires no wiki
  edits because the workflow belongs in the repository.
- **Next action:** Liam starts Claude review using the PR's pinned review packet.
  Codex then preserves and resolves findings, arranges any needed re-review and
  requests merge approval. Do not start dependent implementation while waiting.

## Available data and scope

Liam confirmed on 11 November that the files in the current workspace are all
the available data. New dumps and regular refreshes are future work.

The initial inspection found RDF exports in 14 graph folders under `raw_data/`,
CKG source dumps/crosswalk artifacts, a root RISM dump and AcousticBrainz
archives/extracted data. Original MusicBrainz and DIAMM conversion inputs were
not found. Snapshot pairing, checksums, extraction completeness and historical
converter versions remain to be established in LM-DATA01. File modification
dates do not establish source snapshot dates.

Prioritize LinkedMusic graph quality and cross-collection discovery. Validate
conversion fidelity where matching inputs exist; report the limits elsewhere.
Old generic RDF cannot reconstruct discarded roles/qualifiers. Updated upstream
data would establish a new snapshot, not prove the old conversion's fidelity.
Measure storage requirements before large regeneration or staging operations.

## Ordered queue

Each row is a work package that can produce one or more coherent PRs. Create a
task issue only when needed, reusing the linked existing issues.

| ID | Work package and completion evidence | Dependency/status |
| --- | --- | --- |
| LM-WF01 | Adopt workflow, persistent entry instructions, checkpoint and review templates. Complete after Claude review, findings resolution and Liam-approved merge. | Active |
| LM-BASE01 | Settle preservation PR #473: inventory changes/dependencies, reconcile description and recorded checks with its actual head, and establish manageable review units. Split only where independently usable; preserve existing work. | Next after LM-WF01 |
| LM-DATA01 | Inventory available sources, intermediates and RDF; record checksums, known/unknown provenance, graph IRIs, storage needs and which pipelines can be reproduced. | After LM-WF01; can proceed independently of converter changes |
| LM-AUDIT01 | Audit existing RDF with dated denominators, canonical IDs, labels, types, dates and cross-source connections. Classify findings and retain reproducible evidence. | LM-DATA01; reuse evaluation tools from #473 when available |
| LM-AP01 | Validate APSearch interval preservation against the available E6304 source; compare baseline/candidate output, interval queries, unresolved values and size/time. | LM-DATA01 and reviewed relevant #473 implementation; #471 |
| LM-EVAL01 | Run the existing 14 competency queries on versioned data with independently checked answers; review an initial approximately 60 stratified reconciliation cases including unlinked units. | LM-DATA01 and reviewed tooling; #472 |
| LM-FIX01 | Address demonstrated conversion/reconciliation defects in focused PRs. DIAMM parent evidence/type routing remains a candidate; preserve source uncertainty and avoid guessed endpoint types. | Relevant audit evidence; #450, #419, #432 |
| LM-DEPLOY01 | Stage validated regenerations, verify compatibility, prepare backups/rollback, obtain deployment approval, replace affected graphs and record post-deployment results. | Matching source inputs and accepted repairs; #470, #471, #462 |
| LM-APP01 | Coordinate SESEMMI schema/query compatibility with the matching graph version through linked PRs in DDMAL/SESEMMI. | Required before affected graph rollout; broader NLQ evaluation later |
| LM-REFRESH01 | Establish one reproducible new-source refresh, then consider scheduled acquisition, conversion and quality comparisons. | Later backlog |
| LM-REVIEW01 | Optionally configure bounded Claude Code review invocation/collection after access, authentication and usage limits are agreed and verified. | Later convenience task; manual review works first |

## Existing work and references

- [Preservation PR #473](https://github.com/DDMAL/linkedmusic-datalake/pull/473)
  contains completed code and synthetic checks awaiting real-data evaluation
  and deployment. Its description and handoff contain historical status
  statements; reconcile them with the live head before continuing.
- [Pinned preservation handoff](https://github.com/DDMAL/linkedmusic-datalake/blob/3d6906b0090f6bebc40b0dea12c5ed4f221564d6/LINKEDMUSIC-HANDOFF.md)
  records 142 tests and 14 fixture queries on 1 November. These were not rerun
  during workflow setup and are not a current-main baseline.
- [#470 MusicBrainz validation/deployment](https://github.com/DDMAL/linkedmusic-datalake/issues/470),
  [#471 APSearch intervals](https://github.com/DDMAL/linkedmusic-datalake/issues/471),
  [#472 independent evaluation](https://github.com/DDMAL/linkedmusic-datalake/issues/472).
- [#450 source meaning](https://github.com/DDMAL/linkedmusic-datalake/issues/450),
  [#419 identifier retrieval](https://github.com/DDMAL/linkedmusic-datalake/issues/419),
  [#432 P2888 queries](https://github.com/DDMAL/linkedmusic-datalake/issues/432),
  [#462 RISM identifiers](https://github.com/DDMAL/linkedmusic-datalake/issues/462).
- [Documentation PR #469](https://github.com/DDMAL/linkedmusic-datalake/pull/469)
  corrects APSearch/ELAR terminology; account for it when reconciling CKG docs.
- AcousticBrainz/RELICS ingestion and optional reasoning experiments remain
  separate backlog work. This queue is not an inventory of every repository issue.
