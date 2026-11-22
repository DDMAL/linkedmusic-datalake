# CLAUDE.md

Context for Claude Code working in the `linkedmusic-datalake` monorepo. Per-subproject READMEs are authoritative — read the relevant one before touching that subproject.

## What this repo is

A data-ingestion monorepo. Each top-level folder (`acousticbrainz/`, `cantus/`, `ckg-musiconn/`, `ckg-detmold/`, `ckg-apsearch/`, `diamm/`, `dtl/`, `musicbrainz/`, `rism/`, `simssa/`, `theglobaljukebox/`, `thesession/`) is an independent pipeline that produces RDF Turtle reconciled against Wikidata. The nominal pipeline is **fetch → extract → reconcile (OpenRefine + Wikidata) → convert to RDF**, but subprojects diverge — see "Subproject quirks" below.

## Environment

- Python **3.12**, Poetry-managed at the repo root. One dependency project covers
  all subprojects. To compare retained lockfiles, install each in its own
  environment outside the checkout. The comparison includes imported Python
  files under the checkout when checking converter code identity.
- Install: `poetry install`. Run scripts via `poetry run python …` or from an activated shell.
- **Most scripts assume CWD is the subproject's `src/` folder** (paths are relative to it). E.g., for AcousticBrainz: `cd acousticbrainz/src && python extract.py`. Check the subproject README before assuming otherwise.

## Data is not in the repo

`.gitignore` excludes `*.ttl`, `*.csv`, `*.jsonl`, `*.tar*`, `*.xz`, `store/` and
`store-*/`. Data-directory layouts vary; source dumps and generated RDF stay
untracked. **Never commit data files.** The maintained vocabulary and SHACL
files in `shared/ontology/*.ttl` are an explicit schema exception.

## `shared/`

Reusable code lives here, but it is **not a package** — there's no install step. Import by path or by running as a module from `/shared`:

- `shared/rdfconv/` — generic config-driven RDF converter. Run as `cd shared && python -m rdfconv.convert <config.toml>`. Configs live in `shared/rdf_config/` (one per subproject).
- `shared/wikidata_utils/client.py` — Wikidata API client used during reconciliation.
- Other scripts in `shared/` (`prop_cli.py`, `get_relations.py`) are utilities, not currently imported by subprojects.

## Subproject quirks (the non-obvious stuff)

- **RISM** starts from RDF (not CSV). It splits via `force_split.py`, reconciles in OpenRefine using the **RDF-transform** extension, then re-emits Turtle. RDF-transform **only works in Chrome** — Firefox/Safari will fail silently.
- **MusicBrainz** skips OpenRefine. Source data already carries Wikidata QIDs; only auxiliary fields (types, keys, genres, languages) are reconciled separately.
- **SIMSSA** has a shared TOML-to-Turtle route using `shared/rdf_config/simssadb.toml`,
  alongside a separate JSON-LD converter. See the [SIMSSA conversion guide](simssa/README.md#6-shared-csv-to-rdf-route)
  and [person identifier mapping](simssa/doc/person_identifier_mapping.md).
  Identifying the route used for a historical artifact requires a conversion record.
- **AcousticBrainz** has separate extraction and RDF conversion steps. Check the actual source/intermediate availability before running a step; script existence does not establish an earlier successful conversion.
- **CKG** (NFDI4Culture Culture Knowledge Graph) is **RDF-native** (per-feed N-Triples dumps, no fetch step) and is split into **three sibling subprojects** — `ckg-musiconn/`, `ckg-detmold/`, `ckg-apsearch/` — one per feed, because each loads as its own Virtuoso named graph. They **share one pipeline, copied verbatim** into each `src/` (the scripts take a feed argument, so the copies are identical and overlap is intentional). Reconciliation is a **deterministic authority-ID→Wikidata crosswalk** (GND `P227` / VIAF `P214` / GeoNames `P1566`), with OpenRefine only for the residue (musiconn/Detmold; APSearch needs none). The CKG's RISM feed (`E5313`) is excluded — LinkedMusic ingests RISM separately. Each feed's `doc/data-model.md` is the authoritative mapping/schema doc.
- **DTL, Global Jukebox, Cantus, DIAMM, TheSession** follow the standard pipeline.

## OpenRefine state

For subprojects that reconcile in OpenRefine, history and export files live under `<subproject>/openrefine/{history,export}/`. Filenames are inconsistent across subprojects (some `_history` / `_export` suffixed, some not, some hyphenated, some underscored). **Do not bulk-rename** without asking — these are referenced manually during reconciliation runs.

## Scope and repository state

Inspect Git status, the actual branch, relevant PR heads and the user's explicit
scope before acting. A branch name does not identify the current task. Preserve
unrelated changes, stashes, source inputs and generated RDF. Do not infer source
availability, conversion provenance or deployment from old documentation.

## Evaluation

Read [evaluation/README.md](evaluation/README.md) before editing manifest records.
Use the versioned adapter in `evaluation/manifest.py`; do not read an unknown
schema version as if it were the legacy inventory. Keep stored, deployed and
candidate populations distinct and retain unknowns. Run:

```sh
poetry run python evaluation/manifest.py validate evaluation/manifests.json
poetry run python scripts/check_offline.py
```

The runner starts a fresh interpreter for each of six required suites, then
checks all 14 competency controls in one fixture run. Install the locked
development dependencies for JSON Schema and SHACL validation. The suites cover
manifest, query, sampler, conversion and evidence-contract behavior with synthetic
inputs. Assessing source fidelity or deployment requires separate evidence.
For measured query runs, select the population and artifact explicitly
with the manifest adapter and retain failed or partial results. Keep large evidence
and generated data outside Git, with hashes and durable availability recorded
where known.

## Wiki

The [wiki](https://github.com/DDMAL/linkedmusic-datalake/wiki) holds Virtuoso
operations, query experiments and cross-cutting reconciliation guidance. Inspect
the relevant page and its revision before proposing changes. Code changes and
wiki publication do not themselves deploy RDF.

## Conventions for new work

- New subprojects follow the `<name>/{src,data,doc,openrefine}/` layout. Add a README at `<name>/README.md` with the same pipeline-stage structure used by AcousticBrainz, Cantus, etc.
- Use the `shared/rdfconv/` converter for new datasets unless the data shape genuinely doesn't fit. Add a config at `shared/rdf_config/<name>.toml` rather than writing a bespoke script.
- `black` is the formatter (in `[tool.poetry.group.dev.dependencies]`). Run before committing Python changes.
