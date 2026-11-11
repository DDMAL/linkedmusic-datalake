# LinkedMusic development and review workflow

This agreement, established on 11 November 2026, keeps work reviewable across
sessions. Codex maintains the records and implementation; Claude independently
reviews; Liam chooses priorities and approves completed changes.

## Responsibilities

| Participant | Responsibility |
| --- | --- |
| Codex | Maintain the roadmap/checkpoint, scope tasks, implement, validate, update docs, publish PRs, prepare review requests and resolve findings. Read posted reviews when work resumes. |
| Claude | Review the specified revision independently, inspect evidence and report concrete defects or unresolved questions. Review mode does not authorize implementation, merge or deployment. |
| Liam | Set priorities, answer domain questions that evidence cannot settle, initiate the initial Claude review, and approve merge/deployment. Routine bookkeeping belongs to Codex. |

The initial review handoff is one prepared prompt, using
[the review template](claude-review.md). Liam can paste it into a fresh Claude Code
session with repository access, or Claude with GitHub access. Findings can be
posted on the PR when authorized, or returned here for Codex to preserve and
address. Preserve their authorship and reviewed revision.

Claude Code is installed in the inspected workspace, but authentication, a
bounded automated review runner and its permissions have not been validated.
No unattended reviewer is configured by this workflow. A later task can automate
invocation and collection after agreeing its access and usage limits. A second
Codex review must never be represented as a Claude review.

## Planning and task boundaries

The [roadmap](roadmap.md) owns priority, dependencies and the current checkpoint.
Issues own detailed acceptance criteria; reuse existing issues when they fit.
PRs own the change, validation and review discussion. The historical
`LINKEDMUSIC-HANDOFF.md`, when available, holds dated implementation evidence.
Update it for completed implementation tasks without duplicating the live queue.
Repository docs own dataset behavior; the wiki owns cross-cutting and operational
guidance. Link these records rather than copying their contents.

Each task states its problem, scope, acceptance criteria, dependencies and
documentation impact before implementation. A coherent PR can deliver an audit,
design decision, converter repair or deployment procedure. Keep code, meaningful
checks and its required documentation together. Avoid arbitrary file/line limits
and unrelated cleanup. Broader discoveries become linked follow-ups.

Normally finish the review cycle before beginning another implementation PR.
Independent inventory or documentation work may proceed if its separate scope
and dependency are recorded. Cross-repository work uses linked PRs with explicit
merge and deployment order; this agreement must be added to each repository's
own entry instructions before relying on automatic discovery there.

## Review cycle

1. **Queued:** scope, acceptance criteria and dependencies are recorded.
2. **Active:** implement the task, inspect the diff, run appropriate checks and
   prepare documentation and evidence.
3. **Awaiting Claude review:** publish the completed scoped work and a review
   packet containing PR URL, base/head SHAs, requirements, checks and evidence.
   Mark the PR ready for review when appropriate. A draft is a publication state,
   not proof that review has occurred.
4. **Revision:** preserve the review, reproduce findings and push fixes to the
   same PR. Record each finding as fixed with evidence, disputed with reasoning,
   or deferred with a linked task. Required acceptance work cannot be deferred
   while claiming the task complete.
5. **Awaiting Liam's approval:** required checks pass and substantive findings
   are resolved. State remaining limitations. Request review of substantive
   revisions; reviews of an older head do not automatically cover newer changes.
6. **Merged:** record the merge and complete in-scope publication steps. Record
   wiki publication and RDF deployment separately, including "not required" or a
   linked pending task. Close the task only when its acceptance criteria are met.

Ask Claude to look for evidence-backed failures, not to manufacture criticism.
For data work, check source meaning, identifiers, qualifiers, joins, negative
controls, unsupported inference and claims beyond the available evidence.
Distinguish source limitations, conversion loss, conversion errors and
reconciliation errors. Synthetic checks do not establish historical data quality.

Use a fresh Claude session for the initial review of each coherent PR. Reuse it
for bounded fix verification while giving the old and new SHAs. If the scope has
changed substantially, prepare a fresh review of the complete final diff.
Source-backed expected results and reproducible counterexamples matter more than
the number of review rounds.

## Session and context management

At the start of each session, inspect the actual repository and remote PR state
before acting on the checkpoint. Read only the relevant contracts and evidence;
the complete chat history is not a prerequisite.

Before yielding or switching tasks, Codex updates the roadmap checkpoint:
task, repository/branch/PR, progress, actual validation and artifact locations,
open findings/decisions, publication/deployment status, and the next action.
Put exact reviewed and tested SHAs in the PR review packet/results. A checkpoint
commit cannot contain its own hash; resolve its PR's live head when resuming.

Liam can open a new chat at any time after a checkpoint. Natural boundaries are a
PR review request, a completed task or a move to a different repository. Keep the
same chat for a focused implementation/fix cycle when useful. Before a long
session ends, Codex should proactively checkpoint and provide the resume phrase:

> Read AGENTS.md and docs/roadmap.md, verify the current PR/review state, and continue the next authorized step.

Before this workflow is merged, open its PR branch or provide its PR URL so the
new session can find these files. Other repositories need their own linked entry
instructions. A new chat in an unrelated checkout cannot discover this state
automatically. These instructions guide the agent; they are not an automated
policy enforcement service. PR checklists and revision-specific reviews make
compliance inspectable.

There is no background monitoring implied by this agreement. On the next user
message, Codex can fetch GitHub review comments and continue. If findings exist
only in a private Claude conversation, Liam supplies its output or an accessible
link once; Codex handles the subsequent bookkeeping.

## Documentation and wiki publication

Review documentation with the implementation. If wiki changes are needed,
include exact proposed Markdown and a publication manifest under
`docs/wiki-changes/<task>/` in the related repository PR. The manifest identifies
the target wiki, page filenames, inspected base commit, changes and when they
should become public. Treat these as reviewed publication artifacts; the wiki
remains the reader-facing operational documentation.

After Liam approves the outcome, recheck the wiki head. If affected pages changed,
resolve the differences and review substantive changes before publication. Publish
the reviewed content, verify it, and record the wiki commit and page links in the
PR/checkpoint. Preserve page filenames and existing links. Clearly label candidate
models versus deployed behavior. A code merge alone does not update the wiki or RDF.

## Completion and evidence

A PR ready for Claude review has:

- A bounded outcome, acceptance criteria and explicit dependencies.
- Appropriate checks with actual results and limitations; docs-only changes use
  content/link/diff checks rather than unnecessary converter tests.
- Updated affected docs, wiki changes or an explanation that none are needed.
- Reviewable evidence and a complete review packet, including any unavailable
  source data or local-only artifacts.

Large dumps and generated RDF remain outside Git. Keep compact findings in the
repository and retained artifacts in an identified durable location with checksums.
A temporary directory or ignored local folder alone is not a remote backup.
Reviewers must be told which evidence they cannot access. Code merge, source
regeneration and production deployment retain separate acceptance records.
