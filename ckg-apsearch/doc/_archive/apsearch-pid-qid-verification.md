# APSearch (`E6304`) — PID/QID verification for manual sign-off

**Produced:** 2026-06-17 · **For:** Liam to manually verify before any of these IDs are wired
into `record_types.json` / `mapping.json` / `crosswalk.json`.

The handoff warned (correctly) that the P/Q IDs floated in `HANDOFF-apsearch.md` were likely
wrong. **Every ID below was looked up against a primary source this session** — but please
spot-check the ones marked ⚠/✗ yourself before trusting them in production. This doc is the
APSearch counterpart to `pid-qid-verification.md`; promote confirmed rows into that file.

**Verification methods used (all 2026-06-17):**
- **WD-API** — `wikidata.org/w/api.php?action=wbgetentities` (label + description + datatype, raw JSON)
- **WDQS** — `query.wikidata.org/sparql` (`?x wdt:P1014 "<aat>"`, deterministic ID match)
- **Getty** — `vocab.getty.edu/sparql.json` (`skos:prefLabel`)
- **NFDI** — `nfdi4culture.de/id/E####` page `owl:sameAs` → Wikidata (authoritative source mapping)
- **TIB** — TIB Terminology Service API (`service.tib.eu/ts4tib`) for CTO ontology labels

**Status legend:** ✅ verified & recommended · ⚠️ needs your decision · ✗ was wrong (caught)

---

## ✅ RESOLVED — sign-off + conversion complete (2026-06-18)

All decisions below are signed off (user feedback 2026-06-18) and **wired + converted**.
APSearch is staged at `raw_data/ckg-apsearch/apsearch.ttl` (**46,203 triples**, 0 blank
nodes, valid Turtle) → graph `https://linkedmusic.ca/graphs/ckg-apsearch/`. musiconn +
Detmold reconvert **identically** (sorted-triple diff = 0) after the shared-converter changes.

**Final P31 type map** (wired into `record_types.json`, keyed by CTO class / AAT URI; feed-safe
because these URIs are APSearch-only):

| Source class | P31 QID | Count emitted |
|---|---|---|
| `CTO_0001043` audio object | **Q3302947** audio recording | 3,005 (+ sound-rec AAT) |
| `CTO_0001044` image object | **Q478798** image | 523 |
| `CTO_0001048` video object | **Q30070675** video recording *(single work — parallels audio; NOT Q34508 the technique)* | 454 |
| `CTO_0001047` text object | **Q234460** text | 52 |
| `aat:300028633` sound recordings | **Q3302947** (deterministic, `P1014`) | (subset of audio) |
| `aat:300265798` cylinder phonographs | **Q691783** phonograph cylinder *(user: "close enough")* | 84 |
| `aat:300234108` ethnographic objects | *(unmapped — AAT URI kept, no P31)* | — |
| `CTO_0001045` media object (1 rec) | *(no entry → fallback)* | — |
| **fallback** (no resolving classifier) | **Q17537576** creative work *(APSearch; Detmold keeps Q838948)* | 2,472 |

Every one of the 6,271 records carries `lmckg:Work` + ≥1 `wdt:P31` (0 untyped — the robust
post-loop fallback also catches the 4 ethnographic-AAT-only records).

**Licenses / publisher** (wired into `crosswalk.json`; emitted as `<record> wdt:P275/P123 <uri>`
+ `<uri> wdt:P2888 <QID>` — the local-node pivot, isolated from musiconn/Detmold whose
license/publisher URIs differ): record-level `E6404→Q20007257` (CC BY 4.0), `E6429→Q18199165`
(CC BY-SA 4.0), publisher `E2431→Q219989` (BBAW); `elararchive.org/legal` → residue (no QID, per
sign-off). **Correction:** the CC-BY-NC-SA value (`Q42553662`) is NOT emitted — it lives only on
the **media bnode** of the 72 SMB records (whose *record-level* license is E6429/CC BY-SA), and we
emit the uniform record-level license only (one P275 per record). Flag if you want the asset-level
CC-BY-NC-SA surfaced instead.

**Other:** P953 ✅ (kept — most apt; repo has no competing URL convention, see §1a note);
content URLs joined off the `associatedMedia` bnode (3,783 → P953 URI nodes); `NFDI_0000125`
(1 dataset-level triple) → drop; metadata predicates (`NFDI_0000146/0000207`, `dateModified`) →
drop confirmed (all constant CKG-ETL provenance, **not** ELAR source data — see §6).

---

## 0. Corrections — IDs from the handoff that were WRONG

| ID in handoff | Handoff claimed | What it actually is | Source |
|---|---|---|---|
| **Q30070** | "video"(?) candidate for a media class | **the year 451** (`instance of: year`) | WD-API |
| **Q478798** | "image (or photograph)" — treated as interchangeable | **"image"** ≠ **"photograph"** (Q125191). Distinct concepts; pick one deliberately | WD-API |
| (P1026) | — (my probe for a "depositor" property) | **"academic thesis"** — there is **no** dedicated depositor property; use **P170** | WD-API |

Everything else in the handoff's prose was directionally right but unverified; the verified
forms are below.

---

## 1. Wikidata properties

### 1a. Used by the APSearch conversion + the Wikidata pivot

| PID | Label (Wikidata) | datatype | Used for | Status |
|---|---|---|---|---|
| **P2888** | exact match | url | the `wdt:P2888` pivot (local URI → QID) | ✅ WD-API |
| **P31** | instance of | wikibase-item | record `P31` → type QID | ✅ WD-API |
| **P275** | copyright license | wikibase-item | `NFDI_0000142` license → license node (which carries P2888→QID) | ✅ WD-API |
| **P123** | publisher | wikibase-item | `NFDI_0000191` published-by → E2431 | ✅ WD-API |
| **P571** | inception | time | `CTO_0001073` creation period → `xsd:date`/`gYear` | ✅ WD-API |
| **P953** | work available at URL | url | `CTO_0001021` content URL (the handle/SMB URL) | ✅ WD-API |
| **P1014** | Art & Architecture Thesaurus ID | external-id | `CTO_0001026` AAT classifier → QID lookup | ✅ WD-API |

Also present in the shared `mapping.json`/crosswalk (not exercised by APSearch — no events, no
authority IDs — but cross-checked so a re-convert of musiconn/Detmold is unaffected):
**P585** point in time ✅, **P361** part of ✅, **P227** GND ID ✅, **P214** VIAF cluster ID ✅,
**P1566** GeoNames ID ✅ (all WD-API).

> Note on P275 datatype: it is `wikibase-item`, so the object must be a QID, not a URL. The
> converter keeps the license **URI** as a local node and pivots it to a QID via P2888 — same
> shape as other local-node-plus-P2888 entities. Consistent; no change needed.

### 1b. Enrichment-candidate properties (for the ELAR stretch — see `elar-enrichment-spike.md`)

Verified now so the enrichment path is ready if pursued; **not used in CKG-only APSearch.**

| PID | Label | datatype | Intended use | Status |
|---|---|---|---|---|
| **P407** | language of work or name | wikibase-item | documented language | ✅ WD-API |
| **P220** | ISO 639-3 code | external-id | language reconciliation key | ✅ WD-API |
| **P1394** | Glottolog code | external-id | language reconciliation key | ✅ WD-API |
| **P218** | ISO 639-1 code | external-id | (major languages only) | ✅ WD-API |
| **P17** | country | wikibase-item | `dc:coverage` country | ✅ WD-API |
| **P131** | located in admin. territorial entity | wikibase-item | place that IS an administrative entity | ✅ WD-API |
| **P276** | location | wikibase-item | generic place (use P131 for admin entities, **P706** for terrain features — per the P276 description) | ✅ WD-API |
| **P706** | located in/on physical feature | wikibase-item | place that is a distinct terrain feature | ✅ WD-API |
| **P170** | creator | wikibase-item | depositor/recorder/speaker (no dedicated depositor PID) | ✅ WD-API |

> Place mapping (enrichment only): pick by entity kind — **P17** country, **P131** administrative
> entity, **P706** terrain feature, **P276** as the generic fallback. (Per your note on the P276
> description: *"In case of an administrative entity use P131. In case of a distinct terrain feature
> use P706."*)

---

## 2. Record-type / media-class `P31` QIDs — **DECISIONS NEEDED**

APSearch records get `P31` two ways: (a) a **media class** via `CTO_0001049 has data concept`,
or (b) the **Work fallback** (every record is `schema:CreativeWork` → `lmckg:Work` → `Q838948`)
when no media class applies. The five CTO media classes (labels from **TIB**, counts from the
dump) and my verified QID proposals:

| CTO class | Label (TIB) | Count | Proposed `P31` QID | QID label (WD-API) | Status |
|---|---|---|---|---|---|
| `CTO_0001043` | audio object | 2,982 | **Q3302947** | audio recording — "single object representing recorded audio data…" | ✅ recommend |
| `CTO_0001044` | image object | 523 | **Q478798** | image — "artifact that depicts or records visual perception" | ⚠️ vs **Q125191** photograph (more specific; ELAR=field photos, SMB=object photos) |
| `CTO_0001048` | video object | 454 | **Q30070675** | video recording — "single work, or take, made using the medium of video" | ✅ recommend (parallels the audio choice) |
| `CTO_0001047` | text object | 52 | **Q234460** | text — "object that can be 'read' by reader; result of writing" | ⚠️ vs **Q49848** document |
| `CTO_0001045` | media object | 1 | *(none — let it fall to Q838948)* | — | ⚠️ generic; 1 record only |

**Work fallback** (classifier-less records):

| QID | Label | Used for | Status |
|---|---|---|---|
| **Q838948** | work of art | `RECORD_KIND_P31["Work"]` fallback (records w/ no media class) | ✅ WD-API (already in `record_types.json` lineage) |

**Decision for you:**
1. Audio = **Q3302947**, Video = **Q30070675** — sign off? (recommended; the two have matched
   "single object/work … recording" definitions.)
2. Image — **Q478798 "image"** (generic, matches the class name) **or Q125191 "photograph"**
   (more specific but mis-types non-photographic images)?
3. Text — **Q234460 "text"** (matches the class name) **or Q49848 "document"**?
4. `media object` (1 record) — leave to Q838948 fallback? (recommended.)

> Cross-check of the existing musiconn record-type QIDs (unchanged, but re-verified):
> **Q207628** "composed musical work" ✅ (also confirmed deterministically: `aat:300417577
> wdt:P1014` → Q207628), **Q6942562** "musical performance" ✅ (also `aat:300262956` → Q6942562).

---

## 3. Licenses (`NFDI_0000142` → `P275`) — values & their QIDs

Four distinct license values in the dump. The two NFDI-id licenses resolve to Wikidata via
`owl:sameAs` on their NFDI4Culture pages (authoritative); the CC value reconciles by exact label.

| License value (count) | Wikidata QID | QID label | Source | Status |
|---|---|---|---|---|
| `nfdi4culture.de/id/E6404` (562) | **Q20007257** | Creative Commons Attribution 4.0 International (CC BY 4.0) | NFDI `owl:sameAs` + `creativecommons.org/licenses/by/4.0/` | ✅ |
| `nfdi4culture.de/id/E6429` (92) | **Q18199165** | Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0) | NFDI `owl:sameAs` + `…/by-sa/4.0/` | ✅ |
| `creativecommons.org/by-nc-sa/4.0` (72) | **Q42553662** | Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International | WD-API (exact label) | ✅ |
| `www.elararchive.org/legal` (5,617) | *(no QID)* | ELAR's own access/legal terms page | — | ⚠️ leave as residue URI (no `P2888`); ELAR custom terms, not a Wikidata-listed license |

> ⚠️ The CC BY-NC-SA value in the dump is the **non-canonical** URL
> `http://creativecommons.org/by-nc-sa/4.0` (missing `/licenses/…/`). It still maps to
> Q42553662; just don't expect the canonical CC URL to appear verbatim.

---

## 4. Publisher (`NFDI_0000191` → `P123`)

| Value (count) | Wikidata QID | QID label | Source | Status |
|---|---|---|---|---|
| `nfdi4culture.de/id/E2431` (6,271, constant) | **Q219989** | Berlin-Brandenburg Academy of Sciences and Humanities (BBAW) | NFDI `owl:sameAs` | ✅ |

Consistent with ELAR's 2021 relocation to BBAW. (This is the *feed* publisher; the modeling
decision `NFDI_0000191 → P123` is already settled in `predicate-evidence.md` §4.)

---

## 5. AAT classifier codes (`CTO_0001026` → `classifier_aat` → `P1014`)

Three distinct AAT codes. `build_crosswalk.py` resolves them via `wdt:P1014`; only one has a
Wikidata match. The converter keeps the AAT URI either way (interoperability), and the record
still gets a `P31` from its media class / Work fallback, so the unmatched two are **fine as-is**.

| AAT code (count) | Getty prefLabel | `P1014`→ Wikidata | QID label | Status |
|---|---|---|---|---|
| `aat:300028633` (84) | sound recordings | **Q3302947** | audio recording | ✅ deterministic (WDQS) |
| `aat:300234108` (92) | ethnographic objects | *(no P1014 match)* | — | ⚠️ keep AAT URI, no `P31` from it (acceptable); likely the SMB/museum items |
| `aat:300265798` (84) | cylinder phonographs (phonographs) | *(no P1014 match)* | — | ⚠️ keep AAT URI; optional hand-pick **Q691783** "phonograph cylinder" (= the *medium*; AAT term is the *device* — imperfect, recommend leaving unmapped) |

---

## 6. Dropped values — identified to confirm the drop is correct

These are dropped in `mapping.json`; identifying them confirms they're metadata/provenance
noise, not content.

| Predicate / value | Resolves to (NFDI `owl:sameAs`) | Meaning | Drop correct? |
|---|---|---|---|
| `NFDI_0000146` = `E3087` | **Q2063** (JSON) | metadata media type | ✅ yes |
| `NFDI_0000207` = `E4022` | **Q54872** (RDF) | metadata standard | ✅ yes |
| `NFDI_0000207` = `E4456` | **Q3475322** (Schema.org) | metadata standard | ✅ yes |
| `NFDI_0000207` = `E6367` | *(no sameAs found)* | metadata standard | ✅ yes (drop regardless) |

---

## 7. Date handling — RESOLVED (was open decision #2)

**Correction to the earlier claim.** `CTO_0001073` (4,214 total) has **zero day-precision dates** —
*every* value is a Jan-01 full-day placeholder (`00:00:00–23:59:59` on Jan 1):
- **4,086** single-year (`"2015-01-01/2015-01-01"`) = year only;
- **128** multi-*year* ranges (`"1909-01-01/1950-01-01"` — 107 of them are 1909–1950), which the
  earlier doc wrongly called "genuine multi-day intervals." They are year ranges, also placeholders.

(As-written `coerce_date` would have emitted a **false** `xsd:date "2015-01-01"` for these.)

**Done:** feed-conditional coercion — for APSearch every interval → **`xsd:gYear` of the start
year** (single-year → that year; range → the earliest, e.g. `"1909"`). All 4,214 P571 values are
`xsd:gYear`. (Detmold/musiconn untouched: Detmold has 0 Jan-01 same-day spans, musiconn 0 intervals.)
The only loss is the end-year of the 128 ranges — say if you want it preserved as `P582`.

**Querying impact (your question).** Within APSearch, P571 is uniformly `xsd:gYear`, so year
queries are trivial. The thing to know is *lake-wide*: dates are mixed-precision (`xsd:date` /
`gYearMonth` / `gYear` across Detmold/musiconn/APSearch). Implications:
- **Listing/retrieving** dates (`?rec wdt:P571 ?d`) needs no awareness — all datatypes return.
- **Filtering by year** is datatype-strict: `?d = "2015"^^xsd:gYear` won't match `"2015-..."^^xsd:date`,
  and you can't range-compare `gYear` against `date` directly. The robust, datatype-agnostic pattern
  (also the one to teach SESEMMI) is **`FILTER(STRSTARTS(STR(?d), "2015"))`** — `YEAR(?d)` only works
  on `xsd:date`/`dateTime`, so it breaks on `gYear` in some engines.

---

## 8. Sign-off checklist

- [ ] §2 media-class P31s: audio **Q3302947**, video **Q30070675** ✓?
- [ ] §2 image: **Q478798** (image) or **Q125191** (photograph)?
- [ ] §2 text: **Q234460** (text) or **Q49848** (document)?
- [ ] §3 licenses E6404→**Q20007257**, E6429→**Q18199165**, CC-BY-NC-SA→**Q42553662**, ELAR-legal→residue ✓?
- [ ] §4 publisher E2431→**Q219989** (BBAW) ✓?
- [ ] §5 AAT: only `300028633`→**Q3302947** emits P31; other two stay as AAT URIs ✓?
- [ ] §7 dates: Jan-01 placeholders → **gYear** ✓?

Once signed off, I'll wire the confirmed media-class QIDs into `record_types.json`
(feed-conditional so musiconn/Detmold re-convert identically), confirm the license/publisher
QIDs land in `crosswalk.json`, and proceed with the APSearch conversion (Stage A–E in the handoff).
