# RISM and VIAF identifier text

Implemented 27 October 2026. Archive RISM identifiers and person RISM/VIAF
identifiers now load from reconciled CSVs as text. Default pandas inference
previously changed `00123` to an integer or a floating-point value, and a blank
in the same column could turn `9007199254740993` into `9007199254740992.0`.
NA-like strings could disappear. This repair preserves the supplied cells;
it does not validate external identifiers or infer new matches.

The subsequent [identifier-list repair](external_identifier_selection.md) on
27 October preserves all archive/person entries and replaces the first/last
selection described below for new extractions. This document records the
earlier scalar repair and remains the contract for legacy CSV fallback.

## Source and export boundary

The upstream [archive identifier model](https://github.com/diamm/diamm/blob/052004f86960a5dc4d1e7446be8d5a6ac8594bd1/diamm/models/data/archive_identifier.py)
and [person identifier model](https://github.com/diamm/diamm/blob/052004f86960a5dc4d1e7446be8d5a6ac8594bd1/diamm/models/data/person_identifier.py)
store identifiers in character fields and request identifiers rather than full
URLs. Their [archive](https://github.com/diamm/diamm/blob/052004f86960a5dc4d1e7446be8d5a6ac8594bd1/diamm/serializers/website/archive.py)
and [person](https://github.com/diamm/diamm/blob/052004f86960a5dc4d1e7446be8d5a6ac8594bd1/diamm/serializers/website/person.py)
serializers expose each identifier as a string alongside a label and URL.
The [identifier definitions](https://github.com/diamm/diamm/blob/052004f86960a5dc4d1e7446be8d5a6ac8594bd1/diamm/helpers/identifiers.py)
name the relevant types `RISM Online` and `VIAF`. These observations are pinned
to revision `052004f86960a5dc4d1e7446be8d5a6ac8594bd1`, not to a verified
historical snapshot or running API version.

[`to_csv.py`](../src/to_csv.py) copies selected `identifiers[].identifier`
strings into three columns. No extraction change was needed for this boundary.

| Table | CSV column | Selection before the identifier-list repair | RDF property |
| --- | --- | --- | --- |
| Archives | `rism_id` | First label containing RISM, case-insensitive | `wdt:P5504` |
| People | `rism_id` | Last label containing RISM, case-insensitive | `wdt:P5504` |
| People | `viaf_id` | Last label containing VIAF, case-insensitive, excluding RISM-labelled entries | `wdt:P214` |

These are the only RISM/VIAF columns in the tracked nine-table export layout.
Other JSON identifier lists, including source identifiers, are not covered by
these columns. The selected text is preserved without taking the identifier's
URL, splitting punctuation, trimming, casting to a number or normalizing it.
Absent matching entries and null/empty selected values become empty CSV cells.
Non-string JSON identifiers, missing identifier-object keys and absent/null
identifier lists are outside the reviewed extraction contract.

The [archive export](../openrefine/export/archives_export.json) and
[people export](../openrefine/export/people_export.json) retain the three original
columns with `entity-name` output and `blankUnmatchedCells=false`. Their
histories use IDs as hints when reconciling the copied name columns; they do
not transform or reconcile these ID columns. Import archive and people CSVs
as strings with automatic numeric/date parsing and whitespace trimming disabled.
Configure parsing before creating the project, as described in OpenRefine's
[project preview](https://openrefine.org/docs/manual/starting#project-preview).
Those settings apply to the project; any name cleanup needed for reconciliation
belongs on the copied name column. An export template cannot undo coercion
that already occurred during import.

## RDF behavior and compatibility

The RDF loader applies text converters only to these three additional columns.
Nonempty cells remain ordinary string literals under the existing P5504/P214
properties on their DIAMM source nodes. Leading zeros, long digit strings,
`0`, decimal/exponent-looking strings, NA-like text, Unicode, punctuation,
quotes, line breaks and whitespace survive. An empty cell emits no identifier
statement; whitespace alone is retained. Missing, null and empty source values
are not distinguished by this CSV route.

An ID-like value such as `Q42` or a full URL stays literal in these fields.
Preserving unexpected text is not a claim that it is a valid RISM or VIAF ID.
No canonical authority URL, P2888 assertion or identity inference is derived
from it. Name reconciliation still independently supplies P2888 links under the
[bare-QID contract](identifier_validation.md). Local nodes, labels and source
relationships retain their existing behavior. Multiple CSV rows for one local
node retain their different identifier values; identical triples collapse.

Previously numeric RDF objects now become string literals. Queries using
numeric comparisons or typed numeric constants for identifiers need string
comparisons instead. For example:

```sparql
PREFIX diamm: <https://linkedmusic.ca/graphs/diamm/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
SELECT ?person WHERE {
  ?person a diamm:Person; wdt:P214 "00123" .
}
```

Scope this pattern to the DIAMM graph when querying multiple datasets. This
synthetic example checks exact identifier text, not a verified person's identity.
Already-rounded or stripped CSV values cannot be reconstructed by this repair.
In particular, `123.0` is preserved as supplied rather than guessed to mean `123`.

## Validation and remaining work

Five [offline tests](../tests/test_external_identifier_text.py) exercise all
three columns through the actual converter, independently specified full graph
expectations and Turtle round trips. Numeric-only fixtures expose inference
that mixed text would mask. Controls cover empty columns, long digits, zeros,
NA-like and punctuated text, QIDs/URLs, duplicate/conflicting rows and absent
matches. The extraction/export/RDF CLI test checks the string boundary, blank
and null cases, a supplied name match, archive/location/composition relationships
and an exact-string SPARQL lookup. The export/history checks guard the original
columns. Before the fix the five tests reported six failures (including
subtests); all pass after the fix.
The complete offline command passes **104 tests and 14 competency fixture
queries**, including all 21 DIAMM tests, at that repair. Black and diff checks passed.

The export projection is synthetic; no OpenRefine GUI or reconciliation-service
replay was performed. Historical affected counts, source/version compatibility
and actual identifier shapes remain unmeasured. Other CSV columns keep their
existing parsing. This scalar repair did not preserve every list entry; the
subsequent [selection repair](external_identifier_selection.md) addresses that
boundary for new extractions. Historical old outputs still require regeneration.

When snapshot access is confirmed, compare raw identifiers, extracted CSVs,
OpenRefine project cells and reconciled exports by DIAMM row ID. Record checksums
and conversion version, recover already-coerced values only from matching source
evidence, and regenerate into a separate directory. Check exact text and
identifier datatypes, omitted blanks, reconciliation links and source
relationships before replacing any stored or live graph. No source data was
regenerated and no production graph was changed by this repair.
