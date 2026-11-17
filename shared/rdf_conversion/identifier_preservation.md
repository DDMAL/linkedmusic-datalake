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
   Existing date handling remains; language and datatype cannot be combined.
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

## Source and mapping contracts

[DTL export instructions](../../dtl/doc/reconciliation_procedures.md#export-procedures)
provide matched entity IDs. [The Session history](../../thesession/openrefine/history/events_history.json)
constructs complete Wikidata page URLs. Checked-in Global Jukebox, Cantus,
Cantus Index and UTSI export templates distinguish entity IDs from entity names;
they support complete IDs/URLs, not ID extraction from display prose. Inspect
the selected export and actual cells before regeneration: tracked instructions
do not establish the contents of historical CSVs.

All nine tracked TOML configurations are exercised by the offline suite. Local
prefixes protect source keys; explicit datatypes protect text and date values.
The [Global Jukebox contract](../../theglobaljukebox/doc/alternative_names_mapping.md)
uses string alternative labels for all 19 social-factors name columns. The
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
