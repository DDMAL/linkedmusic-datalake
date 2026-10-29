# Archive and person identifier lists

Implemented 27 October 2026. Archive extraction previously selected the first
RISM-labelled entry; person extraction selected the last RISM/VIAF-labelled
entry. Additional identifiers disappeared, a blank could hide a nonempty value,
and substring label matching could assign an unrelated or ambiguous label to
RISM or VIAF. Synthetic records reproduce these conversion defects. Their
historical prevalence has not been measured.

## Evidence and scope

The upstream [archive identifier model](https://github.com/diamm/diamm/blob/052004f86960a5dc4d1e7446be8d5a6ac8594bd1/diamm/models/data/archive_identifier.py)
and [person identifier model](https://github.com/diamm/diamm/blob/052004f86960a5dc4d1e7446be8d5a6ac8594bd1/diamm/models/data/person_identifier.py)
associate identifier rows with an archive/person, without declaring one preferred
identifier or a uniqueness constraint per scheme. The
[archive](https://github.com/diamm/diamm/blob/052004f86960a5dc4d1e7446be8d5a6ac8594bd1/diamm/serializers/website/archive.py)
and [person](https://github.com/diamm/diamm/blob/052004f86960a5dc4d1e7446be8d5a6ac8594bd1/diamm/serializers/website/person.py)
detail serializers expose all related identifier rows with `label`, `identifier`
and `url`. The [label definitions](https://github.com/diamm/diamm/blob/052004f86960a5dc4d1e7446be8d5a6ac8594bd1/diamm/helpers/identifiers.py)
name the two schemes `RISM Online` and `VIAF`.

These files were inspected at revision
`052004f86960a5dc4d1e7446be8d5a6ac8594bd1`. This supports preserving the list
without choosing a preferred entry. It does not establish the deployed API or
historical snapshot version, actual occurrence counts, or identifier correctness.
No live DIAMM records or stored snapshots were inspected for this repair.

## Extraction and reconciliation

Both archive and person CSVs append `source_identifiers`: a JSON serialization
of the complete supplied `identifiers` value. List order, repeated entries,
string contents, labels, URLs, additional object keys, nulls and unexpected
entries survive. Object keys are sorted and JSON whitespace is normalized;
this preserves the parsed JSON value, not the original JSON bytes. An absent
field becomes `[]`; an explicit null remains `null`. An unexpected top-level
value other than a list or null stops extraction with an error.

Full labels `RISM Online` and `VIAF` are recognized case-insensitively, without
trimming or substring matching. `RISM`, `Not RISM Online`, `VIAF extra` and
`VIAF / RISM Online` are not reviewed aliases. They remain in the evidence but
do not produce scheme-specific assertions. Missing/non-string labels or
identifier values and non-object entries likewise remain evidence. Values are
never inferred from URLs or converted from numbers to strings.

The existing `rism_id` and person `viaf_id` columns now serve as scalar
reconciliation hints. A hint contains the exact source string only when there
is one distinct nonblank string for the supported scheme. Repeated identical
strings yield one hint; different strings leave it empty. Nulls, empty strings
and whitespace-only strings do not replace a useful hint. Whitespace-only
values remain in the JSON and RDF projection. Distinctness is exact: `001` and
`1`, or `001` and ` 001 `, are not merged. A hint is not identifier validation.

The existing histories already read the scalar columns as P5504/P214 hints and
leave the new evidence column untouched; their reconciliation operations are
unchanged. When several IDs are supplied, matching has less hint information
and may produce different results. Review those matches before deployment;
this change does not assert which supplied ID is correct. Do not concatenate
identifiers into one hint or split the JSON cell into OpenRefine rows.

Import these columns with automatic number/date parsing and whitespace trimming
disabled, then use the updated archive/person export templates. The JSON cell
must remain untouched text. The histories' record selection and actual service
behavior were not replayed in OpenRefine. Existing projects without source
lists require the matching raw records to recover them; do not manufacture a
complete list from a previously selected scalar.

## RDF representation

Namespace `diamm:` is `https://linkedmusic.ca/graphs/diamm/`. The following
properties go from the local DIAMM archive/person subject to a literal:

| Property | Readable label and definition | Object | Supported interpretation / limit |
| --- | --- | --- | --- |
| `diamm:sourceIdentifiersJson` | Source identifier list JSON: the exported JSON evidence from this record's `identifiers` field, as defined by the linked serializers above | `xsd:string` containing a JSON list or null | Inspect supplied order, duplicate entries, labels, values and URLs together; not a preferred identifier, canonical authority link or verified identity |
| `wdt:P5504` | [RISM ID](https://www.wikidata.org/wiki/Property:P5504): each nonempty string supplied under a reviewed RISM label, for archives and people | String literal | Query all supplied RISM strings; syntax and correctness remain unverified |
| `wdt:P214` | [VIAF cluster ID](https://www.wikidata.org/wiki/Property:P214): each nonempty string supplied under a reviewed VIAF label, for people | String literal | Query all supplied VIAF strings; no identity inference or preferred-value selection |

The JSON property is a locally defined evidence property, not an upstream DIAMM
ontology term. Its definition retains the distinction between a source list
and the set of queryable identifier assertions. RDF assertions collapse exact
duplicates; the JSON retains multiplicity and order. Different CSV rows for
one subject retain their distinct JSON literals and projected identifiers.
There is no implied pairing between different lists or across RISM/VIAF values.

A nonempty `source_identifiers` cell is authoritative for the projection.
Scalar hints are ignored, even when the list is `[]` or the value is `null`.
Malformed JSON or a non-list/non-null JSON value stops conversion with a
`ValueError` naming the source subject; it does not silently fall back to a
possibly stale hint. Unexpected entries *inside* a valid list are retained in
the evidence and skipped during projection.

For a missing column or empty CSV cell, the prior scalar behavior remains:
archive `rism_id` and person `rism_id`/`viaf_id` are emitted as supplied string
literals. Such a row has no `sourceIdentifiersJson` assertion and makes no
claim of complete source-list preservation. This fallback also permits mixed
legacy/new rows, but cannot distinguish intentional legacy rows from accidental
loss of a new evidence cell. Validate exports against their matching extraction.

No normalization, splitting, identifier validation, authority-URL creation,
P2888 creation or identity inference is performed from this list. `Q42` and full
URLs in a supported identifier field stay literal. Other identifier schemes
and archive VIAF entries survive only inside the retained JSON; mappings for
them remain outside this repair. Source-entity name reconciliation continues
to supply P2888 independently under the existing bare-QID contract. Labels and
source relationships keep their existing behavior.

For example, an archive supplying `00123` and `00456` under `RISM Online` has
two P5504 statements and a blank scalar hint. A person with `00042`, followed
by an empty VIAF entry, retains `00042` as both its hint and P214 literal.
Query multiple supplied IDs without assuming cardinality one:

```sparql
PREFIX diamm: <https://linkedmusic.ca/graphs/diamm/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
SELECT ?person ?id ?evidence WHERE {
  ?person a diamm:Person; wdt:P5504 ?id .
  OPTIONAL { ?person diamm:sourceIdentifiersJson ?evidence }
}
```

Scope this query to the DIAMM named graph in a shared endpoint. JSON is opaque
to ordinary triple patterns: parse the literal to audit occurrence counts or
individual entry labels/URLs. Multiple evidence literals can multiply query
rows; count distinct identifiers separately from source occurrences.

## Validation and regeneration

Seven [regression tests](../tests/test_external_identifier_selection.py) run
actual extraction, tracked export-column projection, CSV loading and RDF CLI
conversion. They cover repeated/conflicting IDs, input-order changes, blank/null
entries, label near misses, unknown schemes, unexpected entry shapes, full JSON
retention, strings with zeros/long digits/Unicode/newlines, old columns, malformed
JSON, authoritative empty lists, duplicate rows, source links, independently
specified graph assertions, Turtle round trips and a SPARQL lookup. The old
pipeline reported 11 failures (including subtests); the seven tests now pass.
Existing text/name tests also assert the additional evidence triples.
At the 27 October list repair, the complete offline command passed **111 tests and 14 competency fixture
queries**, including all 28 DIAMM tests. Black and diff checks pass. Self-review
found no introduced correctness defects and added controls for the optional
absent identifier list and labels with surrounding whitespace. No independent
agent review was performed.

The full offline command, `poetry run python scripts/check_offline.py`, is the
validation route. Synthetic export projection is not an OpenRefine GUI or
reconciliation-service replay. Historical prevalence, source-version agreement,
export completeness and graph-size increase remain unmeasured. Other DIAMM
identifier lists and non-identifier CSV coercion remain outside this scope.

When snapshot access resumes, record source checksums and conversion revision,
compare all archive/person list entries to extracted JSON cells, and audit
recognized/unknown labels, duplicates, empty entries and distinct candidate
counts per scheme. Re-extract from matching raw records into a separate
directory, reconcile using the new hints and export templates, then compare
the JSON evidence and all supported string assertions in staging. Inspect
changed name matches as well as multiple-ID query behavior. Old scalar CSVs
and RDF cannot reconstruct omitted entries. Back up and replace the graph
only after those checks; appending would retain old misclassified assertions.
No source data was regenerated, published or deployed by this local repair.
