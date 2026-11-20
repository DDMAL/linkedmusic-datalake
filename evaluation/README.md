# Evaluation tools and manifests

The manifest records evidence about source snapshots and RDF artifacts for
[the evaluation protocol](protocol.md). It separates three populations:

| Population | What the record identifies |
| --- | --- |
| `stored` | An identified local RDF file, which may differ from production |
| `deployed` | A graph observed at an endpoint, with dated observation/load evidence |
| `candidate` | Output of a particular converter run, without implying deployment |

[manifests.json](manifests.json) contains six migrated pilot datasets. Their
expected graph IRIs are inherited v1 assertions. Pinned CKG READMEs support
three graph names; the cited Weimar, MusicBrainz and RISM READMEs do not state
the other three, whose evidence remains unknown. Artifact inventories
remain unknown; there are no measured population artifacts in this pilot.
Neither an expected IRI nor a folder name establishes deployment. The format
permits any number of datasets and multiple artifacts per population.

## Commands

From the repository root, install the locked Python 3.12 dependencies, including
the development group (`jsonschema` validates manifests and `pySHACL` runs
the RDF evidence-contract tests):

```sh
poetry install --no-interaction --no-root
poetry run python evaluation/manifest.py validate evaluation/manifests.json
poetry run python scripts/check_offline.py
```

The offline runner explicitly requires `evaluation/tests`, `rism/tests`,
`musicbrainz/tests`, `ckg-apsearch/tests`, `shared/tests` and `diamm/tests`.
It fails if a required suite is absent, has zero tests,
fails to import, or reports a failing test.
Each required suite runs in its own interpreter. The GitHub workflow runs the
same checks, all 14 synthetic competency queries and formatting. These are
synthetic controls, not a data census, historical converter-fidelity measurement
or endpoint probe.

Migrate a legacy manifest to a **new** path:

```sh
mkdir -p evaluation/audits
poetry run python evaluation/manifest.py migrate \
  evaluation/tests/fixtures/manifests-v1.json \
  --output evaluation/audits/migrated.json
```

Migration refuses to overwrite the source or an existing output. The example
output must be absent before this command runs. `validate` and `select` are
read-only. The Python API `load(path)` returns the same normalized v2 model for
either supported input version without writing to disk. All consumers must
use this adapter and reject unknown versions.

For an inventory that has actual artifact records, select a population and,
when necessary, an exact artifact ID:

```sh
poetry run python evaluation/manifest.py select path/to/inventory.json \
  --dataset wjazzd --population stored --artifact export-1 --verify-file
```

This example requires a real entry named `export-1`; it is not present in the
pilot. Selection fails when no matching available artifact exists or multiple
records match. `--verify-file` streams the selected local file through SHA-256,
fails for missing/mismatched bytes and rejects paths or symlinks outside the
repository root. `--root` explicitly selects a different checkout/staging root.
Deployed graphs cannot use local-file verification; the tool never contacts an
endpoint or downloads an archive. Selecting a deployed record checks its
recorded evidence structure, not whether it is still deployed today.

## Query execution and controls

[cases.json](cases.json) defines 14 manually authored competency controls.
[identifier_review.md](identifier_review.md) documents the separate identifier
patterns. Run the synthetic fixture to a fresh directory:

```sh
poetry run python evaluation/run_queries.py --fixture \
  --output-dir evaluation/audits/fixture-run
```

All 14 cases compare complete RDF bindings as multisets, preserving duplicates,
IRIs, literal lexical forms, datatype and language. Equivalent JSON literal
encodings are normalized; language tags compare without case. Projection
variables are checked even for empty results. Blank-node labels are compared
literally; these fixtures contain no blank nodes in expected answers, and the
runner is not a general blank-node-isomorphism scorer. Exact fixture answers
are synthetic controls, not independently verified answers for real datasets.

Fixture graph IRIs are fixed independently of the manifest. Both supported
manifest versions go through `manifest.py`, and the report records input and
normalized schema versions. Future converter paths in legacy metadata are not
required fixture inputs. CQ07–09 test a specific MusicBrainz role/observation
model and separate schema graph; CQ10–11 test paired CKG periods. Their design
references pin that model's source revision. Verify those predicates and their
meaning in any measured population before interpreting results.
The three CKG feeds use shared `https://linkedmusic.ca/graphs/ckg/Work` and
`Person` classes inside their separate per-feed named graphs. Negative fixture
records exercise class constraints, identifier shapes, one-hop link limits and
inclusive/exclusive year boundaries.

Measured runs require a population and an exact artifact binding for each query
graph. `--artifact KEY=ID` selects an artifact in dataset KEY; a colon is part of
the ID, so `wjazzd=export:2026-11` selects that exact ID within `wjazzd`.
Primary graph keys cannot select another dataset. The declared auxiliary key
uses `--artifact musicbrainz_schema=musicbrainz/ID` to select a schema artifact
from `musicbrainz`; `/` cannot occur in an artifact ID. Repeat the option for
cross-source queries. Each binding must have a distinct known graph IRI. There is no fallback
to an expected graph, unrelated dataset or endpoint default union.

For a real inventory containing a stored `wjazzd` artifact named `export-1`:

```sh
poetry run python evaluation/run_queries.py --local --population stored \
  --manifest path/to/inventory.json --artifact wjazzd=export-1 --case cq01 \
  --output-dir evaluation/audits/stored-query
```

Use `--population candidate` for candidate files. Local mode loads **one file
per named graph**. It accepts single-graph `.ttl` and `.nt` files, verifies their
SHA-256 before and after loading, and assigns each to its selected named graph.
An answer about an entire graph requires a file containing that entire graph.
For exports split across files, such as MusicBrainz or RISM, selecting one part
does not load the others. Assemble all required parts into a separate derived
artifact before running a whole-graph query. Record its own SHA-256, the assembly
procedure and every input part's identity/hash as lineage evidence; preserve
the originals. The manifest and runner do not aggregate parts automatically.

A deliberately selected subset answers only for that subset. Record its coverage
and exclusions explicitly; both empty and nonempty `ok` answers can omit matches
from unselected parts and cannot establish a whole-graph result.
`--root` selects the
root for repository-relative artifact paths. Paths must remain inside that
root. Relative IRIs require an explicit base in the RDF; the file's machine
path is not an implicit base. Local loading uses RDFLib's in-memory store and
has no time or memory bound. Large whole-graph queries may require a separately
staged complete graph with its own deployment evidence. Quad formats and archives are not
accepted in local mode.

For an explicitly authorized endpoint observation with a deployed record:

```sh
poetry run python evaluation/run_queries.py \
  --endpoint https://example.org/sparql --population deployed \
  --manifest path/to/inventory.json --artifact wjazzd=observed-graph --case cq01 \
  --timeout 10 --output-dir evaluation/audits/endpoint-query
```

These IDs and paths are placeholders. The supplied pilot has no selectable
population artifacts. A selected deployed record identifies the declared
observation target; it cannot prove that the endpoint still contains the same
snapshot, nor establish a stored/deployed correspondence. Record matching load
and endpoint evidence in the manifest and inspect it before running. Do not use
an arbitrary endpoint with an unrelated deployment record.

Only SELECT/ASK are accepted. Updates, SERVICE and FROM clauses are rejected.
The runner uses one GET per case without retries or redirects. Remote timeouts
use a 1–60 second server budget, a 5 second connect timeout and a read timeout
five seconds longer than the server budget; these are not a total wall-clock
bound or an assurance that a server stops work. External authority responses
must be archived separately under the protocol; this tool does not fetch them.

Each fresh run directory preserves the exact manifest input, normalized manifest,
rendered queries, raw responses and a checkpointed `report.json`. Reports include
query/response hashes, adapter/schema/catalogue/protocol/lock/code hashes,
actual Python/client versions, Git head and dirty status, population and selected
artifact IDs. Local file verification is separate from converter provenance;
reading a file never assigns the current query runtime to its conversion.

Execution statuses distinguish `ok`, `partial`, `timeout`, `endpoint_error`,
`invalid_response`, `query_error` and `configuration_error`. Every case records
whether a request was attempted. Missing artifacts, graph bindings or local
parse/hash failures produce configuration errors without querying that case;
other independently configured cases continue. Timeout/HTTP/partial/invalid
responses are retained and cause a nonzero exit. HTTP 206 and Virtuoso-style
`X-SPARQL-Anytime`/`X-SQL*` headers flag partial results. Other server-side limits
may not be detectable: an `ok` response alone never establishes completeness.
If downloading a response body times out, the report records `timeout` and
retains the HTTP status, diagnostic headers and decoded body bytes received
before the failure. A generic connection failure remains `endpoint_error`.

A row count at or above the catalogue limit is explicitly flagged. CQ12 is an
unsupported full question even if its necessary-condition probe returns rows;
its support status remains visible alongside execution and fixture validation.
Other measured answers require independent source review, including successful
empty results. Exit zero means execution/fixture checks completed, not that
real answers are correct or complete or that every question is supported.
Reports are evidence artifacts, not manifest measurements automatically written
back into an inventory. Keep the directories outside Git and archive them with
availability information before citing empirical results.

## Stratified reconciliation sampling

Start from [the frame template](templates/reconciliation-frame.json), filling
its provenance and every source entity before declaring `complete: true`.
The frame uses schema/protocol `1.0` and manifest schema `2.0`; unknown or missing
versions fail. Provenance requires source snapshot and reconciliation-export
SHA-256 values, extraction command, UTC extraction time, unit definition and
explicit exclusions. When a single source export contains accepted targets,
its checksum can identify both inputs. The sampler checks their structure,
not the truth or completeness of the extraction; archive those inputs.

Each unique source-entity ID has dataset, entity type, matching method, linked
boolean, source locator and whole accepted `target` set. A linked target is an
absolute IRI or a nonempty list of distinct absolute IRIs; direct-QID entities
belong in the frame too. Unlinked units use null or an empty list. Unknown
matching methods use the literal string `unknown`. The first three stratum
fields cannot contain `|`, which separates them in quota keys.
Unit objects accept exactly `id`, `dataset`, `entity_type`, `method`, `linked`,
`target` and `source_locator`; unknown fields are rejected. Keep prior reviewer
notes, labels and judgments outside the sampling frame. Use `source_locator`
to identify separately archived source context for independent review.

Supply a JSON quota object covering every observed stratum exactly, for example:

```json
{
  "detmold|Person|authority_crosswalk|true": 7,
  "detmold|Person|unknown|false": 3
}
```

Freeze positive quotas between 1 and N per nonempty stratum and a randomly
chosen seed before examining outcomes. Adjust short strata and redistribute
quotas under the protocol before sampling; the tool never silently changes
quotas. An empty complete frame with empty quotas produces a zero-unit census.

```sh
poetry run python evaluation/sample_review.py \
  --frame path/to/frame.json --quotas path/to/quotas.json \
  --seed RECORDED_RANDOM_SEED --output evaluation/audits/review-sample.json
```

SHA-256 priorities over seed, stratum and ID select without replacement and
are invariant to input order. Each output retains the complete accepted target
set, N, n, inclusion probability n/N, seed, input hashes and sampler/adapter/
protocol hashes. Verdicts, evidence and reviewer fields start unreviewed. The
output is exclusively created; an existing sample is never overwritten. Keep
the frozen frame and quota files alongside it. Probability interpretation
requires a seed chosen independently of outcomes and a genuinely complete
frame, neither of which the program can verify. Human identity review and
weighted estimates remain separate work under the protocol.

## Version and migration contract

[manifest_schema.json](manifest_schema.json) is the structural authority, using
JSON Schema Draft 2020-12. `manifest.py` validates it with `jsonschema` and
explicit format checks. The six custom formats (`repository-path`, `absolute-iri`,
`evidence-location`, `archive-iri`, `utc-timestamp`, `calendar-date`) are enforced
by this adapter; generic validators may treat them only as annotations, even
with their stock format checker. Supported manifest schemas are `1.0` and `2.0`, with
protocol `1.0`. A legacy input without `schema_version` is interpreted as v1;
unknown versions fail. Protocol and manifest-schema versions are separate.

V2 has `schema_version`, `protocol_version`, `scope`, `datasets` and `legacy`.
Each dataset has a unique `key`, name, expected graph, artifact-inventory status,
source snapshots, code references, artifacts and preserved legacy metadata.
An expected graph IRI and its evidence may also be explicitly unknown; adding
a dataset never requires inventing a graph name.
Source/artifact IDs are unique within a dataset; measurement IDs are unique
within their artifact. References never silently select another dataset.

Migration is deterministic and preserves every original dataset field under
that dataset's `legacy` object, and all original top-level fields other than
`datasets` under top-level `legacy`. This includes extensions, old single
`counts`, free-text availability and `working_tree` revision descriptions.
Those values are historical input, **not current verified facts**. Legacy
counts are never assigned to stored, deployed or candidate populations. The
source snapshot's explicit ID/date/retrieval/hash, when supplied, retain their
distinct meanings; migration does not independently verify them. Expected graph
IRIs are retained as assertions, but their evidence becomes unknown until
independently checked. Original references remain in `legacy.graph_iri_evidence`.
The live pilot adds pinned CKG documentation evidence to the migration; it need
not remain byte-identical to a fresh migration.

The preserved [v1 fixture](tests/fixtures/manifests-v1.json) comes byte-for-byte
from `evaluation/manifests.json` at source revision
`3d6906b0090f6bebc40b0dea12c5ed4f221564d6`. It is test input, not a second live
inventory. Legacy mentions of candidate behavior are not claims about the
current converter. Code references have unknown availability and null hashes
until separately inspected. A future converter path retained from v1 does not
become a required runtime input merely because it is listed.

## Unknowns, availability and locations

Evidence values such as hashes, revisions and dates use a tagged object:

```json
{"status": "unknown", "value": null, "reason": "Original converter revision is unavailable."}
```

| Value status | Meaning |
| --- | --- |
| `known` | `value` satisfies its field type; `reason` is null |
| `unknown` | Value not established; null value and explanation required |
| `unavailable` | Relevant evidence cannot be accessed; null value and explanation required |
| `not_applicable` | Field does not apply, with an explicit explanation |

Availability is a separate `status` (`available`, `unavailable`, `unknown` or
`not_applicable`) plus a reason. An available stored/candidate artifact requires
a known repository-relative file path and SHA-256. An available deployed record
requires a known graph IRI, graph evidence, observation timestamp and deployment
evidence. A live-only graph may explicitly mark its local file/hash not applicable.
Mark absent artifacts unknown/unavailable; never invent output files or counts.

`file.path` is a working path. `storage.location` is a separate durable archive
IRI with its own availability; an ignored `raw_data/` path is not an archive.
Local `file:` URIs are not durable public archive locations.
Working paths cannot be absolute, contain traversal or use home-directory
notation. Evidence locations are repository-relative paths or HTTP(S) URLs.
Do not publish private machine paths, credentials or sensitive archive details.
Inspect legacy free text before publishing a migrated external inventory.

An empty list means no **recorded entries** in that collection. It does not
establish a zero-sized underlying population. In particular, `artifacts: []`
with `artifact_inventory.status: unknown` means no artifacts have been
identified. Only an explicitly `complete` inventory with supporting rationale
asserts that the recorded collection is exhaustive.

## Sources, converter identity and lineage

Source records retain snapshot ID/date, retrieval time, original record IDs,
file/hash, durable location, reconciliation intermediates and snapshot-specific
licence evidence. A modification time or current API response cannot identify
an old imported snapshot. Licence URLs alone are discovery references.

Converter revisions must be full 40- or 64-character hexadecimal Git IDs or
explicitly unknown. A dirty conversion requires a nonempty list of exact file
hashes; a bare commit does not identify dirty bytes. The validator checks syntax
and relationships, not Git reachability or the truth of a supplied checksum.
Only explicit selected-file verification checks local bytes. Known converter
identity (revision, dirty state or file references) requires generation lineage;
unknown identity uses an unknown revision, null dirty state and empty file list.

Optional artifact relations require evidence:

- `loaded_from` belongs to a deployed artifact and names a stored artifact in
  the same dataset. Its converter-run ID is not applicable and its source list
  is empty. A shared graph IRI alone does not establish this relation.
- `generated_from` belongs to a stored or candidate artifact and names source
  snapshots plus a known converter-run ID. Its artifact target is null.

Artifact-level `source_snapshot_ids` is exactly the union of its evidenced
`generated_from` source lists, not an unverified assertion. Unknown linkage uses
empty source and relation lists. Deployed artifacts express provenance through
`loaded_from`; inspect the referenced stored artifact for generation identity.
Stored-file findings do not automatically transfer to deployed RDF. Artifacts may retain an
unknown (`null`) environment; a later query environment cannot identify an old
conversion environment.
The adapter validates an artifact environment's structure but does not require
generation lineage for that field. Reviewers must verify its attribution to the
conversion; deployed artifacts should leave it null and refer to stored lineage.

## Measurements

Measurements are nested under their identified artifact and record an ID,
metric, denominator, status, value, UTC observation time, method kind/description
and hash, evidence references, reason and environment. File-parse counts belong
to stored/candidate RDF; remote-query counts belong to deployed RDF. Source
record and RDF entity counts retain distinct method/denominator descriptions.
Any complete/partial artifact measurement requires a known file hash for local
RDF or known graph IRI for deployed RDF, independently of current availability.
This permits historical measurements whose identified bytes are now unavailable.

In v2, `source_count` attaches to a stored/candidate artifact with evidenced
source lineage. Its denominator and evidence must identify the counted source
snapshot IDs, hashes and any subset. Reusing a source count across artifacts
requires an explicit reference to that same measurement evidence; it is not an
RDF count. Standalone source counts collected before an artifact is identified
remain in external evidence until attachment is possible. Source-level
measurement storage is outside this version's contract.
The adapter checks source-lineage references, but does not require a known hash
or snapshot identifier on the counted sources. Reviewers must verify source
identity and the denominator against the evidence; the required RDF artifact
hash does not identify the counted source bytes.

- `complete`: a nonnegative numeric result, including a genuine zero; no failure
  reason. Observation time, method hash, evidence and runtime identity required.
- `partial`: a positive observed count with a reason and the same provenance.
  It is not a complete population total. A partial attempt with no established
  count is recorded as failed with null value, not a measured zero.
- `failed`, `unmeasured`, `not_applicable`: null value and an explicit reason.

Complete/partial results identify the actual counting client/tool and version
in `environment.other.runtime`. Record known lockfile/Python/rdflib/oxrdflib
identity when used; unused fields are `not_applicable` with a reason, never
unknown/unavailable. This applies to file parsing too: direct PyOxigraph parsing
records its version in `other.runtime` and marks unused rdflib/oxrdflib entries
not applicable. Installed but unused libraries do not establish runtime identity.
All complete/partial deployed measurements additionally require `other.endpoint`
(an absolute IRI) and `other.server` (server identity/version), regardless of
method kind. For example, an isql observation
can mark unused Python/library/lock fields not applicable and record its isql
version, endpoint and Virtuoso version in these keys. Additional relevant
versions or settings can also go in `other`.
Unavailable historical counts stay in legacy metadata until provenance permits
assignment. Do not turn null into zero or reuse a file count as a remote count.

## Templates and validation limits

Start an artifact with [population-artifact.json](templates/population-artifact.json).
The [fidelity review](templates/fidelity-review.json) records a source occurrence,
intermediate and RDF trace with the selected population/artifact identity.
The [reconciliation frame](templates/reconciliation-frame.json) records a
complete selection frame including linked and unlinked source entities.
Templates are blank contracts, not measurements or executed reviews.

Structural validation comes from the schema. Semantic checks in the adapter
cover the six custom formats, unique IDs, same-dataset references, evidenced
source lineage, relation direction, measured population identity and dirty-file
identity. Artifact selection and local byte verification are separate explicit
operations. The protocol describes additional manual evidence
requirements that schema validation cannot establish. See
[#472](https://github.com/DDMAL/linkedmusic-datalake/issues/472) for the evaluation
outcomes beyond this inventory contract.
