# Evaluation manifests

The manifest records evidence about source snapshots and RDF artifacts for
[the evaluation protocol](protocol.md). It separates three populations:

| Population | What the record identifies |
| --- | --- |
| `stored` | An identified local RDF file, which may differ from production |
| `deployed` | A graph observed at an endpoint, with dated observation/load evidence |
| `candidate` | Output of a particular converter run, without implying deployment |

[manifests.json](manifests.json) contains six migrated pilot datasets. Their
expected graph IRIs come from repository documentation. Artifact inventories
remain unknown; there are no measured population artifacts in this pilot.
Neither an expected IRI nor a folder name establishes deployment. The format
permits any number of datasets and multiple artifacts per population.

## Commands

From the repository root, install the locked Python 3.12 dependencies, including
the development group (`jsonschema` is required by these evaluation tools):

```sh
poetry install --no-interaction --no-root
poetry run python evaluation/manifest.py validate evaluation/manifests.json
poetry run python scripts/check_offline.py
```

The offline runner explicitly requires `evaluation/tests` and fails if the
suite is absent, has zero tests, fails to import, or reports a failing test.
Each required suite runs in its own interpreter. The GitHub workflow runs the
same checks and formatting. These are synthetic contract tests, not a data
census, converter-fidelity test, query execution or endpoint probe.

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

## Version and migration contract

[manifest_schema.json](manifest_schema.json) is the structural authority, using
JSON Schema Draft 2020-12. `manifest.py` validates it with `jsonschema` and
explicit format checks. Supported manifest schemas are `1.0` and `2.0`, with
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
distinct meanings; migration does not independently verify them.

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
Only explicit selected-file verification checks local bytes.

Optional artifact relations require evidence:

- `loaded_from` belongs to a deployed artifact and names a stored artifact in
  the same dataset. Its converter-run ID is not applicable and its source list
  is empty. A shared graph IRI alone does not establish this relation.
- `generated_from` belongs to a candidate artifact and names source snapshots
  from that artifact’s source list plus a known converter-run ID. Its artifact target is null.

Unknown linkage remains an empty list of recorded relations. Stored-file
findings do not automatically transfer to deployed RDF. Artifacts may retain an
unknown (`null`) environment; a later query environment cannot identify an old
conversion environment.

## Measurements

Measurements are nested under their identified artifact and record an ID,
metric, denominator, status, value, UTC observation time, method kind/description
and hash, evidence references, reason and environment. File-parse counts belong
to stored/candidate RDF; remote-query counts belong to deployed RDF. Source
record and RDF entity counts retain distinct method/denominator descriptions.

- `complete`: a nonnegative numeric result, including a genuine zero; no failure
  reason. Observation time, method hash, evidence and runtime identity required.
- `partial`: a positive observed count with a reason and the same provenance.
  It is not a complete population total. A partial attempt with no established
  count is recorded as failed with null value, not a measured zero.
- `failed`, `unmeasured`, `not_applicable`: null value and an explicit reason.

Measured results require the lockfile SHA-256 and actual Python, rdflib and
oxrdflib versions. Relevant additional runtime versions can go in `other`.
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
cover unique IDs, same-dataset references, relation direction, count population
and dirty-file identity. Artifact selection and local byte verification are
separate explicit operations. The protocol describes additional manual evidence
requirements that schema validation cannot establish. See
[#472](https://github.com/DDMAL/linkedmusic-datalake/issues/472) for the evaluation
outcomes beyond this inventory contract.
