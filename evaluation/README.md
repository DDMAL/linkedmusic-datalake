# Independent LinkedMusic graph evaluation

This is the bounded pilot for #472. It runs independently of SESEMMI and paid
model calls. It supplies six dataset manifests, a fidelity/reconciliation
protocol, 14 manually written competency queries, and reproducible query and
sampling tools. Historical source snapshots and their deployment revisions
remain unknown; this directory does not establish population accuracy.

- [Dataset manifests](manifests.json): snapshot, graph, converter, licence,
  selected fields, exclusions and dated-count slots. `null` means unknown,
  never zero. The runner hashes the actual working-tree conversion/config files.
- [Protocol](protocol.md): units, sampling, source tracing and review decisions.
- [Question catalogue](cases.json): question, query, interpretation limits and
  evidence needed to check each answer independently.
- [Findings](findings-2026-10-20.md): measurements and outstanding work, separate
  from protocol design.

The three task families are jazz discovery across Weimar/MusicBrainz, historical
person/source lookup across RISM/CKG, and preservation of roles and dates. Cases
were chosen for coverage, including unsupported questions and negative controls.
They are not a random sample of user questions or a held-out NLQ benchmark.

## Reproduce the offline checks

To run all preservation suites and these query controls together, use
`poetry run python scripts/check_offline.py` from the repository root. This is
also the GitHub Actions entry point. Its optional `--output-dir` retains query
reports in a new directory; otherwise they are temporary.

Run from the repository root in the Python 3.12 Poetry environment:

```bash
poetry run python -m unittest discover -s evaluation/tests -v
poetry run python evaluation/run_queries.py --fixture \
  --output-dir /tmp/linkedmusic-evaluation-fixture
```

Use a new output directory for each run. All 14 queries are checked against
[hand-authored expected bindings](fixtures/expected.json) for the
[synthetic named graphs](fixtures/pilot.trig). The fixture is a query control,
not source data, converter output, or historical truth about the real QIDs
used as join tokens. Existing converter suites remain the source-to-RDF checks.

The expected results distinguish RDF term types and duplicates. Controls include
direct and local-node identity paths, identifier-based recording joins, a
photographer excluded from the engineer query, an unrelated schema graph,
explicit versus unspecified composer roles, 1909–1950 overlap, unresolved
periods, retained `9009`, and an audio record lacking the evidence needed for
the full Arabic/vocal/field-recording question. A title coincidence never
establishes identity.

## Bounded endpoint probes

```bash
poetry run python evaluation/run_queries.py \
  --endpoint https://virtuoso.simssa.ca/sparql --timeout 10 \
  --output-dir /tmp/linkedmusic-evaluation-live
```

This executes SELECT queries sequentially, with no retries or SERVICE calls.
Each query returns at most 25 rows and asks Virtuoso for a 10-second server
timeout. An ordered LIMIT bounds output, not the work required to compute it
or the population being sampled. HTTP connection/read timeouts are also set.
No production write, inference configuration or source/API fetch is performed.

CQ08 requires the actual matching schema graph. Without it the runner records
`configuration_error` and continues the other cases; an unconfigured graph is
not an empty answer. For staging, override graph IRIs explicitly:

```bash
poetry run python evaluation/run_queries.py \
  --endpoint https://virtuoso.simssa.ca/sparql \
  --case cq07 --case cq08 --case cq09 \
  --graph musicbrainz=urn:linkedmusic:pilot:data \
  --graph musicbrainz_schema=urn:linkedmusic:pilot:schema \
  --output-dir /tmp/linkedmusic-evaluation-staging
```

These are example staging IRIs, not a claim that the graphs exist. Graph
overrides preserve the original class/predicate namespaces. Current production
does not automatically contain the candidate MusicBrainz/APSearch models.

Every run writes `report.json`, the exact rendered `.rq` files and raw
`.response` bodies. It records UTC times, graph settings, Git HEAD **and dirty
status**, Python/dependency versions, file/query/body hashes, elapsed time,
HTTP status and diagnostic response headers. Reports checkpoint after each
case. Archive the entire directory outside Git for durable evidence.

Status meanings:

| Status | Meaning |
| --- | --- |
| `ok` | A structurally valid response arrived. Live answers still require independent source review. |
| `partial` | HTTP 206 or an anytime/SQL diagnostic header; retained rows cannot establish completeness or absence. |
| `timeout` | Client timed out; no absence claim. |
| `endpoint_error` | HTTP/network failure; response body retained when received. |
| `invalid_response` | HTTP succeeded but the body was not the expected SPARQL result shape. |
| `configuration_error` | A required graph/parameter is unknown. |
| `query_error` | Offline execution failed. |

Exit code 1 means any execution/configuration failure or fixture mismatch.
`requires_independent_source_review` is not a pass/fail accuracy judgment.
`at_row_limit` flags results reaching the cap; fewer rows do not by themselves
certify endpoint completeness. The runner conservatively treats `X-SQL-*` and
`X-SPARQL-Anytime*` headers as partial signals, following the documented
[Virtuoso anytime-query mechanism](https://docs.openlinksw.com/virtuoso/anytimequeries/).
Installed server limits and inference settings remain uninspected.

## Reconciliation review sampling

Prepare a frozen, complete source-entity frame using the
[frame template](templates/reconciliation-frame.json), then allocate quotas
after inspecting stratum sizes, before reviewing outcomes. The template is
intentionally marked incomplete and cannot be sampled as real evidence.

```bash
poetry run python evaluation/sample_review.py \
  --frame /path/to/complete-frame.json \
  --quotas /path/to/quotas.json --seed recorded-independent-seed \
  --output /tmp/linkedmusic-reconciliation-sample.json
```

A quota file maps `dataset|entity_type|method|linked` to the sample size, for
example `"detmold|Person|gnd_crosswalk|true": 7`. Every observed stratum needs
a positive quota no larger than its population. The complete-frame assertion
and provenance must be checked by the operator; the tool cannot prove an
export is complete. Frame units have unique source-entity IDs. Preserve all
targets of a multi-target entity together in its `target` array.

Selection uses SHA-256 priority within each stratum, without replacement, with
a seed chosen independently of outcomes and frozen before review. It is
reproducible under input reordering. The output includes stratum sizes,
inclusion probabilities, source locations, frame/quotas/sampler hashes and
unreviewed verdict fields. It does not manufacture identity judgments or
interpret identifier agreement as verified identity.

The initial target is 60 reviews including unlinked units. No real frame or
50–100-case review has yet been completed. Use the
[protocol](protocol.md) and [fidelity review template](templates/fidelity-review.json)
when the corresponding snapshots are available.
