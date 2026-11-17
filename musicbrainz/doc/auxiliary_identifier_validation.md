# Auxiliary CSV identifier validation

The six auxiliary lookup routes in
[`convert_to_rdf.py`](../src/convert_to_rdf.py) cover types, keys, genders,
languages, packaging and statuses. Their bare-ID contract is distinct from
[URL relationships](url_recognition.md) and the
[role representation](representation_review.md).

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
Missing/non-string candidates, including pandas `NaN` supplied by older loaders,
are rejected without evaluating their truth value or passing them to a regex.

## CSV text and field-specific lookups

Two boundaries prevent text loss and cross-field matches:

- Default pandas NA detection would erase textual keys such as `nan` and `None`,
  and unmatched candidate text such as `NA`. A supplied language match under
  `nan` would otherwise disappear. The tracked packaging history explicitly
  contains `None`; it is source text, not a missing cell.
- A shared dictionary for auxiliary fields and entity types would let a label
  such as `Other` acquire a different field's match. The tracked artist-type and packaging histories
  both contain `Other`, and the reconciliation guide describes the gender
  `other` match. Packaging could overwrite the gender entry; without packaging,
  the gender entry could overwrite a type. Historical exports are still needed
  to measure which collisions actually occurred.

Every auxiliary and type CSV now uses `load_reconciliation_csv`, with
`dtype=str` and `keep_default_na=False`. This retains textual values such as
`nan`, `None`, `NA`, `null` and `001` without missing-value or numeric inference.
Empty candidate cells remain empty strings and use the documented source
fallback. Rows with an empty lookup key are ignored. Whitespace is preserved;
whitespace-only language text remains a literal, as before. This deliberately
does not introduce source-text cleanup.

`load_auxiliary_reconciliations` builds separate `key`, `gender`, `language`,
`packaging` and `status` dictionaries. Type lookups are scoped under `type` and
then the entity kind, so an artist type cannot acquire a work-type match or
pass its type map to a recursively converted entity of another kind. A missing
file or entry uses the source fallback for that field, never another field's
candidate. Each entity conversion reads only its own lookup table.

The command-line arguments and CSV filenames/columns are unchanged. Internal
Python callers of `process_entity`/`process_chunk` must now supply field-scoped
mappings, for example `{"gender": {"Other": "Q42"}}` or
`{"type": {"artist": {"Other": "Q43"}}}` (synthetic IDs). Empty `{}` still
means no auxiliary matches. This is a lookup change, not a new RDF predicate or
identity rule; existing source nodes, language fallbacks and status predicates
remain as documented below.

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

Complete-ID checking prevents malformed candidates from becoming IRIs, while
literal fallbacks let later fields finish conversion. Source subject IRIs,
entity relationships and ordinary names remain intact. Validation does not
change mapping choices or exported CSV files.

## Validation and remaining limits

Seven [offline tests](../tests/test_auxiliary_identifiers.py) exercise the
production entity converter with the tracked field, attribute and relationship
mappings. Expected RDF triples are specified independently. Coverage includes:

- Accepted IDs and rejected forms at every helper call site, including all
  three end-status values, and an identifier-like ordinary name.
- Absent mappings, blank strings, pandas missing values and other non-string
  candidates, plus partially reconciled primary/secondary types.
- Synthetic CSVs with all 14 tracked export layouts, parsed by the production
  CSV loader, with exact triples and Turtle round trips, including packaging
  `None` as an actual CSV lookup key.
- Source artist/release-group links and the existing URL branch in a record
  with invalid and missing auxiliary matches, checking that conversion proceeds.

The [loader regressions](../tests/test_reconciliation_loading.py) cover text,
empty cells, same-label collisions across fields/entity kinds, and missing
files. They exercise production loaders, per-file conversion and the actual
asynchronous CLI with temporary CSV/JSONL inputs and Turtle outputs. Expected
triples include source links and an embedded recording. Run all controls with:

```sh
poetry run python -m unittest discover -s musicbrainz/tests -v
poetry run python scripts/check_offline.py
```

Affected-record counts and historical fidelity require matching source/export
snapshots. Before a candidate regeneration, record the source/export
versions and checksums, count accepted/rejected/missing candidates by field,
verify the language fallback against the original cells, and compare generated
RDF in staging before any reload. Duplicate keys within a single CSV still use
the last row, as before; this repair isolates fields without redesigning
within-table conflict resolution. SESEMMI, inference settings and live graphs
are outside this change. Queries consuming regenerated data must still allow
literal fallbacks, including the previously documented P31 fallback for types.
