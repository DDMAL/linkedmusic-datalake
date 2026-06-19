# HANDOFF — Wikidata reconciliation (CKG names)

**Written:** 2026-06-17
**For:** the next Claude Code agent picking up CKG reconciliation
**Status:** BLOCKED on a diagnostic mystery (see §3). Do not proceed past it without resolving it.

---

## 0. How to work on this (read first)

- **One task at a time.** This project is run as a sequence of discrete tasks with the user reviewing between each. Do not batch several steps and run them all. Finish a step, report results, wait.
- **Ask the user questions when uncertain.** The user explicitly wants to be consulted. There is a list of open questions for them at the very bottom (§9) — ask those before making irreversible decisions.
- **OpenRefine must run in Chrome** (Firefox/Safari break the RDF-transform extension silently — a repo-wide rule, see root `CLAUDE.md`).
- **All scripts assume CWD = `ckg/src/`.** Run via `poetry run python <script>.py` from there.
- **Never commit data files.** `*.csv`, `*.ttl`, `*.jsonl` are gitignored. Data lives on disk only.
- Reconciliation standard for the whole repo is **Wikidata**, pivoted via `wdt:P2888` (exact-match). This is non-negotiable. See the wiki: `Data-Reconciliation-Guidelines` and `OpenRefine-Tips` (local clone at `/Users/liampond/Documents/GitHub/linkedmusic-datalake.wiki/`, pull it first — it was 396 commits behind).

---

## 1. Project context

We are ingesting the **Culture Knowledge Graph (CKG)** into LinkedMusic for the Hermes *"From Notes to Nodes"* data challenge. **Submission deadline: 2026-06-30.**

CKG combines two feeds:
- **musiconn** (`musiconn.performance`) — a German **historical concert-programme** database. Performers, ensembles, venues, works from documented concerts. *This is the crucial fact for §3: most entities are obscure regional German performers/ensembles.*
- **Detmold** (Detmold court theatre / Hoftheater data).

The pipeline: **fetch → extract → reconcile (against Wikidata) → convert to RDF (Turtle)**. We are in the **reconcile** stage.

Relevant background docs in `ckg/doc/`:
- `INGESTION-PLAN.md` — the master plan.
- `HANDOFF.md` and `HANDOFF-openrefine.md` — earlier handoffs (fetch stage, OpenRefine plan).
- `pid-qid-verification.md`, `predicate-evidence.md`, `musiconn-api-spike.md` — supporting evidence.

Also see the persistent memory note `ckg-hermes-ingestion` and `ckg-converter-model` (in the user's Claude memory) for the data model and crosswalk strategy.

---

## 2. Where we are in the pipeline

**Done (prior sessions):**
- Fetched authority names for all entities that carry a GND / VIAF / GeoNames authority URI (`fetch_authority_names.py`, then `fetch_viaf_fallback.py` for VIAF residue via MusicBrainz URL lookup).
- Produced `ckg/data/openrefine/names_for_reconciliation.csv` — **7,758 rows** (header + 7,758 = 7,759 lines). Columns: `authority_uri, name, name_original, entity_type, scheme`.
  - Wait — the on-disk file has columns `authority_uri, name, entity_type, scheme` (no `name_original`; that column only exists inside the OpenRefine project). Confirm the header before scripting against it.
- `fetch_404s.txt` — **575 irrecoverable** authority URIs (574 VIAF whose backend is down + 1 deleted GND). Accepted as residue.

**In progress (this session):**
- Reconciling the `name` column against Wikidata. Two approaches attempted; see §3 and §4.

**Not started:**
- Task 3: merge reconciled QIDs into `crosswalk.json`, then reconvert both feeds to RDF.
- Task 4: load into production Virtuoso.

---

## 3. ⚠️ THE BLOCKER — resolve this before anything else

We pivoted from OpenRefine to a **direct Wikidata SPARQL lookup** on the authority IDs (we have exact GND/VIAF/GeoNames IDs, so an ID→QID SPARQL lookup is strictly more precise than fuzzy name matching). Script: `ckg/src/wikidata_authority_lookup.py`.

**The problem: the SPARQL lookup returns 0 matches for EVERY ID read from the CSV, across all schemes and entity types** (GND Person 0/300, GND Org 0/300, GND Place 0/300, GND Collection 0/300, VIAF 0/300, GeoNames 0/4).

**BUT hand-typed famous IDs match correctly:**
- `?item wdt:P227 "11850553X"` → **Q1339** (J.S. Bach) ✓
- `?item wdt:P227 "2007744-0"` → **Q707283** (Berliner Philharmoniker) ✓

So the SPARQL query mechanism works. The contradiction is: **hand-typed IDs match; IDs extracted from the CSV never match.** This is the whole mystery.

### Two competing hypotheses (must distinguish before proceeding)

**Hypothesis A — value-format bug (most likely).** The IDs extracted from the CSV differ subtly from clean hand-typed strings — a hidden/zero-width character, trailing whitespace, a BOM on the first column, an encoding artifact, or a wrong split. When interpolated into the SPARQL `VALUES` clause they don't string-match. The fact that *every* CSV-sourced ID fails while hand-typed ones succeed points strongly here.
- **Decisive test:** print `repr()` of an ID extracted from the CSV next to a hand-typed equivalent. Look for any difference. Also `repr()` the raw DictReader keys (a BOM shows up as `﻿` prefixed to the first column name).

**Hypothesis B — genuine near-zero Wikidata coverage.** This is musiconn concert-programme data: obscure regional German performers/ensembles. The d-nb.info record for `10010392-3` (Heinrich-Schütz-Konservatorium Dresden) links to VIAF and LoC but **NOT Wikidata** — real evidence that these entities aren't in Wikidata. Modern 10-digit GND IDs (`1011620472` = "Plešak, Viktor V." etc.) are recently-minted authority records for non-notable people.
- **Counter-evidence against B:** the four GeoNames rows are *major cities* (Aarau, Mannheim, Hamm, Aachen) — Mannheim (~300k people) is certainly in Wikidata with a P1566 GeoNames ID, yet it returned 0. That shouldn't happen under pure low-coverage… UNLESS Wikidata stores a *different* GeoNames ID for Mannheim than the one in our CSV.

### Single most useful next experiment (reverse lookup)

Don't keep sampling forward (ID→QID). Go **backward** to definitively settle A vs B:

1. Pick an entity we are confident is both in the CKG data AND in Wikidata. Good candidates: query Wikidata for the P227 (GND) of a famous German orchestra/venue/person that plausibly appears in concert programmes (e.g. Gewandhausorchester Leipzig, Thomanerchor, a major conductor).
2. Take the GND/VIAF/GeoNames ID **from Wikidata's side**.
3. `grep` that ID in `ckg/data/openrefine/names_for_reconciliation.csv`.
   - **If it's present but in a different textual form** (extra char, different format) → **Hypothesis A confirmed**: fix the extraction/normalization, re-run, done.
   - **If it's genuinely absent from our CSV** → coverage really is low for the slice we tested; broaden the reverse search to estimate the true ceiling.

Also worth: dump 5 raw CSV ID strings to a file and `hexdump -C` them to catch invisible bytes.

---

## 4. What has been tried (so you don't repeat it)

### OpenRefine (partial success — KEEP the person results)
- Loaded the 7,758-row CSV, duplicated `name` → `name_original`, built helper ID columns: `gnd_id`, `viaf_id`, `geonames_id` (GREL regex extraction from `authority_uri`).
- **Person reconciliation succeeded** (type Q5, helper props P227 + P214, auto-match high-confidence on). Exported to **`ckg/openrefine/export/persons_openrefine.csv`** (129 KB) and these flowed into **`ckg/openrefine/export/names_reconciled.csv`** = **362 matched persons**. History saved at `ckg/openrefine/history/ckg-2026-06-17-history.json`.
- **Organization / Place reconciliation FAILED to start** — clicking "Start reconciling" did nothing (silent failure), repeatedly, after Person worked. Tried: removing the P1566 helper, "no particular type", closing/reopening, waiting, single vs. multiple facets. None worked. Root cause never found (possibly the Wikidata reconciliation service rate-limiting / a stuck background job / a browser-session issue). This silent failure is *why* we pivoted to SPARQL.

### SPARQL (`wikidata_authority_lookup.py`) — produced 0, see §3
- GET-based `VALUES` query. Works for hand-typed IDs, returns 0 for all CSV IDs.
- **Known bug to fix regardless:** VIAF batch of 400 IDs via **GET** → **HTTP 431 (Request Header Fields Too Large)** because some VIAF IDs are 19–22 digits long (see length distribution below) and the URL blows past header limits. **Fix: use `requests.post` with `data={'query': q}`** (POST verified working: `application/sparql-results+json` returned correctly). Or shrink VIAF batch size to ~100. Either way, switch the whole script to POST.
- The failed run left near-empty outputs: `names_reconciled_sparql.csv` (header only, 0 rows) and `names_reconciled.csv` (362 rows — *those are the OpenRefine persons that got merged in, NOT SPARQL hits*). Regenerate both once §3 is resolved.

### Authority ID facts discovered
- GND IDs in our data: corporate-body form `10010392-3` (8 digits + hyphen + check) AND modern person form `1011620472` (10 digits) AND older `118505533`/`11850553X`. Wikidata P227 stores the **canonical hyphenated/check-char form verbatim** (`2007744-0`, `11850553X` both match). So our format *looks* correct — reinforcing Hypothesis A (something non-visible is wrong).
- VIAF ID length distribution in our CSV: `{9-digit: 1920, 22-digit: 685, 8-digit: 203, 21-digit: 181, 20-digit: 92, 19-digit: 29, 7-digit: 12}`. The 19–22-digit values are **source-record IDs, not permanent VIAF cluster IDs** — Wikidata P214 stores the permanent cluster ID, so those long ones will never match P214 even after §3 is fixed. Consider resolving long VIAF source IDs to cluster IDs, or accept them as residue.

---

## 5. File inventory (exact, as of 2026-06-17)

| Path | Size / rows | What it is |
|---|---|---|
| `ckg/data/openrefine/names_for_reconciliation.csv` | 7,758 data rows | INPUT. `authority_uri, name, entity_type, scheme`. Verify exact header before scripting. |
| `ckg/data/openrefine/fetch_404s.txt` | 575 | Irrecoverable authority URIs (574 VIAF backend-down + 1 deleted GND). Residue. |
| `ckg/data/openrefine/authority_name_cache.json` | 1.2 MB | Name fetch cache (incl. `mb_lookup:{uri}` keys from the VIAF/MusicBrainz fallback). |
| `ckg/data/openrefine/viaf_via_gnd_resolved.json` | 16 KB | 345 VIAF→GND→QID direct resolutions from the fetch stage (already merged into crosswalk in a prior session — verify). |
| `ckg/data/mappings/crosswalk.json` | ~14,842 entries | The authority_URI → QID crosswalk. Target of Task 3. |
| `ckg/openrefine/export/persons_openrefine.csv` | 129 KB | OpenRefine Person matches. `authority_uri, qid`. **Keep.** |
| `ckg/openrefine/export/names_reconciled.csv` | 362 rows | Currently = the OpenRefine persons (SPARQL added 0). Will be regenerated. |
| `ckg/openrefine/export/names_reconciled_sparql.csv` | 0 rows (header only) | SPARQL output from the failed run. Regenerate. |
| `ckg/openrefine/history/ckg-2026-06-17-history.json` | 3.7 KB | OpenRefine operation history (extract). |

### Entity-type breakdown of the GND slice (for context)
`Collection: 2017, Person: 1441, Organization: 621, Place: 553` (GND total 4,632). VIAF total 3,122. GeoNames 4.

---

## 6. Scripts

| Script (`ckg/src/`) | Purpose | State |
|---|---|---|
| `fetch_authority_names.py` | Original name fetch (lobid GND, lobid sameAs VIAF, GeoNames hard-coded). | Done. Note: lobid can 404 GND IDs that d-nb.info still has — add a d-nb.info fallback if re-run. |
| `fetch_viaf_fallback.py` | VIAF residue via MusicBrainz URL lookup. ~7% hit rate. | Done. Re-run when VIAF backend restored (MB results cached). |
| `wikidata_authority_lookup.py` | NEW. SPARQL ID→QID for P227/P214/P1566, then merges OpenRefine persons. SPARQL results take priority over OpenRefine on conflicts. | **Blocked (§3). Also switch GET→POST (§4).** |
| `merge_openrefine.py` | Reads `ckg/openrefine/export/names_reconciled.csv` (`authority_uri, qid`) → merges into `crosswalk.json`. Accepts plain or `wd:`-prefixed QIDs. `--dry-run` supported. | Ready. Run in Task 3. |
| `convert_to_rdf.py` | Converts a feed to RDF. Usage: `poetry run python convert_to_rdf.py musiconn` / `... detmold`. | Ready. Run in Task 3. |
| `build_crosswalk.py`, `preprocess.py`, `profile_predicate.py` | Supporting. | — |

---

## 7. After §3 is resolved — the remaining tasks

**Task 3 — merge + reconvert** (only after reconciliation output is trustworthy):
1. `cd ckg/src && poetry run python merge_openrefine.py --dry-run` — review additions.
2. Without `--dry-run` to write `crosswalk.json`.
3. `poetry run python convert_to_rdf.py musiconn` and `poetry run python convert_to_rdf.py detmold`.
4. **Verify: 0 blank nodes**, sane triple counts. Report before/after.

**Task 4 — Virtuoso load:** see the memory note `virtuoso-prod-loading` for the runbook (server, paths, graph IRIs, `ld_dir` procedure). Give the user scp + ISQL commands; confirm before running anything outward-facing.

---

## 8. Decisions already locked (don't relitigate)

- Wikidata pivot via `wdt:P2888`. Standard.
- The 575 entries in `fetch_404s.txt` are accepted residue. Do not spend more time recovering them now (VIAF backend is down server-side; unfixable client-side).
- OpenRefine Person matches are kept and supplement SPARQL (OpenRefine catches Wikidata items that lack a recorded authority ID, which SPARQL can't find).

---

## 9. Questions to ask the user (do this early)

1. **On the §3 blocker:** once you've run the reverse-lookup test, tell the user which hypothesis it confirmed and how many matches are realistically achievable. If coverage is genuinely low (Hypothesis B), ask: *is a low Wikidata match rate acceptable for the submission, given this is obscure concert-programme data?* (The unreconciled entities still get emitted as string literals per repo convention.)
2. **Long VIAF IDs (19–22 digits):** confirm whether to resolve them to permanent cluster IDs or accept as residue.
3. **OpenRefine org/place failure:** does the user want to retry OpenRefine for orgs/places in a fresh browser session, or rely entirely on the (fixed) SPARQL path?
4. Anything ambiguous about the data model — defer to the user and the memory notes rather than guessing.

**Tell the user: if anything here is unclear, ask before proceeding.** This is a deadline-bound submission (2026-06-30) and the user reviews each step.
