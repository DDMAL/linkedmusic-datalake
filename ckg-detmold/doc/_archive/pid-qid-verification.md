# Manually verified PIDs and QIDs

Entries in this file were **not produced deterministically** (i.e., not via the WDQS crosswalk). Each was looked up manually during ingestion work and should be spot-checked before trusting in production. The verification date and source are recorded for each entry.

---

## Wikidata properties (P-IDs)

| PID | Label | Description (from Wikidata) | Used for | Verified |
|---|---|---|---|---|
| P57 | director | "director(s) of film, TV-series, stageplay, video game or similar" | `Inszenierung` on musiconn event pages | 2026-06-16 via wikidata.org/wiki/Property:P57 |
| P86 | composer | "person(s) who wrote the music" | `Komposition` on musiconn event pages | 2026-06-16 via wikidata.org/wiki/Property:P86 |
| P87 | librettist | "author of the libretto of an opera, operetta, oratorio or cantata" | `Libretto` on musiconn event pages | 2026-06-16 via wikidata.org/wiki/Property:P87 |
| P175 | performer | "actor, musician, band or other performer associated with this role or musical work" | Event→performer link for voice-type roles (Tenor/Sopran/Bass Stimmlage) | 2026-06-16 via wikidata.org/wiki/Property:P175 |
| P412 | voice type | "person's voice type" — **used on persons, not events**; expected values: soprano, mezzo-soprano, contralto, countertenor, tenor, baritone, bass | Emitted on the person node to capture voice type from Stimmlage strings; paired with P175 on the event | 2026-06-16 via wikidata.org/wiki/Property:P412 |
| P664 | organizer | "person or institution organizing an event" | `Veranstalter` on musiconn event pages (organisations) | 2026-06-16 via wikidata.org/wiki/Property:P664 |
| P710 | participant | "a person, group or organization that actively takes/took part in an event or process" | Fallback for unrecognised German role strings where no specific property can be confirmed | 2026-06-16 via wikidata.org/wiki/Property:P710 |
| P3300 | musical conductor | "the person who directs a musical group, orchestra or chorus" | `Dirigat` on musiconn event pages | 2026-06-16 via wikidata.org/wiki/Property:P3300 |
| ~~P3831~~ | ~~object of statement has role~~ | qualifier only — cannot be expressed in our Turtle without blank nodes; **dropped from Track-2 output** | — | 2026-06-16 |

### Previously proposed but WRONG

| PID | What I claimed | What it actually is | Notes |
|---|---|---|---|
| P3381 | "stage director" | **File Format Wiki page ID** — external identifier for the Archive Team's file format wiki | Corrected 2026-06-16 |

---

## Wikidata items (Q-IDs)

### musiconn record-type QIDs (Track-1 spine, already in `record_types.json`)

| QID | Label | Used for | Verified |
|---|---|---|---|
| Q6942562 | musical performance | `wdt:P31` for musiconn Events (aat:300262956 classifier) | Earlier session |
| Q207628 | composed musical work | `wdt:P31` for musiconn Works (aat:300417577 classifier) | Earlier session |
| Q838948 | work of art | `wdt:P31` fallback for classifier-less **Detmold** Works | Earlier session |

### APSearch (`E6304`) record-type / media-class QIDs (`record_types.json`)

Signed off 2026-06-18. Media classes keyed by CTO URI, AAT by Getty URI; all APSearch-only so they
don't affect musiconn/Detmold. See `apsearch-pid-qid-verification.md` for full reasoning.

| QID | Label | Used for | Verified |
|---|---|---|---|
| Q3302947 | audio recording | `CTO_0001043` audio + `aat:300028633` sound recordings | 2026-06-17/18 WD-API; AAT deterministic via P1014 |
| Q478798 | image | `CTO_0001044` image object | 2026-06-18 WD-API (chosen over Q125191 photograph) |
| Q30070675 | video recording ("single work or take") | `CTO_0001048` video object | 2026-06-18 WD-API (chosen over Q34508 "the technique"; parallels the audio "single object" choice) |
| Q234460 | text | `CTO_0001047` text object | 2026-06-18 WD-API (chosen over Q49848 document) |
| Q691783 | phonograph cylinder | `aat:300265798` cylinder phonographs (the medium, not the device — "close enough") | 2026-06-18 WD-API |
| Q17537576 | creative work | `wdt:P31` fallback for classifier-less **APSearch** records (incl. 4 ethnographic-AAT-only) | 2026-06-18 WD-API (chosen over Q838948 — ELAR records are linguistic documentation, not art) |

`aat:300234108` "ethnographic objects" is deliberately **left unmapped** (no precise Wikidata item;
it tags audio/image/text alike on the cylinder-collection records, which are already typed). The AAT
URI is kept for interoperability.

### APSearch license / publisher QIDs (`crosswalk.json`, via `wdt:P2888` pivot)

| Source URI | QID | Label | Source | Verified |
|---|---|---|---|---|
| nfdi4culture.de/id/E6404 | Q20007257 | CC BY 4.0 | NFDI `owl:sameAs` | 2026-06-18 WD-API |
| nfdi4culture.de/id/E6429 | Q18199165 | CC BY-SA 4.0 | NFDI `owl:sameAs` | 2026-06-18 WD-API |
| nfdi4culture.de/id/E2431 | Q219989 | Berlin-Brandenburg Academy of Sciences and Humanities (BBAW) | NFDI `owl:sameAs` | 2026-06-18 WD-API |

Note: `creativecommons.org/by-nc-sa/4.0` → Q42553662 is **NOT emitted** — it sits only on the media
bnode of 72 SMB records (whose record-level license is E6429); we emit the uniform record-level
license per record. `elararchive.org/legal` stays a residue URI (no QID).

### Track-2 role QIDs

#### Voice types — used with P412 on person nodes

| QID | Label | Description | Verified |
|---|---|---|---|
| Q27914 | tenor | "voice type, male singing voice" | 2026-06-16; provided by user, confirmed via wikidata.org |
| Q30903 | soprano | "type of singing voice with the highest vocal range" | 2026-06-16; provided by user, confirmed via wikidata.org |
| Q27911 | bass | "type of classical male singing voice" | 2026-06-16; provided by user, confirmed via wikidata.org |
| Q186506 | mezzo-soprano | "type of classical female singing voice between soprano and contralto" | 2026-06-16; provided by user, confirmed via wikidata.org |
| Q31687 | baritone | "vocal and pitch range above bass and below tenor" | 2026-06-16; provided by user, confirmed via wikidata.org |
| Q6983813 | alto | "vocal and pitch range above tenor and below soprano in polyphonic settings" | 2026-06-16; provided by user, confirmed via wikidata.org |
| Q223166 | countertenor | "high classical male singing voice" | 2026-06-16; provided by user, confirmed via wikidata.org |

Note: P412 (voice type) is a property on **persons**, so these QIDs are emitted as `<person_node> wdt:P412 wd:Q<voice>`, not on the event. Paired with `<event> wdt:P175 <person>`.

#### Occupation QIDs — secondary signal for ambiguous role strings (not emitted as main triples)

| QID | Label | Used as | Verified |
|---|---|---|---|
| Q3387717 | theatre director | P106 occupation to confirm P57 (director) mapping for `Inszenierung` | 2026-06-16 via wikidata.org/wiki/Property:P57 constraints |
| Q28054786 | opera director | P106 occupation to confirm P57 mapping for opera `Inszenierung` | 2026-06-16 via wikidata.org/wiki/Property:P57 constraints |

#### Detmold place QIDs (GeoNames → Wikidata, manual same-as)

These two Detmold places are major cities but were **not** caught by the deterministic ID crosswalk: Wikidata records the *admin-level* GeoNames ID on the city item, not the *populated-place* ID the Detmold source uses, so `haswbstatement:P1566=<source id>` returns nothing. The QIDs were confirmed manually and added to `crosswalk.json` as `wdt:P2888` same-as links (the two URIs denote the same city). The other two Detmold places (Minden→Q3846, Aachen→Q1017) *were* ID-matched deterministically and need no manual entry.

| Source GeoNames URI | City | QID | Wikidata's own P1566 (differs) | Verified |
|---|---|---|---|---|
| sws.geonames.org/2657896 | Zürich | Q72 | 7287650 (admin) | 2026-06-17 via wikidata.org/wiki/Q72 + sws.geonames.org/2657896 |
| sws.geonames.org/2910831 | Hannover | Q1715 | 6559065 (admin) | 2026-06-17 via wikidata.org/wiki/Q1715 + sws.geonames.org/2910831 |

Note: the GeoNames names were also corrected in this session — `GEONAMES_HARDCODED` in `fetch_authority_names.py` had mis-entered names (Aarau/Mannheim/Hamm) that did not match their IDs (Zürich/Minden/Hannover).

#### Role QIDs previously listed as output — removed

| QID | Why removed |
|---|---|
| Q779817 (event organizer) | Was proposed for P3831 qualifier — P3831 dropped from output; use P664 directly instead |

### Previously proposed but WRONG

| QID | What I claimed | What it actually is | Notes |
|---|---|---|---|
| Q2656775 | "organiser" | **Kineta** — 2005 film by Yorgos Lanthimos | Corrected 2026-06-16 |

---

## Notes

- **P3831 is dropped from our Track-2 output.** It is a Wikidata qualifier only; expressing it in Turtle requires blank-node reification (Wikidata uses `pq:P3831`), which violates our no-blank-nodes rule. Use specific direct properties (P57, P664, P3300, P175, P86, P87, P412) instead. Fall back to plain P710 for truly unresolvable roles.
- **Voice types:** emitted on the person node (`<person> wdt:P412 wd:Q<voice>`) paired with `<event> wdt:P175 <person>`. P412 is defined for persons, not events.
- **German role strings not yet enumerated** — a ~1k event dry-run is needed to collect all strings that actually appear before `role_map.json` can be completed. Strings expected but not yet verified: `Leitung` (direction), `Choreographie` (choreography), `Bühnenbild` (set design), `Dramaturgie` (dramaturgy), `Lichtgestaltung` (lighting), `Kostüm` (costume design), `Text` (lyrics/text). Each needs a Wikidata property lookup before being added to this table.
