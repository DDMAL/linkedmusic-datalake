# LinkedMusic working agreement

Follow this agreement for implementation and review work in this repository.

- At session start, inspect the working tree, branch, current remote PR state and
  [roadmap checkpoint](docs/roadmap.md). Read the [workflow](docs/workflow.md),
  applicable subproject documentation and relevant implementation handoff.
  Resolve stale status against actual commits and evidence; preserve unrelated work.
- The roadmap owns the task queue and current checkpoint. Existing
  `LINKEDMUSIC-HANDOFF.md`, where present, retains dated implementation evidence.
  Follow the user's current scope over historical task instructions.
- Work in coherent PRs with acceptance criteria, appropriate validation, relevant
  documentation and explicit limitations. Normally keep one implementation PR
  awaiting independent review. Record dependencies across repositories.
- Publish authorized PRs and refinements without repeatedly requesting permission.
  Request Claude review once the scoped work is reviewable. Record the exact
  reviewed revision and resolve substantive findings before recommending merge.
  Author self-review is not independent Claude review.
- Liam approves merging and production deployment. Publishing a PR, merging code,
  publishing wiki documentation and deploying RDF have distinct recorded states.
- Before yielding, changing tasks or recommending a new chat, update the roadmap
  checkpoint with branch/PR, completed work, validation and evidence locations,
  pending review/decisions and the next action. Do not require Liam to reconstruct
  context or maintain these records.
- On "continue", refresh the checkpoint and PR/review state, then take the next
  authorized action. If awaiting external review or a required decision, report
  that dependency; do not silently bypass it or claim background monitoring.
- Keep source dumps and generated RDF outside Git. Track compact findings and
  reproducible procedures; record durable locations and hashes for large evidence.
