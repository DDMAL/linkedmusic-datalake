# Social-factors alternative names

Repaired 21 October 2026. The social-factors society table maps all
`alternative_names 1`–`19` to `skos:altLabel` with `datatype = "xsd:string"`.
The direction is local society (`https://theglobaljukebox.org/culture/{society_id}`)
to alternative-name text. No name becomes a reconciled entity, even if its
entire text is `Q42` or a URL. No language is inferred. This is a bounded
configuration repair; the converter and other tables are unchanged.

## Evidence and decision

- [Reconciliation procedures](reconcile_procedures.md#social-factors) reuse the
  Cantometrics society procedure: split alternative names on semicolons and use
  them as evidence when reconciling the **society** column. They do not instruct
  reconciliation of the names themselves.
- [Societies history](../openrefine/history/societies_history.json) splits the
  column and uses names 1 and 2 as P4970 reconciliation inputs. The tracked
  Cantometrics and minutage histories also split names. None of these operations
  establishes that name cells contain entity IDs. P4970 as a reconciliation
  hint is not a requirement to emit direct P4970 RDF assertions.
- [Societies export](../openrefine/export/societies_export.json) includes all
  19 columns with `output="entity-name"`, `blankUnmatchedCells=false` and
  `linkToEntityPages=true`. For the unreconciled name columns, this retains
  text. This is contract evidence, not proof about historical exports: a
  manually reconciled cell could be exported differently. The split operations
  also use `guessCellType=true`; pre-CSV lexical changes cannot be undone here.
- `git log --follow -p -- shared/rdf_config/theglobaljukebox.toml` traces the
  earlier path `code/rdf_config/theglobaljukebox.toml`. Commit `ee27fbd1`
  (4 July 2025, “use skos:altLabel instead of P4970”) changed other society
  tables but omitted social factors. Commit `781beaf5` (12 August 2025)
  replaced only the old column-14 line with names 1–14 mapped to SKOS, leaving
  duplicate keys 1–13 and old P4970 mappings 15–19. The reorganization commit
  `e07dd5c1` carried this conflict forward. This supports completing the
  interrupted mapping change, not interpreting duplicates as a dual mapping.

Authoritative definitions checked 21 October 2026:

- [Wikidata P4970](https://www.wikidata.org/w/index.php?title=Property:P4970&oldid=2549057901)
  describes alternative names in database/reference contexts and specifies
  qualifier/reference scope. Its string datatype does not imply an entity link.
- [SKOS lexical labels](https://www.w3.org/TR/skos-reference/#labels) allow
  alternative labels on resources of any type (§5.6.1), so the local Culture
  resource need not be retyped as a SKOS concept. The predicate expresses an
  alternative lexical label, not identity, membership or a separate society.
- [RDF 1.1 literals](https://www.w3.org/TR/rdf11-concepts/#section-Graph-Literal)
  represent untagged strings with `xsd:string`. The explicit datatype applies
  the shared converter's literal precedence without inventing a language tag.

For example, local society `culture/Q42` can have alternative labels
`"Q42"^^xsd:string` and `"Study Q42 (draft)"^^xsd:string`. Neither asserts a
relationship to Wikidata Q42. Multiple distinct names survive; RDF set semantics
do not retain duplicate occurrences or original column order.

## Validation and remaining limits

The complete configuration parses and passes `rdf_process_predicates` for all
17 data tables. All nine tracked TOML configurations now participate in the
shared compatibility test with no Global Jukebox exclusion.

The synthetic test in [test_identifier_conversion.py](../../shared/tests/test_identifier_conversion.py)
uses the actual social-factors table and `build_rdf_graph`, with independently
specified expected predicates, subject namespace, Culture type and literals.
It checks all 19 columns, multiple names, a blank society, a sparse subsequent
society, Unicode, punctuation, whitespace, bare IDs, ID-containing text and
URLs. Exact graph equality and a Turtle round trip reject lost text, accidental
entity objects, extra predicates and fill-down leakage across society records.

At the 21 October repair, the offline command passed 65 tests and 14 competency fixture queries. Black
and `git diff --check` pass. No historical CSVs, stored RDF or production graphs
were inspected or regenerated for this repair. Actual affected counts, export
fidelity and deployment implications remain unverified until snapshot access
resumes. Other tables' untyped labels and the converter's existing missing-value
markers remain outside this repair; synthetic checks do not prove every source
name survives those pre-existing conventions. Validate source cells and regenerate
separately before replacing stored RDF. Do not infer live data used this invalid
configuration or attempt to reconstruct names from old entity links.
