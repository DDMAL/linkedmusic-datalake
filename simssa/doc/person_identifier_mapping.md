# Person exact-match links in the shared TOML route

Repaired 21 October 2026. In `shared/rdf_config/simssadb.toml`, `person_name`
now produces P2888 only when its converted object is a canonical Wikidata item
IRI with positive ASCII digits and no leading zero. `person_name_original`
is explicitly an `xsd:string` label. Local person IDs and work author/composer
links retain their SIMSSA namespaces. The shared converter is unchanged.

## Evidence and export contract

The [merge script](../src/merge.py) constructs `person_name` from given name and
surname and retains local person IDs. The tracked
[person history](../openrefine/history/history_person.json) reconciles
`person_name` against Wikidata humans (Q5), first by name and then with VIAF
as supporting evidence. It then copies `grel:value` into
`person_name_original` without a facet restriction. This supports separate
reconciliation and original-text columns. The copy is made after reconciliation;
we have not verified historical execution or actual cell contents.

No SIMSSA export template is checked in. For this TOML route, export accepted
matches in `person_name` as complete Wikidata IDs or item URLs, retain unmatched
text, and export `person_name_original` as the original cell value. Preserve
that original column for every named record, whether matched or unmatched.
Do not replace the original text with a matched entity label or URL.

The shared identifier parser accepts bare QIDs, `wd:Q…`, and complete
HTTP/HTTPS `/wiki/Q…` or `/entity/Q…` URLs on `wikidata.org` or
`www.wikidata.org`. These normalize to `http://www.wikidata.org/entity/Q…`.
The person-specific guard then requires precisely that item-IRI shape. This
also rejects malformed canonical-looking URLs that the general parser correctly
retains as external IRIs. Arbitrary external URLs and property entities are
not supported person matches under this Wikidata-only reconciliation history.
An IRI-valued object alone is insufficient evidence for this mapping.

| Input | Person RDF |
| --- | --- |
| `person_name=Q42`, original name `Example person` | Local person P2888 `wd:Q42`, with literal original label |
| Unmatched text or `Q42 / Q43`, original name present | Original label; no P2888 |
| Empty match, original name present | Original label; no P2888 |
| Unrelated URL, malformed item URL or property ID | Original label; no P2888 |
| Original name `Q42` or a complete Wikidata URL | Original text remains an `xsd:string` label; it does not itself create a match |

The mapping does not infer a match from `person_name_original`, select a
candidate from a list, verify that a QID exists or establish that a supplied
match identifies the correct person. A complete QID in the reconciliation column
is treated as an exported match under the stated contract; CSV alone cannot
prove its OpenRefine judgment. No `owl:sameAs` or identity inference is added.

## Tests and limitations

Three [offline tests](../../shared/tests/test_simssa_mapping.py) use the actual
person/work mappings and `build_rdf_graph` with temporary CSVs. Independently
specified expected triples cover all ten accepted ID/URL forms, unmatched and
ambiguous values, malformed canonical-looking URLs, external URLs, property IDs,
blank cells, Unicode/whitespace in names, and ID-like original names. Exact graph
comparison and Turtle round trips check both missing and extra triples. Work
composer/author links still point to local people; a local key `Q42` remains
in the SIMSSA namespace. The tests failed against the old mapping and now pass.

The unified offline command passes **77 tests and 14 competency fixture queries**,
up from 74 and 14, including validation of all nine tracked TOML configurations.
Black and diff checks pass. No historical dumps or live graph queries were used.

If the original-name cell is blank, there is no label to emit; this repair does
not reconstruct missing original text from the reconciliation column. The input
contract requires the copied original for named records. Before regeneration,
audit missing originals and actual export shapes against source cells. The
converter's existing missing-value conventions and fill-down behavior are
unchanged. This is not proof of preservation through the preceding merge/export
steps or of historical deployment of the TOML route.

The work-title IRI guard, work-original label mapping, date transformations,
other fields and the separate JSON-LD approach remain unchanged. Do not apply
this Wikidata-only guard indiscriminately to other datasets: P2888 can have
non-Wikidata targets in their own contracts. Snapshot validation, affected counts
and regeneration remain deferred until access resumes; stored/live RDF and
SESEMMI are unchanged.
