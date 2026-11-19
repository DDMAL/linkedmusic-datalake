# APSearch (`E6304`) — data model and mapping decisions

APSearch uses the same converter and predicate mapping as
[musiconn](../../ckg-musiconn/doc/data-model.md) and Detmold. This document describes
the configured APSearch behavior. It does not identify the code or input revision
of any stored/deployed graph; measurements require their own input hashes and
converter revision.

## Source identity

The primary [NFDI4Culture E6304 record](https://nfdi4culture.de/resource/E6304/about.html)
identifies APSearch as **Arab Phonogram Search**, a portal aggregating Arabic
phonogram metadata, with BBAW as publisher. The feed uses nfdicore/CTO terms.
In the E6304.nt snapshot with SHA-256
`4579a5cec820d87a7d3838e014176c85c6c6c68a863903134e3ee45cf663e891`,
5,617 of 6,271 distinct `CTO_0001005` source items link to
`https://www.elararchive.org/legal` via `NFDI_0000142` asserted on the record
(counted directly from the source triples with RDFLib 7.1.4). APSearch and
ELAR are distinct, and these references identify only the cited licence terms.
Check where each content link resolves and what access it allows at its source.

The converter handles media classifiers and content URLs. It does not run an
APSearch-specific label-reconciliation workflow. Assess missing fields and access
conditions against the particular source export and repository, not the feed name.

## Predicate map

| Source predicate | Action | Output |
| --- | --- | --- |
| `rdf:type CTO_0001005` | type records with an indexed is-about kind | corresponding `lmckg:` class |
| `rdfs:label` | preserve labels | `rdfs:label` |
| `CTO_0001049` | media classifier lookup | configured `wdt:P31` |
| `CTO_0001026` | AAT classifier lookup | configured `wdt:P31`; retain AAT URI |
| `CTO_0001073` creation period | date coercion | `wdt:P571` with date-dependent datatype; unrecognized values unchanged |
| `NFDI_0000142` licence | remap and crosswalk | `wdt:P275` source URI; optional `wdt:P2888` target |
| `NFDI_0000191` publisher | remap and crosswalk | `wdt:P123` source URI; optional `wdt:P2888` target |
| `CTO_0001021` content URL | join through `schema:associatedMedia` | `wdt:P953` URI |

`lmckg:` is `https://linkedmusic.ca/graphs/ckg/`, shared across the three feeds;
the APSearch named graph is `https://linkedmusic.ca/graphs/ckg-apsearch/`.
The graph IRI is not the class namespace.

The mapping drops envelope/metadata properties including `schema:dateModified`,
`schema:item`, `schema:dataFeedElement`, `schema:sameAs`, and the configured
metadata-standard/media-type properties. `dateModified` is not used as a creation
date. A constant timestamp alone would not prove its provenance. The
`schema:associatedMedia` edge is used for the content-URL join before being dropped.

## Record typing

An indexed is-about kind supplies the local class, but the converter emits it
only when the record also has its own `rdf:type CTO_0001005` source-item assertion.
An index entry alone does not guarantee an `lmckg:` type. Resolving media/AAT
classifier mappings add `wdt:P31`. If none resolves, APSearch assigns
`wdt:P31 wd:Q17537576` (creative work) only to records indexed as `Work`,
even when the source-item assertion is absent. An indexed `Event` has no
configured fallback.
The broad fallback avoids asserting a specific media class without a mapping.
It is not a claim that all source objects have the same medium.

The APSearch entries in `data/mappings/record_types.json` use full IRI keys.
In the table, `cto:` expands to `https://nfdi4culture.de/ontology/` and
`aat:` to `http://vocab.getty.edu/aat/`.

| Source classifier | Configured `wdt:P31` |
| --- | --- |
| `cto:CTO_0001043` audio object | `Q3302947` audio recording |
| `cto:CTO_0001044` image object | `Q478798` image |
| `cto:CTO_0001048` video object | `Q30070675` video recording |
| `cto:CTO_0001047` text object | `Q234460` text |
| `aat:300028633` sound recordings | `Q3302947` audio recording |
| `aat:300265798` cylinder phonographs | `Q691783` phonograph cylinder |
| `aat:300234108` ethnographic objects | Intentionally unmapped |
| `cto:CTO_0001045` media object | Intentionally unmapped |

`build_crosswalk.py` writes each indexed AAT code's `wdt:P1014` match to
`record_types.json`, replacing any previous value for that code. It silently
skips AAT codes without a match and reports CTO media classes for manual
mapping. The cylinder mapping (`aat:300265798` → `Q691783`) is configured by
hand. An unmapped classifier contributes no
`wdt:P31` of its own. The converter retains the source AAT URI even when it
has no mapping. Check changes to these choices against all three feeds.

## Creation dates

The APSearch date branch coerces a recognized creation-period interval to the
start year as `xsd:gYear`. It does not retain the original interval or the ending
year. For example, `1909-01-01T00:00:00/1950-01-01T23:59:59` becomes the start
year and cannot support an interval-overlap answer after conversion. Date-only
ranges such as `1909-01-01/1950-01-01` do not match this interval branch and remain
unchanged. A valid full date such as `2010-04-20` becomes `xsd:date`; partial
year/month/day forms use the existing date-coercion rules, including
`2010-04-00` becoming `xsd:gYearMonth` and `2010` becoming `xsd:gYear`.
For a date-shaped value with an invalid day, the converter keeps the year and
a valid month (`2010-02-30` becomes `"2010-02"^^xsd:gYearMonth`). An invalid
month leaves only the year (`2010-13-05` becomes `"2010"^^xsd:gYear`).
Unrecognized values remain unchanged. January-01 boundaries alone do not
establish exact day precision. Creation dates must not become performance dates.

The feeds use mixed date datatypes. Queries must inspect the datatype/lexical
form before applying date functions; `YEAR` is not portable over `xsd:gYear`.
Do not derive corpus-wide interval or precision counts from this contract.

## Licences and publisher

Source licence/publisher URIs remain the `wdt:P275`/`wdt:P123` objects. When the
selected crosswalk supplies a target, a separate `wdt:P2888` edge links that URI
to Wikidata. The existing mapping choices include NFDI resources `E6404` to
`Q20007257`, `E6429` to `Q18199165`, and `E2431` to `Q219989`.
An unmapped source URI remains available without a fabricated QID.

The converter emits a licence supplied directly on a record. It skips licences
on associated-media blank nodes. These RDF links
preserve the supplied level of description; they do not decide access or reuse
rights. Compare the exact source and mapping snapshot when auditing the output.

## Content URLs and queries

Preprocessing follows `schema:associatedMedia` from a record to a blank node.
For each such node it keeps the last referring record and the last literal
`CTO_0001021` value encountered in input order. An IRI object is skipped.
The converter emits the joined value as a `wdt:P953` URI on that record.
A record can acquire several URLs through separate media nodes.
A URL hostname alone does not prove repository ownership, link availability,
or the population's source composition.
Keep record counts, link counts and distinct URL counts separate.

```turtle
@prefix lmckg: <https://linkedmusic.ca/graphs/ckg/> .
@prefix wdt: <http://www.wikidata.org/prop/direct/> .
@prefix wd: <http://www.wikidata.org/entity/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

<urn:synthetic:record> a lmckg:Work ;
    wdt:P31 wd:Q3302947 ;
    rdfs:label "Synthetic recording" ;
    wdt:P571 "2010"^^xsd:gYear ;
    wdt:P123 <https://nfdi4culture.de/id/E2431> .
<https://nfdi4culture.de/id/E2431> wdt:P2888 wd:Q219989 .
```

This example describes RDF shape, not an observed source record. Exact source,
crosswalk and code revisions are needed for a reproducible candidate conversion;
publication of this documentation does not update stored or deployed RDF.
