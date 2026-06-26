# CKG — Detmold (`E5305`) → LinkedMusic

Ingestion of the **Hoftheater Detmold** feed of the NFDI4Culture **Culture Knowledge Graph
(CKG)** into the LinkedMusic data lake as RDF Turtle, reconciled to Wikidata. The feed is the
**repertoire of the court theatre at Detmold** — a heterogeneous mix of operas, spoken plays
and Singspiele — with the persons (composers, librettists, authors) and places involved.

Like the other CKG feeds, Detmold is delivered **RDF-native** (a per-feed N-Triples dump),
so there is **no fetch/scrape step**, and reconciliation is a **deterministic authority-ID
crosswalk** (GND/VIAF for persons, GeoNames for places). OpenRefine is used only for the
residue.

This is one of three CKG feeds ingested as **separate sibling subprojects** —
[`ckg-musiconn`](../ckg-musiconn), [`ckg-detmold`](../ckg-detmold),
[`ckg-apsearch`](../ckg-apsearch) — because each loads as its **own Virtuoso named graph**.
The CKG's RISM feed (`E5313`) is **excluded by design** (LinkedMusic ingests RISM separately).

| | |
|---|---|
| CKG dump | `E5305` (5 MB, ~31k triples, 1,694 records) |
| Output | `data/rdf/detmold.ttl` — **~14,835 triples**, 0 blank nodes, 588 `wdt:P2888` pivots |
| Records | 1,694 works (`lmckg:Work`), each typed `wdt:P31` |
| Entities | Person 570 · Place 38 (distinct, deduped) |
| Graph IRI | `https://linkedmusic.ca/graphs/ckg-detmold/` |

Why each mapping decision was made — the source CTO model, the predicate table, the
classifier-less typing, the interval-date handling, reconciliation rates, and the emitted
schema (for SESEMMI) — is in [`doc/data-model.md`](doc/data-model.md).

All scripts assume **CWD = `ckg-detmold/src/`** and use the repo-root Poetry env
(`poetry run python …`). Everything under `data/` is **gitignored**.

> Detmold runs the **same machinery** as musiconn (same `src/`, same `mapping.json`), with a
> few feed-specific paths: records have no AAT classifier (so `wdt:P31` comes from a fallback),
> dates are `schema:DateTime` intervals, and places reconcile via GeoNames.

---

## 1. Getting the data dump

The per-feed N-Triples dump is gitignored and read directly from disk at:

```
raw_data/ckg/mnt/data/culture-kg-kitchen/data/production/E5305/nt/E5305.nt
```

`preprocess.py` reads it via `--raw-root` (default above).

## 2. Preprocess + crosswalk

**`preprocess.py`** — one streaming pass that builds the **entity index** (authority blank
node → `{local class, GND/VIAF/GeoNames URI}`), the **record-kind index** (record →
Work, via the `schema:CreativeWork` is-about bnode — Detmold carries **no** AAT classifier),
and collects the deduped authority IDs (GND + VIAF for persons, **GeoNames** for places).

```bash
python preprocess.py detmold
# -> data/extracted/detmold.norm.nt, .entities.json, .authorities.json
```

**`build_crosswalk.py`** — resolves the deduped authority IDs to Wikidata QIDs via batched
SPARQL: `GND → P227`, `VIAF → P214`, **`GeoNames → P1566`** (all 38 Detmold places are
`sws.geonames.org`). The crosswalk cache is **shared and additive** across the three feeds.

```bash
python build_crosswalk.py detmold
# -> data/mappings/crosswalk.json, record_types.json
```

## 3. Reconciliation

- **Deterministic crosswalk** covers most entities: persons ~95.8% (GND 464/487 + VIAF
  82/83), places GeoNames 34/38 (89.5%).
- **Two places needed manual same-as** — Zürich (`Q72`) and Hannover (`Q1715`) — because
  Wikidata records the *admin-level* GeoNames ID, not the *populated-place* ID the source uses,
  so the deterministic match missed them. Added to `crosswalk.json` as `wdt:P2888` links.
- **Residue name fetch + OpenRefine.** Entity nodes carry no labels, so names are fetched from
  the authority services (`fetch_authority_names.py`, `fetch_viaf_fallback.py`) → emitted as
  `rdfs:label` and used for an OpenRefine name-reconciliation pass (RDF-transform, **Chrome
  only**; shared musiconn+Detmold project in [`openrefine/`](openrefine)). `merge_openrefine.py`
  folds vetted matches into the crosswalk; the precise ID matcher is `wikidata_id_lookup.py`.

Unreconciled entities are kept intact (local `lmckg:*` class, no `P2888`), never dropped.

## 4. Convert to RDF

**`convert_to_rdf.py`** — the shared two-pass converter (see
[`doc/data-model.md`](doc/data-model.md)): drops the envelope, collapses entity bnodes to
their authority URIs (no blank nodes; dedupes), pivots reconciled nodes via `wdt:P2888`,
types entities `lmckg:*`, and gives each record `rdf:type lmckg:Work` + a **fallback**
`wdt:P31 → wd:Q838948` (work of art) — Detmold has no AAT classifier to type from.

```bash
python convert_to_rdf.py detmold          # -> data/rdf/detmold.ttl
```

Verify: `grep -c '_:' data/rdf/detmold.ttl` == 0, an `rdflib` parse, and ~14,835 triples /
1,694 `wdt:P31` / 588 `wdt:P2888`.

## 5. Load

Bulk-load `detmold.ttl` as its own named graph with the Virtuoso loader (`ld_dir` +
`rdf_loader_run`), per the wiki's `Virtuoso-Setup-Guide.md`:

| feed | graph IRI |
|---|---|
| Detmold | `https://linkedmusic.ca/graphs/ckg-detmold/` |

After loading, the dataset's schema must be documented for **SESEMMI**;
[`doc/data-model.md`](doc/data-model.md) is that reference.

---

## Layout

```
ckg-detmold/
├── src/                           # shared CKG pipeline (copied verbatim; takes a feed arg)
│   ├── preprocess.py              # normalize + index
│   ├── build_crosswalk.py         # authority-id → QID (incl. GeoNames P1566)
│   ├── fetch_authority_names.py   # GND/VIAF/GeoNames name fetch
│   ├── wikidata_id_lookup.py      # precise ID→QID residue match
│   ├── merge_openrefine.py        # fold OpenRefine matches into crosswalk
│   ├── convert_to_rdf.py          # NT → TTL
│   └── ontology/mapping.json      # runtime predicate map
├── data/                          # gitignored (extracted / mappings / openrefine / rdf)
├── openrefine/                    # residue name reconciliation (history + export)
└── doc/
    └── data-model.md              # schema + mapping decisions + verified IDs (the "why")
```

> The `src/` scripts are **shared across all three CKG feeds** and copied verbatim; `data/`
> and `openrefine/` here hold only the Detmold slice. Feeds: musiconn `E5320`, Detmold
> `E5305`, APSearch `E6304`.
