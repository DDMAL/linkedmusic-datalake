# RISM and VIAF identifier text

Archive RISM identifiers and person RISM/VIAF identifiers remain strings through
CSV loading and RDF conversion. Leading zeros, long digits and NA-like strings
are preserved. This does not validate the identifiers or infer new matches.

The [identifier-list contract](external_identifier_selection.md) determines
which values are emitted. A nonempty `source_identifiers` cell supplies the
complete list, including authoritative `[]` or `null`. Missing/empty evidence
cells use the legacy scalar columns described here.

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

[`to_csv.py`](../src/to_csv.py) retains the complete parsed identifier list and
supplies scalar hints only for one distinct nonblank string per supported scheme.
Recognized labels are complete `RISM Online` and `VIAF`, case-insensitive without
trimming. Unknown labels and unexpected list entries remain JSON evidence.

| Table | Scalar column | RDF property | Projection |
| --- | --- | --- | --- |
| Archives | `rism_id` | `wdt:P5504` | All nonempty RISM strings from supplied JSON, or the scalar fallback |
| People | `rism_id` | `wdt:P5504` | All nonempty RISM strings from supplied JSON, or the scalar fallback |
| People | `viaf_id` | `wdt:P214` | All nonempty VIAF strings from supplied JSON, or the scalar fallback |

These are the only RISM/VIAF columns in the nine-table export layout. Other
entities' identifier lists are outside this contract. No identifier is taken
from a URL, split, trimmed, cast to a number or normalized. Within retained JSON,
nulls, empty strings, missing object keys and non-string values remain distinct;
they do not supply identifier assertions. Legacy empty scalar cells do not
distinguish missing, null and empty source values.

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

The RDF loader applies text converters to all three scalar columns and the
archive/person JSON evidence columns, alongside the other documented text fields.
Nonempty cells remain ordinary string literals under the existing P5504/P214
properties on their DIAMM source nodes. Leading zeros, long digit strings,
`0`, decimal/exponent-looking strings, NA-like text, Unicode, punctuation,
quotes, line breaks and whitespace survive. An empty cell emits no identifier
statement; whitespace alone is retained. Missing, null and empty values
are not distinguished by the legacy scalar fallback.

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
Already-rounded or stripped CSV values cannot be reconstructed by the converter.
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
columns. Run from the repository root:

```sh
poetry run python scripts/check_offline.py
```

The export projection is synthetic; no OpenRefine GUI or reconciliation-service
replay was performed. Historical affected counts, source/version compatibility
and actual identifier shapes remain unmeasured. Other CSV columns keep their
existing parsing. The complete-list contract preserves all supplied archive/person
entries in new extractions. Historical scalar outputs require the matching raw snapshot to
recover omitted entries.

When snapshot access is confirmed, compare raw identifiers, extracted CSVs,
OpenRefine project cells and reconciled exports by DIAMM row ID. Record checksums
and conversion version, recover already-coerced values only from matching source
evidence, and regenerate into a separate directory. Check exact text and
identifier datatypes, omitted blanks, reconciliation links and source
relationships before replacing any stored or live graph. Synthetic checks do not establish historical export fidelity or deployed behavior.
