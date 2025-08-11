Developer Cheat Sheet: LinkedMusic Dataset Pipelines & Mapping Assets
====================================================================
Purpose
-------
Practical, consolidated reference for NLQ→SPARQL development. Summarizes: fetch + processing flows, reconciliation approach, where existing Wikidata (or interim) mappings live, typical property usage, lexical phrases likely to map to Wikidata PIDs, and seeding sources for `property_mappings.json`.

High‑Value Takeaways (TL;DR)
----------------------------
- We already have rich per‑dataset mapping artefacts: reuse them instead of recreating.
- MusicBrainz & DIAMM provide the densest Wikidata PID surface (relationships + attributes) → prime for initial lexicon.
- RISM & Cantus supply edge cases (specialist musical source / liturgy terms) → include controlled expansion tokens.
- The Session adds community / performance context (sessions, sets, tune popularity) → expect NL about “popular tunes”, “sets containing X”, “recordings by artist Y”.
- Many interim properties (JSON‑LD contexts, made‑up Cantus URIs) must be normalized to Wikidata before relying on them in prompts.

Dataset Summaries
-----------------

### MusicBrainz
Source Type: Public JSON dump (.tar.xz → JSONL). 11 entity files (area, artist, event, instrument, label, place, recording, release-group, release, series, work).
Key Scripts:
- `fetch.py` → download dumps
- `untar.py` → extract JSONL
- `extract_for_reconciliation.py` → harvest unreconciled categorical fields (types, genders, keys, languages, statuses, packagings)
- `extract_relations.py` → enumerate relation types → `rdf_conversion_config/relations.json`
- `convert_to_rdf.py` → large-scale parallel conversion using `MappingSchema` + attribute + relation mappings
Mapping Assets:
- `mapping_schema.py` (class) + JSON `mappings.json` produce per-entity property dictionaries (MB internal predicates → Wikidata PIDs)
- `attribute_mapping.json` & `relations.json` under `rdf_conversion_config/`
Reconciliation Strategy:
- Many entities already carry Wikidata QIDs (artist, etc.)
- Type-like fields (subtypes, genres, keys, genders, languages, statuses, packaging) reconciled → CSVs with `*_@id` columns
Representative Wikidata Properties In Use:
- Identity & Typing: P31 (instance of)
- People / Roles: P86 (composer), P175 (performer appears implicitly through artist links in future), P123 (publisher), P463 (member of)
- Location: P131 (admin area), P276 (location), coordinates as WKT literal
- Temporal: P571 (inception) sometimes, P577 (publication date) not yet explicit, custom date handling via literal conversions
- Structural: P361 (part of), P527 (has part) potential future; relationships encode many domain types (collaboration, production roles)
Lexical Seeds (examples → candidate PIDs):
- “composer”→P86, “performer”/“performed by”→P175, “genre”→P136, “member of”→P463, “part of”→P361, “has part”→P527, “location”→P276, “country”→P17, “area”/“administrative area”→P131, “alias”→(internal label, or rdfs:label / altLabel external), “length”/“duration”→P2047 or custom; currently length stored as decimal seconds internal predicate.
Notes:
- Multi‑stage mapping means we can programmatically extract property IDs for lexicon seeding by scanning mapping + relation JSON.
- Some relation types remain unmapped (value = null) → treat as backlog for property curation.

### DIAMM
Source Type: Web pages (HTML) with JSON via content negotiation; async scraper available.
Key Scripts:
- `async_fetch.py` / `fetch.py` (rate limiting + queueing)
- `to_csv.py` → normalized CSVs + `relations.csv`
- `convert_rdf.py` → merges reconciled CSVs + relationships; central `DIAMM_SCHEMA` defines property usage.
Mapping Assets:
- `convert_rdf.py` constant `DIAMM_SCHEMA` (explicit PIDs for ~30 predicates)
- `relations.json` (organization & people relation phrase → PID, null for unresolved)
Reconciliation Strategy:
- Entities (archives, cities, countries, organizations, people, regions, sets, sources, compositions) — matched via `*_@id` fields; store P2888 (exact match) for reconciled.
- Fallback uses literal labels when reconciliation fails.
Representative Wikidata Properties In Use:
- Identity / Matching: P2888 (exact match)
- Naming: rdfs:label + P1476 (title) for compositions
- Location / Hierarchy: P131, P17, P276, P361
- People / Roles: P86 (composer), P11603 (transcribed by), P1071 (copied at / scriptorium), P1449 (nickname / variant names), P217 (inventory number / shelfmark)
- Classification: P31 (type), P136 (genre)
- External IDs: P214 (VIAF), P5504 (RISM ID)
Lexical Seeds:
- “shelfmark”→P217, “nickname”/“variant name”→P1449, “transcribed by” / “copied by”→P11603, “exact match”→P2888, “siglum”→P11550, “rism id”→P5504.
Notes:
- Rich specialized relation phrases in `relations.json` (e.g., “commissioned by”→P88) – integrate these phrases directly into lexicon.
- Null mappings flag phrases needing manual Wikidata property decisions.

### RISM
Source Type: Large RDF (n‑triples / turtle) provided externally; processes involve splitting + OpenRefine reconciliation + rejoining.
Key Scripts:
- `force_split.py` / `force_join.py` for chunking & reassembly.
Mapping Assets:
- `ontology/mapping.json` (predicate URI → Wikidata PID or empty for unresolved)
- `ontology/mappingWithLog.json5` (full log with rationale / comments)
Reconciliation Strategy:
- OpenRefine with custom JSON step files; multiple passes (type, label for persons, etc.).
Representative Properties: P50 (creator), P1319 (earliest date), P1326 (latest date), P195 (collection), P1922 (incipit), P361 (part of), P921 (main subject), P1071 (copied at), P131 (admin area) etc.
Lexical Seeds:
- “incipit”→P1922, “earliest date”→P1319, “latest date”→P1326, “holding institution”→P195, “subject”→P921.
Notes:
- Many dataset‑specific predicates still unmapped (empty string). These represent extension/cleanup tasks; still useful phrases to capture for lexicon with status=unmapped.

### Cantus (CantusDB)
Source Type: API -> multiple per‑source CSVs combined.
Key Scripts: `fetch.py`, `merge.py` → consolidated `cantus.csv` (handles abbreviation expansion via `genres.tsv`, `services.tsv`).
Mapping Assets:
- Abbreviation expansions (genre/service) implicitly create lexical surface forms → candidate mapping terms for genre/service classification.
- JSON‑LD approach (context + generate script) currently uses temporary made‑up property IRIs (e.g., `https://cantusdatabase.org/office`).
Reconciliation Strategy:
- Manual OpenRefine steps (service, genre, mode) against: Q3406098 (Prayer in the Catholic Church), Q188451 (music genre), Q731978 (mode). Some entries become new Wikidata items or local placeholders.
Lexical Seeds:
- “mode” (dorian, phrygian etc.) → eventual mapping to musical mode concept (may use P???; often represented via item classification rather than property).
- “service” / “office” → may map to liturgical context; property selection TBD (could become part of local ontology layer first).
Notes:
- Need a Turtle conversion (TODO) before full SPARQL integration; until then treat Cantus as partial for NL queries.

### The Session
Source Type: Provided CSV dumps via script; plus incremental web scraping for artist profile URL enrichment.
Key Scripts: `fetch_data.py`, `find_artist.py`.
Entities: tunes, tune aliases, tune sets, sessions (events), recordings, events, tune popularity.
Reconciliation Strategy:
- Currently little direct Wikidata reconciliation (artist URLs internal). Potential mapping: tune popularity → numeric literal; sessions/events → temporal + location (future mapping plan).
Lexical Seeds:
- “tune popularity”, “recordings of”, “sets containing”, “sessions in [location]”, “events on [date]”. Need property design (either local graph predicates or reuse schema.org / Wikidata equivalents e.g., P1552 (has quality) for popularity? Might instead store as custom property).
Notes:
- For NLQ, we’ll rely on internal graph predicates first; add bridging mapping layer later.

### The Global Jukebox
Docs Present: `general_reconciliation_notes.md`, `reconcile_procedures.md`.
Content Focus: Instrument / song type reconciliation heuristics (using broader families if specific item missing); detailed notes on ethnic group / language / climate classification.
Lexical Seeds:
- Instrument families (“percussion instrument”→Q133163). Terms like “song type”, “voice type” (Q1063547), “music genre” (Q188451), “ethnic group” (Q41710), climate categories.
Notes:
- Valuable for semantic expansion / disambiguation phrases (e.g., “war dance” vs “music genre”).

### SimssaDB
Pipeline: SQL dump → flattening (SQL_query.py) → reconciliation (OpenRefine) → restructuring → JSON‑LD generation.
Current State: JSON‑LD path; Turtle conversion TODO.
Lexical Seeds: “musical work”, “file”, “performance”, plus any reconciled fields in flattened CSV (need to inspect final schema once Turtle conversion planned).

Cross‑Dataset Property / Phrase Inventory (Seed Candidates)
---------------------------------------------------------
Core People / Authorship: composer(P86), creator(P50), performer(P175), transcribed/copied(P11603), patron(P859), commissioned by(P88), dedicatee(P825).
Structure / Containment: part of(P361), has part(P527), set in source (P361 again in DIAMM context), member of(P463), exact match(P2888).
Location / Provenance: location(P276), administrative area(P131), country(P17), holding institution(P195), provenance organization(P276 reused), copied at(P1071).
Classification / Type: instance of(P31), genre(P136), subject(P921), type (dataset-specific subtyping feeding into P31), mode (mapped to items), key (items), language (items), status (some statuses as items). 
Identification / External IDs: inventory number/shelfmark(P217), VIAF(P214), RISM(P5504), (MusicBrainz IDs are IRIs, internal).
Temporal: earliest date(P1319), latest date(P1326), (birth/death P569/P570 implied for people), inception(P571 potential), publication date(P577 potential).
Descriptive: title(P1476), nickname / variant name(P1449), name(label), incipit(P1922).

How to Build property_mappings.json (Proposed Steps)
---------------------------------------------------
1. Aggregate: Parse DIAMM_SCHEMA, RISM mapping.json (non-empty values), MusicBrainz `mappings.json`, DIAMM relations.json (non-null), plus manually curated high-value unresolved DIAMM/RISM relation phrases.
2. Normalize Keys: Lowercase phrase, strip punctuation; keep canonical phrase; store alternative surface forms (synonyms) as array.
3. Structure:
   {
     "composer": {"pid": "P86", "aliases": ["written by", "music by"], "domains": ["composition","work"], "confidence": 0.95},
     "shelfmark": {"pid": "P217", "aliases": ["inventory number"], ...},
     ...
   }
4. Mark Unmapped: For phrases with null mapping (relations.json / mapping.json empty strings) create stubs: {"pid": null, "status": "unmapped"}.
5. Regenerate Deterministic Hash snapshot to detect drift (future CI enhancement).

Potential NL Disambiguation Patterns
-----------------------------------
- “part of” vs “has part” (directional) → ensure both lexical entries.
- “location” vs “located in” vs “in” (preposition) → unify to P276.
- “administrative area” / “area” / “region” sometimes ambiguous between P131 (admin unit) and P276 (physical location) → choose context by entity type.
- “copyist” / “transcribed by” / “copied by” → P11603.
- “inventory number” / “shelfmark” / “call number” → P217.
- “subject” / “about” / “topic” → P921.

Gaps / Actionable Follow‑Ups
---------------------------
- Need automated extractor script to generate initial `property_mappings.json` (could live at `ontology/build_property_mappings.py`).
- Cantus & Simssa: finalize Turtle conversion to expose graph predicates; decide on property mappings for made‑up IRIs.
- RISM: fill empty mappings in `mapping.json` guided by `mappingWithLog.json5` commentary.
- Add tests verifying bidirectional phrase ↔ PID lookup determinism.

Suggested Minimal JSON Schema (Draft)
------------------------------------
{
  "composer": {"pid": "P86", "aliases": ["music by"], "domains": ["work"], "status": "mapped"},
  "patron": {"pid": "P859", "aliases": [], "domains": ["organization","people"], "status": "mapped"},
  "flyleaves": {"pid": null, "aliases": ["fly leaves"], "status": "unmapped"}
}

Integration Notes for Prompt Builder
------------------------------------
- Provide condensed block: each query → only include mappings relevant to recognized surface forms in NL question + ontology slice classes.
- Cache phrase→PID resolution; prefer exact match, fallback fuzzy (RapidFuzz ratio ≥ threshold) but only if unique high score.
- Log unresolved phrases for curation queue.

Risk / Ambiguity Watchlist
--------------------------
- Overlapping role predicates (composer vs author vs creator) – context resolution (entity type: composition vs treatise vs source description) needed.
- Multi-language queries (future) will require alias localization; current lexicon English-only.
- Rate limiting during dynamic Wikidata expansion; prefer offline lexicon first, then tool calls for novel phrases.

Maintenance Pattern
-------------------
1. After any dataset mapping update → run extractor → diff JSON.
2. If new phrases unmapped > threshold count → open curation issue.
3. Keep STATUS.md inventory section in sync (lightweight updates only when categories change).

Last Compiled: 2025-08-11
