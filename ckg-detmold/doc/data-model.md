# Detmold (`E5305`) — data model & mapping decisions

The authoritative reasoning behind the Detmold conversion. Detmold uses the **same converter
and `mapping.json`** as musiconn ([`../../ckg-musiconn/doc/data-model.md`](../../ckg-musiconn/doc/data-model.md)
has the full predicate map); this doc records what is **Detmold-specific**. Counts are from
the staged `detmold.ttl`. Historical handoffs and the predicate evidence sheet are in
[`_archive/`](_archive).

## 1. What the source looks like

CKG remodels the Hoftheater Detmold repertoire into the **nfdicore / CTO** ontology. Every
record is a `CTO_0001005` "source item" (1,694) and — unlike musiconn — **every record is a
Work** (operas, spoken plays, Singspiele). The relational backbone is the same reified shape
as musiconn: `has related person/location` → blank nodes typed `NFDI_0000004` (person) /
`NFDI_0000005` (place), each carrying one authority identifier. Collapsing the bnodes by
authority URI yields **570 distinct persons** and **38 distinct places**.

Two structural differences from musiconn shape the conversion:

1. **No AAT classifier.** Records carry no `CTO_0001026`; the is-about bnode is the generic
   `schema:CreativeWork` (not `schema:MusicEvent`/`MusicComposition`). So `P31` comes from a
   **fallback keyed on the record kind**, not from a classifier (§3).
2. **Places are GeoNames, not GND/VIAF.** Persons are GND/VIAF; all 38 distinct places are
   `sws.geonames.org` → reconciled via `wdt:P1566` (§4).

## 2. Predicate map

Identical to the shared map (remap to `wdt:P*` where faithful, keep CTO for the role-agnostic
backbone, drop provenance). Detmold exercises: `rdfs:label` (work title) kept; `CTO_0001073`
→ `wdt:P571` (date, §5); `CTO_0001009` related person → `cto:CTO_0001009` → `lmckg:Person`;
`CTO_0001011` related location → `cto:CTO_0001011` → `lmckg:Place`; `NFDI_0001006` → the
`wdt:P2888` pivot.

**`NFDI_0001008` "has url" is dropped** — like every feed, its object literal is
byte-identical to the record's own subject IRI (self-referential), *correcting* the earlier
plan's guess that Detmold's was a distinct external permalink. The subject IRI already *is*
the source permalink, so no triple is emitted.

## 3. Record typing — the classifier-less path (`P31` fallback)

Detmold records have no classifier to type from, so the converter emits a fallback `wdt:P31`
keyed on the record kind:

| Record | local class | `wdt:P31` |
|---|---|---|
| every Detmold record (is-about `schema:CreativeWork`) | `lmckg:Work` | `wd:Q838948` work of art |

**Q838948 "work of art"** was chosen deliberately for the heterogeneous repertoire on two
axes:

- **Correctness:** it is a verified `P279*` superclass of **both** `Q25379` play and `Q1344`
  opera. `Q207628` "composed musical work" (musiconn's work type) is a superclass of opera but
  **not** play, so it would mis-type the spoken dramas.
- **Federation:** among the valid common ancestors it is the best-connected hub (~67 sitelinks,
  vs 23 for `Q17537576` "creative work", 18 for `Q386724` "work").

This fallback is feed-conditional (`RECORD_KIND_P31_BY_FEED["detmold"]`) and applied
post-loop to any record without a resolving classifier — musiconn is unaffected (its records
all carry an AAT classifier), and APSearch uses `Q17537576` instead.

## 4. Reconciliation (incl. GeoNames)

Deterministic crosswalk: persons `P227`/`P214`, **places `P1566`** (GeoNames).

| population | resolved | rate |
|---|---|---|
| persons (GND 464/487 + VIAF 82/83) | ~546/570 | ~95.8% |
| places (GeoNames) | 34/38 | 89.5% |
| **total** | **580/608** | ~95% |

Examples: `geonames/2761369` → `Q1741` Vienna, `→ Q64` Berlin, `→ Q1085` Prague; Minden
(`Q3846`) and Aachen (`Q1017`) ID-matched directly.

**Two manual same-as additions** (in `crosswalk.json`): Zürich `Q72` and Hannover `Q1715`.
Wikidata stores the *admin-level* GeoNames ID on these city items, not the *populated-place*
ID the Detmold source uses, so `haswbstatement:P1566=<source id>` returned nothing. The QIDs
were confirmed manually and added as `wdt:P2888` links — see
[`_archive/pid-qid-verification.md`](_archive/pid-qid-verification.md). (A fix was also made to
`GEONAMES_HARDCODED` in `fetch_authority_names.py`, which had mis-entered names that didn't
match their IDs.)

Staged: **588 `wdt:P2888` pivots**, 2,225 `rdfs:label`. The remaining residue (a few persons,
4 places) is kept as typed `lmckg:*` nodes with no `P2888`.

## 5. Dates — `schema:DateTime` intervals

Detmold's `CTO_0001073` "creation period" is **not** a plain date: every one of the ~254
values is a `schema:DateTime` `START/END` interval whose span encodes the intended precision.
`coerce_date` reduces it accordingly:

| interval span | emitted as `wdt:P571` |
|---|---|
| same day (`…T00:00:00/…T23:59:59`) | `xsd:date` (≈193) |
| a full calendar month | `xsd:gYearMonth` (≈5) |
| a full calendar year (Jan 1 – Dec 31) | `xsd:gYear` (≈56) |

This branch is Detmold-specific: musiconn carries no interval dates, and APSearch's intervals
are all Jan-01 placeholders coerced straight to `gYear` (see the APSearch data-model). So all
three feeds reconvert correctly from the one shared `coerce_date`.

## 6. Emitted schema (SESEMMI reference)

```turtle
<work-iri> rdf:type lmckg:Work ;
           wdt:P31 wd:Q838948 ;                 # work of art (fallback)
           rdfs:label "…title…" ;
           wdt:P571 "1853"^^xsd:gYear ;          # inception (from the interval)
           cto:CTO_0001009 <gnd-or-viaf-uri> ;   # related person (composer/author — role-agnostic)
           cto:CTO_0001011 <geonames-uri> .      # related location

<geonames-uri> rdf:type lmckg:Place ;
           wdt:P2888 wd:Q64 ;
           rdfs:label "Berlin" .
```

Filter records by `lmckg:Work`; entities by `lmckg:Person` / `lmckg:Place`. Reconciled
entities reach Wikidata via `wdt:P2888`; residue has the local class + label but no `P2888`.
Namespaces as in the musiconn data-model (`lmckg:` local classes, `cto:` kept relations).

## 7. Manually verified IDs

Record type **Q838948** (work of art) and the two manual place QIDs (Zürich `Q72`, Hannover
`Q1715`) are in [`_archive/pid-qid-verification.md`](_archive/pid-qid-verification.md). The
GND/VIAF/GeoNames → QID crosswalk is deterministic and needs no manual verification.
