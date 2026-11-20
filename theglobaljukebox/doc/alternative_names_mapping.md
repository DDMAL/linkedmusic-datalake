# Society alternative names

Six [Global Jukebox societies tables](../../shared/rdf_config/theglobaljukebox.toml)
map the exported alternative-name columns to `skos:altLabel` with datatype
`xsd:string`. All use the same local society IRI,
`https://theglobaljukebox.org/culture/{society_id}`. An identical name from
two tables therefore produces one triple in the converter's RDFLib graph.
A name such as `Q42` or a URL stays text.

| Societies export | Alternative-name columns emitted |
| --- | --- |
| Cantometrics, ensembles, instrument, social factors | 1–19 |
| Minutage | 1–12 |
| Phonotactics | 1–10 |
| Parlametrics | None. Its mapping omits the alternative-name columns. |

## Preparing the CSV

Trim the outside of the raw `alternative_names` cell in OpenRefine, then split
it using the regular expression `\s*;\s*` with cell-type guessing disabled.
This removes padding around the semicolon in `First name; Second name`,
preserves spaces within each name, and keeps values such as `0007` as text.
The shared converter preserves whitespace in the CSV it receives. An older
export containing `" Laptan"` needs a fresh export or a verified correction
before conversion. See the [reconciliation instructions](reconcile_procedures.md#societies-1)
and the [societies history](../openrefine/history/societies_history.json).

The [export template](../openrefine/export/societies_export.json) includes up
to 19 split columns. Check that each exported cell contains the source name.
Reconciliation or cell-type guessing earlier in the workflow can change it.
The shared loader also recognizes missing-value tokens such as `NA` and `?`.
Keep the raw file for comparison.

## Meaning and validation

The history uses Wikidata P4970 as a hint when reconciling a society. The RDF
mapping describes a lexical alternative for that local society. SKOS permits
labels on resources of any type. Repeated occurrences and source column order
are lost in an RDF graph. [SKOS lexical labels](https://www.w3.org/TR/skos-reference/#labels)
· [Wikidata P4970](https://www.wikidata.org/wiki/Property:P4970)

The [offline tests](../../shared/tests/test_identifier_conversion.py) load all
nine TOMLs and resolve their predicates. Conversion tests cover Global Jukebox
societies, DTL performers and SIMSSA people and works. The societies fixtures
check shared labels, distinct names, the Parlametrics omission and exact RDF
terms after Turtle serialization. Run `poetry run python scripts/check_offline.py`
from the repository root.

Before regenerating the Global Jukebox graph, reconcile SESEMMI’s
[graph schema](https://github.com/DDMAL/SESEMMI/blob/874e77089df425fb56b5eea1f1a6778245143b24/llm-service/app/graph/schema_corpus.py#L447)
with the candidate: the schema entry for `gj:Culture` advertises `wdt:P4970`,
while the converter emits `skos:altLabel`. Before rollout, test an exact
alternative-name query against the candidate and coordinate the schema switch
with deployment. Record source/export revisions and checksums for the comparison.
