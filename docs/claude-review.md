# Claude review request

Codex fills this template with concrete values and gives Liam one prompt when a
PR is ready. Start the initial review in a fresh Claude session with repository
access. If the head changes during review, report which revision was inspected;
do not silently switch revisions.

## Prompt template

> Independently review PR {URL} in {owner/repository}.
> Base commit: {full SHA}. Head commit: {full SHA}.
> Task and acceptance criteria: {issue/roadmap link and bounded scope}.
> Review the exact diff and relevant surrounding code, source contracts,
> documentation and tests. Read AGENTS.md and docs/workflow.md at the head.
> For this request your role is reviewer: do not implement, commit, merge,
> publish wiki changes or deploy. Report the review in this conversation unless
> Liam explicitly asks you to post it to GitHub.
>
> Validation reported by the author: {commands, results, tested revisions}.
> Evidence available to you: {links/paths and provenance}.
> Evidence unavailable to you: {missing inputs or inaccessible local artifacts}.
> Related PRs/wiki changes: {links, dependencies and publication status}.
> Areas needing particular scrutiny: <specific risks, without narrowing the
> review to those areas>.
>
> Look for concrete failure cases, source meaning loss, unsupported assertions,
> identifier/join errors, compatibility regressions, inadequate validation and
> documentation claims exceeding the evidence. Check whether the scoped
> acceptance criteria are met. Distinguish source limitations from pipeline errors.
> Do not assume reported tests ran or that passing fixtures establish real-data
> quality. Run appropriate available checks when feasible; state what you actually
> checked and any access limitations.
>
> Return the reviewed SHA, findings ordered by severity, file/line references,
> evidence or reproductions, consequences and proposed corrections. Separate
> blocking defects, nonblocking suggestions and unresolved questions. State
> whether the scoped change is ready for Liam's decision. If no substantive
> findings are supported, say so; do not invent issues.

## After review

Codex preserves the full review or an accessible reference and records each
finding's disposition in the PR. Include fix commits and checks, or reasoned
disagreement. Report unverified claims as unverified. Give Claude the revised
head and the relevant diff for fix verification; request a full fresh review if
scope changed substantially. Liam receives a short decision summary with
remaining risks rather than being asked to maintain the review log.
