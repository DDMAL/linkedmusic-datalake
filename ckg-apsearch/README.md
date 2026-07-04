# CKG — APSearch (`E6304`) → LinkedMusic

Ingestion of the **APSearch** feed of the NFDI4Culture **Culture Knowledge Graph (CKG)** into
the LinkedMusic data lake as RDF Turtle. APSearch is **ELAR (Endangered Languages Archive)**
data — audio/image/video/text field recordings of endangered languages (host
`elararchive.org`; publisher BBAW). It is ~98.9% ELAR plus ~1.1% (72 records) Staatliche
Museen zu Berlin objects.

APSearch is a **media/content feed and differs from musiconn/Detmold**: it has **no persons,
no relational backbone, and ~0% authority IDs**. Titles are free-text descriptions, not
entities. So there is **no label-based OpenRefine surface in the dump** — its reconciliation
is small and **fully deterministic** (licenses, publisher, media classes, AAT codes). The
reconcilable content (languages, countries, depositors) lives in the ELAR *source*, which is
access-walled, so it is not represented in this dataset.

This is one of three CKG feeds ingested as **separate sibling subprojects** —
[`ckg-musiconn`](../ckg-musiconn), [`ckg-detmold`](../ckg-detmold),
[`ckg-apsearch`](../ckg-apsearch) — each loading as its **own Virtuoso named graph**. The
CKG's RISM feed (`E5313`) is **excluded by design** (LinkedMusic ingests RISM separately).

Codes like `E6304` are **NFDI4Culture resource identifiers**: every CKG feed — and every
license and publisher it references — is a registered `E…` entity in the NFDI4Culture
knowledge graph.

| | |
|---|---|
| CKG dump | `E6304` (23 MB, ~129k triples, 6,271 records) |
| Output | `data/rdf/apsearch.ttl` — **~46,203 triples**, 0 blank nodes |
| Records | 6,271 works (`lmckg:Work`), each typed `lmckg:Work` + ≥1 `wdt:P31` |
| Media | 3,783 `wdt:P953` content URLs; 3 `wdt:P2888` pivots (2 licenses + publisher) |
| Graph IRI | `https://linkedmusic.ca/graphs/ckg-apsearch/` |

Why each mapping decision was made — the media-class typing, license/publisher pivots, date
handling, content-URL join, and the emitted schema (for **SESEMMI**, LinkedMusic's
natural-language→SPARQL query tool) — is in [`doc/data-model.md`](doc/data-model.md).

All scripts assume **CWD = `ckg-apsearch/src/`** and use the repo-root Poetry env. Everything
under `data/` is **gitignored**.

> APSearch runs the **same machinery** as musiconn/Detmold (same `src/`, same `mapping.json`),
> exercising the media-feed paths: `CTO_0001049` media classes, `associatedMedia` content-URL
> join, license/publisher `P2888` pivots, and an APSearch-specific date coercion. There is no
> OpenRefine pass and no relational backbone.

---

## 1. Getting the data dump

The per-feed N-Triples dump is gitignored and read directly from disk at:

```
raw_data/ckg/mnt/data/culture-kg-kitchen/data/production/E6304/nt/E6304.nt
```

`preprocess.py` reads it via `--raw-root` (default above).

## 2. Preprocess + crosswalk

**`preprocess.py`** — one streaming pass that builds the **record-kind index** (every record
is `schema:CreativeWork` → Work), the **classifier index** (record → `CTO_0001049` media
class / AAT code), and joins each record to its content URL through the `associatedMedia`
blank node → `CTO_0001021` chain (the URL sits on the bnode, which is never emitted, so it is
joined back to the record → `wdt:P953`).

```bash
python preprocess.py apsearch
# -> data/extracted/apsearch.norm.nt, .entities.json (record kind/classifier/content-url maps)
```

**`build_crosswalk.py`** — resolves the AAT classifier codes via `wdt:P1014`. (There are no
GND/VIAF/GeoNames authority IDs in APSearch, so the authority crosswalk is empty here.)

```bash
python build_crosswalk.py apsearch
# -> data/mappings/record_types.json (+ shared crosswalk.json)
```

## 3. Reconciliation

**No OpenRefine.** The dump's reconciliation surface is small and **fully deterministic**, so
all of it is wired into the mapping files rather than reconciled by hand:

- **Media classes / AAT codes** → `wdt:P31` QIDs (hand-verified) in `record_types.json`.
- **Licenses / publisher** → `wdt:P2888` pivots in `crosswalk.json` (resolved via the NFDI
  `owl:sameAs` on the `nfdi4culture.de/id/E####` pages).

All QIDs were verified against primary sources — see [`doc/data-model.md`](doc/data-model.md).

The label-based reconciliation (languages → ISO 639-3/Glottolog, countries, depositors) is
**not in the CKG dump** — it requires the ELAR source, which is access-walled, so it is not
represented in this dataset.

## 4. Convert to RDF

**`convert_to_rdf.py`** — the shared two-pass converter (see
[`doc/data-model.md`](doc/data-model.md)): types every record `lmckg:Work` + `wdt:P31` (media
class, or the `Q17537576` "creative work" fallback for classifier-less records), emits the
license/publisher `P2888` pivots, coerces dates to `xsd:gYear`, and emits the joined
`wdt:P953` content URLs post-loop. No blank nodes survive.

```bash
python convert_to_rdf.py apsearch          # -> data/rdf/apsearch.ttl
```

Verify: `grep -c '_:' data/rdf/apsearch.ttl` == 0, an `rdflib` parse, and ~46,203 triples /
6,271 records each with ≥1 `wdt:P31` / 3,783 `wdt:P953`.

## 5. Load

Bulk-load `apsearch.ttl` as its own named graph with the Virtuoso loader (`ld_dir` +
`rdf_loader_run`), per the wiki's `Virtuoso-Setup-Guide.md`:

| feed | graph IRI |
|---|---|
| APSearch | `https://linkedmusic.ca/graphs/ckg-apsearch/` |

After loading, the dataset's schema must be documented for **SESEMMI**;
[`doc/data-model.md`](doc/data-model.md) is that reference.

---

## Layout

```
ckg-apsearch/
├── src/                           # shared CKG pipeline (copied verbatim; takes a feed arg)
│   ├── preprocess.py              # normalize + index + content-URL join
│   ├── build_crosswalk.py         # AAT classifier → QID
│   ├── convert_to_rdf.py          # NT → TTL
│   └── ontology/mapping.json      # runtime predicate map
│   # (the GND/VIAF name-fetch + OpenRefine-merge scripts are copied too but unused here)
├── data/                          # gitignored (extracted / mappings / rdf)
└── doc/
    └── data-model.md              # schema + mapping decisions + verified IDs (the "why")
```

> The `src/` scripts are **shared across all three CKG feeds** and copied verbatim; the
> person/residue-reconciliation scripts don't apply to APSearch (no persons). There is no
> `openrefine/` folder — APSearch's dump reconciliation is deterministic. Feeds: musiconn
> `E5320`, Detmold `E5305`, APSearch `E6304`.
