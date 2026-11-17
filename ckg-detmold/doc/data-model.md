# Detmold (`E5305`) — data model and mapping decisions

Detmold uses the [shared CKG predicate map](../../ckg-musiconn/doc/data-model.md)
and converter. This guide describes code behavior; stored/deployed graphs and
population counts require separately identified inputs and converter revisions.

## Records and relationships

Preprocessing derives record kinds from the source's is-about information.
Indexed Work records become `lmckg:Work`. Reified person/place nodes collapse
to their authority URIs; configured crosswalk targets add `wdt:P2888` links.
Labels on records are retained. Auxiliary labels depend on the supplied
crosswalk/name inputs; the converter does not invent missing names.

`lmckg:` means `https://linkedmusic.ca/graphs/ckg/`, shared across the feeds.
The Detmold named graph is `https://linkedmusic.ca/graphs/ckg-detmold/`; its
IRI is not the class namespace.

| Source predicate | Output behavior |
| --- | --- |
| `rdfs:label` | Retain the work label |
| `CTO_0001073` creation period | Existing `wdt:P571` date coercion below |
| `CTO_0001009` related person | Keep CTO relation to an `lmckg:Person` node |
| `CTO_0001011` related location | Keep CTO relation to an `lmckg:Place` node |
| `NFDI_0001006` authority identifier | Used to resolve the entity URI/crosswalk |
| `NFDI_0001008` URL | Dropped by the shared mapping |

A related-person link does not specify composer, author or performer. The
person's occupation in Wikidata cannot supply the missing role for this record.
Likewise, a creation period does not independently establish a performance date.

## Typing and crosswalks

A Detmold Work without a resolving classifier receives the configured fallback
`wd:Q838948` (work of art). This is a broad configured type, not a determination
that each record is an opera or musical composition. APSearch has a different
fallback; musiconn's record types come from its supplied classifier map.

The shared crosswalk machinery uses GND `P227`, VIAF `P214` and GeoNames `P1566`.
An explicit identifier match is evidence to audit, not a guarantee of identity.
Manual links, including place links, need their own source-backed evidence; an
administrative place and a populated-place feature must not be merged solely
because their labels agree. Unresolved authority nodes remain available without
a fabricated `P2888` target. Coverage and correctness have different denominators.

## Existing date conversion

For recognized timestamp intervals, equal valid calendar dates project to
`xsd:date`; bounds within the same year/month project to `xsd:gYearMonth`; bounds
within the same year project to `xsd:gYear`. Other multiyear intervals remain
source terms. This legacy coercion is lossy and does not retain paired endpoints
for these projections or fully validate all interval ordering/components.
It must not be treated as the APSearch interval model.

The [APSearch preservation branch](../../ckg-apsearch/doc/creation-period-preservation.md)
retains source assertions and paired bounds with parse/review evidence. It runs
only for APSearch creation periods. Detmold's existing behavior remains unchanged;
compare its exact source/output sets when validating shared converter changes.

## Query boundaries

Filter source works by `lmckg:Work`; related entities by `lmckg:Person` or
`lmckg:Place`. Follow the explicit relation to the authority URI and then any
`wdt:P2888` target. A missing target is unresolved. Inspect the date datatype
before applying date functions, and do not infer role or timing from a nearby
record's metadata. Identify the loaded graph revision before interpreting answers.
