# Identifier preservation in the shared CSV converter

The shared converter recognizes complete identifiers after honoring explicit
literal declarations and local prefixes. It does not search prose or unrelated
URLs for Wikidata IDs. The interactive `wikidata_utils.extract_wd_id` helper
retains its separate permissive search behavior.

## Input contract and precedence

This contract applies after CSV loading. The existing missing-value tokens
(including `NA`, `N/A`, `None`, `null`, `nan`, `-` and `?`, with configured case
variants) and record fill-down still apply. An explicit string datatype cannot
recover a value lost during loading. This is not a lossless CSV reader.

For a nonempty string:

1. `datatype` or `lang` selects a literal, including for an entire QID or URL.
   A literal declaration also takes precedence over a configured prefix.
   Use one of datatype or language per column. Temporal mappings preserve the
   [precision of the supplied value](#date-precision).
2. A configured `prefix` expands a non-HTTP(S) value into a local identifier.
   For example, `Q42` with the DTL track prefix denotes a local track.
3. Otherwise, a complete structured Wikidata identifier is normalized. Items
   accept `Q42`, `wd:Q42`, and HTTP(S) URLs on `wikidata.org` or
   `www.wikidata.org` with `wiki/Q42` or `entity/Q42`. Property entities accept
   `P175`, `wd:P175`, `wdt:P175`, and URLs with `entity/P175`,
   `wiki/Property:P175` or `prop/direct/P175`. Objects use the configured `wd`
   namespace; predicates use `wdt` for complete recognized property IDs.
4. Other HTTP(S) URLs remain external IRIs, with the existing escaping behavior
   for invalid URI characters. Remaining values become literals.

IDs require positive ASCII digits without leading zeroes. No whitespace is
trimmed. Suffixes, query strings, fragments and unrelated hosts do not qualify.
`Q42 / Q43` remains one literal, not a selected match or two invented values.
Predicates accept full external URLs and configured prefixed names; unresolved
text such as `performer P175` raises a configuration error.

| Input and configuration | Result |
| --- | --- |
| `Q42` without an explicit literal/local declaration | `wd:Q42` |
| `https://www.wikidata.org/wiki/Q42` | `wd:Q42` |
| `https://example.org/Q42` | Original external IRI |
| `Study Q42 (draft)` or `Q42 / Q43` | Original literal |
| `Q42` with `datatype="xsd:string"` | Original typed string |
| A URL with `datatype="xsd:anyURI"` | Original URL as a typed literal |
| `Q42` with a local prefix | Local namespace plus `Q42` |

An untyped label consisting only of `Q42` is ambiguous. Configure a datatype or
language for text columns. A syntactically valid ID does not establish a correct
reconciliation, and this converter does not infer a column's meaning.

## Date precision

The `datatype` setting describes the expected precision of the column. The
shared converter uses the same subject and predicate for a typed value and for
source text. For chronological queries, filter by the temporal datatypes your
query can use. For display, include the text. These rules apply to loaded cells.

| Source cell | Column declaration | Turtle object |
| --- | --- | --- |
| `1850` | `xsd:gYear`, `xsd:date` or `xsd:dateTime` | `"1850"^^xsd:gYear` |
| `1850-01-01` | `xsd:date` or `xsd:dateTime` | `"1850-01-01"^^xsd:date` |
| `2000-02-29-03:30` | `xsd:date` | `"2000-02-29-03:30"^^xsd:date` |
| `2000-02-29 12:34:56.123456789+05:30` | `xsd:dateTime` | `"2000-02-29T12:34:56.123456789+05:30"^^xsd:dateTime` |
| `c. 1850`, `1850-06`, `1900-02-29` or `abc` | Any of the three | Plain literal with the complete cell text |
| Blank on a new record | Any of the three | No date triple |

The date and timestamp profiles accept calendar years 0001 through 9999.
An explicit `xsd:gYear` column also accepts signed and extended XML Schema
years. An eight-digit cell in a date column stays text because it could be a
compact date. A calendar date requires a real month and day. Timestamps also require hours, minutes and
seconds, separated from the date by `T` or one space. The output keeps
fractional seconds and any supplied `Z` or numeric offset (up to ±14:00).
End-of-day `24:00:00` denotes midnight on the following day when that day is
in range. Other spellings and values more precise than the declared column
remain plain text. The CSV reader's missing tokens and within-record fill-down
apply as described above.

These direct mappings retain qualifiers in text such as `c. 1850`. A mapping
that also extracts a searchable year from that wording needs a source-specific
interpretation and a date observation to carry the qualifier.
[Shared approximation contract](../ontology/date_approximation.md)

### Checking inputs before regeneration

| Profile | Source fields and preparation to check |
| --- | --- |
| [Weimar](../../wjazzd/doc/reconciliation_procedures.md#track_infocsv) | Track `recordingdate` (P10135) accepts full dates or years. Record `releasedate` (P577) expects a year. Earlier track histories padded partial dates and collapsed multi-day text. Compare January 1 and first-of-month dates with the original track cells. |
| [SIMSSA](../../simssa/src/merge.py) | Person `birth_year` (P569) and `death_year` (P570) expect years. The merge reads year-only ranges. For example, `[1850, 1851)` and `[1850, 1850]` each specify one year. Wider or open-ended ranges and uncertain text keep their wording. Earlier merges extracted a lower bound and padded it to January 1. Recover the original ranges before using those exports. |
| [DTL](../../dtl/doc/digthatlick_data_schema.md) | Track `session_date` (P10135) is documented as a calendar date. Compare partial or malformed cells with the recording date in the source. |
| [Global Jukebox](../rdf_config/theglobaljukebox.toml) | Cantometrics song `Year` (P585), instrument source `Year` (P577) and Parlametrics conversation `Date` (P585) use the date mapping. Check the exported display values and cell types against the source. |
| [The Session](../../thesession/doc/thesession_data_schema.md) | Event `dtstart` (P580), `dtend` (P582) and set `date` (P571) use timestamp mappings. Earlier event histories replaced the eleventh character unconditionally. Compare partial or malformed exports with their original cells. |

Compare each affected subject and predicate across the original source,
reconciled CSV and candidate Turtle. Count complete, reduced-precision,
uncertain, invalid and missing cells separately. An exported January 1 alone
cannot identify padding. Keep genuine January 1 dates. Resolve ambiguous
legacy values against source records before replacing a graph.

## Source and mapping contracts

[DTL export instructions](../../dtl/doc/reconciliation_procedures.md#export-procedures)
provide matched entity IDs. [The Session history](../../thesession/openrefine/history/events_history.json)
constructs complete Wikidata page URLs. Checked-in Global Jukebox, Cantus,
Cantus Index and UTSI export templates distinguish entity IDs from entity names;
they support complete IDs/URLs, not ID extraction from display prose. Inspect
the selected export and actual cells before regeneration: tracked instructions
do not establish the contents of historical CSVs.

The offline suite loads all nine tracked TOMLs and resolves their predicates.
CSV-to-Turtle tests cover DTL performers, SIMSSA people and works, and the
Global Jukebox societies tables.
The [Global Jukebox contract](../../theglobaljukebox/doc/alternative_names_mapping.md)
uses string alternative labels across the six societies tables that emit names. The
[SIMSSA person contract](../../simssa/doc/person_identifier_mapping.md) preserves
original labels and requires canonical item targets for person exact matches.
These source-specific restrictions do not apply indiscriminately to P2888 in
other datasets, where non-Wikidata targets can be valid.

## Validation and regeneration

The [identifier tests](../tests/test_identifier_conversion.py) and
[SIMSSA tests](../tests/test_simssa_mapping.py) exercise actual tracked mappings,
expected triple sets, negative forms, local IDs and Turtle round trips. DTL's
performer mapping receives a five-row synthetic CSV. Global Jukebox checks every
name column plus blank/sparse records, ID-like text, Unicode and punctuation.
Run from the repository root:

```sh
poetry run python scripts/check_offline.py
```

Before replacing stored RDF, identify corresponding source/export snapshots,
record checksums and converter/configuration revisions, generate separate output
and compare changed terms against source cells. Inspect newly literal values and
mapping guards that omit them. Preserve source subjects and complete target sets.
Do not reconstruct original text from an old collapsed QID. Synthetic tests do
not measure historical incidence, source-export fidelity or production accuracy.
