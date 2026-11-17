# Social-factors alternative names

The [social-factors mapping](../../shared/rdf_config/theglobaljukebox.toml)
maps all `alternative_names 1` through `alternative_names 19` to `skos:altLabel`
with `datatype="xsd:string"`. Subjects remain local society IRIs in
`https://theglobaljukebox.org/culture/`. ID-like names and URLs stay text; no
language, entity match or separate society is inferred.

## Mapping evidence

[Reconciliation procedures](reconcile_procedures.md#social-factors) split names
on semicolons and use them to support society reconciliation. The
[society history](../openrefine/history/societies_history.json) uses P4970 as a
reconciliation hint, which does not require emitting that direct RDF property.
The [export template](../openrefine/export/societies_export.json) includes all
19 columns with entity-name output, retained unmatched cells and page-link
settings. Unreconciled cells remain text under this contract; manually reconciled
cells could export differently. Historical CSV contents are not established by
the template. Earlier cell-type guessing can also alter text before CSV loading.

[SKOS lexical labels](https://www.w3.org/TR/skos-reference/#labels) may label
resources of any type, so a local Culture does not need to become a SKOS concept.
[Wikidata P4970](https://www.wikidata.org/wiki/Property:P4970) has a string datatype
and qualifier/reference scope. [RDF 1.1 literals](https://www.w3.org/TR/rdf11-concepts/#section-Graph-Literal)
represent untagged strings with `xsd:string`. The selected mapping preserves
lexical alternatives without asserting identity or inventing a language tag.

For example, society `culture/Q42` can have labels `"Q42"^^xsd:string` and
`"Study Q42 (draft)"^^xsd:string`, without a link to Wikidata Q42. Distinct names
survive, but RDF set semantics do not preserve duplicate occurrences or column
order. Each alternative-name key is declared once in TOML.

## Validation and limits

The [synthetic regression](../../shared/tests/test_identifier_conversion.py)
uses the actual social-factors table and graph builder. It checks all 19 columns,
multiple names, blank/sparse societies, Unicode, punctuation, whitespace,
bare IDs and URLs against an independently specified graph and Turtle round trip.
All nine tracked TOML configurations participate in the compatibility check.
Run from the repository root:

```sh
poetry run python scripts/check_offline.py
```

The shared loader's missing-value tokens and record fill-down still apply.
Other tables' untyped labels retain their own contracts. These tests do not
establish historical affected counts, export fidelity or deployed behavior.
Obtain matching source/export snapshots, retain their hashes and generate a
separate candidate before replacing stored RDF. Lost names cannot be recovered
from old entity links without the original source value.
