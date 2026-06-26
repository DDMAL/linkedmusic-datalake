# musiconn (`E5320`) — data model & mapping decisions

The authoritative reasoning behind the musiconn conversion: the source CTO shape, the
predicate map ([`../src/ontology/mapping.json`](../src/ontology/mapping.json) is its runtime
distillation), record typing, dates, reconciliation, the residue policy, and the emitted
schema (the SESEMMI reference). Counts are from `musiconn.ttl`.

## 1. What the source looks like

CKG remodels musiconn.performance into the **nfdicore / CTO** ontology. Every record is a
`CTO_0001005` "source item" (106,169 of them); each is an **Event** or a **Work**. The
relational backbone — who/where/what-collection — is **reified**: `has related person/org/
location` and `part of` point to **blank nodes**, and each blank node carries exactly two
triples: an `rdf:type` and one authority identifier:

```
_:bb277260  rdf:type      nfdi:NFDI_0000004          # person
_:bb277260  nfdi:NFDI_0001006  <https://d-nb.info/gnd/118508288>   # its GND id
```

| Relation (object = bnode) | count | typed entity | authority |
|---|---|---|---|
| `CTO_0001009` has related person | 128,205 | `NFDI_0000004` person | `NFDI_0001006` GND/VIAF |
| `CTO_0001011` has related location | 84,244 | `NFDI_0000005` place | GND/VIAF |
| `CTO_0001010` has related organization | 65,724 | `NFDI_0000003` organization | GND/VIAF |
| `BFO_0000050` part of | 35,418 | `NFDI_0000107` collection | GND/VIAF |

Authority IDs are **GND (`d-nb.info`, ~57%) and VIAF (`viaf.org`, ~43%) only** — no
Getty/TGN/Iconclass on the music entities.

Four consequences drive the whole conversion:

1. **Names are not in the dump.** Entity nodes have no label, only an authority ID
   (`rdfs:label` is on 100% of records, 0% of entity nodes). Display names come from
   Wikidata (reconciled) or the authority-service name fetch.
2. **No blank nodes in output** (LinkedMusic rule): collapse each entity bnode **to its
   authority URI**, and add a separate `wdt:P2888` → QID pivot when reconciled. The relation
   always points to the persistent authority-URI node — never directly to the QID, never to a
   blank node. Same shape as `mb:Area` / `diamm:City`.
3. **This dedupes for free.** The same real-world entity is reified as a *separate* bnode in
   every record. Collapsing by authority URI merges them — so the 128,205 person *links*
   become **19,775 distinct** `lmckg:Person` nodes.
4. **Roles are flattened.** Each of the 128,205 person↔event links is fully identified but
   carries **zero role/voice-type** — performer, composer and conductor roles are not
   represented in this dataset.

## 2. Predicate map

`convert_to_rdf.py` rewrites each triple by `mapping.json`; an absent predicate is dropped
and logged. **Policy: remap to `wdt:P*` where a faithful Wikidata equivalent exists; keep the
CTO IRI for the role-agnostic relations** (musiconn's whole backbone is role-agnostic, so
forcing it into specific Wikidata properties would assert roles the data doesn't have); drop
provenance noise.

### Record fields (on `CTO_0001005`)

| Source predicate | Action | Result |
|---|---|---|
| `rdf:type` | type | record → `lmckg:Event`/`Work` (from its is-about kind) |
| `rdfs:label` | label | keep `rdfs:label` (event/work title) |
| `CTO_0001070` has temporal coverage | remap_date | `wdt:P585` point in time → `xsd:date` |
| `CTO_0001026` has external classifier | classifier_aat | `wdt:P31` from AAT→QID **and keep the `cto:CTO_0001026` AAT URI** |
| `NFDI_0000191` published by | remap | `wdt:P123` |
| `NFDI_0000142` has license | remap | `wdt:P275` |
| `NFDI_0001008` has url | **drop** | self-referential (object == the record's own IRI) in every feed; the subject IRI already *is* the permalink |
| `CTO_0001007` has license statement | **drop** | values are stringified bnode ids (a CKG export bug) — the real license is `NFDI_0000142` |

### Relational backbone (kept as CTO; object collapsed to the authority-URI node)

| Source predicate | Action | Result |
|---|---|---|
| `CTO_0001009` has related person | keep_relation | `cto:CTO_0001009` → person node (typed `lmckg:Person`) |
| `CTO_0001010` has related organization | keep_relation | `cto:CTO_0001010` → `lmckg:Organization` |
| `CTO_0001011` has related location | keep_relation | `cto:CTO_0001011` → `lmckg:Place` |
| `CTO_0001019` has related item | keep_relation | `cto:CTO_0001019` (structural bridge, untyped object) |
| `CTO_0001006` is referenced in | keep_relation | `cto:CTO_0001006` (structural bridge) |
| `CTO_0001025` is about real-world entity | is_about | used to type the record, then **dropped** (the is-about bnode has no identity) |
| `BFO_0000050` part of | remap_relation | `wdt:P361` → collection node (typed `lmckg:Collection`) |
| `NFDI_0001006` has external identifier | resolved via crosswalk | becomes the `wdt:P2888` pivot on the collapsed node |

### Dropped (provenance / structural noise)

`dateModified`, `CTO_0001080` (source-file/API placeholder), `NFDI_0000207` (metadata
standard), `NFDI_0000146` (metadata media type), `schema:item`, `schema:dataFeedElement`,
`schema:associatedMedia`, `schema:sameAs`.

## 3. Record typing (`P31`)

Every record is typed two ways: a **local `lmckg:` class** (for cheap kind-filtering in
SESEMMI without federation) **and** a `wdt:P31` → QID from its AAT classifier. musiconn
records all carry a resolving AAT classifier, so the cross-feed `RECORD_KIND_P31` fallback
never fires here.

| Record (AAT classifier `CTO_0001026`) | local class | `wdt:P31` |
|---|---|---|
| event (`aat:300262956` "musical performances") | `lmckg:Event` | `wd:Q6942562` musical performance |
| work (`aat:300417577` "musical compositions") | `lmckg:Work` | `wd:Q207628` composed musical work |

Both QIDs are also confirmed deterministically (`aat:… wdt:P1014 → QID`). Real-world entities
(person/place/org/collection) get only the local `lmckg:` class, **not** a `wdt:P31` —
Wikidata already supplies the type for reconciled ones, and the local class is enough to
filter by kind.

## 4. Dates

`CTO_0001070` (performance date) is a uniform `YYYY-MM-DD` literal across all 65,348 event
records → coerced to `xsd:date` (`coerce_date`, with a `xsd:gYear` fallback for `YYYY` /
`YYYY-00-00`). musiconn carries **no** `schema:DateTime` interval dates, so the interval branch
(used by Detmold/APSearch) never fires — musiconn dates stay byte-identical regardless of the
feed-conditional logic.

## 5. Reconciliation rates

The crosswalk is **deterministic** GND `P227` + VIAF `P214`. The real coverage:

- **Distinct authorities → QID: ≈62%** (GND 61.9%, VIAF 61.8%).
- **Relation-weighted** (how many *links* land on a reconciled node): person **79.1%**,
  location 54.2%, organization 47.7% — popular composers reconcile far better than venues and
  orgs.
- Output: **14,165 distinct `wdt:P2888` pivots**, 110,684 `rdfs:label` (Wikidata names
  for reconciled nodes + fetched authority names for residue).

The unreconciled remainder is **genuinely absent from Wikidata** (~0.5% ID-hit on the residue
after the targeted ID lookup), not a pipeline bug. It is kept intact — never dropped.

## 6. Emitted schema (SESEMMI reference)

Namespaces: `lmckg:` = `https://linkedmusic.ca/graphs/ckg/` (local classes), `wdt:`/`wd:`
Wikidata, `cto:` = `https://nfdi4culture.de/ontology/` (kept role-agnostic relations).

```turtle
# a record (event)
<event-iri> rdf:type lmckg:Event ;
            wdt:P31 wd:Q6942562 ;              # musical performance
            rdfs:label "…title…" ;
            wdt:P585 "1919-11-15"^^xsd:date ;  # performance date
            cto:CTO_0001009 <gnd-or-viaf-uri> ;   # related person (role-agnostic)
            cto:CTO_0001010 <gnd-or-viaf-uri> ;   # related organization
            cto:CTO_0001011 <gnd-or-viaf-uri> ;   # related location
            wdt:P361        <collection-uri> .    # part of

# a collapsed, reconciled entity node (the relation object)
<https://d-nb.info/gnd/118508288> rdf:type lmckg:Person ;
            wdt:P2888 wd:Q255 ;                # exact match → Wikidata
            rdfs:label "Ludwig van Beethoven" .
```

Filter records by `lmckg:Event` / `lmckg:Work`; entities by `lmckg:Person/Place/Organization/
Collection`. Reconciled entities reach Wikidata via `wdt:P2888`; residue entities have the
local class and label but no `P2888`.

## 7. Verified record-type IDs

The deterministic crosswalk QIDs are trustworthy by construction. The record-type QIDs in use
are **Q6942562** musical performance and **Q207628** composed musical work, both confirmed
against Wikidata (`aat:… wdt:P1014 → QID`).
