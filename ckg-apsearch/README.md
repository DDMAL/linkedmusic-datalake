# CKG — APSearch (`E6304`) → LinkedMusic

Ingestion of the **APSearch (Arab Phonogram Search)** feed of the NFDI4Culture
**Culture Knowledge Graph (CKG)** into LinkedMusic as RDF Turtle. The primary
[NFDI4Culture E6304 record](https://nfdi4culture.de/resource/E6304/about.html)
describes an aggregator/search portal for Arabic phonogram recordings and names
BBAW as publisher. APSearch is distinct from the Endangered Languages Archive
(ELAR). A record's licence URI or content-link host does not identify the whole
feed with that repository.

This converter uses the media-feed paths: media classifiers, content-URL joins
and configured licence/publisher crosswalks. It has no APSearch-specific
label-reconciliation pass. Missing exported fields do not establish that upstream
metadata is unavailable, and access conditions must be checked at the source.

This is one of three CKG feeds ingested as **separate sibling subprojects** —
[`ckg-musiconn`](../ckg-musiconn), [`ckg-detmold`](../ckg-detmold),
[`ckg-apsearch`](../ckg-apsearch) — each loading as its **own Virtuoso named graph**. The
CKG's RISM feed (`E5313`) is **excluded by design** (LinkedMusic ingests RISM separately).

Codes like `E6304` are **NFDI4Culture resource identifiers**: every CKG feed — and every
license and publisher it references — is a registered `E…` entity in the NFDI4Culture
knowledge graph.

| | |
|---|---|
| CKG feed | `E6304` |
| Output | `data/rdf/apsearch.ttl` |
| Record class | `https://linkedmusic.ca/graphs/ckg/Work` |
| Graph IRI | `https://linkedmusic.ca/graphs/ckg-apsearch/` |

Why each mapping decision was made — the media-class typing, license/publisher pivots, date
handling, content-URL join, and the emitted schema (for **SESEMMI**, LinkedMusic's
natural-language→SPARQL query tool) — is in [`doc/data-model.md`](doc/data-model.md).

All scripts assume **CWD = `ckg-apsearch/src/`** and use the repo-root Poetry env. Everything
under `data/` is **gitignored**.

> APSearch runs the **same machinery** as musiconn/Detmold (same `src/`, same `mapping.json`),
> exercising the media-feed paths: `CTO_0001049` media classes, `associatedMedia` content-URL
> join, license/publisher `P2888` pivots, and an APSearch-specific date coercion. No APSearch-specific
> OpenRefine pass is configured.

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

**`build_crosswalk.py`** — resolves AAT classifier codes via `wdt:P1014` and
available authority identifiers through the shared pipeline. Inspect the selected
input and retained crosswalk evidence before making population claims.

```bash
python build_crosswalk.py apsearch
# -> data/mappings/record_types.json (+ shared crosswalk.json)
```

## 3. Reconciliation

No APSearch-specific OpenRefine pass is configured. The converter consumes:

- Media-class and AAT mappings from `record_types.json` for `wdt:P31`.
- Licence/publisher targets in `crosswalk.json` for `wdt:P2888` links.

These are configured mappings, not evidence that every candidate or source
licence has been independently verified. Record the exact mapping files and
source snapshot used for a conversion; see [the data model](doc/data-model.md).

## 4. Convert to RDF

**`convert_to_rdf.py`** — the shared two-pass converter (see
[`doc/data-model.md`](doc/data-model.md)): types every record `lmckg:Work` + `wdt:P31` (media
class, or the `Q17537576` "creative work" fallback for classifier-less records), emits the
license/publisher `P2888` pivots, coerces dates to `xsd:gYear`, and emits the joined
`wdt:P953` content URLs post-loop. No blank nodes survive.

```bash
python convert_to_rdf.py apsearch          # -> data/rdf/apsearch.ttl
```

Validate each candidate by parsing it and comparing its record, type, date,
content-link and crosswalk sets with the identified input. Historical output
counts are not acceptance criteria for a different source or converter revision.

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
    └── data-model.md              # schema + mapping decisions and their limits
```

> The `src/` scripts are **shared across all three CKG feeds** and copied verbatim; the
> person/residue-reconciliation scripts are not an APSearch-specific workflow.
> There is no `openrefine/` folder for this feed. Feeds: musiconn
> `E5320`, Detmold `E5305`, APSearch `E6304`.
