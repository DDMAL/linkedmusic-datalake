# Original person names and floruit text

Implemented 26 October 2026. The extractor used to remove a parenthesized date
suffix from `full_name` and save only the cleaned result. For a name such as
`Scribe (fl. ca. 1500–1520?)`, that lost the only exported activity-date evidence.
New extractions retain the original display name as well as the cleaned name.

## Source and pipeline evidence

The upstream [Person model](https://github.com/diamm/diamm/blob/052004f86960a5dc4d1e7446be8d5a6ac8594bd1/diamm/models/data/person.py)
formats `full_name` with lifespan years or, when those are absent, `fl.` plus
floruit text. The [person detail serializer](https://github.com/diamm/diamm/blob/052004f86960a5dc4d1e7446be8d5a6ac8594bd1/diamm/serializers/website/person.py)
exports `full_name` but declares no separate floruit field. Keeping only a
cleaned name therefore loses source information. These are pinned source-code
observations; no historical JSON snapshot or live DIAMM API was inspected.

[`to_csv.py`](../src/to_csv.py) now appends two columns after the existing person
columns. The name-cleaning rule and the reconciliation name are unchanged.

| CSV column | Meaning | RDF on the DIAMM person |
| --- | --- | --- |
| `full_name` | Existing cleaned name for reconciliation | Existing `rdfs:label` |
| `source_full_name` | Exact original JSON `full_name` string | `diamm:sourceFullName`, `xsd:string` |
| `floruit` | Separate JSON `floruit` text, if supplied | `diamm:floruit`, `xsd:string` |

`diamm:` means `https://linkedmusic.ca/graphs/diamm/`. The optional separate
floruit column supports inputs that supply it; it is normally blank for the
reviewed detail serializer. Floruit present only in a display name stays in
`source_full_name`. It is not copied into a purported independent source field,
and neither text field supplies birth/death dates or parsed year bounds.
If the two source fields disagree, both remain available without choosing one.

The [people export template](../openrefine/export/people_export.json) includes
both appended columns. The existing [history](../openrefine/history/people_history.json)
does not transform or reconcile them, and its old column insertion positions
are retained. For new projects, import these cells as strings and disable
automatic numeric/date conversion and whitespace trimming. Preserve the two
columns through all edits and use the updated export template. See OpenRefine's
[import settings](https://openrefine.org/docs/manual/starting#project-preview)
and [cell data types](https://openrefine.org/docs/manual/exploring#data-types).
Do not reconcile or clean the evidence columns; work on `full_name_@id` instead.

The RDF loader reads `full_name`, `source_full_name` and `floruit` as text so
`NA`, `nan`, `0012`, quotes, Unicode, line breaks and surrounding spaces survive.
This also prevents cleaned names from becoming missing values or numbers.
If cleaning leaves an empty name (for example, a name consisting only of
`(fl. ca. 1500)`), its label is the empty string and the full source name still
survives. The converter does not invent a person's name.
QID-looking text and URLs in the two evidence columns remain literals. Missing,
null or empty optional source fields give no extra RDF statement; whitespace
alone remains text. Preservation is of decoded string values, not JSON/CSV
serialization bytes or a distinction between absent, null and empty fields.
The other people columns retain their existing parsing, including the separate
[person-year contract](person_years.md).

## Query and compatibility

For a converted DIAMM graph, original names and optional floruit are available as:

```sparql
PREFIX diamm: <https://linkedmusic.ca/graphs/diamm/>
SELECT ?person ?originalName ?floruit WHERE {
  ?person a diamm:Person; diamm:sourceFullName ?originalName .
  OPTIONAL { ?person diamm:floruit ?floruit }
}
```

For display-name floruit, add `FILTER(CONTAINS(STR(?originalName), "(fl."))`.
That is a text filter for the documented display form, not a complete activity
date parser. Keep the full text and qualifiers in results. Scope the query to
the DIAMM named graph when using a multi-graph store. P569/P570 still use only
the independent year/flag cells described in the year contract.

Older reconciled CSVs without either new column still convert. The converter
does not manufacture original names or floruit from already cleaned names.
Existing labels and source relationships stay in place; names formerly damaged
by pandas' default type inference now retain their text. Existing OpenRefine
projects need the two fields from their matching raw snapshot before exporting
them; an updated template cannot restore missing source cells. Keep an old
project's export selection if those fields have not been added.

Regenerate new CSVs and RDF in separate staging directories after snapshot
access is confirmed. Record checksums and converter version, verify row IDs,
reconciliation decisions, original strings and relationships, and review the
result before replacing stored output. Re-fetching today's display name is not
evidence of what a historical snapshot contained.

## Validation and remaining limits

Four [tests](../tests/test_person_name_preservation.py) exercise the actual
JSON-to-CSV CLI, the tracked export column selection, and the actual RDF CLI
with independently specified full graphs and a floruit-text query. They cover
floruit and lifespan suffixes, ordinary parentheses, Unicode, quotes/newlines,
NA-like strings, leading zeros, missing/null optional fields, legacy exports,
and composition, copyist and ownership relationships. The new tests reported
seven failing assertions/subtests before the repair; all now pass. At the
26 October repair, the common offline check passed **99 tests and 14 competency fixture queries**.
Claude's static review found no introduced correctness defects. Follow-up
controls cover an empty cleaned name and guard against future history operations
that might drop appended columns; these extend the same four tests.

The tests simulate column selection and supplied matches at the OpenRefine
boundary; they do not run its GUI, replay its reconciliation service or verify
historical project settings. All inputs are synthetic. Other source fields,
including person roles and notes, are outside this repair. RISM/VIAF identifier
text was subsequently repaired on 27 October under its
[separate contract](external_identifier_text.md).
No stored data or production graph was regenerated by this work.
