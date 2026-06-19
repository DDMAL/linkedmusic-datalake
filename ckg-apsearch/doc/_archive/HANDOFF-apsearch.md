# CKG ingestion — handoff (APSearch / `E6304`)

**Written:** 2026-06-17 · **For:** the next agent converting + reconciling APSearch ·
**Deadline:** Hermes "From Notes to Nodes" submission **2026-06-30**.

APSearch (`E6304`) is the **last CKG feed**. musiconn + Detmold are fully done, reconciled,
and staged. Your job: convert APSearch to RDF (it's a *different shape* — a media feed) and
**investigate Wikidata reconciliation seriously** (user's explicit instruction — "new data,
might work well with Wikidata, you never know"). Work **one stage at a time, report, then
continue.** Ask the user when a decision is theirs (open questions in §7).

---

## 0. Orientation (read in this order)

1. **`CLAUDE.md`** (repo root) — house rules. Non-negotiable: **no blank nodes in output**,
   **Wikidata pivot via `wdt:P2888`**, **never commit data files**, run via
   `poetry run python …` (Python 3.12, one Poetry env at repo root). **All CKG scripts assume
   CWD = `ckg/src/`.**
2. **`ckg/README.md`** — pipeline + the 3-command-per-feed workflow + graph IRIs.
3. **`ckg/doc/INGESTION-PLAN.md`** — full plan (§4 stage spec, §5 property mapping).
4. **`ckg/doc/predicate-evidence.md`** §4 — authoritative mapping table.
5. **`ckg/doc/pid-qid-verification.md`** — every manually verified P/Q ID. **Cross-check here
   before using any P/Q ID, and add any new ones you choose** (with source URL + date).
6. **`ckg/doc/HANDOFF.md` §TASK 2** — the *earlier* APSearch spec. Still mostly valid; **this
   doc supersedes it** where they differ (it predates the reconciliation work + the label
   convention).
7. Recalled **memories**: `ckg-hermes-ingestion` (project status), **`ckg-converter-model`**
   (the settled Stage E model — trust over the evidence sheet where they differ),
   `virtuoso-prod-loading` (load runbook). 
8. Scripts in `ckg/src/`: `profile_predicate.py` (A), `preprocess.py` (B),
   `build_crosswalk.py` (C), `convert_to_rdf.py` (E), `ontology/mapping.json` (runtime map),
   and **`wikidata_id_lookup.py`** (NEW — exact authority-ID→QID via `haswbstatement`).

---

## 1. Current state (everything except APSearch is DONE)

- **musiconn** — staged `raw_data/ckg-musiconn/musiconn.ttl` (**1,588,653 triples**, 14,165
  P2888 pivots, 4,515 authority labels, 0 blank nodes, valid Turtle) →
  `https://linkedmusic.ca/graphs/ckg-musiconn/`.
- **Detmold** — staged `raw_data/ckg-detmold/detmold.ttl` (**14,835 triples**, 588 pivots,
  27 labels, 0 blank nodes) → `https://linkedmusic.ca/graphs/ckg-detmold/`.
- **Reconciliation finished** for both. Shared, additive crosswalk
  `ckg/data/mappings/crosswalk.json` = **15,186 entries**. Built by `build_crosswalk.py`
  (deterministic ID→QID) + a residue pass (`wikidata_id_lookup.py` `haswbstatement` lookup +
  vetted OpenRefine name matches, merged via `merge_openrefine.py`).
- **`convert_to_rdf.py` now emits `rdfs:label`** on authority entities (the GND/VIAF/GeoNames
  preferred names in `data/openrefine/names_for_reconciliation.csv`) — the house
  "name + `P2888`" convention. APSearch has ~no authority entities, so this won't add APSearch
  labels, but APSearch records carry their own `rdfs:label` titles (kept via the `label` action).
- **The user loads Virtuoso themselves** — never attempt the load.
- **APSearch: not started.** `raw_data/ckg-apsearch/` exists but is empty. Raw dump (gitignored):
  `raw_data/ckg/mnt/data/culture-kg-kitchen/data/production/E6304/nt/E6304.nt` (23 MB, 129,448
  triples).

---

## 2. What APSearch IS (profiled 2026-06-17 — confirm with `--predicate`)

It's **ELAR — the Endangered Languages Archive** (host `elararchive.org`): archival **audio +
image** field recordings of endangered languages. **6,271 records** (`CTO_0001005`). It is a
**media/content feed** — no relational backbone, no persons, **~0% authority-ID coverage**, so
it differs fundamentally from musiconn/Detmold.

Top-level predicate profile (`profile_predicate.py … --top 40`):

| count | obj kind | predicate | meaning / disposition |
|---|---|---|---|
| 22,602 | uri | `rdf:type` | record + media-object typing |
| 18,813 | uri | `NFDI_0000207` | already `drop` in `mapping.json` (confirm) |
| 6,343 | uri | `NFDI_0000142` | **license → P275** (4 distinct values, see below) |
| 6,272 | literal | `schema:dateModified` | metadata mod-date — likely `drop` (decide) |
| 6,271 | uri | `NFDI_0000191` | **publisher → P123** — but a CONSTANT (`…/id/E2431`) |
| 6,271 | literal | `CTO_0001080` | API base — `drop` |
| 6,271 | uri | `schema:item` / `dataFeedElement` | feed envelope — `drop` |
| 6,271 | uri | `NFDI_0000146` | (check) |
| 6,271 | literal | `NFDI_0001008` | self-referential — **`drop`** (every feed) |
| 6,271 | bnode | `CTO_0001025` | is-about bnode — **`drop`** (typing only) |
| 6,271 | uri | `CTO_0001006` | feed/source ref — CONSTANT (`…/id/E6304`); likely `drop` |
| 6,269 | literal | `rdfs:label` | **record title** (free text) — emit as `rdfs:label` |
| 4,214 | literal | `CTO_0001073` | **date → P571** (`schema:DateTime`, see below) |
| 4,012 | uri | `CTO_0001049` | **media class → record P31** (audio/image, hand-map) |
| 3,783 | bnode | `schema:associatedMedia` | media bnode → carries the content URL |
| 3,783 | literal | `CTO_0001021` | **content URL → P953** (needs bnode traversal) |
| 2,926 | literal | `CTO_0001007` | license stmt (broken stringified bnode ids) — **`drop`** |
| 260 | uri | `CTO_0001026` | **AAT classifier → P31** (auto via `build_crosswalk` P1014) |
| 2 | uri | `schema:sameAs` | `drop` |

Deep-profile findings (the non-obvious bits):

- **`CTO_0001049` media class** → objects are `CTO_0001043` (audio) and `CTO_0001044` (image);
  4,012 over 3,783 subjects (≈229 records carry both). These are **CTO classes, NOT AAT**, so
  `build_crosswalk.py` only *warns* — you **hand-add them to `record_types.json`** with verified
  QIDs; the converter's `classifier_media` action then emits `wdt:P31` from those. Candidate QIDs
  (VERIFY both on wikidata.org and log in `pid-qid-verification.md`): image → `Q478798`
  (photograph) or a more apt image-object class; audio → a sound-recording/audio QID
  (e.g. `Q30070` "video"? no — pick the audio recording class deliberately). ~6,271−3,783 = 2,488
  records have **no** media class — decide their P31 (they fall to the `CreativeWork` →
  `RECORD_KIND_P31["Work"]=Q838948` fallback, already wired; confirm that's acceptable, or refine).
- **Content URL (`CTO_0001021`/P953) sits on the `schema:associatedMedia` bnode**, not the record.
  The converter **skips bnode subjects**, so as-is the URL is LOST. Index
  `record → associatedMedia-bnode → CTO_0001021 URL` in `preprocess.py` (like the is-about join)
  and emit `<record> wdt:P953 <url>` in `convert_to_rdf.py`; drop the bnode. `associatedMedia` is
  currently `drop` in `mapping.json` — you'll change how it's handled. (~72 media objects are
  URI-identified `AudioObject`/`ImageObject`/`MediaObject` carrying their own license + URL —
  handle or accept.)
- **Dates `CTO_0001073`** → `"2015-01-01T00:00:00/2015-01-01T23:59:59"^^schema:DateTime` —
  same-day start/end intervals, and they're **almost all `01-01` placeholders** (i.e. year-only
  precision dressed up as a full Jan-1 day). `coerce_date` already parses `schema:DateTime`
  intervals (Detmold), so it won't break — **but decide precision**: a Jan-1 placeholder probably
  means `gYear "2015"`, not `xsd:date "2015-01-01"` (cf. musiconn's `-00` placeholder handling).
- **License `NFDI_0000142`** (→ P275) has only **4 distinct objects**: `elararchive.org/legal`
  (5,617 — ELAR's own page, likely no QID), `nfdi4culture.de/id/E6404` (562) and `…/E6429` (92)
  (NFDI license entities — identify what license each is), and **`creativecommons.org/by-nc-sa/4.0`
  (72) → reconcilable to a Wikidata CC-license item** (e.g. CC BY-NC-SA 4.0 — verify the QID).
- **Publisher `NFDI_0000191`** (→ P123) is the **constant** `…/id/E2431` for all 6,271 records
  (one publisher entity — reconcile that single entity if it has a QID).
- **Record titles (`rdfs:label`)** are free-text ELAR descriptions — `"fishing story with poem"`,
  `"story of Qertaasah"`, `"the hyena"`, `"20141024_MehriNdet_M029_poem2"`. **Not reconcilable
  entities.** Keep them as `rdfs:label`.

---

## 3. Stage A–E — the conversion (do this first)

The 3 commands (from `ckg/src/`):
```bash
poetry run python preprocess.py      apsearch   # B: index records, media-bnode→URL join
poetry run python build_crosswalk.py apsearch   # C: AAT→QID (P1014); warns on media classes
poetry run python convert_to_rdf.py  apsearch   # E: NT→TTL → data/rdf/apsearch.ttl
```
Steps:
1. **Re-profile** (`--top 40`, then `--predicate` on each kept predicate) to confirm the §2
   table against the current scripts. **Diff APSearch's predicate set against `mapping.json`** and
   handle every predicate the converter reports as `UNKNOWN (dropped)`.
2. **Hand-map media classes** `CTO_0001043` (audio) + `CTO_0001044` (image) → `record_types.json`
   with **verified** QIDs (log in `pid-qid-verification.md`). Confirm record typing: classifier
   path for records with a media/AAT class; `RECORD_KIND_P31["Work"]=Q838948` fallback for the rest
   (already wired via `preprocess.py`'s `schema:CreativeWork → "Work"`).
3. **Implement the `associatedMedia` → content-URL (P953) traversal** in `preprocess.py` +
   `convert_to_rdf.py` (§2). Drop the media bnode itself.
4. **Confirm/extend predicate mappings**: license `NFDI_0000142`→P275, publisher
   `NFDI_0000191`→P123, date `CTO_0001073`→P571 (decide precision), `schema:dateModified`→drop,
   `CTO_0001006`/`NFDI_0001008`/`CTO_0001025`/`CTO_0001080`/`CTO_0001007`→drop. **Any shared-artifact
   change must be feed-conditional/generic so musiconn + Detmold still reconvert identically** —
   verify the precondition (e.g. they have 0 `associatedMedia`).
5. **Verify** (checklist §6) → **stage** to `raw_data/ckg-apsearch/` (graph
   `https://linkedmusic.ca/graphs/ckg-apsearch/`) → report triple count, P31 distribution,
   P953 count, coverage. **Then stop.**

---

## 4. Reconciliation — investigate seriously (user's instruction)

The user wants Wikidata reconciliation **investigated in a significant capacity** — APSearch is
new data and may reconcile better than expected. Do that honestly. **But set expectations from
the profile (§2):** the CKG-flattened APSearch has a **small structured reconciliation surface** —
there are no person/place/language predicates, and the titles are free text. Concretely, what *is*
reconcilable in the dump:

- **Licenses** (`NFDI_0000142`): the CC license → a Wikidata CC-license QID; the two NFDI license
  entities (E6404, E6429) → identify and map if they correspond to Wikidata license items.
- **Media classes** (audio/image) and **AAT codes** — controlled vocab, handled in §3.
- **Publisher** (E2431) — one entity, reconcile if it has a QID.

How to reconcile:
- **ID-first.** For anything carrying a GND/VIAF/GeoNames/AAT ID, use `build_crosswalk.py` /
  `wikidata_id_lookup.py` (exact `haswbstatement` ID→QID — no false positives). This is strictly
  better than name matching.
- **OpenRefine (RDF-transform, Chrome only — fails silently in Firefox/Safari)** for any
  label-based residue: flatten the relevant column(s) to CSV → reconcile → **commit** matches
  (auto-match above a score *or* click ✓ — an uncommitted candidate exports as the name, not the
  QID) → export with **"Matched entity's ID"** format → store history in `ckg/openrefine/history/`,
  export in `ckg/openrefine/export/` → merge into `crosswalk.json`.

**The real Wikidata opportunity is an enrichment stretch (flag to the user before investing).**
Like the musiconn Track-2 situation (CKG flattened roles away; the native API has them), the **ELAR
source** (`elararchive.org`, an Endangered Languages Archive catalog/API) almost certainly exposes
per-recording **languages (ISO 639-3 / Glottolog), countries/places, and depositors** — all of
which reconcile *excellently* to Wikidata (every ISO 639-3 language has a Wikidata item). CKG
dropped these. If broad Wikidata coverage is the goal, the path is to **enrich from ELAR keyed on
the record**, not from the sparse CKG dump. **Spike it first** (a tiny probe, polite, set a
`User-Agent` = `liam.pond@mail.mcgill.ca`; tell the user before any larger fetch) and report
feasibility, exactly like `musiconn-api-spike.md`.

---

## 5. Lessons carried over from the musiconn/Detmold reconciliation (read these)

- **ID-based matching ≫ name matching.** Deterministic ID→QID (`build_crosswalk.py`) +
  `wikidata_id_lookup.py` (`haswbstatement:P227/P214/P1566=<id>`) give zero false positives.
- **Name reconciliation is namesake-prone for niche data.** OpenRefine scores primarily on name
  similarity; helper ID properties *boost* but don't *exclude*, so when the real (obscure) entity
  isn't in Wikidata it happily matches a famous same-name one at ~100. **Never auto-match persons
  by score alone**; use type constraints + ID helper properties; leave residue when uncertain.
- **OpenRefine "candidate" ≠ "match".** You must **commit** candidates before exporting, and use
  the **"Matched entity's ID"** column format, or the export contains names instead of QIDs.
- **Residue is fine** — unmatched entities are emitted as raw URIs (local `rdf:type`, no `P2888`),
  per the converter model. **No synthetic labels** (but real authority preferred names *are* now
  emitted as `rdfs:label` — see §1).
- **Verify hard-coded values against the source.** A `GEONAMES_HARDCODED` dict in
  `fetch_authority_names.py` had 3/4 names mis-entered (claimed "verified"); caught via GeoNames
  Linked Data. Don't trust "verified" comments — re-verify.

---

## 6. Gotchas + verification

- **Shared artifacts are additive + feed-conditional.** `crosswalk.json`, `record_types.json`,
  `mapping.json` are shared across feeds — extend, don't fork; make every change generic or
  feed-conditional and **re-confirm musiconn + Detmold reconvert identically**.
- **`black` won't run** here (Python 3.12.5 ↔ Black incompat). Write in Black style, skip it.
- **Verification checklist** (every feed):
  ```bash
  grep -c '_:' data/rdf/apsearch.ttl     # MUST be 0
  poetry run python -c "from rdflib import Graph; g=Graph(); g.parse('data/rdf/apsearch.ttl',format='turtle'); print(len(g))"
  ```
  Also: every record has `rdf:type lmckg:*` + one `wdt:P31`; content URLs emitted as `P953`;
  dates are `xsd:date`/`gYearMonth`/`gYear`; spot-check `P2888`/`P31` targets resolve correctly.
- **Staging** (after verify):
  ```bash
  mv ckg/data/rdf/apsearch.ttl raw_data/ckg-apsearch/
  printf 'https://linkedmusic.ca/graphs/ckg-apsearch/\n' > raw_data/ckg-apsearch/global.graph
  ```
  Match exactly (trailing slash, single newline) — see `raw_data/ckg-detmold/`.
- **Virtuoso load runbook** (the user runs it): `memory/virtuoso-prod-loading.md`; graph IRI
  `https://linkedmusic.ca/graphs/ckg-apsearch/`.

---

## 7. Open decisions — ask the user

1. **Media-class QIDs** — propose audio + image P31 QIDs (verify on wikidata.org), get user
   sign-off, log in `pid-qid-verification.md`. (Image candidate `Q478798`; pick the audio class
   deliberately.)
2. **Date precision** — Jan-1 `schema:DateTime` placeholders → `gYear` (recommended) or `xsd:date`?
3. **ELAR enrichment stretch** — pursue the ELAR-source spike (languages/places/depositors → strong
   Wikidata reconciliation) or ship CKG-only APSearch for the 2026-06-30 deadline?
4. **License/publisher entities** — confirm QIDs for the CC license + E2431 publisher + E6404/E6429.

**Finish a stage, run the checklist, report, and ask before anything outward-facing (ELAR fetch,
Virtuoso load). The user reviews each step.**
