# CKG ingestion — handoff (continue after musiconn + Detmold)

You are continuing the **CKG → LinkedMusic** ingestion for the Hermes "From Notes to
Nodes" data challenge (submission due **2026-06-30**). Two Track-1 vertical slices —
**musiconn** (`E5320`) and **Detmold** (`E5305`) — are **done, validated, and staged for
loading**. Your job is the next two tasks, **one at a time, in this order**:

1. **Track 2 — F0 spike** (musiconn native-API feasibility check) ⟵ do this first
2. **APSearch** (`E6304`) — Track 1 spine, but a *different shape* (media feed)

Do **one task, then stop and report.** The user will re-handoff if context runs long.
Don't start the next task in the same turn unless explicitly told to.

---

## 0. Get oriented first (read in this order)

1. **`CLAUDE.md`** (repo root) — monorepo house rules. Non-negotiable for this work:
   **no blank nodes in output**, **Wikidata pivot via `wdt:P2888`**, **never commit data
   files**, run via `poetry run python …` (Python 3.12, one Poetry env at the repo root).
2. **`ckg/README.md`** — the pipeline, the 3-command-per-feed workflow, the graph IRIs.
3. **`ckg/doc/INGESTION-PLAN.md`** — the full plan (stages A–H, scope, risks). §4 is the
   stage-by-stage spec; §5 the property mapping; §7 the milestones; §8 risks (the F0 spike
   is **risk #1**).
4. **`ckg/doc/predicate-evidence.md`** — the evidence behind every mapping decision. §4 is
   the authoritative mapping table. It has been kept current through Detmold (NFDI_0001008,
   CTO_0001073 intervals, GeoNames, the Detmold record-type row).
5. Your recalled **memories** carry the settled decisions and the load runbook:
   `ckg-hermes-ingestion` (scope/strategy), **`ckg-converter-model`** (the corrected Stage E
   model — **trust this over the evidence sheet where they differ**; it has the musiconn +
   Detmold refinements), `virtuoso-prod-loading` (the load runbook).
6. Skim the four scripts in **`ckg/src/`**: `profile_predicate.py` (Stage A profiler),
   `preprocess.py` (B), `build_crosswalk.py` (C), `convert_to_rdf.py` (E), and
   `ckg/src/ontology/mapping.json` (the runtime predicate map).
7. Cross-cutting infra/query context (Virtuoso ops, SESEMMI) lives in the sibling wiki at
   `/Users/liampond/Documents/GitHub/linkedmusic-datalake.wiki` — check there before grepping.

**All CKG scripts assume CWD = `ckg/src/`.** Raw dumps (gitignored):
`raw_data/ckg/mnt/data/culture-kg-kitchen/data/production/<E####>/nt/<E####>.nt`.
Feed map: musiconn=`E5320`, Detmold=`E5305`, **APSearch=`E6304`** (RISM=`E5313` excluded —
LinkedMusic ingests RISM separately).

---

## 1. Current state (what's already done)

- **musiconn fully converted** (~1.58M triples, 0 blank nodes, parses in rdflib) — staged at
  `raw_data/ckg-musiconn/{musiconn.ttl,global.graph}` → `https://linkedmusic.ca/graphs/ckg-musiconn/`.
- **Detmold fully converted** (31,460 → **14,800** triples, 0 blank nodes, parses in rdflib) —
  staged at `raw_data/ckg-detmold/{detmold.ttl,global.graph}` → `https://linkedmusic.ca/graphs/ckg-detmold/`.
  - Records → `lmckg:Work` + `wdt:P31 wd:Q838948` (work of art); 580 P2888 pivots; dates coerced.
- **The user loads Virtuoso themselves** (don't attempt the load).
- **Shared, re-runnable caches** in `ckg/data/mappings/` (used by the converter, merged across feeds):
  - `crosswalk.json` — `{authority_URI → QID}`, currently ~14,497 entries (musiconn + Detmold).
  - `record_types.json` — `{classifier_URI → QID}`: `aat:300262956→Q6942562` (musical performance),
    `aat:300417577→Q207628` (composed musical work). **You will hand-add APSearch's media classes here.**
- **Stage B/C outputs** for musiconn + Detmold in `ckg/data/extracted/`.

### Coverage so far (the real reconciliation rates — report yours too; risk #2)
- **musiconn**: ~62% of distinct authorities (GND 61.9%, VIAF 61.8%); relation-weighted person 79.1%,
  location 54.2%, org 47.7%. Residue is expected and fine — OpenRefine/Track-2 can reconcile some later.
- **Detmold**: persons GND 464/487 + VIAF 82/83 (≈95.8%); places GeoNames 34/38 (89.5%); total 580/608.

---

## 2. The pipeline + critical things learned (read before touching a new feed)

**The 3 commands per feed** (from `ckg/src/`):
```bash
poetry run python preprocess.py     <feed>   # B: normalize typos, build indexes -> data/extracted/
poetry run python build_crosswalk.py <feed>  # C: GND/VIAF/GeoNames->QID + AAT types -> data/mappings/ (merged)
poetry run python convert_to_rdf.py <feed>   # E: NT->TTL -> data/rdf/<feed>.ttl
```

**Gotchas (these will save you time):**

- **PROFILE EVERY NEW FEED FIRST.** The scripts were built/validated on musiconn + Detmold.
  Run `poetry run python profile_predicate.py <feed.nt> --top 40`, then for any relation/typed/
  date predicate, `--predicate <substr>` (deep mode: subject-type dist, object kinds, hosts,
  co-occurring predicates, samples). **Do not assume musiconn's or Detmold's shape carries over.**

- **The relation model has two shapes:**
  (a) *authority blank nodes* (typed `NFDI_0000003/4/5/107` + one `NFDI_0001006` GND/VIAF/GeoNames) →
  collapsed to the authority URI, typed `lmckg:*`, `+P2888` when reconciled; and
  (b) *bare source-URI residue* (e.g. `performance.musiconn.de/…` with no authority) → kept as a
  residue node, typed from the relation, **no P2888**. `preprocess.py` indexes (a); `convert_to_rdf.py`
  handles (b) inline via `entity_class` in `mapping.json`. **Keep all residue** (user-confirmed);
  it's the OpenRefine/Track-2 target. **No synthetic labels** for unreconciled nodes (user-confirmed).
  (Detmold happens to have **0** residue — all its relations point to bnodes.)

- **Record typing differs per feed — there are now TWO P31 paths:**
  1. *Classifier path* (musiconn, APSearch-media): `CTO_0001026` (AAT) → `classifier_aat`, or
     `CTO_0001049` (CTO media class) → `classifier_media`. `build_crosswalk.py` resolves AAT codes
     automatically (P1014); **non-AAT classifiers (CTO media classes) it only warns about — you
     hand-add them to `record_types.json`** with verified QIDs.
  2. *Classifier-less fallback* (Detmold): records whose is-about bnode is the generic
     `schema:CreativeWork` and which carry **no** classifier get their `wdt:P31` from
     **`RECORD_KIND_P31`** in `convert_to_rdf.py`, keyed on the record *kind*, emitted **only when
     `s not in record_classifier`**. Currently `{"Work": "Q838948"}` (work of art). `preprocess.py`
     maps `schema:CreativeWork → "Work"`. **APSearch hits the same `CreativeWork` gap** (see Task 2).

- **`record_types.json`, `mapping.json`, `crosswalk.json` are shared and additive.** Extend them
  for a new feed (and note the reasoning in `predicate-evidence.md`); don't fork. **Any shared change
  must be feed-conditional or generic so musiconn + Detmold still reconvert identically.** (Verify the
  precondition: e.g. musiconn has 0 `schema:CreativeWork` and 0 GeoNames, so the Detmold-era changes
  don't touch it.)

- **Crosswalk WDQS limits**: the shared client GETs the query in the URL, so `BATCH=150` (bigger →
  HTTP 431) and `RETRIES`/low concurrency absorb 429s (you *will* see the occasional 429 — the retry
  handles it). Already tuned in `build_crosswalk.py`; don't raise the batch size. `SCHEME_PROP` now has
  `gnd→P227, viaf→P214, geonames→P1566`.

- **Dates**: `coerce_date` in `convert_to_rdf.py` handles `YYYY-MM-DD`, musiconn's `-00` placeholders
  (→ `gYearMonth`/`gYear`), bare `YYYY`, **and Detmold's `schema:DateTime START/END` intervals**
  (same day→`xsd:date`, full month→`gYearMonth`, full year→`gYear`). Profile a new feed's date
  predicates; extend `coerce_date` only with a branch that can't change existing feeds' output.

- **`black` will not run** here (Python 3.12.5 ↔ Black incompatibility). Write in Black style
  (4-space, double quotes, ≤88–100 cols) and skip it.

- **Staging for the user's Virtuoso load** (after a feed converts & verifies):
  ```bash
  mkdir -p raw_data/ckg-<feed>
  mv ckg/data/rdf/<feed>.ttl raw_data/ckg-<feed>/
  printf 'https://linkedmusic.ca/graphs/ckg-<feed>/\n' > raw_data/ckg-<feed>/global.graph
  ```
  Match the convention exactly (see `raw_data/diamm/` and `raw_data/ckg-detmold/`): one `<feed>.ttl`
  + one `global.graph` holding the IRI with a trailing slash and a single newline.

**Verification checklist (run for every feed's TTL):**
```bash
grep -c '_:' data/rdf/<feed>.ttl                 # MUST be 0 (no blank nodes)
poetry run python -c "from rdflib import Graph; g=Graph(); g.parse('data/rdf/<feed>.ttl',format='turtle'); print(len(g))"
```
Also confirm: every record has a local `rdf:type lmckg:*` + (where applicable) one `wdt:P31`; every
relation object carries an `rdf:type lmckg:*`; dates are `xsd:date`/`gYearMonth`/`gYear`; spot-check a
few `P2888` targets resolve to the right Wikidata items.

### What changed during the Detmold pass (so you know the current script state)
- `preprocess.py`: `EVENT_WORK_KIND` gained `schema:CreativeWork → "Work"`; `authority_id()` +
  `auth_uris` + authorities.json now capture a **`geonames`** bucket.
- `build_crosswalk.py`: `SCHEME_PROP` gained `geonames → P1566`.
- `convert_to_rdf.py`: added `RECORD_KIND_P31` + a classifier-less P31 fallback in the `type` action;
  `coerce_date` extended for `schema:DateTime` intervals.
- `mapping.json`: `NFDI_0001008` changed from `url_permalink`/P973 to **`drop`** (it's self-referential
  in *every* feed — the object literal equals the record's own subject IRI; the original plan's guess
  that Detmold's was an external permalink was wrong). The `url_permalink` action handler is retained
  but currently unused.

---

## TASK 1 — Track 2 F0 spike (musiconn native API)  ⟵ do this first

A **throwaway feasibility check** (not production code), the highest-risk item in the plan (risk #1).
Goal: confirm the native musiconn API exposes what CKG flattened away (CKG collapses every
performer/composer/conductor relation to a role-agnostic "has related person", dropping the role).

**Confirm three things** for a handful of events:
1. per-event person **roles / voice-types** are exposed (composer/performer/conductor/…);
2. person **names** are available;
3. records are addressable by the **same permalink** we use as the record URI
   (e.g. `https://performance.musiconn.de/event/<slug>`).

**How:** the API base appears in the data as `https://performance.musiconn.de/api` (the dropped
`CTO_0001080` values). Pick a few real event permalinks from `ckg/data/extracted/musiconn.norm.nt`
(subjects under `…/event/`), probe the API (the "musiconn.performance" project — likely JSON), and
inspect the response for roles/names + how to join by permalink. Be polite: a few requests, low rate,
set a `User-Agent` (use `liam.pond@mail.mcgill.ca`, matching the crosswalk client). **Hitting an
external service — keep it to a tiny probe and tell the user before any larger fetch.**

**Deliverable:** a short findings note `ckg/doc/musiconn-api-spike.md`: can roles be recovered? what's
the API shape and join key? If **yes**, sketch `fetch_musiconn.py` (emit a parallel graph
`https://linkedmusic.ca/graphs/musiconn/` keyed on the permalink; model roles with Wikidata props where
faithful — composer `P86`, performer `P175`, conductor `P3300`, librettist `P87` — else
`participant P710` + `object has role P3831`). If **no**, say so plainly → Track 2 falls back to
spine-only (still on-brief). **Then stop.**

---

## TASK 2 — APSearch (`E6304`)  ⟵ do this second

The **separate, different-shaped track**: a media/content feed. **No persons, no relational backbone,
~0% authority crosswalk** → not role recovery; it needs media handling and (a little) label
reconciliation. **What was profiled earlier (re-profile to confirm — it predates the Detmold scripts):**

- 6,271 records (`CTO_0001005`); is-about bnodes are `schema:CreativeWork` (so `record_kind` would be
  empty without the fix — **but the Detmold pass already added `schema:CreativeWork → "Work"` to
  `preprocess.py`, so APSearch records now kind as "Work" automatically**). Decide whether
  `RECORD_KIND_P31["Work"] = Q838948` is right for APSearch's media records, or whether APSearch
  records should be typed by their **media class** instead (most APSearch records carry a classifier —
  see next bullet — so they take the *classifier* P31 path, not the `RECORD_KIND_P31` fallback).
- **Record type via `CTO_0001049`** "has data concept" (~4,012) → CTO media classes (`CTO_0001043`
  audio, `CTO_0001044` image). These are **NOT AAT**, so `build_crosswalk.py` **warns and skips them** —
  you must **hand-add** them to `record_types.json` with verified QIDs (plan §5: audio → a
  sound-recording QID; image → `Q478798`, verify both via Wikidata). The converter's `classifier_media`
  action already emits `P31` from `record_types[<media-class>]`. Also: ~260 records carry `CTO_0001026`
  (AAT) — `build_crosswalk.py` resolves those automatically.
- **Content URLs need a bnode traversal (converter work):** `schema:associatedMedia` (~3,783, bnode) +
  `CTO_0001021` (content url →P953, ~3,783) co-occur — the content URL almost certainly sits on the
  *associatedMedia media bnode* (typed `AudioObject`/`ImageObject`/`MediaObject`), **not on the record**.
  The current converter **skips bnode subjects**, so as written **the P953 content URL would be lost.**
  Verify with `--predicate CTO_0001021` / `--predicate associatedMedia`, then handle it: index
  `record → media-bnode → CTO_0001021 URL` in `preprocess.py` (like the is-about join) and emit
  `<record> wdt:P953 <url>` in `convert_to_rdf.py`. Drop the bnode itself. (`schema:associatedMedia` is
  currently in `mapping.json` as `drop` — you'll change how it's handled.)
- `CTO_0001007` (license statement) → **drop** (broken stringified bnode ids, already mapped);
  `NFDI_0000207`, `NFDI_0000146`, `CTO_0001080`, `schema:item/dataFeedElement/sameAs` → drop (already in
  `mapping.json`). `NFDI_0000142` → P275 (license), `NFDI_0000191` → P123, `CTO_0001073` → P571 (already
  handled — but **profile its date format**; APSearch may differ from Detmold's intervals).
- `NFDI_0001008` is **dropped now** (self-referential in every feed). Confirm APSearch's is too (expected).
- **Stage D (OpenRefine) for label residue:** APSearch references some entities only by label. Per the
  RISM precedent, flatten the relevant column(s) to CSV → reconcile in OpenRefine with the
  **RDF-transform** extension (**Chrome only** — Firefox/Safari fail silently) → export; store history in
  `ckg/openrefine/history/`. Small and isolated, may yield few targets — **profile before investing**.
  It does **not** block the conversion.

**Steps:** profile → hand-map the media classes into `record_types.json` (verified QIDs) → extend
`preprocess.py`/`convert_to_rdf.py` for the associatedMedia→content-url traversal and confirm record
typing → run the 3 commands → (optional) OpenRefine pass for label residue → verify (checklist above) →
stage to `raw_data/ckg-apsearch/` (graph `https://linkedmusic.ca/graphs/ckg-apsearch/`) → report
coverage + counts + decisions. **Then stop.**

---

## When to stop / re-handoff
- Finish **one** task, run the verification checklist, stage the TTL (Task 2), and **report results +
  any new decisions** (record typing, new QIDs, converter changes) to the user.
- If you change shared artifacts (`mapping.json`, `record_types.json`, the scripts), make the change
  **feed-conditional or generic** so musiconn **and Detmold** still reconvert identically — and verify
  the precondition that makes it safe.
- If context is getting long, summarize state and stop — the user will re-handoff for the next task.
- Record genuinely new, non-obvious findings in the memory files (update `ckg-converter-model`).
