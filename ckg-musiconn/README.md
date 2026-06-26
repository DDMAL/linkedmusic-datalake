# CKG — musiconn (`E5320`) → LinkedMusic

Ingestion of the **musiconn.performance** feed of the NFDI4Culture **Culture Knowledge
Graph (CKG)** into the LinkedMusic data lake as RDF Turtle, reconciled to Wikidata.
musiconn.performance (SLUB Dresden) is a German concert-performance database: events
(concerts/opera performances) and the works performed at them, linked to the persons,
organizations and venues involved.

Unlike most LinkedMusic subprojects, CKG is delivered **RDF-native** (per-feed N-Triples
dumps), so there is **no fetch/scrape step**, and reconciliation is a **deterministic
authority-ID crosswalk** (GND/VIAF → Wikidata), not column-by-column OpenRefine. OpenRefine
is used only for the residue (entities with an authority ID but no Wikidata item).

This is one of three CKG feeds ingested as **separate sibling subprojects** —
[`ckg-musiconn`](../ckg-musiconn), [`ckg-detmold`](../ckg-detmold),
[`ckg-apsearch`](../ckg-apsearch) — because on the triplestore each loads as its **own
Virtuoso named graph**. The CKG's RISM feed (`E5313`) is **excluded by design**:
LinkedMusic ingests RISM separately.

| | |
|---|---|
| CKG dump | `E5320` (537 MB, ~3.0M triples, 106,169 records) |
| Output | `data/rdf/musiconn.ttl` — **~1.59M triples**, 0 blank nodes, 14,165 `wdt:P2888` pivots |
| Records | 65,359 events (`lmckg:Event`) + 40,810 works (`lmckg:Work`), each typed `wdt:P31` |
| Entities | Person 19,775 · Place 6,160 · Organization 3,499 · Collection 1,336 (distinct, deduped) |
| Graph IRI | `https://linkedmusic.ca/graphs/ckg-musiconn/` |

Why each mapping decision was made — the source CTO model, the predicate table, record
typing, reconciliation rates, and the emitted schema (for SESEMMI) — is in
[`doc/data-model.md`](doc/data-model.md). musiconn flattens performer/composer **roles**:
every person↔event link is role-agnostic, so performer, composer and conductor roles are not
represented in this dataset.

All scripts assume **CWD = `ckg-musiconn/src/`** and use the repo-root Poetry env
(`poetry run python …`). Everything under `data/` is **gitignored**.

---

## 1. Getting the data dump

The per-feed N-Triples dump is gitignored and read directly from disk at:

```
raw_data/ckg/mnt/data/culture-kg-kitchen/data/production/E5320/nt/E5320.nt
```

`preprocess.py` reads it via `--raw-root` (default above); no copy into `data/archived/`
is required. The dump is **not subject-sorted**, so the converter builds an entity index
in a first pass before rewriting.

## 2. Preprocess + crosswalk

**`preprocess.py`** — one streaming pass that (a) repairs the missing-underscore
`NFDI0001006` typo (1,704 triples — otherwise those authority links are lost), (b) builds
the **entity index** (each authority blank node → `{local class, GND/VIAF URI}`), the
**record-type index** (record → AAT classifier and Event/Work kind), and (c) collects the
deduped GND + VIAF authority IDs.

```bash
python preprocess.py musiconn
# -> data/extracted/musiconn.norm.nt, .entities.json, .authorities.json
```

**`build_crosswalk.py`** — resolves the deduped authority IDs to Wikidata QIDs via batched
SPARQL (`GND → P227`, `VIAF → P214`) through `shared/wikidata_utils`, plus the AAT
record-type codes (`P1014`). Re-runnable; the crosswalk cache is **shared and additive**
across the three feeds. **It prints the real reconciliation rate** — ≈62% of distinct
authorities (GND 61.9%, VIAF 61.8%).

```bash
python build_crosswalk.py musiconn
# -> data/mappings/crosswalk.json, record_types.json
```

## 3. Reconciliation

The crosswalk above resolves every authority-linked entity that *is* in Wikidata. The rest
is handled in two ways:

- **Residue name fetch.** Entity nodes carry **no labels** in the CKG dump (only an
  authority ID), so names are fetched from the authority services for the unresolved IDs:
  `fetch_authority_names.py` (GND via lobid.org, VIAF API) and `fetch_viaf_fallback.py`
  → `data/openrefine/names_for_reconciliation.csv`. These preferred names are also emitted
  as `rdfs:label` on the authority nodes by the converter (the house "name + `P2888`"
  convention).
- **Residue reconciliation.** Two passes attach `P2888` to residue that *is* in Wikidata
  but wasn't caught by the bulk crosswalk: `wikidata_id_lookup.py` (precise
  `haswbstatement:P227/P214` ID lookup) and an OpenRefine name-reconciliation pass
  (RDF-transform, **Chrome only**; project in [`openrefine/`](openrefine)).
  `merge_openrefine.py` folds the vetted matches into `crosswalk.json` (ID lookup wins
  conflicts; name matching is namesake-prone for this niche German data, so prefer IDs).

Whatever still doesn't resolve stays as an un-reconciled node (a GND/VIAF authority URI, or
a bare `performance.musiconn.de/…` source URI) with **no `P2888`** — preserved intact, never
dropped. The residue is genuinely absent from Wikidata (~0.5% ID-hit rate on what's left);
see [`doc/data-model.md`](doc/data-model.md) for the rates.

## 4. Convert to RDF

**`convert_to_rdf.py`** — two-pass streaming NT→TTL converter applying
[`src/ontology/mapping.json`](src/ontology/mapping.json): drops the DataFeed envelope and
provenance noise, remaps predicates to `wdt:P*`, **collapses every entity blank node to its
authority URI** (no blank nodes in output; this also dedupes the entity reified once per
record), emits a `wdt:P2888`→QID pivot for reconciled nodes, types every entity with a local
`lmckg:*` class, and gives each record an `rdf:type lmckg:Event`/`Work` + `wdt:P31`→QID.

```bash
python convert_to_rdf.py musiconn          # -> data/rdf/musiconn.ttl
```

Verify: `grep -c '_:' data/rdf/musiconn.ttl` == 0, and an `rdflib` parse. Expect ~1.59M
triples, 106,169 `wdt:P31`, 14,165 `wdt:P2888` pivots.

## 5. Load

Bulk-load `musiconn.ttl` as its own named graph with the Virtuoso loader (`ld_dir` +
`rdf_loader_run`), per the wiki's `Virtuoso-Setup-Guide.md`:

| graph IRI | contents |
|---|---|
| `https://linkedmusic.ca/graphs/ckg-musiconn/` | the musiconn dataset (this README) |

After loading, the dataset's schema must be documented for **SESEMMI** (LinkedMusic's
NL→SPARQL tool); [`doc/data-model.md`](doc/data-model.md) is that schema reference.

---

## Layout

```
ckg-musiconn/
├── src/
│   ├── profile_predicate.py       # predicate profiler
│   ├── preprocess.py              # normalize + index
│   ├── build_crosswalk.py         # authority-id → QID
│   ├── fetch_authority_names.py   # GND/VIAF name fetch (for residue + labels)
│   ├── fetch_viaf_fallback.py     # VIAF fallback names
│   ├── wikidata_id_lookup.py      # precise ID→QID residue match
│   ├── merge_openrefine.py        # fold OpenRefine matches into crosswalk
│   ├── convert_to_rdf.py          # NT → TTL
│   └── ontology/mapping.json      # runtime predicate map
├── data/                          # gitignored (extracted / mappings / openrefine / rdf)
├── openrefine/                    # residue name reconciliation (history + export)
└── doc/
    └── data-model.md              # schema + mapping decisions + verified IDs (the "why")
```

> The `src/` scripts are **shared across all three CKG feeds** (each takes a feed argument)
> and are copied verbatim into each subproject; `data/` and `openrefine/` here hold only the
> musiconn slice. Feeds: musiconn `E5320`, Detmold `E5305`, APSearch `E6304`.
