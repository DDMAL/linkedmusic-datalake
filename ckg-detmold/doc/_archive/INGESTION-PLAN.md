# CKG → LinkedMusic Ingestion Plan

**Status:** proposed, for review · **Target:** Hermes "From Notes to Nodes" submission, 2026-06-30
**Companion doc:** [predicate-evidence.md](predicate-evidence.md) — the empirical basis (and the
authoritative mapping table, §4) for every mapping decision below.

---

## 0. Context — why we are doing this

LinkedMusic maintains a data lake in which every music database is ingested as RDF, **reconciled to
Wikidata**, and loaded into a single Virtuoso triplestore as one named graph per database. Cross-database
questions are answered by pivoting on shared Wikidata QIDs. A natural-language→SPARQL tool, **SESEMMI**
(`DDMAL/SESEMMI`, sesemmi.linkedmusic.ca), queries that store.

For the Hermes data challenge we are ingesting the **NFDI4Culture Culture Knowledge Graph (CKG)** as a new
dataset. CKG is delivered RDF-native (N-Triples), split into per-feed dumps. A new dataset must (a) load
into Virtuoso, (b) carry Wikidata links, and (c) have its schema documented for SESEMMI.

**The central problem:** CKG is **not a passthrough** — it is a lossy ETL remodel into the nfdicore/CTO
ontology. It harmonizes many sources and adds uniform authority links (GND, VIAF, Getty), but it *flattens*
source-specific structure. In musiconn, every performer/composer/conductor relation is collapsed to a
generic "has related person" with **no role**, and person/place/org names are dropped in favour of an
authority ID. (See [predicate-evidence.md](predicate-evidence.md) §2 for the evidence.)

**Decision (settled with the user):** a **hybrid** ingestion —
1. **CKG spine** — the converted CKG data itself, the backbone this track produces (the deliverable):
   ingest the CKG per-feed dumps, pivoted on Wikidata, as per-feed named graphs. This is on-brief and
   gives us CKG's harmonized breadth and authority links cheaply.
2. **Native music supplement** (the differentiator): for the music feeds — primarily **musiconn** — pull
   the native source API to recover the flattened roles (and names), landing in a *parallel* graph joined
   to the CKG spine by the source permalink and the shared QID. This targets the challenge's
   "musicological adequacy" criterion at the one place CKG loses it.

Two LinkedMusic house rules constrain the modelling: **(a) no blank nodes in output**, and **(b) Wikidata
is the pivot** — a reconciled entity is linked to its QID via `wdt:P2888` ("exact match") as a separate
triple, the convention used across `rism`, `diamm`, and the `shared/rdf_config/*.toml` configs.

---

## 1. Scope

| Item | Decision |
|---|---|
| **RISM `E5313`** (88.4M triples) | **Excluded** — LinkedMusic already ingests RISM separately. Possible stretch re-ingest later. |
| **musiconn `E5320`** (3.0M) | **In — pilot/vertical slice.** Richest structure; 100%-identified backbone; primary native-supplement target. |
| **Detmold `E5305`** (31k) | In — a small musiconn (person-centric); same machinery. |
| **APSearch `E6304`** (129k) | In — **separate track**: media/content records, no persons, no authority IDs → needs label reconciliation, not role recovery. |
| **Image feeds** `E6161`+`E6064` (~21M) | **Stretch** — near-free to add via the same crosswalk (≈0 OpenRefine targets, mostly images). |
| Other non-music feeds | Out of initial scope; same machinery applies if revisited. |

**Two tracks:**
- **Track 1 — CKG spine** (fully scripted, deterministic). Critical path.
- **Track 2 — native musiconn supplement** (API-driven). Differentiator; runs in parallel after the F0 API feasibility check.

---

## 2. Architecture overview

```
                 ┌──────────────────────── TRACK 1: CKG SPINE ───────────────────────────┐
 per-feed .nt ──▶ A. profile ──▶ B. preprocess ──▶ C. build crosswalk ──▶ E. convert ──▶ TTL ──▶ G. Virtuoso
 (CKG dumps)        (done)       (normalize,         (GND/VIAF→QID,         (apply mapping,        …/graphs/ckg-<feed>
                                  collapse plan)      cached map)            collapse, pivot)
                                                          │
                                       D. APSearch residue ─▶ OpenRefine (RDF-transform, Chrome) ─┘

                 ┌──────────────── TRACK 2: NATIVE MUSIC SUPPLEMENT ──────────────────────┐
 musiconn API ──▶ F0. feasibility check ──▶ F. fetch roles/names ──▶ emit TTL ──▶ G. Virtuoso
                                             join key = permalink                  https://linkedmusic.ca/graphs/musiconn/
```

- **Reconciliation is deterministic for musiconn/Detmold** (100% of entities carry GND/VIAF) → **no
  OpenRefine needed** for those feeds. OpenRefine (RDF-transform, **Chrome-only**) is used **only** for
  APSearch's label-based residue. This is the major simplification versus the RISM pipeline, which
  OpenRefines everything.
- **rdfconv is not usable here.** `shared/rdfconv/` is CSV-in only and loads the whole table in memory; CKG
  is RDF-native, reification-heavy, and multi-million-triple. We build a **bespoke two-pass streaming
  NT→TTL converter**, modelled on [rism/src/convert_to_rdf.py](../../rism/src/convert_to_rdf.py) and the
  existing streaming parser in [ckg/src/profile_predicate.py](../src/profile_predicate.py).

---

## 3. Repository layout to create

Follows the standard `<name>/{src,data,doc,openrefine}/` convention (cf. `cantus/`, `diamm/`, `rism/`).

```
ckg/
├── README.md                      # NEW — pipeline doc, standard 4-section structure
├── src/
│   ├── profile_predicate.py       # EXISTS — N-Triples predicate profiler
│   ├── preprocess.py              # NEW — normalize + build entity index + collapse plan (Stage B)
│   ├── build_crosswalk.py         # NEW — authority-ID → QID map via Wikidata (Stage C)
│   ├── convert_to_rdf.py          # NEW — two-pass NT→TTL: mapping + collapse + pivot (Stage E)
│   ├── fetch_musiconn.py          # NEW — native API supplement (Track 2)
│   └── ontology/
│       └── mapping.json           # NEW — runtime predicate map (reasoning log = predicate-evidence.md)
├── data/                          # gitignored; on disk only
│   ├── archived/                  # the CKG per-feed .nt dumps (source of truth)
│   ├── extracted/                 # normalized .nt + entity index (Stage B output)
│   ├── unreconciled/              # APSearch CSV for OpenRefine (Stage D input)
│   ├── reconciled/                # APSearch reconciled CSV (Stage D output)
│   ├── rdf/                       # final per-feed .ttl (Stage E output)
│   └── mappings/                  # crosswalk caches (authority→QID JSON, record-type QIDs, AAT QIDs)
├── openrefine/                    # APSearch only
│   ├── history/                   # OpenRefine operation-history JSON
│   └── export/                    # RDF-transform export template
└── doc/
    ├── INGESTION-PLAN.md          # this file
    ├── predicate-evidence.md      # EXISTS — finalized mapping + evidence
    └── sesemmi-schema.md          # NEW — schema doc for SESEMMI (Stage H)
```

**Conventions to honour (verified against committed code):**
- Namespaces: `wd: http://www.wikidata.org/entity/`, `wdt: http://www.wikidata.org/prop/direct/`,
  `lmckg: https://linkedmusic.ca/graphs/ckg/` — the **shared class namespace** for local types
  (`lmckg:Person/Place/Organization/Collection/Event/Work`), the same across all three feed graphs (the
  per-feed **graph IRIs** below are separate). Keep the CTO/NFDI predicate IRIs verbatim for "keep CTO"
  relations (`cto:` = `https://nfdi4culture.de/ontology/`, `nfdicore:` = `https://nfdi.fiz-karlsruhe.de/ontology/`).
- Wikidata pivot: separate triple `<authority-URI node> wdt:P2888 wd:Q…`, emitted **only when reconciled**.
- Graph IRIs (one named graph per feed): `https://linkedmusic.ca/graphs/ckg-musiconn/`,
  `https://linkedmusic.ca/graphs/ckg-detmold/`, `https://linkedmusic.ca/graphs/ckg-apsearch/`; Track 2
  supplement `https://linkedmusic.ca/graphs/musiconn/` (the native ingestion, kept distinct from CKG's
  `ckg-musiconn`).
- Python 3.12, Poetry at repo root; deps already available: `rdflib 7`, `aiohttp`, `aiolimiter`, `pandas`,
  `tomli`, `tqdm`, `isodate`. Formatter: `black`. Run scripts from `ckg/src/` (CWD convention).

### Inputs & implementation gotchas (read before coding)

- **Raw dumps (current location):** the per-feed N-Triples live at
  `raw_data/ckg/mnt/data/culture-kg-kitchen/data/production/E####/nt/E####.nt` (gitignored). Feed map:
  **musiconn = `E5320`**, **Detmold = `E5305`**, **APSearch = `E6304`** (RISM = `E5313`, excluded; image
  feeds = `E6161`/`E6064`). Stage B reads these directly, or copy them to `data/archived/` first.
- **Per-feed files are NOT subject-sorted** (only the merged `hermes-data-challenge.rdf.nt` is). Do **not**
  rely on streaming group-by-subject for them — the two-pass converter must build the entity/record index
  in pass 1 (hence Stage B's `<feed>.entities.json`), then rewrite in pass 2. On macOS, `awk` is BSD awk
  (no GNU 3-arg `match`); prefer Python for parsing.
- **`mapping.json` shape:** model it on `rism/src/ontology/mappingWithLog.json5` (source-predicate →
  `wdt:P*` with an inline reasoning log; a blank/absent target = drop). The authoritative mapping is
  [predicate-evidence.md](predicate-evidence.md) §4 — `mapping.json` is its runtime distillation.
- **Do NOT materialize Wikidata labels.** Reconciled entities stay as bare authority-URI nodes +
  `P2888`→QID (no fetched `rdfs:label`), matching every other LinkedMusic DB (e.g. TheSession performers
  are bare QIDs). Only **source-derived** labels — record/event/work titles via `rdfs:label` — are emitted.
  Human-readable names for reconciled entities are a query-side / SESEMMI concern, not an ingest concern.

---

## 4. The pipeline, stage by stage

### Stage A — Profiling (DONE)
[profile_predicate.py](../src/profile_predicate.py) characterised every predicate across the three music
feeds; results and the finalized mapping are in [predicate-evidence.md](predicate-evidence.md). No further
work unless we extend to the image feeds (then re-profile those).

### Stage B — Preprocess / normalize (`preprocess.py`, NEW)
A single streaming pass per feed producing (1) a cleaned N-Triples file and (2) an **entity index** the
converter needs. Memory is bounded by the entity index (~22.7k entities for musiconn → trivial).

Operations:
1. **Normalize the typo predicate** `…/NFDI0001006` → `…/NFDI_0001006` (1,704 musiconn triples; otherwise
   those VIAF links are lost).
2. **Build the entity index**: for every entity node (blank node typed `NFDI_0000003/4/5/107`), record
   `{bnode_id → (type, authority_URI)}`. These nodes carry *only* a type + one authority ID (verified).
3. **Build the record-type index**: for every record (`CTO_0001005` source item), record its classifier —
   the AAT URI from `CTO_0001026` (musiconn) or the CTO media class from `CTO_0001049` (APSearch) — so the
   converter can emit `P31`.
4. **Collect distinct authority IDs** (dedup the GND/VIAF URIs) → feed to Stage C.
5. **Note** record subjects are already stable URIs (the source permalink, e.g.
   `https://performance.musiconn.de/event/…`); **no record-URI minting is required.** Only entity blank
   nodes are collapsed (Stage E).

Output → `ckg/data/extracted/<feed>.norm.nt` + `ckg/data/extracted/<feed>.entities.json`.

### Stage C — Build the Wikidata crosswalk (`build_crosswalk.py`, NEW)
Resolve the deduped authority IDs to QIDs. **Volume (musiconn): 22,700 distinct IDs — 12,108 GND +
10,592 VIAF.** Method:
- Use [shared/wikidata_utils/client.py](../../shared/wikidata_utils/client.py) (`WikidataAPIClient.sparql`,
  async, rate-limited 20 req/s). Batch with SPARQL `VALUES` (~500 IDs/query):
  ```sparql
  SELECT ?id ?qid WHERE { VALUES ?id { "118508288" "..." } ?qid wdt:P227 ?id . }   # GND  (P227)
  SELECT ?id ?qid WHERE { VALUES ?id { "204566" "..." }   ?qid wdt:P214 ?id . }    # VIAF (P214)
  ```
  ≈ 25 GND + 22 VIAF batches ≈ **~50 queries total** → seconds of querying. (QLever is unnecessary at this
  scale; reserve it only if the image-feed stretch needs millions of IDs.)
- **AAT record types** (2 codes): resolve `?q wdt:P1014 "300262956"` / `"300417577"`, hand-verify; expect
  *musical performances* and *musical compositions* → e.g. works = `wd:Q207628`.
- **Cache** everything to `ckg/data/mappings/crosswalk.json` (`{authority_URI → QID}`) and
  `record_types.json` (`{classifier_URI → QID}`). Re-runnable; shared across feeds.

Coverage check: report % of distinct IDs that resolved (the unresolved remainder is the "residue" kept as
authority URIs). This number is the real reconciliation rate; surface it, don't hide it.

### Stage D — APSearch residue (OpenRefine, Chrome only)
APSearch has **no authority IDs** (crosswalkable 0.4%). For whatever entities it references by label,
follow the RISM precedent: flatten the relevant columns to CSV → reconcile in OpenRefine with the
**RDF-transform** extension (Chrome only) → export. Store history in `ckg/openrefine/history/`. This track
is small and isolated; it does **not** block the musiconn pilot.

### Stage E — Convert to RDF (`convert_to_rdf.py`, NEW)
Two-pass streaming converter (rdflib for emission, plain dict index for traversal, per RISM). Per feed:

**Pass 1** — load the entity index + crosswalk + record-type map (from B/C).

**Pass 2** — stream the normalized N-Triples and rewrite each triple by the finalized mapping
([predicate-evidence.md](predicate-evidence.md) §4), applying these rules:
- **Drop** the envelope/noise predicates (`dateModified`, `CTO_0001080`, `NFDI_0000207`, `NFDI_0000146`,
  `schema:item`, `schema:dataFeedElement`, `schema:associatedMedia`, `schema:sameAs`, `CTO_0001007`).
- **Remap** to `wdt:P*`: `NFDI_0000191→P123`, `NFDI_0000142→P275`, `CTO_0001070→P585`
  (coerce → `xsd:date`/`xsd:gYear`), `CTO_0001073→P571` (coerce), `BFO_0000050→P361`, `CTO_0001021→P953`.
  `NFDI_0001008→P973` **for Detmold only** — its value is a genuine external permalink; in musiconn and
  APSearch the value is just the record's own URI (self-referential), so **drop it** there.
- **Keep CTO** (verbatim IRI) for the role-agnostic backbone: `CTO_0001009/10/11/19/25/06`.
- **Collapse entity objects** (the no-blank-node rule): replace each entity blank node with its
  **authority URI** (GND/VIAF) — *always*, reconciled or not. The relation points to that authority-URI
  node; the QID is attached to the node via a separate `P2888` pivot (next bullet), never inlined as the
  relation object. Never emit a blank node; never mint a per-record node. This also **dedupes** (the same
  person reified across many records becomes one authority-URI node). This is the `mb:Area`-style
  local-node + `P2888` shape, not a direct relation→QID.
- **Pivot triple**: for each resolved entity, also emit `<authority_URI> wdt:P2888 <wd:QID>` once. (Entity
  "home URI" = its GND/VIAF URI; SESEMMI joins cross-DB through the P2888→QID bridge. Residue entities get
  no P2888.)
- **Type every node with a local class** (`rdf:type`), as the other LinkedMusic converters do: records →
  `lmckg:Event`/`lmckg:Work` (from the classifier); entities → `lmckg:Person`/`Place`/`Organization`/
  `Collection` (from the NFDI bnode type). Records *additionally* get `<record> wdt:P31 <record-type QID>`
  from the classifier map. **Do not** emit a `wdt:P31`→QID on real-world entities (Wikidata provides that
  for reconciled ones; the local `lmckg:` class is enough for SESEMMI to filter by kind).
- **`rdfs:label`** on records (event/work titles): keep verbatim.

Output → `ckg/data/rdf/<feed>.ttl`. Multiprocess per file if needed (RISM uses 6 workers).

### Stage F — Native musiconn supplement (`fetch_musiconn.py`, Track 2)
- **F0 — API feasibility check (a quick throwaway "spike"; do this in week 1, in parallel):** hit
  `performance.musiconn.de` for a handful of events and confirm (a) per-event person **roles/voice-types**
  are exposed, (b) person **names** are available, (c) records are addressable by the **same permalink**
  used as our record URI. If roles are *not* recoverable, Track 2's value collapses — we need to know
  early. (Open risk; see §8.)
- **F — build:** fetch roles for musiconn events, emit a parallel graph `https://linkedmusic.ca/graphs/musiconn/` keyed on the
  permalink. Model roles with Wikidata properties where faithful (e.g. composer `P86`, performer `P175`,
  conductor `P3300`, librettist `P87`), or `participant P710` + qualifier "object has role `P3831`" when a
  role lacks a dedicated property. Final modelling decided once the spike shows the API's actual shape.

### Stage G — Load into Virtuoso
- One named graph per feed: `https://linkedmusic.ca/graphs/ckg-musiconn/`, `https://linkedmusic.ca/graphs/ckg-detmold/`, `https://linkedmusic.ca/graphs/ckg-apsearch/`; supplement
  `https://linkedmusic.ca/graphs/musiconn/`.
- Bulk-load Turtle with the Virtuoso bulk loader (`ld_dir` + `rdf_loader_run`), **not** `file_to_string`,
  for large files (standard Virtuoso practice). Per the wiki's load runbook
  (`Virtuoso-Setup-Guide.md`), after loading rebuild the text index and register prefixes:
  ```sql
  ld_dir('/database/ckg', 'musiconn.ttl', 'https://linkedmusic.ca/graphs/ckg-musiconn/');
  rdf_loader_run();
  checkpoint;
  VT_INC_INDEX_DB_DBA_RDF_OBJ ();  urilbl_ac_init_db ();  s_rank ();
  ```
  Register `wd:`/`wdt:` namespaces in Conductor. Confirm graph IRIs match the SESEMMI schema doc.

### Stage H — Document for SESEMMI (`sesemmi-schema.md`)
Document each graph: the predicates in use (kept CTO relations + the `wdt:P*` set), the record types
(`P31` values), the `P2888` pivot, the permalink join key, and **example SPARQL** (within-graph,
cross-graph via `GRAPH`/`UNION`, and federated to Wikidata via `SERVICE` through `P2888`). Note image
fields for embedding (`P953` content URLs; rights via `NFDI_0000142`/`CTO_0001022`).

The kept CTO/NFDI predicates need human-readable labels so SESEMMI can interpret them (e.g. `CTO_0001009`
= "has related person"). Regenerate the full label dictionary from the merged dump with:
```
grep -E '^<https://(nfdi4culture\.de|nfdi\.fiz-karlsruhe\.de)/ontology/(CTO|NFDI)_[0-9]+> <http://www\.w3\.org/2000/01/rdf-schema#label>' raw_data/ckg/hermes-data-challenge.rdf.nt
```

---

## 5. Finalized property mapping (authoritative)

Reproduced from [predicate-evidence.md](predicate-evidence.md) §4 so this plan stands alone. All rows are
evidence-confirmed.

**Per-record fields** (subject = `CTO_0001005` source item, already a permalink URI):

| Source predicate | Mapping |
|---|---|
| `rdf:type` | local `rdf:type lmckg:*` (+ record `wdt:P31`→QID from classifier; see below) |
| `rdfs:label` | keep `rdfs:label` (event/work title) |
| `NFDI_0001008` has url | `P973` **(Detmold only)**; **drop** for musiconn + APSearch (self-referential) |
| `NFDI_0000191` published by | `P123` |
| `NFDI_0000142` has license | `P275` |
| `CTO_0001070` has temporal coverage | `P585` (→ `xsd:date`) |
| `CTO_0001073` has creation period | `P571` (→ `xsd:date`) |
| `CTO_0001026` has external classifier (AAT) | crosswalk AAT→QID via `P1014`, emit `P31` **and keep the AAT URI** |
| `CTO_0001049` has data concept (CTO media class) | class→QID, emit **`P31` only** |
| `CTO_0001021` has content url | **`P953`** |
| `CTO_0001007` has license statement | **drop** (values are broken stringified bnode IDs) |

**Relational backbone** — keep the CTO IRI; **object → the authority-URI node** (which carries
`rdf:type lmckg:*` and, when reconciled, `P2888`→QID):
`CTO_0001009` person · `CTO_0001010` organization · `CTO_0001011` location · `CTO_0001019` related item ·
`CTO_0001025` is-about · `CTO_0001006` is-referenced-in. And `BFO_0000050` part of → **`P361`**.

**Crosswalk + drops:** `NFDI_0001006` → resolve GND `P227` / VIAF `P214` → QID, pivot via `P2888`;
normalize `NFDI0001006`→`NFDI_0001006`; **drop** the DataFeed envelope (`dateModified`, `CTO_0001080`,
`NFDI_0000207`, `NFDI_0000146`, `schema:item`, `schema:dataFeedElement`, `schema:associatedMedia`,
`schema:sameAs`, `CTO_0001007`).

**`P31` record-type subtable** (records get a `wdt:P31`→QID below; every entity instead gets a local
`rdf:type lmckg:*` class — see Stage E):

| Record | `P31` QID |
|---|---|
| musiconn event (`aat:300262956` "musical performances") | musical-performance QID (verify via P1014) |
| musiconn work (`aat:300417577` "musical compositions") | `Q207628` (verify) |
| APSearch audio object (`CTO_0001043`) | audio/sound-recording QID |
| APSearch image object (`CTO_0001044`) | `Q478798` image (verify) |

---

## 6. Worked example — one musiconn work, before and after

**CKG input** (blank-node reification, no name, no role):
```
<…/work/polonaise-concertante-beethoven-ludwig-van> rdf:type            cto:CTO_0001005 .
<…/work/polonaise-concertante-beethoven-ludwig-van> cto:CTO_0001026     <aat/300417577> .
<…/work/polonaise-concertante-beethoven-ludwig-van> rdfs:label          "Polonaise concertante" .
<…/work/polonaise-concertante-beethoven-ludwig-van> cto:CTO_0001009     _:b277260 .
_:b277260  rdf:type        nfdicore:NFDI_0000004 .
_:b277260  nfdicore:NFDI_0001006  <https://d-nb.info/gnd/118508288> .
```

**LinkedMusic output** (no blank node; record + entity both locally typed; entity kept as its authority
URI; separate `P2888` pivot):
```
<…/work/polonaise-concertante-beethoven-ludwig-van> rdf:type    lmckg:Work ;
                                                    wdt:P31     wd:Q207628 ;          # musical composition
                                                    rdfs:label  "Polonaise concertante" ;
                                                    cto:CTO_0001009  <https://d-nb.info/gnd/118508288> .
<https://d-nb.info/gnd/118508288>  rdf:type   lmckg:Person ;
                                   wdt:P2888   wd:Q255 .                              # GND → Beethoven
```
The role ("composer") is recovered separately into `https://linkedmusic.ca/graphs/musiconn/` by Track 2.

---

## 7. Sequencing & milestones (today 2026-06-15 → due 2026-06-30)

| Days | Track 1 (spine) | Track 2 (supplement) |
|---|---|---|
| **1–2** | `preprocess.py` + `build_crosswalk.py` on musiconn; report QID coverage | **F0 spike**: confirm musiconn API exposes roles/names + permalink join |
| **3–5** | `convert_to_rdf.py` → `musiconn.ttl`; load `https://linkedmusic.ca/graphs/ckg-musiconn/`; validate with SPARQL → **pilot done** | — |
| **6–8** | Detmold (same machinery, ~1 day); finalize record-type QIDs | build `fetch_musiconn.py`; emit `https://linkedmusic.ca/graphs/musiconn/` |
| **9–11** | APSearch: flatten → OpenRefine reconcile → convert → load | join supplement ↔ spine; validate role queries |
| **12–13** | `sesemmi-schema.md` + example queries; image-URL embedding | — |
| **14–15** | buffer; **stretch**: image feeds breadth; polish; submit | — |

**Critical path = the musiconn vertical slice (days 1–5).** Every hard problem — blank-node collapse,
crosswalk join, date coercion, Virtuoso load, P2888 pivot — surfaces there at small scale before we widen.

---

## 8. Risks & open questions

1. **musiconn native API exposes roles? (highest risk.)** Track 2's entire value rests on it. Retire via
   the F0 spike in week 1. If roles aren't recoverable, fall back to spine-only (still on-brief) and say so.
2. **GND/VIAF → QID coverage.** 22,700 IDs resolve at some rate < 100%; the unresolved remainder stays as
   authority URIs (no QID). Report the real rate from Stage C; it sets expectations for cross-DB recall.
3. **Record-type & AAT QID picks** (§5 subtable) need human verification — small, do during the pilot.
4. **Virtuoso TTL bulk-load.** The wiki documents the JSON-LD load path explicitly; the TTL `ld_dir`/
   `rdf_loader_run` path is standard Virtuoso but should be confirmed on the staging server early.
5. **Role modelling vocabulary** (Stage F) — dedicated properties vs `P710`+`P3831` qualifier — decided
   after the spike reveals the API's shape; affects how SESEMMI queries roles.
6. **`is about real world entity` (`CTO_0001025`) indirection** points to a *bare* MusicEvent node. Decide
   during the pilot whether to keep it (as CTO) or collapse it into the record (the record already *is* the
   event). Low stakes.

---

## 9. Verification / testing

- **Stage B:** entity-index count == distinct entity bnodes; 0 occurrences of `NFDI0001006` (typo) remain.
- **Stage C:** crosswalk coverage report (resolved / 22,700); spot-check 10 known composers (Beethoven GND
  118508288 → Q255, etc.).
- **Stage E:** output TTL parses (`rdflib`); **0 blank nodes** in output (`grep -c '_:' == 0`); every
  `CTO_0001009` object is a GND/VIAF authority URI carrying `rdf:type lmckg:*` (and `P2888`→QID when
  reconciled); every record has a local `rdf:type` and exactly one `wdt:P31`; dates are typed.
- **End-to-end (pilot):** load `https://linkedmusic.ca/graphs/ckg-musiconn/`, then run example SPARQL:
  - "works that are musical compositions" (`?w wdt:P31 wd:Q207628`) returns ~40,810.
  - "events with their date and venue" (`P585` + `CTO_0001011`).
  - cross-DB: a composer's CKG works **and** RISM sources via the shared QID through `P2888`.
  - federated: pull the composer's Wikidata label via `SERVICE` (proves the pivot works without local names).
- **Track 2:** for a sample event, the native graph attaches the correct role (e.g. composer) to the same
  permalink that the spine graph uses.

---

## 10. Summary of decisions baked in

- Hybrid: **CKG spine + native musiconn supplement**, per-feed named graphs.
- **No OpenRefine** for musiconn/Detmold (deterministic GND/VIAF crosswalk); OpenRefine only for APSearch.
- **No blank nodes**: entity bnodes collapse to their authority URI (a persistent local node + `P2888`→QID when reconciled; also dedupes).
- **Wikidata pivot** via `wdt:P2888` on the persistent authority-URI node (relation→node→`P2888`→QID, not
  relation→QID). **Local `rdf:type` (`lmckg:*`) on every node**; records also get a `wdt:P31`→QID.
- **Bespoke streaming converter** (rdfconv is CSV-only); reuse the `shared/wikidata_utils` client for the crosswalk.
- Classifiers → **`P31` + keep the AAT URI**; content URL → **P953**; `CTO_0001007` → **drop**;
  `NFDI_0001008` → **P973 (Detmold only)**; role recovery via Track 2.
