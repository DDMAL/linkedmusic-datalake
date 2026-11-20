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

NFDI4Culture identifies the feed as `E6304` and its publisher as `E2431`.
Individual records can also reference external resources, including a repository's
own licence URL.

| | |
|---|---|
| CKG feed | `E6304` |
| Output | `data/rdf/apsearch.ttl` |
| Work class | `https://linkedmusic.ca/graphs/ckg/Work` |
| Graph IRI | `https://linkedmusic.ca/graphs/ckg-apsearch/` |

Why each mapping decision was made — the media-class typing, license/publisher pivots, date
handling, content-URL join, and the emitted schema (for **SESEMMI**, LinkedMusic's
natural-language→SPARQL query tool) — is in [`doc/data-model.md`](doc/data-model.md).

All scripts assume **CWD = `ckg-apsearch/src/`** and use the repo-root Poetry env. Everything
under `data/` is **gitignored**.

> APSearch runs the **same machinery** as musiconn/Detmold (same `src/`, same `mapping.json`),
> exercising the media-feed paths: `CTO_0001049` media classes, `associatedMedia` content-URL
> join, license/publisher `P2888` pivots, and an APSearch-specific creation-period representation. No APSearch-specific
> OpenRefine pass is configured.

---

## 1. Getting the data dump

The per-feed N-Triples dump is gitignored and read directly from disk at:

```
raw_data/ckg/mnt/data/culture-kg-kitchen/data/production/E6304/nt/E6304.nt
```

`preprocess.py` reads it via `--raw-root` (default above).

## 2. Preprocess + crosswalk

**`preprocess.py`** follows the record's `CTO_0001025` (is about) link to index
its kind. For example, a linked blank node typed `schema:CreativeWork` gives the
record the indexed kind `Work`. The same pass indexes media/AAT classifiers.
For each `schema:associatedMedia` blank node, it joins the last literal
`CTO_0001021` URL to the last record that references that node, in input order.
It skips IRI-valued URLs.

```bash
python preprocess.py apsearch
# -> data/extracted/apsearch.norm.nt, .entities.json (record kind/classifier/content-url maps)
```

**`build_crosswalk.py`** looks for Wikidata matches for indexed AAT classifier codes
via `wdt:P1014` and for available authority identifiers. Inspect the selected
input and retained crosswalk evidence before making population claims.

```bash
python build_crosswalk.py apsearch
# -> data/mappings/record_types.json (+ shared crosswalk.json)
```

After each build, match the APSearch entries in `data/mappings/record_types.json`
to the [classifier table](doc/data-model.md#record-typing). Use full IRI keys
and bare QID values for all six mapped terms, including the manual CTO entries
and the cylinder mapping (`aat:300265798` → `Q691783`). Remove any entries for
the two intentionally unmapped classifiers and preserve the other feeds' entries.

The builder fills `data/mappings/crosswalk.json` from authority identifiers.
Keep those entries and manually add the three [licence and publisher mappings](doc/data-model.md#licences-and-publisher).
For each key, append the E-number to `https://nfdi4culture.de/id/`. Use the
bare QID as its value.

## 3. Reconciliation

No APSearch-specific OpenRefine pass is configured. The converter consumes:

- Media-class and AAT mappings from `record_types.json` for `wdt:P31`.
- Licence/publisher targets in `crosswalk.json` for `wdt:P2888` links.

These are configured mappings, not evidence that every candidate or source
licence has been independently verified. Record the exact mapping files and
source snapshot used for a conversion; see [the data model](doc/data-model.md).

## 4. Convert to RDF

**`convert_to_rdf.py`** emits the indexed local class when the record has its own
`rdf:type CTO_0001005` (source item) assertion. A mapped media or AAT classifier
supplies `wdt:P31`. When none resolves, only an indexed `Work` gets the APSearch
fallback `wd:Q17537576` (creative work). The converter also emits joined content
URLs as `wdt:P953` and links licence/publisher URIs to Wikidata when the
crosswalk supplies a match.

For each creation period, the converter retains the source term and links the
record to an observation with its parse status, available year bounds and any
review flags. A parsed period also supplies its start year as `wdt:P571`. Use
the [paired bounds](doc/creation-period-preservation.md) for overlap queries.
An unexpected blank-node period stops conversion. Write to a fresh output
directory and check the exit status and audit before using the Turtle.

```bash
python convert_to_rdf.py apsearch --outdir /path/to/new-candidate
# Writes apsearch.ttl and apsearch.creation-period-audit.json
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
