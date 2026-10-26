# Auxiliary CSV identifier validation

Implemented locally on 26 October 2026. This repair covers the six
`matched_wikidata` call sites in
[`convert_to_rdf.py`](../src/convert_to_rdf.py): types, keys, genders, languages,
packaging and statuses. It is separate from the completed
[URL-relationship repair](url_recognition.md) and
[relationship-role representation](representation_review.md).

## Export evidence and input contract

The [reconciliation guide](miscellaneous_reconciliation.md) describes these
auxiliary fields. All 14 tracked [export templates](../openrefine/export/) use
CSV with headers, `entity-id` for the match column and
`blankUnmatchedCells: false`. All 14 corresponding
[histories](../openrefine/history/) first copy the original text with
`grel:value`, without facets, then reconcile the copy. The original lookup
column is retained. Stored exports were not available for verification.

| Export files | Lookup column | Candidate column |
| --- | --- | --- |
| Nine entity-type exports: area, artist, event, instrument, label, place, release-group, series, work | `type` | `type_@id` |
| Keys | `key` | `key_@id` |
| Genders | `gender` | `gender_@id` |
| Languages | `language` (source code) | `full_language_@id` |
| Packagings | `packaging` | `packaging_@id` |
| Statuses | `status` | `status_@id` |

These are bare-ID exports. A match must be a whole string beginning with `Q`
and containing positive ASCII digits with no leading zero, such as `Q42`.
It becomes `http://www.wikidata.org/entity/Q42`. This checks syntax only;
it does not verify item existence or the correctness of the reconciliation.

Suffixes, multiple IDs, whitespace/newlines, Unicode digits, `Q0`, `Q042`,
property IDs, prefixed IDs and full URLs are not matches. No trimming,
substring extraction or URL normalization is applied here. The separately
documented URL-relationship branch continues to accept its item-URL forms.
Missing/non-string candidates, including pandas `NaN` from empty CSV cells,
are rejected without evaluating their truth value or passing them to a regex.

## Preserving unmatched source values

Types, keys, genders, packaging and statuses fall back to the original JSON
field as a literal. Source types now survive when a mapping is absent or blank;
previously the type branch omitted them or failed on a non-string candidate.
Primary and secondary release-group types are handled individually. Status
predicates retain their existing distinction: `Cancelled`, `Withdrawn` and
`Expunged` use P1534; other release statuses use P31.

Languages deliberately have a different fallback. The tracked history copies
the full language name into `full_language_@id`; an unmatched export can thus
contain `Syriac` while its lookup key is `syr`. Nonempty unmatched strings in
that column remain literals exactly as supplied, preserving the existing
full-name behavior. This includes malformed ID-like strings and URLs: rejecting
them as identifiers does not discard that exported text. A missing, empty or
non-string candidate falls back to the original source language code. The
converter does not invent a name from an ID or replace the exported fallback
with a fresh lookup.

At baseline `5f23d0a4`, the regex `^Q\d+` accepted partial, ambiguous,
zero/leading-zero and Unicode-digit IDs. Truthy non-string candidates raised
exceptions; the chunk handler could then retain only the triples emitted
before that error. This repair preserves literal fallbacks and lets later
fields finish conversion. Source subject IRIs, entity relationships and
ordinary names remain intact. No mapping choices or exported CSV files change.

## Validation and remaining limits

Seven [offline tests](../tests/test_auxiliary_identifiers.py) exercise the
production entity converter with the tracked field, attribute and relationship
mappings. Expected RDF triples are specified independently. Coverage includes:

- Accepted IDs and rejected forms at every helper call site, including all
  three end-status values, and an identifier-like ordinary name.
- Absent mappings, blank strings, pandas missing values and other non-string
  candidates, plus partially reconciled primary/secondary types.
- Synthetic CSVs with all 14 tracked export layouts, parsed using the same
  pandas settings as the loaders, with exact triples and Turtle round trips.
- Source artist/release-group links and the existing URL branch in a record
  with invalid and missing auxiliary matches, checking that conversion proceeds.

The regression cases failed against the previous converter and pass after the
repair. The unified command, `poetry run python scripts/check_offline.py`, now
passes **84 tests and 14 competency fixture queries**. Black and diff checks
also pass. The CSV tests exercise parsing and entity conversion; they do not
run the full asynchronous CLI or a historical dump.

Snapshot access, affected-record counts, full-dump conversion and production
regeneration remain deferred. Once access resumes, record the source/export
versions and checksums, count accepted/rejected/missing candidates by field,
verify the language fallback against the original cells, and compare generated
RDF in staging before any reload. The merged lookup dictionary can still have
colliding keys across auxiliary tables; this repair does not redesign it or
establish whether collisions occur in stored data. SESEMMI, inference settings
and live graphs are outside this change.
