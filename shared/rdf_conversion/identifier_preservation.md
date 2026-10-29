# Identifier preservation in the shared CSV converter

Implemented 21 October 2026, following the
[identifier review](../../evaluation/identifier_review.md). The previous
converter searched every cell and predicate for a Wikidata ID, selecting the
last match. This could turn prose or another site's identifier into a Wikidata
entity, including when the configuration explicitly requested a literal.

The repair is confined to `rdfconv/convert.py`. The permissive
`wikidata_utils.extract_wd_id` search helper and its interactive/labeling callers
retain their existing behavior. That parser repair left dataset mappings and source exports unchanged. The later
Global Jukebox mapping repair is recorded below.

## Input contract and precedence

This contract applies after CSV loading. The existing loader still treats its
configured missing-value tokens (including `NA`, `N/A`, `None`, `null`, `nan`,
`-` and `?`, with listed case variants) as missing, then fills down within
OpenRefine records. Explicit `xsd:string` does not recover a cell lost at that
stage. The identifier repair did not change those rules or establish lossless
preservation of every CSV text value.

For nonempty string cells:

1. A configured `datatype` or `lang` selects literal handling, even for a whole
   QID or URL. Existing date conversion handling remains in place.
2. A configured `prefix` expands a non-HTTP(S) value as a local identifier. Thus
   `Q42` with `prefix="dtlt"` identifies a DTL track, not a Wikidata item.
3. Otherwise, only a **complete** structured Wikidata identifier is normalized.
   Items accept bare `Q42`, `wd:Q42`, and HTTP/HTTPS URLs on `wikidata.org` or
   `www.wikidata.org` with `/wiki/Q42` or `/entity/Q42`. Property entities accept
   bare `P175`, `wd:P175`, `wdt:P175`, and the corresponding `/entity/P175`,
   `/wiki/Property:P175` or `/prop/direct/P175` URLs. Object IDs use the configured
   `wd` namespace; predicate IDs use `wdt`. Existing configs declare the canonical
   HTTP namespaces.
4. Other HTTP(S) URLs remain their own IRIs, retaining existing escaping of
   invalid URI characters. All remaining values become literals.

IDs require positive ASCII digits without leading zeroes. No whitespace is
trimmed, and URL fragments, queries, suffixes or unrelated hosts do not qualify
for Wikidata normalization. A value such as `Q42 / Q43` remains one literal:
conversion neither chooses a candidate nor invents separate matches. Split
intentional multiple values during export using the established row structure.

| Input and configuration | Result |
| --- | --- |
| `Q42`, no explicit type/prefix | `wd:Q42` |
| `https://www.wikidata.org/wiki/Q42` | `wd:Q42` |
| `https://example.org/Q42` | Original external IRI |
| `Study Q42 (draft)` or `Douglas Adams (Q42)` | Original literal text |
| `Q42 / Q43` | Original literal text |
| `Q42`, `datatype="xsd:string"` | `"Q42"^^xsd:string` |
| Wikidata URL, `datatype="xsd:anyURI"` | Typed literal containing the original URL |
| `Q42`, configured local prefix | Local namespace plus `Q42` |
| Predicate `https://example.org/P175` | Original external predicate IRI |
| Predicate `performer P175` | Configuration error; no extracted PID |

A bare QID in an untyped label column remains inherently ambiguous. Configure
`datatype="xsd:string"` or `lang` when a column is literal text. This change does
not infer a column's meaning from its predicate or claim that a syntactically
valid ID establishes a correct reconciliation.

## Tracked export contracts reviewed

The pre-change baseline is `93642c26`. These tracked artifacts support whole-ID
and URL inputs; they do not justify searching arbitrary text for an ID:

- [DTL export instructions](../../dtl/doc/reconciliation_procedures.md#export-procedures)
  specify matched entity IDs; the performer workflow copies IDs into the mapped
  column and retains original names separately.
- [The Session event history](../../thesession/openrefine/history/events_history.json)
  explicitly builds `https://www.wikidata.org/wiki/` URLs from `cell.recon.match.id`.
- [Global Jukebox song export](../../theglobaljukebox/openrefine/export/songs_export.json),
  the other nine tracked Global Jukebox export templates,
  [Cantus](../../cantus/openrefine/export/export_template.json),
  [Cantus Index](../../cantusindex/openrefine/export/export.json) and
  [UTSI](../../utsi/openrefine/export/utdb_songs_export.json) distinguish
  `entity-id` from `entity-name`, with `linkToEntityPages=true` and retained
  unmatched cells. Accepting both complete IDs and complete Wikidata URLs
  accommodates those settings without guessing IDs from entity names.
- Existing shared mappings use local prefixes for source keys and explicit
  datatypes for date/coordinate values. All nine configurations have no mapping that combines
  `prefix` with `datatype`/`lang`.

This is an inspection of checked-in contracts, not a fresh OpenRefine export
or verification of historical CSV contents. Label-plus-ID display strings are
not an accepted export contract; they now remain literals.

## Validation and limits

Eleven [offline tests](../tests/test_identifier_conversion.py) exercise identifiers,
negative controls, explicit literals, local keys, predicates, and dates. A
five-row synthetic CSV runs through the **existing DTL performer mapping** and
the real graph builder; exact triples and a Turtle serialization round trip
are checked. All nine tracked shared TOML configurations now validate.
The tests run in the common offline command and CI:

```bash
poetry run python scripts/check_offline.py
```

The subsequent [Global Jukebox mapping repair](../../theglobaljukebox/doc/alternative_names_mapping.md)
resolves the duplicate social-factors alternative-name declarations. All 19
columns now use `skos:altLabel` with explicit `xsd:string` handling. Its synthetic
CSV test covers all 19 columns, blank and sparse records, ID-like names and a
Turtle round trip through the actual mapping. The configuration compatibility
test no longer excludes Global Jukebox. At that repair on 21 October, the
complete offline command passed 65 tests and 14 competency fixture queries.
See the [current validation baseline](../../README.md#preservation-and-evaluation-status)
for subsequent additions.

Before replacing stored RDF, obtain the corresponding snapshots, record input
checksums and conversion revisions, regenerate into a separate directory, and
compare changed terms with their source cells. Review identifiers that become
literals and mappings whose `if` guards consequently exclude them. Confirm local
subjects, canonical joins and literal labels before staging/replacement. Do not
try to repair an old collapsed QID without the original source value.
Historical impact and production migration remain deferred. Separate repairs
now cover [MusicBrainz URLs](../../musicbrainz/doc/url_recognition.md),
[MusicBrainz auxiliary CSVs](../../musicbrainz/doc/auxiliary_identifier_validation.md),
[DIAMM identifiers](../../diamm/doc/identifier_validation.md) and
[SIMSSA person matches](../../simssa/doc/person_identifier_mapping.md).
