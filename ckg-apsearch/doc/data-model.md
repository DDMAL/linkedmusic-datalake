# APSearch (`E6304`) — data model & mapping decisions

The authoritative reasoning behind the APSearch conversion. APSearch uses the **same converter
and `mapping.json`** as the other feeds ([`../../ckg-musiconn/doc/data-model.md`](../../ckg-musiconn/doc/data-model.md)
has the full predicate map); this doc records what is **APSearch-specific** — it exercises the
media-feed paths, not the relational backbone. Counts are from `apsearch.ttl`.

## 1. What the source looks like

APSearch is **ELAR (Endangered Languages Archive)** documentation — audio/image/video/text
recordings of endangered languages — remodeled into the **nfdicore / CTO** ontology. 6,271
records, each a `CTO_0001005` "source item" and `schema:CreativeWork`. It is **~98.9% ELAR +
~1.1%** (72) Staatliche Museen zu Berlin objects (those 72 are exactly the records carrying the
CC BY-NC-SA license and `id.smb.museum` URLs).

**It differs from musiconn/Detmold:** no persons, no `has related person/organization/location`
backbone, and **0 authority IDs** (~0.4% Wikidata-crosswalkable). The reconcilable content
(languages, countries, depositors) is **not in the CKG dump** — it lives in the ELAR source,
behind an access wall — so it is not represented in this dataset. What *is* reconcilable is
small and fully deterministic: media-class typing, AAT classifiers, and the license/publisher
pivots. There is no relational backbone to collapse and no OpenRefine pass.

## 2. Predicate map (APSearch-exercised rows)

| Source predicate | Action | Result |
|---|---|---|
| `rdf:type` | type | record → `lmckg:Work` |
| `rdfs:label` | label | keep `rdfs:label` (free-text description/title) |
| `CTO_0001049` has data concept | classifier_media | `wdt:P31` from the media class (§3) |
| `CTO_0001026` has external classifier | classifier_aat | `wdt:P31` from AAT (deterministic) + keep the AAT URI (§3) |
| `CTO_0001073` has creation period | remap_date | `wdt:P571` → `xsd:gYear` (§4) |
| `NFDI_0000142` has license | remap (+ pivot) | `wdt:P275` → license URI; the URI carries `wdt:P2888` → QID (§5) |
| `NFDI_0000191` published by | remap (+ pivot) | `wdt:P123` → publisher URI; carries `wdt:P2888` → QID (§5) |
| `CTO_0001021` has content url *(via `associatedMedia` bnode)* | join + remap | `wdt:P953` content URL (§6) |

### Dropped — confirmed CKG provenance, not ELAR content

- `dateModified` — a single constant (`2025-11-21`) across all records = CKG's harvest date,
  not a per-record ELAR edit date.
- `NFDI_0000146` "metadata media type" = E3087 (application/json) — describes how CKG
  *serialized* its metadata (the export is JSON), **not** the audio/image content type (there
  is no content-MIME field in the dump).
- `NFDI_0000207` "metadata standard" (RDF/Schema.org) — constant CKG-ETL values.
- `NFDI_0000125` — one dataset-level link (subject is the dataset entity, not a record).
- `schema:associatedMedia` — the record→media-bnode edge; used to join the content URL back to
  the record (§6), then dropped (the bnode is never emitted).
- `schema:dateModified`, `schema:item`, `schema:dataFeedElement`, `schema:sameAs` — envelope.

## 3. Record typing (`P31`)

Every record is `lmckg:Work` and gets `wdt:P31` from its media class (`CTO_0001049`), with an
AAT classifier (`CTO_0001026`) adding a second `wdt:P31` on the few records that carry one. A
record with no resolving classifier falls back to **`Q17537576` "creative work"** — chosen
over Detmold's `Q838948` "work of art" because ELAR records are **linguistic documentation,
not art**. (6,271 records, 6,590 `wdt:P31` total → ~319 records carry a 2nd, AAT-derived type.)

| Source class / code | `wdt:P31` QID | count | note |
|---|---|---|---|
| `CTO_0001043` audio object | `Q3302947` audio recording | 3,005 | "single object representing recorded audio" |
| `CTO_0001044` image object | `Q478798` image | 523 | chosen over `Q125191` photograph (not all are photos) |
| `CTO_0001048` video object | `Q30070675` video recording | 454 | "single work/take" — parallels audio; **not** `Q34508` (the technique) |
| `CTO_0001047` text object | `Q234460` text | 52 | chosen over `Q49848` document |
| `aat:300028633` sound recordings | `Q3302947` audio recording | 84 | **deterministic** via `wdt:P1014` |
| `aat:300265798` cylinder phonographs | `Q691783` phonograph cylinder | 84 | the *medium*, not the device ("close enough") |
| `aat:300234108` ethnographic objects | *(unmapped)* | 92 | no precise Wikidata item; AAT URI kept, no `P31` from it (the record is already typed by its media class / fallback) |
| `CTO_0001045` media object (1 rec) | *(none → fallback)* | 1 | too generic |
| **fallback** (no resolving classifier) | `Q17537576` creative work | 2,472 | incl. the 4 ethnographic-AAT-only records (caught by the post-loop fallback) |

All media-class/AAT URIs are **APSearch-only**, so wiring them into `record_types.json` leaves
musiconn/Detmold reconverting byte-identically.

## 4. Dates — all-placeholder `gYear`

`CTO_0001073` "creation period" (4,214 values) has **zero day-precision dates**: *every* value
is a Jan-01 full-day placeholder — 4,086 single-year (`"2015-01-01/2015-01-01"`) and 128
multi-*year* ranges (`"1909-01-01/1950-01-01"`, mostly 1909–1950). A naïve `xsd:date` would
assert false day precision, so APSearch coerces **every interval → `xsd:gYear` of the start
year** (`coerce_date(o, "apsearch")`). All `wdt:P571` values are `xsd:gYear`; the end-year of
the 128 multi-year ranges is not retained. This branch is APSearch-only — Detmold has no
Jan-01 same-day spans and musiconn has no intervals.

> **Lake-wide date note for SESEMMI:** dates are mixed-precision across feeds (`xsd:date` /
> `gYearMonth` / `gYear`). The robust, datatype-agnostic year filter to teach the query layer
> is `FILTER(STRSTARTS(STR(?d), "2015"))` — `YEAR(?d)` only works on `xsd:date`/`dateTime` and
> breaks on `gYear`. (SESEMMI is LinkedMusic's natural-language→SPARQL query tool.)

## 5. Licenses & publisher (`P2888` pivots)

License/publisher URIs are kept as the object and pivoted to a QID via the **same local-node +
`P2888`** shape used for backbone entities (`P275`/`P123` are `wikibase-item` properties, so
the object must be a QID — the URI node carries the pivot). QIDs resolved via NFDI `owl:sameAs`:

| field | source URI | `wdt:P2888` QID | label |
|---|---|---|---|
| license `P275` | `nfdi4culture.de/id/E6404` (562) | `Q20007257` | CC BY 4.0 |
| license `P275` | `nfdi4culture.de/id/E6429` (92) | `Q18199165` | CC BY-SA 4.0 |
| license `P275` | `www.elararchive.org/legal` (5,617) | *(residue, no QID)* | ELAR custom access terms |
| publisher `P123` | `nfdi4culture.de/id/E2431` (6,271) | `Q219989` | BBAW (Berlin-Brandenburg Academy) |

→ 3 distinct `wdt:P2888` pivots in the output. **Not emitted:** the CC BY-NC-SA value
(`Q42553662`) — it sits only on the *media bnode* of the 72 SMB records (whose *record-level*
license is E6429/CC BY-SA); we emit the uniform record-level license per record.

## 6. Content URLs (`P953`)

The content URL (`CTO_0001021`) sits on the `schema:associatedMedia` **blank node**, not the
record. `preprocess.py` joins record → `associatedMedia` bnode → `CTO_0001021` and the
converter emits `<record> wdt:P953 <url>` (a URI node, post-loop) — **3,783** of them. The
URLs split two ways: 3,711 `hdl.loc.gov/hdl:2196/…` ELAR handles + 72 `id.smb.museum/…` SMB
assets (the rest have no content URL). `P953` "work available at URL" was chosen because the
repo has no competing convention for access pages (diamm uses `P856` for institution sites,
cantusdb `P18` for direct image files — neither fits these access/landing pages).

## 7. Emitted schema (SESEMMI reference)

Namespaces: `lmckg:` = `https://linkedmusic.ca/graphs/ckg/` (local classes), `wdt:`/`wd:`
Wikidata, `cto:` = `https://nfdi4culture.de/ontology/`.

```turtle
<record-iri> rdf:type lmckg:Work ;
             wdt:P31  wd:Q3302947 ;                 # audio recording (media class)
             rdfs:label "…description…" ;
             wdt:P571 "2010"^^xsd:gYear ;            # inception
             wdt:P275 <nfdi…/E6404> ;                # license (URI node, pivoted)
             wdt:P123 <nfdi…/E2431> ;                # publisher (URI node, pivoted)
             wdt:P953 <https://hdl.loc.gov/hdl:2196/…> .   # content URL

<nfdi…/E6404> wdt:P2888 wd:Q20007257 .               # → CC BY 4.0
<nfdi…/E2431> wdt:P2888 wd:Q219989 .                 # → BBAW
```

Every record is `lmckg:Work`; there are **no entity nodes** (no persons/places). Reconciled
licenses/publisher reach Wikidata via `wdt:P2888`. Namespaces as in the musiconn data-model.

## 8. Manually verified IDs

All record-type and license/publisher QIDs were confirmed against Wikidata — media:
`Q3302947` audio, `Q478798` image, `Q30070675` video, `Q234460` text, `Q691783` phonograph
cylinder, `Q17537576` creative-work fallback (`aat:300234108` ethnographic deliberately left
unmapped); licenses/publisher: `Q20007257`, `Q18199165`, `Q219989`.
