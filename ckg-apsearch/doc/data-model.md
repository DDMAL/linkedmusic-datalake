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
APSearch is distinct from ELAR. An ELAR legal URI on an individual record is
retained source metadata; it does not establish that the whole feed is ELAR,
that every content link resolves there, or that all upstream access is restricted.

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
classifier mappings add `wdt:P31`; otherwise the APSearch fallback for indexed
records is `wd:Q17537576` (creative work). That fallback does not require the
source-item assertion and therefore does not guarantee a local class.
The broad fallback avoids asserting a specific media class without a mapping.
It is not a claim that all source objects have the same medium.

The current configured mapping choices include audio recording (`Q3302947`),
image (`Q478798`), video recording (`Q30070675`), text (`Q234460`) and phonograph
cylinder (`Q691783`). These choices and their target validity need independent
source-backed review when the mapping snapshot changes. An unmapped AAT term
can remain as an external-classifier URI without acquiring a guessed class.
A mapping change must be checked against all three feeds even when a sampled
classifier occurs in only one feed.

## Creation dates

The APSearch date branch coerces a recognized creation-period interval to the
start year as `xsd:gYear`. It does not retain the original interval or the ending
year. For example, `1909-01-01T00:00:00/1950-01-01T23:59:59` becomes the start
year and cannot support an interval-overlap answer after conversion. Date-only
ranges such as `1909-01-01/1950-01-01` do not match this interval branch and remain
unchanged. A valid full date such as `2010-04-20` becomes `xsd:date`; partial
year/month/day forms use the existing date-coercion rules, including
`2010-04-00` becoming `xsd:gYearMonth` and `2010` becoming `xsd:gYear`.
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

Only record-level licence assertions are emitted by this path. A licence on an
associated-media node is not substituted for a record licence. These RDF links
preserve the supplied level of description; they do not decide access or reuse
rights. Compare the exact source and mapping snapshot when auditing the output.

## Content URLs and queries

Preprocessing joins record → `schema:associatedMedia` → `CTO_0001021` and the
converter emits the resulting `wdt:P953` URI. A URL hostname alone does not prove
repository ownership, link availability, or the population's source composition.
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
