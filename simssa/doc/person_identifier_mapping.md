# Person exact-match links in the shared TOML route

The [SIMSSA configuration](../../shared/rdf_config/simssadb.toml) emits P2888
from `person_name` only when the converted value is a canonical Wikidata item
IRI with positive ASCII digits and no leading zero. `person_name_original`
emits an explicit string label. Local person IDs and work author/composer links
retain their SIMSSA namespaces.

## Export contract

The [merge script](../src/merge.py) constructs names from given name and surname.
The [person history](../openrefine/history/history_person.json) reconciles names
against Wikidata humans, using VIAF as supporting evidence, then copies the
cell value into `person_name_original` without a facet restriction. This supports
separate match and original-text columns; it does not prove historical execution.

No SIMSSA export template is checked in. For this route, export accepted matches
in `person_name` as complete item IDs or URLs, retain unmatched text, and export
`person_name_original` as the original cell value for every named record. Do not
replace original text with a matched entity's label or URL.

The [shared parser](../../shared/rdf_conversion/identifier_preservation.md)
normalizes complete bare/prefixed QIDs and recognized HTTP(S) item URLs. The
person-specific guard then requires the precise canonical item-IRI shape.
Malformed item URLs, unrelated URLs, property entities and unmatched text do
not create person exact-match links. The original label can still survive.

| Input | Output |
| --- | --- |
| Match `Q42`, original `Example person` | Local person P2888 `wd:Q42` and original string label |
| Empty, ambiguous or malformed match; original present | Original label without P2888 |
| Original name `Q42` or a complete URL | Original string label, not an inferred match |
| Local person ID `Q42` | SIMSSA person IRI; local work links keep that endpoint |

A complete QID in the match column is treated as an exported match, not verified
identity. CSV alone does not prove its OpenRefine judgment. The converter does
not select a candidate from a list, infer a match from the original name, check
QID existence or add identity inference.

## Checks and limits

[Offline tests](../../shared/tests/test_simssa_mapping.py) use actual person/work
mappings and temporary CSVs. Exact expected graphs and Turtle round trips cover
all accepted item forms, rejected URLs/IDs, Unicode/whitespace, blank cells,
ID-like names and local author/composer links. Run from the repository root:

```sh
poetry run python scripts/check_offline.py
```

Blank original-name cells produce no label; this route cannot reconstruct lost
text. Audit missing originals and export shapes before regeneration. The shared
loader's existing missing-value and fill-down conventions remain limits. Work
title guards, other mappings and the separate JSON-LD route retain their own
contracts. Tests do not establish which route produced a historical graph or
validate the preceding merge/export steps. Regenerate separately from originals
and inspect source-backed changes before any replacement.
