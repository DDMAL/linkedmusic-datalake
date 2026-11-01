# Person years and approximation

Implemented 26 October 2026. This repairs the separate people year branches in
`convert_rdf.py`: they previously concatenated any non-null `*_year_@id` value
onto the Wikidata namespace and discarded the original year and approximation
flag. The repair covers reconciled CSV → RDF, not all DIAMM extraction.

## Meaning and evidence

The upstream DIAMM website's
[Person model](https://github.com/diamm/diamm/blob/052004f86960a5dc4d1e7446be8d5a6ac8594bd1/diamm/models/data/person.py)
defines nullable integer earliest/latest years, separate Boolean approximation
flags, and a separate `floruit` field. Its field guidance reserves floruit for
people without known birth/death dates; its display method renders earliest
and latest as a lifespan, with `ca.` for the respective approximate endpoints.
The [2023 floruit migration](https://github.com/diamm/diamm/blob/052004f86960a5dc4d1e7446be8d5a6ac8594bd1/diamm/diamm_data/migrations/0013_person_floruit.py)
contains the same guidance. The
[person serializer](https://github.com/diamm/diamm/blob/052004f86960a5dc4d1e7446be8d5a6ac8594bd1/diamm/serializers/website/person.py)
also separates the person fields from dates on roles.

We infer from this documented source model that person `earliest_year` and
`latest_year` are birth/death years, distinct from activity dates. We retain
[P569](https://www.wikidata.org/wiki/Property:P569) and
[P570](https://www.wikidata.org/wiki/Property:P570) for that interpretation.
This is code/model evidence pinned to an upstream revision, not verification
of each historical record or the version that supplied a stored snapshot.

Locally, [`to_csv.py`](../src/to_csv.py) copies both year values and both flags
from the person JSON. The [people history](../openrefine/history/people_history.json)
copies each year into its `*_@id` column without facets, then reconciles it
against year items (Q577). The [export](../openrefine/export/people_export.json)
retains all six cells; unmatched ID-column text is not blanked. This means an
unmatched year can reappear in its ID column. It is not an entity identifier.

## Conversion contract

The six year-related CSV columns use string converters. Their parsed cell
text survives pandas, including empty cells, `NA`, `nan`, leading zeros, flag
case and decimal spelling. The later [person-name repair](person_name_preservation.md)
also protects `full_name`, `source_full_name` and `floruit` as text. Other columns
retain their existing loading behavior.
Preservation here means decoded CSV cell values, not CSV quoting or JSON bytes.

- A year accepts one to four ASCII digits, optionally followed by a decimal
  point and only zeros, with integer value 1–9999. Integral decimal forms such
  as `1500.0` accommodate pandas CSV output from nullable integer fields.
  Typed values have four digits and use
  [`xsd:gYear`](https://www.w3.org/TR/xmlschema11-2/#gYear), e.g. `0012` or `1500`.
  No month, day, timezone or uncertainty interval is invented.
- Unsupported years (including zero, negative values, ranges, fractional years,
  whitespace and prose) remain original strings with `invalid-year`; an empty
  year gets `missing-year`. These flags describe this conversion contract,
  not a judgment that the historical source is wrong.
- Flags accept case-insensitive `true`/`false`, and `1`/`0`, without trimming.
  Blank and unrecognized flags remain unknown, with `missing-approximation`
  or `invalid-approximation`. Missing never defaults to false.
- Year IDs use the [complete bare-QID contract](identifier_validation.md):
  `Q[1-9][0-9]*`. Invalid nonempty candidates get `invalid-year-identifier` and
  remain literal evidence. Empty candidates are allowed. Syntax validation
  does not verify existence, year class, or agreement with the source year.
  An ID never supplies or overrides the source year.
- A direct person P569/P570 triple is emitted only for a supported source year
  whose flag explicitly means **false**. Its object is an `xsd:gYear` literal.
  Approximate or unknown-precision values remain on observations, even when
  their year and reconciled ID parse successfully. A rejected ID does not
  invalidate an independently supported, non-approximate source year.

## Evidence representation

`diamm:` is `https://linkedmusic.ca/graphs/diamm/`. Each nonempty group of year,
ID and flag creates a `diamm:PersonYearObservation`, attached to its source
person by `diamm:personYear`. All three empty means no observation. A flag or
ID without a year still creates an observation, but no date.
Consequently, explicit false flags on people without years still produce
observations. Their population and RDF expansion require snapshot measurement.

| Observation property | Value |
| --- | --- |
| `dcterms:source` | DIAMM person URL |
| `diamm:sourceField` | `earliest_year` or `latest_year`, as `xsd:string` |
| `diamm:dateProperty` | P569 or P570, describing the field's interpretation |
| `diamm:sourceValue` | Original year cell, including empty text, as `xsd:string` |
| `diamm:sourceIdentifier` | Original ID cell, including empty text, as `xsd:string` |
| `diamm:sourceApproximate` | Original flag cell, including empty text, as `xsd:string` |
| `diamm:year` | Supported source year as `xsd:gYear`, when available |
| `diamm:approximate` | Parsed Boolean, when available |
| `diamm:reconciledYear` | Canonical Wikidata IRI for a complete bare QID, when available |
| `diamm:validationFlag` | Zero or more validation status strings listed above |

Raw-cell literals have explicit `xsd:string` datatypes; validation flags are
plain literals. For datatype-sensitive clients such as RDFLib, match raw cells
with a typed term (e.g. `"True"^^xsd:string`) or compare `STR(?rawFlag)`.

Observation IRIs are `diamm:person-year/` followed by the full SHA-256 of a UTF-8
JSON array containing the person IRI, field name and three raw cells. The array
uses `ensure_ascii=False` and separators `(',', ':')`. Exact duplicates collapse;
different cells, fields or people remain separate. Row order has no effect.
These are evidence identities, not row numbers, source occurrence counts or
snapshot provenance. Conflicting records retain separate observations; no
chronology repair or preferred birth/death value is inferred.

For example, year `1500`, candidate `Q42 / Q43` and flag `True` retain all three
strings, a typed observation year, `diamm:approximate true` and the invalid-ID
flag. They produce neither a reconciled-year IRI nor a direct P569 triple.

## Query compatibility and regeneration

This deliberately changes P569/P570 objects from year-item IRIs to year
literals and excludes approximate/unknown-precision values from direct dates.
Existing queries that traverse year-item entities must change. To include
approximate births while keeping the uncertainty visible:

```sparql
PREFIX diamm: <https://linkedmusic.ca/graphs/diamm/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
SELECT ?person ?year ?raw ?candidate ?approximate WHERE {
  ?person a diamm:Person; diamm:personYear ?observation .
  ?observation diamm:dateProperty wdt:P569;
               diamm:sourceValue ?raw;
               diamm:sourceIdentifier ?candidate .
  OPTIONAL { ?observation diamm:year ?year }
  OPTIONAL { ?observation diamm:approximate ?approximate }
}
```

This example targets one converted DIAMM graph. Add the deployment's explicit
`GRAPH` scope in a multi-graph store. Unknown flags leave `?approximate` unbound;
do not coalesce them to false. Direct `?person wdt:P569 ?year` selects only
source years explicitly marked non-approximate. A year item join, if needed,
goes through the same observation's `diamm:reconciledYear` and retains its flag.
These `xsd:gYear` values also differ from Wikidata's `xsd:dateTime` values.
Cross-graph date comparisons need explicit year extraction; do not assume
`YEAR()` or direct comparisons support both datatypes in a given query engine.
For this contract's supported years, `xsd:integer(STR(?year))` supplies a numeric
year for comparisons, while the observation retains uncertainty.

Regenerate from matching reconciled CSVs into a separate output directory;
record source checksums and converter version first. Audit actual year/flag/ID
forms, counts of supported and rejected values, source relationships and both
query paths before replacement. Old Turtle lacks the discarded raw year/flag
cells and cannot reconstruct them reliably. This change does not migrate or
replace stored graphs, and historical affected counts remain unknown.

## Validation and limits

Seven [regression tests](../tests/test_person_years.py) use the real converter,
tracked CSV layouts and independently specified triples. They cover both year
fields, valid and malformed IDs, original text and NA-like strings, Boolean
forms, blank/unknown flags, unsupported years, integral decimal spelling,
duplicate/conflicting rows, stable observation IDs, labels/relationships,
Turtle round trips, the real CLI and direct/approximate SPARQL query results.
Before the change they reported 65 failing assertions/subtests; all now pass.
The follow-up review added near-miss year cases and a short-year Turtle check
within the existing tests; the 65 failures describe the original regression run.
The existing five DIAMM tests also passed. At this repair, the unified offline
check passed
**95 tests and 14 competency fixture queries**; the two date-query assertions
are additional regression controls, not new competency questions.

Historical exports and API snapshots were not inspected. A source year/ID
disagreement is retained, not resolved. The later person-name repair preserves
the original display name (including floruit) and optional separate floruit
text across JSON → CSV → RDF. It added four tests for a baseline of **99 tests
and 14 competency fixture queries** on 26 October. Subsequent repairs are
listed in the [current status](../../README.md#preservation-and-evaluation-status).
Neither change can recover source
text already lost from historical exports or establish complete DIAMM fidelity.
