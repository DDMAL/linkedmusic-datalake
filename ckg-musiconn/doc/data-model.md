# musiconn (`E5320`) — data model & mapping decisions

The [shared predicate map](../src/ontology/mapping.json) controls record typing,
dates, relationships and reconciliation output. This guide describes configured
behavior, not current population measurements or deployment. Identify the input,
mapping files and converter revision before reporting counts or link coverage.

## 1. Source shape and identity boundaries

Preprocessing indexes source records as Events or Works. Reified relationships
can point to person, place, organization or collection blank nodes carrying
an authority identifier. Conversion collapses these to persistent authority
URIs and adds supplied `wdt:P2888` crosswalk links separately. Repeated authority
URIs coalesce; this does not independently establish real-world identity.

Record labels are retained. Related-node names depend on supplied Wikidata or
authority-name inputs; missing names are not invented. `CTO_0001009` is a
related-person association with an unspecified role. It cannot establish
composition, performance or conducting, even if the person's Wikidata occupation
is known. Roles and performance dates must come from evidence about that event.

## 2. Predicate map

`convert_to_rdf.py` rewrites each triple by `mapping.json`; an absent predicate is dropped
and logged. **Policy: remap to `wdt:P*` where a faithful Wikidata equivalent exists; keep the
CTO IRI for role-unspecified relations**; drop only the configured properties.
Inspect reported unknown predicates before accepting a conversion.

### Record fields (on `CTO_0001005`)

| Source predicate | Action | Result |
|---|---|---|
| `rdf:type` | type | record → `lmckg:Event`/`Work` (from its is-about kind) |
| `rdfs:label` | label | keep `rdfs:label` (event/work title) |
| `CTO_0001070` has temporal coverage | remap_date | `wdt:P585` point in time → `xsd:date` |
| `CTO_0001026` has external classifier | classifier_aat | `wdt:P31` from AAT→QID **and keep the `cto:CTO_0001026` AAT URI** |
| `NFDI_0000191` published by | remap | `wdt:P123` |
| `NFDI_0000142` has license | remap | `wdt:P275` |
| `NFDI_0001008` has url | **drop** | the configured map emits no separate URL for this property |
| `CTO_0001007` has license statement | **drop** | this configured drop does not replace record-level `NFDI_0000142` licence assertions |

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

Indexed records receive a local `lmckg:` class. A resolving AAT classifier can
also add `wdt:P31` using the supplied record-type map. The configured choices are:

| Record (AAT classifier `CTO_0001026`) | local class | `wdt:P31` |
|---|---|---|
| event (`aat:300262956` "musical performances") | `lmckg:Event` | `wd:Q6942562` musical performance |
| work (`aat:300417577` "musical compositions") | `lmckg:Work` | `wd:Q207628` composed musical work |

Related person/place/organization/collection nodes receive local classes.
Identifier mappings and type choices require source-backed review; neither
syntax nor a deterministic lookup proves a link is correct.

## 4. Dates

`CTO_0001070` maps to `wdt:P585`. The existing coercion preserves supported valid
dates as `xsd:date`, reduces unknown day/month components to `xsd:gYearMonth` or
`xsd:gYear`, and can lose precision for unsupported/invalid components. This
behavior is unchanged by the [APSearch interval model](../../ckg-apsearch/doc/creation-period-preservation.md).
A performance date is distinct from a work's creation period or a catalogue
record's modification date. Inspect the source and output datatype for each claim.

## 5. Reconciliation evidence

The shared `crosswalk.json` contains matches from Wikidata identifier lookups
(GND `P227`, VIAF `P214` and GeoNames `P1566`), name matches imported from
OpenRefine, and manually entered links such as the
[Detmold place mappings](../../ckg-detmold/README.md#3-reconciliation).
The converter emits the same `wdt:P2888` predicate for all three. To audit a
link, check the identifier response, the name-reconciliation export or the
evidence for the manual choice. Source nodes without a crosswalk target remain
in the graph. A missing match can reflect lookup or cache limitations.
Review identity independently under the
[evaluation protocol](../../evaluation/protocol.md).
Report distinct-node and relation-weighted coverage separately from correctness.

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
