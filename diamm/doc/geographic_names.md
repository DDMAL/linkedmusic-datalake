# Geographic name preservation

Implemented locally on 29 October 2026 for city, country and region `name`
columns. Default pandas parsing previously stripped leading zeros, changed
numeric spellings and treated NA-like names as missing. Unconditional RDF
labels then turned missing/empty cells into `"None"`. Synthetic CSVs reproduce
these conversion defects; their historical prevalence is unknown.

## Evidence and input boundary

The upstream [geographic-area model](https://github.com/diamm/diamm/blob/052004f86960a5dc4d1e7446be8d5a6ac8594bd1/diamm/models/data/geographic_area.py)
defines a character-field name shared by cities, countries and regions. The
[city](https://github.com/diamm/diamm/blob/052004f86960a5dc4d1e7446be8d5a6ac8594bd1/diamm/serializers/website/city.py),
[country](https://github.com/diamm/diamm/blob/052004f86960a5dc4d1e7446be8d5a6ac8594bd1/diamm/serializers/website/country.py)
and [region](https://github.com/diamm/diamm/blob/052004f86960a5dc4d1e7446be8d5a6ac8594bd1/diamm/serializers/website/region.py)
detail serializers expose `name` as a string. All four files were inspected at
revision `052004f86960a5dc4d1e7446be8d5a6ac8594bd1`; this does not establish the
version of the deployed API or a historical snapshot. No live DIAMM records or
stored snapshots were inspected.

[`to_csv.py`](../src/to_csv.py) copies each name directly into its table. It
does not strip parenthetical text or normalize names. JSON null and empty
strings both become empty CSV cells, losing that distinction. Null names are
defensive test inputs, not asserted to be valid upstream model data. Missing
required keys and unexpected non-string JSON values remain outside this text
contract; extraction has no new validation or fallback behavior.

The tracked histories for [cities](../openrefine/history/cities_history.json),
[countries](../openrefine/history/countries_history.json) and
[regions](../openrefine/history/regions_history.json) reconcile `name_@id`
copies, leaving the original `name` untouched. City and region copy expressions
remove parenthetical suffixes for matching. The region copy step also contains
a pre-existing judgment facet referring to `name_@id` itself; its effect on
history replay and match coverage is unverified. This repair does not change
that history or claim that it successfully copies every row.

The [city](../openrefine/export/cities_export.json),
[country](../openrefine/export/countries_export.json) and
[region](../openrefine/export/regions_export.json) export templates retain the
original name and export the separate match column as an entity ID, with
unmatched cells retained. No extraction/history/export changes were needed for
name preservation. Import with automatic numeric/date parsing and whitespace
trimming disabled; those project-wide settings are not recorded by the history.
Keep normalization confined to the match copy. Changed import settings can
change matching inputs and require review before deployment.

## RDF behavior and compatibility

Only the three `name` columns gain text-preserving CSV converters. Other
columns retain their existing parsing. Names use the existing `rdfs:label`
predicate, directed from the local geographic resource to a string literal:

| Table | Local subject | Existing type |
| --- | --- | --- |
| cities | `https://www.diamm.ac.uk/cities/{id}` | `diamm:City` |
| countries | `https://www.diamm.ac.uk/countries/{id}` | `diamm:Country` |
| regions | `https://www.diamm.ac.uk/regions/{id}` | `diamm:Region` |

Here `diamm:` means `https://linkedmusic.ca/graphs/diamm/`. Every nonempty name
becomes a plain string literal, retaining leading zeros, long digits, exponent
notation, NA-like values, Unicode, quotes, newlines and whitespace. QIDs and
URLs in the original name are text, not identity assertions. Whitespace-only
names remain nonempty. Empty cells emit no label; local subjects, types,
supplied matches and existing links still survive. No name is inferred from
a QID or country hint. A supplied `"None"` is retained and differs from an empty
cell. Previously numeric label objects now become strings.

P2888 still uses only `name_@id` and the complete bare-QID check. The existing
export ambiguity remains: unmatched text such as `Q42` can also occupy that
column and pass the syntax check. Tests explicitly retain this behavior;
syntactic validity does not establish verified identity.

City `country` text comes from the supplied `country.name`; region `country`
text comes from `parent`. Their `country_@id` copies are reconciliation hints,
not RDF relationships. The RDF converter does not use either hint column to
create P17, labels or fallback matches. Geographic relationships instead come
from `relations.csv`, including city-to-country P17, city-to-region P131,
region-to-country P17, archive/organization-to-city P131, source-to-city P131
and organization-to-country P17. Their existing mapping and direction are
unchanged; this name repair does not validate their geographic semantics.

Review at the name repair exposed separate relationship limits: city extraction assumes
that the supplied `country` URL identifies a country, while the inspected
serializer obtains it from a general geographic parent. Extracted
region-to-source and organization-to-region rows lacked RDF conversion branches.
Source provenance qualifiers are also not retained by that extraction route.
The subsequent [geographic relationship review](geographic_relationships.md)
repairs the organization/region omission. Parent routing and qualified source
provenance remain separate; the name tests do not establish complete geographic
relationship fidelity.
Variant names and other unmapped fields remain outside this repair.

Duplicate triples collapse. Conflicting rows retain all distinct names and
supplied matches, without preserving name/match pairing by CSV row. No new
observations, identity inference or reconciliation policy are introduced.

An exact-string query can now join names to the existing local relationships:

```sparql
PREFIX diamm: <https://linkedmusic.ca/graphs/diamm/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
SELECT ?source ?city ?country ?countryName WHERE {
  ?source a diamm:Source; wdt:P131 ?city .
  ?city rdfs:label "00123"; wdt:P17 ?country .
  OPTIONAL { ?country rdfs:label ?countryName }
}
```

Scope queries to the DIAMM graph in a shared endpoint. Numeric-literal filters
for formerly coerced names need updating, and optional labels accommodate
empty names. Do not delete every old `"None"` label without matching source
evidence: the spelling may have been supplied literally.

## Validation and regeneration

Seven [regressions](../tests/test_geographic_names.py) cover actual CSV loading,
extraction and RDF CLIs, tracked export projection, independently specified
full graphs, Turtle round trips and an exact-string SPARQL join. They include
all three tables, numeric-only columns, NA-like text, Unicode, parentheses,
null/empty/whitespace names, supplied and rejected matches, duplicate/conflicting
rows, existing geographic/source links and country hints that must not create
relationships. The tests do not replay OpenRefine or call its service.

The pre-repair converter reported ten failures, including subtests, across six
tests; the history/export inspection test passed. All seven pass after the
repair. Full offline validation and review results are recorded in the
[handoff](../../LINKEDMUSIC-HANDOFF.md). The tests use synthetic data only.

When snapshot access resumes, record input checksums and conversion revisions,
compare raw names with extracted/reconciled cells, and count changed or empty
values with explicit denominators. Validate the region history's replay and
review regenerated matches. Re-extract from matching evidence wherever old
exports have already lost text. Regenerate into a separate directory, check
label strings and datatypes alongside matches and source relationships, and
stage queries with a backup before replacing the graph. Appending would retain
old numeric labels and fabricated missing-value labels.

Historical affected counts, actual export fidelity and source-version
compatibility remain unknown. No stored RDF was regenerated or deployed.
