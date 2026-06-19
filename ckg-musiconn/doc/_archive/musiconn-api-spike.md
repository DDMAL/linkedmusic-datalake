# musiconn Track-2 API spike — findings (2026-06-16)

## Summary

**Roles can be recovered. No JSON API exists yet; the only access mechanism is HTML scraping of the event permalink pages.**

All three feasibility checks pass (via HTML), but the access route is scraping, not a clean API:

| Check | Result | Notes |
|---|---|---|
| 1. Per-event person roles/voice-types exposed? | **YES** | "Beteiligte Personen" section of event HTML; German role strings |
| 2. Person names available? | **YES** | Shown in the event HTML link text; full record on person page |
| 3. Events addressable by CKG permalink? | **YES** | CKG event slug URIs serve the HTML page directly |

---

## What the site exposes

### Event page (event permalink slug → HTML)

URL pattern: `https://performance.musiconn.de/event/<slug>`  
The CKG's event URIs are exactly these slugs, so they serve as direct join keys.

The HTML "Beteiligte Personen" section contains one `<li>` per person:

```html
<a href="/person/id/13307/">Mauceri, John</a>
<ul class="list-inline sep--comma-brackets"><li>Dirigat</li></ul>

<a href="/person/id/3430/">Klotz, Helmut</a>
<ul class="list-inline sep--comma-brackets"><li>Tenor (Stimmlage)</li></ul>

<a href="/person/id/13306/">Heinicke, Michael</a>
<ul class="list-inline sep--comma-brackets"><li>Inszenierung</li></ul>
```

Each person gives: **numeric site-ID**, **display name**, and **role string(s)** (comma-separated in the `<li>`s).

A parallel "Beteiligte Körperschaften" section does the same for organisations, also with optional role strings (e.g. "Veranstalter").

### Person page (numeric ID → HTML)

URL pattern: `https://performance.musiconn.de/person/id/<numeric-id>/`  
(Slug-based person pages like `performance.musiconn.de/person/kaufmann-f` return HTTP 200 but render empty — only the CMS shell, no data. The CKG's slug-based person residue URIs cannot be looked up this way.)

The person page exposes:
- Display name + alternate names
- Birth year and place
- Wikidata QID **directly** (e.g., `Q3182015`)
- GND, VIAF (authority IDs we already have in `crosswalk.json`)

### No JSON API

All `/api/*` paths return 404. The FAQ states (verbatim):

> *"Wir planen unsere GraphQL-Schnittstelle zeitnah bereitzustellen."*  
> ("We plan to provide our GraphQL interface soon.")

The `CTO_0001080` value `"https://performance.musiconn.de/api"` in the CKG feed is a placeholder pointing at an API base that is not yet deployed.

---

## Join strategy

Two populations of persons in the CKG event graph:

**A — Authority-backed** (bnodes with GND/VIAF → collapsed to authority URI; QID in `crosswalk.json`):  
Event HTML → person numeric ID → person page → **use Wikidata QID shown directly on the page** (no crosswalk fetch needed). Fallback: GND→crosswalk, VIAF→crosswalk.

**B — Residue** (bare slug URIs like `performance.musiconn.de/person/kaufmann-f`, no authority):  
No direct link from the event HTML (which uses numeric IDs) to the slug form. Residue persons cannot be looked up by slug.  
**Decision: emit the role triple with the CKG slug URI as the person node; leave the node unreconciled for OpenRefine later.** Don't skip — the role data is still worth keeping.

---

## Role string → Wikidata property mapping (draft)

The German role strings from the HTML need mapping before a full run; the ones observed in this spike.
All PIDs and QIDs in this table have been manually verified — see `ckg/doc/pid-qid-verification.md`.

| German string | Wikidata property | Notes |
|---|---|---|
| `Dirigat` | **P3300** musical conductor | unambiguous |
| `Tenor/Sopran/Bass/etc. (Stimmlage)` | **P175** performer on event + **P412** voice-type QID on person | P412 is person-level only; emit both. Voice QIDs verified in pid-qid-verification.md |
| `Inszenierung` | **P57** director | Covers stageplay/opera; opera director (Q28054786) in P57's scope |
| `Komposition` (expected) | **P86** composer | |
| `Libretto` (expected) | **P87** librettist | |
| `Veranstalter` | **P664** organizer | Direct property; cleaner than P710 + P3831 qualifier (P3831 requires blank nodes, dropped) |
| other / unrecognised | **P710** participant | Fallback; person's Wikidata P106 occupation may help resolve ambiguous strings |

**Join strategy update (2026-06-16):**
- **Authority-backed persons (A):** Use the Wikidata QID exposed directly on the musiconn person page — no need to re-crosswalk via GND/VIAF.
- **Residue persons (B):** Emit the role triple with the raw person slug URI as subject and no `P2888`; leave for OpenRefine reconciliation later (same policy as Track-1 residue). Do not skip entirely.

A full inventory of role strings requires a broader crawl (not done in this spike — too many pages). A dry-run pass could collect all `<li>` texts from the "Beteiligte Personen" sections before any triple emission.

---

## Sketch: `fetch_musiconn.py`

Would live at `ckg/src/fetch_musiconn.py`. Outline:

```
Inputs:
  ckg/data/extracted/musiconn.entities.json  — event IRI list (subjects of CTO_0001005)
  ckg/data/mappings/crosswalk.json          — authority_URI → QID
  ckg/src/ontology/role_map.json            — German role string → { prop, object_qid? } (to create)

Output:
  ckg/data/rdf/musiconn-roles.ttl
  Staged to: raw_data/ckg-musiconn-roles/ → graph https://linkedmusic.ca/graphs/musiconn/

For each event URI (65,359 events):
  1. GET https://performance.musiconn.de/event/<slug>
     User-Agent: LinkedMusic-datalake/1.0 (liam.pond@mail.mcgill.ca)
     Rate: ~1 req/s or configurable; retry on 429/5xx; skip on 404
  2. Parse HTML: extract "Beteiligte Personen" / "Beteiligte Körperschaften" sections
     → list of (person_numeric_id, display_name, [role_string, ...])
  3. For each person with at least one role string:
     a. GET /person/id/<numeric_id>/  (first-time only; cache numeric_id → QID)
     b. Parse Wikidata QID directly from the person page (shown as "Wikidata: QNNN")
        — no crosswalk needed for authority-backed persons
     c. If no Wikidata QID on page: try GND→crosswalk, then VIAF→crosswalk
     d. If still unresolved (residue slug URI only): keep the person's CKG slug URI as-is,
        emit the role triple against it, leave for OpenRefine (do not skip)
  4. Map role strings to Wikidata properties via role_map.json
     - known role → emit e.g. `<event> wdt:P3300 wd:QNNN .`  (conductor)
     - voice type string → emit `<event> wdt:P175 <person_IRI> .`
                          AND `<person_IRI> wdt:P412 wd:Q<voice_type> .`
     - unknown role → check person's Wikidata P106 occupation as secondary signal,
       else emit `<event> wdt:P710 <person_IRI> .` (participant fallback, role info lost)
  5. Write TTL; verify (0 blank nodes, rdflib parse, spot-check)
```

Scale note: 65k event GETs + N person GETs (cached across events) → days of crawling at 1 req/s.  
Realistic approach: start with a subset (e.g., events from `Staatsoper Dresden` or a single series), validate the shape, then decide whether to crawl fully or wait for the GraphQL API.

---

## Recommendation

**Track 2 is feasible — proceed via HTML scraping, with caveats.**

1. The data is unambiguously there (roles, names, authority IDs on the HTML pages).  
2. The join key works for authority-backed persons (~79% of relation-weighted persons); residue persons would be skipped in Track 2 (acceptable — same policy as Track 1 residue).  
3. **Pre-condition before a full run:** build `role_map.json` by doing a dry-run pass over a ~1k event sample to enumerate all role strings in the wild; then complete the Wikidata property mappings. This is low-cost.
4. **GraphQL caveat:** the FAQ says the API is coming "soon". If it appears before the 2026-06-30 deadline, switch to it — the scraper is disposable.
5. Rate-limit to ≤ 1 req/s; set the agreed `User-Agent`; don't parallelise across IPs. Contact `musiconn.performance(at)slub-dresden.de` if a full-scale crawl is planned (the FAQ lists them for API inquiries).
