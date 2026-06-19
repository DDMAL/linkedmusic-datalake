# CKG ingestion — handoff (musiconn + Detmold OpenRefine pass)

You are continuing the **CKG → LinkedMusic** ingestion for the Hermes "From Notes to
Nodes" data challenge (submission due **2026-06-30**). Two feeds — **musiconn** (`E5320`)
and **Detmold** (`E5305`) — are converted and staged but **not yet loaded** into
Virtuoso, and their residue (authority IDs that didn't crosswalk) needs an OpenRefine
reconciliation pass before loading. **APSearch (`E6304`) is a separate, lower-priority
to-do — do not start it here; notes are at the end.**

Do **one task at a time in order** and stop to report after each one.

---

## 0. Get oriented first (read in this order)

1. **`CLAUDE.md`** (repo root) — monorepo house rules. Non-negotiable:
   **no blank nodes in output**, **Wikidata pivot via `wdt:P2888`**, **never commit data
   files**, run via `poetry run python …` (Python 3.12, one Poetry env at the repo root).
2. **`ckg/README.md`** — the pipeline and its 3-command-per-feed workflow.
3. **`ckg/doc/INGESTION-PLAN.md`** — stage-by-stage spec (§4), property mapping (§5).
4. **`ckg/doc/predicate-evidence.md`** — §4 is the authoritative mapping table.
5. **`ckg/doc/pid-qid-verification.md`** — every manually verified PID and QID; includes
   known errors that were corrected. **Cross-check here before using any P/Q ID.**
6. Your recalled **memories** (`ckg-hermes-ingestion`, **`ckg-converter-model`** — trust
   these over the evidence sheet where they differ; they have post-Detmold refinements).
7. Skim **`ckg/src/`**: `preprocess.py` (B), `build_crosswalk.py` (C),
   `convert_to_rdf.py` (E), and `ckg/src/ontology/mapping.json`.

**All CKG scripts assume CWD = `ckg/src/`.**

---

## 1. Current state

### What's converted and staged
- **musiconn** (~1.58M triples, 0 blank nodes) — `raw_data/ckg-musiconn/{musiconn.ttl, global.graph}`
- **Detmold** (~14,800 triples, 0 blank nodes) — `raw_data/ckg-detmold/{detmold.ttl, global.graph}`
- These are valid TTLs. The user loads Virtuoso themselves; **do not attempt the load.**

### What's NOT in Virtuoso yet
CKG graphs are confirmed not yet loaded as of 2026-06-15. The server is at
`134.87.8.241` (SSH alias `virtuoso`), Virtuoso runs in Docker container `my_virtdb`.
Loading instructions are in `memory/virtuoso-prod-loading.md`.

### The reconciliation gap

The **crosswalk** (`ckg/data/mappings/crosswalk.json`) maps `authority_URI → QID`.
It currently has **14,497 entries, all with QIDs** — only successful matches are stored;
failures are simply absent.

**musiconn residue:** 8,651 GND/VIAF authority URIs present in
`ckg/data/extracted/musiconn.authorities.json` but absent from `crosswalk.json`.
Breakdown: GND ~4,610 unresolved of 12,108, VIAF ~4,041 unresolved of 10,592
(≈38% overall miss rate — expected, documented in the plan as risk #2).

**Detmold residue:** very small — ~23 GND persons + ~1 VIAF person + ~4 GeoNames
places = ≈28 entities (out of 608 total; 95.5% already resolved).

**Critical:** the CKG entity bnodes carry **only** the authority URI (GND/VIAF/GeoNames
ID) and a type — **no names or labels whatsoever**. The raw NT file has no `rdfs:label`
either. You cannot do name-based OpenRefine reconciliation without first fetching names
from the authority services.

### Bare source-URI residue (separate track — do NOT handle here)
There are also ~45k+ bare `performance.musiconn.de/person|location|corporation/…`
source URIs in the musiconn graph with no authority ID. Their slug pages return empty
HTML (200 but no data). These are deferred to **Track 2 HTML scraping** (see §5).

---

## 2. TASK 1 — Fetch names from authority APIs

Write and run `ckg/src/fetch_authority_names.py`. It should:

1. Read `ckg/data/extracted/musiconn.authorities.json` and
   `ckg/data/extracted/detmold.authorities.json`.
2. Collect all GND IDs, VIAF IDs, and GeoNames IDs.
3. Subtract those already in `crosswalk.json` (already resolved — no need to fetch).
4. For each remaining ID, call the appropriate API to retrieve the preferred name and
   entity type, then write a CSV: `ckg/data/openrefine/names_for_reconciliation.csv`
   with columns:
   ```
   authority_uri, name, entity_type, scheme
   ```
   where `entity_type` is one of `Person`, `Organization`, `Place`, `Collection`.

### API endpoints

**GND (lobid.org JSON API — cleaner than d-nb.info directly):**
```
GET https://lobid.org/gnd/{id}.json
Accept: application/json
User-Agent: LinkedMusic-datalake/1.0 (liam.pond@mail.mcgill.ca)
```
Key response fields:
- `preferredName` — the canonical name string
- `type` — list of GND entity types (e.g. `["Person", "AuthorityResource"]`)
- If the ID doesn't exist: HTTP 404 → skip

**VIAF (JSON API):**
```
GET http://viaf.org/viaf/{id}/viaf.json
User-Agent: LinkedMusic-datalake/1.0 (liam.pond@mail.mcgill.ca)
```
Key response fields:
- `ns2:mainHeadingEl` or the `mainEntry` key — name string (VIAF JSON is nested and
  inconsistent; parse defensively with `.get()` chains)
- Alternatively use the simpler VIAF suggest endpoint for name lookup by ID

**GeoNames (Detmold only — 4 places):**
```
GET http://api.geonames.org/getJSON?geonameId={id}&username=<username>
```
Requires a free GeoNames API account. Key field: `name` (official name) or
`toponymName`. If this is too much friction for 4 entries, look up the 4 names
manually and hard-code them.

### Rate limiting
- Lobid GND: polite 1–2 req/s, they handle it fine
- VIAF: 1 req/s, retry on 429/503 with exponential backoff
- Cache to disk as you go (`ckg/data/openrefine/authority_name_cache.json`) so a
  restart doesn't re-fetch

### Expected output size
≈ 8,651 musiconn rows + ≈28 Detmold rows. Some GND/VIAF IDs may genuinely 404 (the
entity was deleted from the authority file). Skip 404s and log them separately.

---

## 3. TASK 2 — OpenRefine reconciliation

**OpenRefine setup:**
- Use **Chrome** — the RDF-transform extension **fails silently in Firefox and Safari**.
- Download OpenRefine + the RDF-transform extension if not already installed.
  - RDF-transform: https://github.com/AtesComp/rdf-transform
  - Compatible version: check the RDF-transform README for the matching OpenRefine version.

**Process (follows the RISM precedent used in this repo):**

1. Open OpenRefine (localhost:3333 by default).
2. Create a new project from `ckg/data/openrefine/names_for_reconciliation.csv`.
3. On the `name` column → **Reconcile → Start reconciling** →
   select the **Wikidata** reconciliation service.
4. For each entity type, reconcile with the appropriate Wikidata class constraint:
   - `Person` → Q5 (human)
   - `Organization` → Q43229 (organization) 
   - `Place` → Q618123 (geographical feature) or Q17334923 (location)
   Pass the `authority_uri` as an additional property if the service supports
   identifier lookup (GND→P227, VIAF→P214) — this dramatically improves precision.
5. Work through the results: accept auto-matched entries, manually judge uncertain ones.
   The wiki reconciliation guidelines
   (`Guidelines-or-suggestions-for-data-reconciliation-*.md`) are authoritative —
   read §1 (Q and P basics) and §5.1 (prefer smaller QID numbers when ambiguous).
6. After reconciling, export:
   - **History file** → `ckg/openrefine/history/<feed>-<date>-history.json`
   - **Export** the matched QIDs as CSV: `ckg/openrefine/export/names_reconciled.csv`
     with columns `authority_uri, qid` (just the two columns needed to update the
     crosswalk). Format `qid` as plain `Q12345` (no `wd:` prefix — the merge script
     will add it).

---

## 4. TASK 3 — Merge reconciliation results + reconvert

Write a small script `ckg/src/merge_openrefine.py` (or do it inline) that:

1. Reads `ckg/openrefine/export/names_reconciled.csv`.
2. For each `(authority_uri, qid)` row, adds/updates the entry in
   `ckg/data/mappings/crosswalk.json`.
3. Saves `crosswalk.json` back.

Then reconvert both feeds:
```bash
# From ckg/src/
poetry run python convert_to_rdf.py musiconn
poetry run python convert_to_rdf.py detmold
```

Verify:
```bash
grep -c '_:' data/rdf/musiconn.ttl   # MUST be 0
grep -c '_:' data/rdf/detmold.ttl    # MUST be 0
poetry run python -c "from rdflib import Graph; g=Graph(); g.parse('data/rdf/musiconn.ttl',format='turtle'); print(len(g))"
poetry run python -c "from rdflib import Graph; g=Graph(); g.parse('data/rdf/detmold.ttl',format='turtle'); print(len(g))"
```

Also confirm the new triple count is larger than before (new P2888 pivots added) and
spot-check a few newly reconciled items.

Then re-stage:
```bash
mv data/rdf/musiconn.ttl ../../raw_data/ckg-musiconn/musiconn.ttl
mv data/rdf/detmold.ttl ../../raw_data/ckg-detmold/detmold.ttl
```

---

## 5. TASK 4 — Tell the user to load Virtuoso

Once staging is done, report the new triple counts and reconciliation improvement rate,
then give the user these instructions (they load Virtuoso themselves):

```bash
# On laptop: scp staged dirs to prod server
# (mkdir + chown on server first so scp can land files)
ssh virtuoso "sudo mkdir -p /srv/virtuoso/my_virtdb/data/ckg-musiconn /srv/virtuoso/my_virtdb/data/ckg-detmold && sudo chown ubuntu:ubuntu /srv/virtuoso/my_virtdb/data/ckg-musiconn /srv/virtuoso/my_virtdb/data/ckg-detmold"
scp raw_data/ckg-musiconn/musiconn.ttl ubuntu@134.87.8.241:/srv/virtuoso/my_virtdb/data/ckg-musiconn/
scp raw_data/ckg-detmold/detmold.ttl ubuntu@134.87.8.241:/srv/virtuoso/my_virtdb/data/ckg-detmold/
```

Then in Virtuoso ISQL (run inside tmux on server):
```sql
ld_dir('/database/data/ckg-musiconn', '*.ttl', 'https://linkedmusic.ca/graphs/ckg-musiconn/');
ld_dir('/database/data/ckg-detmold', '*.ttl', 'https://linkedmusic.ca/graphs/ckg-detmold/');
rdf_loader_run();   -- silent while working; don't type into session
checkpoint;
-- Verify:
SELECT COUNT(*) FROM DB.DBA.LOAD_LIST WHERE ll_error IS NOT NULL;
SPARQL SELECT (COUNT(*) AS ?n) WHERE { GRAPH <https://linkedmusic.ca/graphs/ckg-musiconn/> {?s ?p ?o} };
SPARQL SELECT (COUNT(*) AS ?n) WHERE { GRAPH <https://linkedmusic.ca/graphs/ckg-detmold/> {?s ?p ?o} };
-- Reindex for full-text search:
DB.DBA.VT_INC_INDEX_DB_DBA_RDF_OBJ();
DB.DBA.urilbl_ac_init_db();
```

---

## 6. Deferred: APSearch (`E6304`) — do not start here

APSearch has **not been processed at all** — `raw_data/ckg-apsearch/` is empty.
Key notes for when it's tackled:

- Raw dump at `raw_data/ckg/mnt/data/culture-kg-kitchen/data/production/E6304/nt/E6304.nt`
- **Profile first:** `poetry run python profile_predicate.py ../../raw_data/ckg/…/E6304.nt --top 40`
- It's a media feed (audio/image objects), different shape from musiconn/Detmold.
  - Record type via `CTO_0001049` (non-AAT media classes) → hand-add to `record_types.json`
  - Content URLs sit on associatedMedia bnodes → need `preprocess.py` extension
  - ~0% authority crosswalk → OpenRefine is the primary reconciliation path
- Full task description in `ckg/doc/HANDOFF.md` §TASK 2.

---

## 7. Deferred: Track 2 bare source-URI residue + role enrichment

The ~45k+ bare `performance.musiconn.de/person|location|corporation/…` entities in
musiconn have no authority IDs and their slug pages return empty HTML. These are
deferred to the Track-2 HTML scraper (`ckg/src/fetch_musiconn.py`, not yet written):
- Scrape event pages → extract person names + roles
- Match to QIDs via the Wikidata ID shown on the person's numeric-ID page
- Spike findings and scraper design in `ckg/doc/musiconn-api-spike.md`
- Role mapping and verified PIDs/QIDs in `ckg/doc/pid-qid-verification.md`

---

## 8. Key decisions and gotchas (critical — read before touching anything)

### Pipeline
- **CWD = `ckg/src/`** for all scripts. Paths are relative to it.
- Run scripts via `poetry run python …` (repo-root Poetry env, Python 3.12).
- `black` does not run here (Python 3.12.5 ↔ Black incompatibility). Write in Black
  style (4-space indent, double quotes, ≤88 cols) and skip it.
- **Never commit data files** (all `ckg/data/` and `raw_data/` are gitignored).

### Crosswalk
- `ckg/data/mappings/crosswalk.json` maps `{authority_URI → QID}` — it is **shared
  across all feeds** and **additive**. Always merge into it, never replace it.
- `ckg/data/mappings/record_types.json` maps `{classifier_URI → QID}` — same pattern.
- The crosswalk only stores successes; absences = unresolved residue.

### Converter model (settled decisions — do not re-litigate)
- **No blank nodes** in output. Zero tolerance — verify with `grep -c '_:'`.
- **No synthetic labels** for unreconciled entities — only source-derived titles.
- Residue nodes (no QID) are kept as raw URIs with local `rdf:type` but no `P2888`.
- `NFDI_0001008` → **drop** in every feed (self-referential in all feeds).
- `CTO_0001025` is-about bnode → **drop** (used only for typing, never a triple).
- Two record-typing paths:
  1. **Classifier path** (musiconn + APSearch-media): `CTO_0001026` AAT → `crosswalk`
  2. **Classifier-less fallback** (Detmold + APSearch non-classifier): `RECORD_KIND_P31`
     in `convert_to_rdf.py`, keyed on record kind. Currently `{"Work": "Q838948"}`.

### OpenRefine
- **Chrome only** — the RDF-transform extension fails silently in Firefox and Safari.
- History → `ckg/openrefine/history/`. Export → `ckg/openrefine/export/`.
- Prefer smaller QID/PID numbers when two candidates are equivalent (wiki §5.1).
- All manually chosen PIDs/QIDs must be added to `ckg/doc/pid-qid-verification.md`
  with the Wikidata source URL and date verified.

### Staging convention (must match exactly)
```
raw_data/ckg-<feed>/<feed>.ttl
raw_data/ckg-<feed>/global.graph    ← one line: https://linkedmusic.ca/graphs/ckg-<feed>/
```
Match the trailing slash and single newline in `global.graph`.

### Graph IRIs
| Feed | Graph IRI |
|---|---|
| musiconn | `https://linkedmusic.ca/graphs/ckg-musiconn/` |
| Detmold | `https://linkedmusic.ca/graphs/ckg-detmold/` |
| APSearch | `https://linkedmusic.ca/graphs/ckg-apsearch/` |
| musiconn roles (Track 2) | `https://linkedmusic.ca/graphs/musiconn/` |

### Virtuoso prod server
- SSH: `virtuoso` alias → `ubuntu@134.87.8.241`. Container: `my_virtdb`.
- Data path: host `/srv/virtuoso/my_virtdb/data/<dataset>/` = container `/database/data/<dataset>/`.
- Files must be scp'd there; the container's virtuoso user (uid 65532) owns the dir —
  mkdir+chown as ubuntu before scp.
- The user runs ISQL loads themselves. Do not attempt loads.
