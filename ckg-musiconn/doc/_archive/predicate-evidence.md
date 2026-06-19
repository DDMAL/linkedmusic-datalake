# CKG Music Feeds — Predicate Evidence Sheet

Evidence for the finalized property mapping; **§4 is the authoritative mapping** an implementer should
follow (the runtime `mapping.json` is its distillation). Produced by `ckg/src/profile_predicate.py` over
the three music feeds at `raw_data/ckg/mnt/data/culture-kg-kitchen/data/production/<E####>/nt/<E####>.nt`
(gitignored); ontology labels and the two AAT concept labels pulled from the merged 14 GB dump and
`vocab.getty.edu`.

- **musiconn** `E5320` — 537 MB, ~3.0M triples, 106,169 records
- **APSearch** `E6304` — 23 MB, ~129k triples, 6,271 records
- **Detmold** `E5305` — 5 MB, ~31k triples, 1,694 records

## 1. The three feeds are structurally different

| | musiconn | Detmold | APSearch |
|---|---|---|---|
| Record class | `CTO_0001005` "source item" | same | same |
| Relational backbone | person + org + place + collection | person (+ a few places) | **none** |
| Authority IDs (`NFDI_0001006`) | 315,691 (GND+VIAF) | 2,690 | **0** |
| Wikidata-crosswalkable | 67.6% (persons/places/orgs 100%) | 35.6% (persons 100%) | **0.4%** |
| Media content | — | — | content URLs + audio/image objects |
| Native-supplement value (roles) | **high** (128k role-stripped person links) | low (2.4k person links) | **n/a** (no persons) |

**Consequence:** native-API role recovery applies to **musiconn** (big) and marginally **Detmold**.
**APSearch has no persons or authority IDs** — it is a media/content feed needing label-based
reconciliation, not role recovery. Treat it as a separate track.

## 2. The entity-reification model (musiconn) — the key structural finding

`has related person/org/location` and `part of` all point to **blank nodes**, and those blank nodes are
**typed entity nodes carrying exactly two triples: an `rdf:type` and one authority identifier — and
nothing else.** A person node, in full:

```
_:bb277260  rdf:type      NFDI_0000004 (person)
_:bb277260  NFDI_0001006  <https://d-nb.info/gnd/118508288>
```

The relation/entity counts match exactly:

| Relation (object = bnode) | bnode count | Typed entity it points to | `NFDI_0001006` count |
|---|---|---|---|
| `CTO_0001009` has related person | 128,205 | `NFDI_0000004` **person** | 128,205 |
| `CTO_0001011` has related location | 84,244 | `NFDI_0000005` **place** | 84,244 |
| `CTO_0001010` has related organization | 65,724 | `NFDI_0000003` **organization** | 65,724 |
| `BFO_0000050` part of | 35,418 | `NFDI_0000107` **collection** | 35,418 |

`NFDI_0001006` objects resolve to **GND (`d-nb.info`, 57%) and VIAF (`viaf.org`, 43%) only** — no Getty/TGN/Iconclass on the music entities.

**Four consequences:**

1. **Names are NOT in the CKG dump.** Entity nodes carry no `rdfs:label`/name — only their authority ID
   (confirmed: `rdfs:label` is on 100% of source-items, 0% of entity nodes). The only literal labels are
   event/work **titles**. Display names must come from Wikidata (reconciled) or the native API (supplement).
2. **No blank nodes in output** (LinkedMusic design rule): **collapse each entity bnode to its authority
   URI** (GND/VIAF), and emit a separate `wdt:P2888` pivot to the QID when reconciled. The relation always
   points to the persistent authority-URI node — never directly to the QID, never to a blank node:
   `<event> cto:hasRelatedPerson <gnd-URI>` plus `<gnd-URI> wdt:P2888 wd:Q255` (reconciled), or just
   `<gnd-URI>` (residue). This matches the local-node-plus-`P2888` shape already used for `mb:Area`/`diamm:City`.
3. **This dedupes for free.** The same real-world entity is reified as a *separate* bnode in every record
   (e.g. one VIAF appears as 3 distinct bnodes across 3 events). Collapsing by authority URI/QID merges
   them — so **skolemize by authority URI, never by bnode id**.
4. **Crosswalk build reduces to two maps: GND→QID (`P227`) and VIAF→QID (`P214`)** — covers 100% of
   musiconn's and Detmold's authority-linked entities. TGN/Iconclass/AAT-of-people not needed.
5. **Role flattening is evidence-backed:** 128,205 person↔event links, each person fully identified but
   with **zero role/voice-type** on the relation — exactly what the native musiconn supplement recovers.

## 3. Data-quality warts

- **`NFDI0001006` (missing underscore)** — 1,704 triples in musiconn, a malformed duplicate of
  `NFDI_0001006`. **Normalize to `NFDI_0001006` on ingest** or those IDs are lost.
- **`CTO_0001007` "has license statement" values are stringified blank-node IDs** (`"Na32a97bf…"`, the
  RDFLib `N`+32-hex format) — a CKG export bug; the real license-statement content is gone/dangling. **Drop.**
- **`CTO_0001070`/`CTO_0001073` dates are plain literals** (e.g. `"1919-11-15"`), not typed. **Coerce to
  `xsd:date`** (year-only → `xsd:gYear`). musiconn `CTO_0001070` is uniformly `YYYY-MM-DD` (all 65,348
  verified; `CTO_0001073` does not occur in musiconn), so coercion is trivial for the pilot; keep a
  fallback that leaves the literal as-is if a value will not parse (for Detmold/APSearch creation periods).

## 4. Finalized mapping table

Status: **confirmed** = settled · **drop** = provenance/structural noise.

### Per-record fields (on `CTO_0001005` "source item")

| Source predicate (label) | Mapping | Status | Evidence |
|---|---|---|---|
| `rdf:type` | local `rdf:type lmckg:*` (+ record `P31`→QID via classifier; see §4) | confirmed | — |
| `rdfs:label` | keep `rdfs:label` | confirmed | record (event/work) titles |
| `NFDI_0001008` has url | **drop (all feeds)** | confirmed (Detmold, 2026-06-15) | object is the record's own URI/URL → self-referential in **every** feed incl. Detmold (the 1,694 Detmold values are byte-identical to the subject IRI), *correcting* the plan's earlier guess that Detmold's was a distinct external permalink. The subject IRI already *is* the source permalink, so no P973 adds information. (`url_permalink` action retained in code but unused.) |
| `NFDI_0000191` published by | `P123` | confirmed | — |
| `NFDI_0000142` has license | `P275` | confirmed | proper license URI (the real license field) |
| `CTO_0001070` has temporal coverage | `P585` point in time (→`xsd:date`) | confirmed | 65,348 event records; performance dates |
| `CTO_0001073` has creation period | `P571` inception (→`xsd:date`/`gYearMonth`/`gYear`) | confirmed | APSearch media + Detmold records. **Detmold (verified 2026-06-15):** all 254 values are `schema:DateTime` `START/END` intervals that encode precision — same day (`…T00:00:00/…T23:59:59`) → `xsd:date`; a full calendar month → `gYearMonth`; a full calendar year (Jan 1–Dec 31) → `gYear`. `coerce_date` was extended to reduce the interval accordingly. |
| `CTO_0001026` has external classifier | crosswalk AAT→QID (via `P1014`), emit `P31` **and keep the AAT URI** | confirmed | `aat:300262956`="musical performances" (events), `aat:300417577`="musical compositions" (works); keep the AAT link for interoperability rather than dropping it |
| `CTO_0001049` has data concept | class→QID, emit **`P31` only** | confirmed | CTO media classes `CTO_0001043` "audio object", `CTO_0001044` "image object"; source classifier dropped |
| `CTO_0001021` has content url | **`P953`** full work available at URL | confirmed | embeddable media URL (APSearch); P953 only, not dual-emitted |
| `CTO_0001007` has license statement | **drop** | confirmed | values are stringified bnode IDs (export bug); real license = `NFDI_0000142`→`P275` |

### Relational backbone (role-agnostic → keep CTO; object → the authority-URI node, which carries `P2888`→QID)

| Source predicate (label) | Mapping | Status | Evidence |
|---|---|---|---|
| `CTO_0001009` has related person | keep CTO | confirmed | → person entity (GND/VIAF), **no role attached** |
| `CTO_0001010` has related organization | keep CTO | confirmed | → organization entity |
| `CTO_0001011` has related location | keep CTO | confirmed | → place entity; role-agnostic (not remapped to P276) |
| `CTO_0001019` has related item | keep CTO | confirmed | 348k in musiconn; structural bridge |
| `CTO_0001025` is about real world entity | keep CTO (or collapse) | confirmed | bridges source-item → bare real-world-entity node |
| `CTO_0001006` is referenced in | keep CTO | confirmed | structural bridge |
| `BFO_0000050` part of | `P361` | confirmed | → collection node (which itself crosswalks) |

### Crosswalk + drops

| Source predicate (label) | Mapping | Status | Evidence |
|---|---|---|---|
| `NFDI_0001006` has external identifier | resolve GND(`P227`)/VIAF(`P214`)/**GeoNames(`P1566`)**→QID; pivot via `P2888` | confirmed | GND 57% / VIAF 43%; one per typed entity. **Detmold (verified 2026-06-15):** persons are GND/VIAF; **all 38 distinct place authorities are GeoNames** (`sws.geonames.org`). `build_crosswalk.py` was extended with GeoNames `P1566` (generic + musiconn-safe — musiconn has 0 GeoNames), resolving **34/38 places (89.5%)** (e.g. `geonames/2761369`→`Q1741` Vienna, `→Q64` Berlin, `→Q1085` Prague); the 4 unresolved stay as `lmckg:Place` residue. |
| `NFDI0001006` (typo, no underscore) | normalize → `NFDI_0001006` | confirmed | 1,704 triples; data fix |
| `dateModified`, `CTO_0001080` source file, `NFDI_0000207` standard, `NFDI_0000146` media type, `schema:item`, `schema:dataFeedElement`, `schema:associatedMedia`, `schema:sameAs`, `CTO_0001007` | drop | confirmed | DataFeed envelope / provenance noise / broken field; collapse `associatedMedia` to its `CTO_0001021` content URL |

### Class→QID subtable (for record `P31`)

We type entities the way the other LinkedMusic converters do: assign a **local class** (`rdf:type`) at
ingest, derived from the source structure. Every collapsed entity node gets a local type from its NFDI
bnode type — `lmckg:Person` (`NFDI_0000004`), `lmckg:Place` (`NFDI_0000005`), `lmckg:Organization`
(`NFDI_0000003`), `lmckg:Collection` (`NFDI_0000107`) — matching the local-typed `mb:Area`/`lmcd:Source`
precedent (the same nodes that carry `P2888`). **Records** additionally get a `wdt:P31`→QID from their
classifier (records are *not* Wikidata entities, so SESEMMI must filter them by kind):

| Record (via its classifier) | `P31` QID | Note |
|---|---|---|
| musiconn event (`aat:300262956`) | musical performance QID | resolve via `?q wdt:P1014 "300262956"` / hand-pick + verify |
| musiconn work (`aat:300417577`) | `Q207628` musical composition | verify via P1014 |
| **Detmold record (no classifier; is-about = `schema:CreativeWork`)** | **`Q838948` work of art** | verified 2026-06-15. Detmold records carry **no** AAT/media classifier, so P31 derives from the record *kind* (`schema:CreativeWork` → `lmckg:Work` → Q838948), emitted via `RECORD_KIND_P31` in `convert_to_rdf.py`, not the classifier path. Heterogeneous Hoftheater Detmold repertoire (operas + spoken plays + Singspiele) needs a class correct for *all* records. Chosen on two axes: (1) Q838948 is a verified `P279*` superclass of **both** `Q25379` play and `Q1344` opera — whereas `Q207628` "composed musical work" is a superclass of opera but **not** play, so it would mis-type the spoken dramas; (2) among the valid common ancestors it is the best-connected federation hub (86 statements / 67 sitelinks, vs 23 for `Q17537576` "creative work", 18 for `Q386724` "work"). |
| APSearch audio object (`CTO_0001043`) | audio/sound-recording QID | hand-pick + verify |
| APSearch image object (`CTO_0001044`) | `Q478798` image (or photograph) | hand-pick + verify |

(The local `lmckg:` class covers both reconciled and residue entities, so SESEMMI can filter by kind
without federation. A `wdt:P31`→QID on real-world entities is *not* emitted — Wikidata already provides
that for reconciled ones, and the local class is enough for filtering.)

## 5. Implications for the plan

- **Crosswalk build is just GND→QID + VIAF→QID** for the music slice (+ 2 AAT codes + ~4 record-type QIDs
  by hand). Much smaller than the original GND/VIAF/AAT/TGN/Iconclass list.
- **musiconn is the right vertical-slice pilot:** richest structure, 100%-identified backbone, and the
  feed where the native supplement pays off.
- **APSearch is a different track** (media + label reconciliation, no roles).
- **No blank nodes** survive: entity bnodes collapse to authority URI / QID; that also dedupes entities.
