# CLAUDE.md

Context for Claude Code working in the `linkedmusic-datalake` monorepo. Per-subproject READMEs are authoritative — read the relevant one before touching that subproject.

For preservation/evaluation work, read [LINKEDMUSIC-HANDOFF.md](LINKEDMUSIC-HANDOFF.md)
first and update it after each completed task with changes, actual validation,
review findings, publication/deployment status, limitations and next work.
The [root README](README.md#preservation-and-evaluation-status) indexes the
current contracts. Source snapshots, regeneration and production deployment
remain deferred until Liam confirms access; synthetic tests do not replace them.

## What this repo is

A data-ingestion monorepo with one pipeline per dataset; see the [dataset list](README.md#datasets). The nominal pipeline is **fetch → extract → reconcile → convert to RDF Turtle**, with OpenRefine, source-supplied links or authority crosswalks depending on the source. AcousticBrainz and RELICS work lives on separate feature branches and is not present in this checkout.

## Environment

- Python **3.12**, Poetry-managed at the repo root. One venv for everything; no per-subproject envs.
- Install: `poetry install`. Run scripts via `poetry run python …` or from an activated shell.
- **Most scripts assume CWD is the subproject's `src/` folder** (paths are relative to it). For DIAMM, use `cd diamm/src && poetry run python convert_rdf.py`. Check the subproject README before assuming otherwise.
- Offline validation from the root: `poetry run python scripts/check_offline.py`. It runs shared CSV/mapping, RISM, MusicBrainz, DIAMM, APSearch and evaluation suites, followed by 14 competency fixture queries; no source dumps or services are required.

## Data is not in the repo

`.gitignore` excludes `*.ttl`, `*.csv`, `*.jsonl`, `*.tar*`, `*.xz`, `store/`, `store-*/`. Every subproject's `data/{archived,extracted,unreconciled,reconciled,rdf}/` lives on disk but is untracked. **Never commit data files.** Some datasets are huge (AcousticBrainz extracted highlevel is ~129 GB).

Tracked synthetic fixtures under `evaluation/fixtures/` are query controls, not
source dumps. Ignored `evaluation/audits/` holds local evidence; it is not
transferred with Git and is not required by offline tests.

## `shared/`

Reusable code lives here, but it is **not a package** — there's no install step. Import by path or by running as a module from `/shared`:

- `shared/rdfconv/` — generic config-driven RDF converter. Run as `cd shared && python -m rdfconv.convert <config.toml>`. Configs live in `shared/rdf_config/` (one per subproject).
- `shared/wikidata_utils/client.py` — Wikidata API client used during reconciliation.
- Other scripts in `shared/` (`prop_cli.py`, `get_relations.py`) are utilities, not currently imported by subprojects.

## Subproject quirks (the non-obvious stuff)

- **RISM** starts from RDF (not CSV). It splits via `force_split.py`, reconciles in OpenRefine using the **RDF-transform** extension, then re-emits Turtle. RDF-transform **only works in Chrome** — Firefox/Safari will fail silently.
- **MusicBrainz** consumes JSONL and supplied Wikidata URL relationships; auxiliary type/key/gender/language/packaging/status CSVs use OpenRefine. Keep field/type lookups isolated. The 33-role pilot retains specific predicates and observations; broad-contributor queries explicitly select the matching schema graph.
- **SIMSSA** has a shared CSV-to-Turtle config at `shared/rdf_config/simssadb.toml` and older JSON-LD files. The person mapping is tested; historical deployment of that route is unverified. Preserve original names and require canonical item IRIs for person P2888.
- **DIAMM** uses bespoke extraction and RDF conversion. Its contracts cover year/approximation observations, original person names/floruit, complete archive/person identifier lists, external-ID strings, archive names/sigla, geographic names and organization/region locations. The new region route uses `diamm:organizationLocation`; do not infer manuscript locations through organizations. Qualified city/region provenance is next; parent types need source evidence. Country matching hints do not create RDF relationships.
- **CKG** (NFDI4Culture Culture Knowledge Graph) is **RDF-native** (per-feed N-Triples dumps, no fetch step) and is split into **three sibling subprojects** — `ckg-musiconn/`, `ckg-detmold/`, `ckg-apsearch/` — one per feed, because each loads as its own Virtuoso named graph. They **share one pipeline, copied verbatim** into each `src/` (the scripts take a feed argument, so the copies are identical and overlap is intentional). Reconciliation is a **deterministic authority-ID→Wikidata crosswalk** (GND `P227` / VIAF `P214` / GeoNames `P1566`), with OpenRefine only for the residue (musiconn/Detmold; APSearch needs none). The CKG's RISM feed (`E5313`) is excluded — LinkedMusic ingests RISM separately. Each feed's `doc/data-model.md` is the authoritative mapping/schema doc.
- **APSearch creation periods** retain original CTO assertions and paired year bounds on named observations; P571 is only a supported start-year projection. Keep all three CKG converter/config copies identical.
- **Shared CSV datasets** use explicit literal declarations for text that may resemble IDs. Whole-ID recognition does not change existing missing-value parsing or conditional mapping omissions. Global Jukebox's 19 social-factor alternative-name columns are `skos:altLabel` strings.

## OpenRefine state

For subprojects that reconcile in OpenRefine, history and export files live under `<subproject>/openrefine/{history,export}/`. Filenames are inconsistent across subprojects (some `_history` / `_export` suffixed, some not, some hyphenated, some underscored). **Do not bulk-rename** without asking — these are referenced manually during reconciliation runs.

## Branches and stashes

- Work happens on per-subproject feature branches (`acousticbrainz`, `relics`, `simssadb-ingestion`, `nlq2sparql-api`, etc.) merged into `main` via PR.
- Inspect existing stashes before using them; their numeric positions can change. Do not drop stashes without checking with the user. The RISM identifier repair is already implemented in this branch.
- Check `git status` and the handoff for the current task. As of 29 October 2026, work is on `preservation-repairs-2026-10-21`; draft PR #473 includes geographic repairs `df7854fe` and `6df2c7a6` after the earlier repairs/documentation. The wiki status updates are also published. Remote `main` requires a pull request; the PR remains unmerged and RDF deployment is separate.

## Wiki

The sibling `../linkedmusic-datalake.wiki/` is a separate Git repository. It holds Virtuoso operations, query guidance and cross-cutting reconciliation/modeling policy. Keep its documentation consistent with local converter contracts, distinguishing historical deployed diagrams/counts from candidate models.

## Conventions for new work

- New subprojects follow the `<name>/{src,data,doc,openrefine}/` layout. Add a README at `<name>/README.md` with the pipeline-stage structure used by existing datasets.
- Use the `shared/rdfconv/` converter for new datasets unless the data shape genuinely doesn't fit. Add a config at `shared/rdf_config/<name>.toml` rather than writing a bespoke script.
- `black` is the formatter (in `[tool.poetry.group.dev.dependencies]`). Run before committing Python changes.
