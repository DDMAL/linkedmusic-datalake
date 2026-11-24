# Archive names, sigla and websites

Archive names and sigla load as text and retain their exact nonempty strings
in RDF. Empty cells emit no corresponding statement. Numeric-looking and
NA-like strings are preserved without inferred numbers or nulls.

## Evidence and input boundary

The upstream [archive model](https://github.com/diamm/diamm/blob/052004f86960a5dc4d1e7446be8d5a6ac8594bd1/diamm/models/data/archive.py)
defines `name` as a character field with default `S.N.` and `siglum` as a
character field allowing blanks and nulls. The
[archive detail serializer](https://github.com/diamm/diamm/blob/052004f86960a5dc4d1e7446be8d5a6ac8594bd1/diamm/serializers/website/archive.py)
exposes both as string fields. Both files were inspected at revision
`052004f86960a5dc4d1e7446be8d5a6ac8594bd1`. This supports preserving supplied
strings; it does not identify the deployed API or historical snapshot version.
Pinned source code does not establish the contents of live or historical records.

[`to_csv.py`](../src/to_csv.py) copies both fields directly from each archive
record. It does not strip whitespace, replace the name with the archive display
name, or derive a siglum from an external identifier. Supplied strings retain
their characters through CSV writing. JSON null and empty strings both become
empty CSV cells, so that boundary does not retain their distinction. Null
names are tested as defensive cases, not claimed as valid upstream model data.
Missing required keys and unexpected non-string JSON values are outside this
text contract; extraction has not gained a schema validator or new fallbacks.

The tracked [history](../openrefine/history/archives_history.json) copies `name`
into `name_@id` and reconciles only that copy. `siglum` is a P11550 matching hint;
the original name and siglum are not edited. The existing
[export template](../openrefine/export/archives_export.json) includes both original
columns with unmatched cells retained and exports `name_@id` as an entity ID.
Identifier-list evidence uses an additional export column; the original name
and siglum columns keep their export settings.

Import with automatic numeric/date parsing and whitespace trimming disabled.
These are project-wide settings, not changes stored in the reconciliation
history. Keep original names and sigla as text throughout; any name normalization
for matching belongs in `name_@id`. Changing import settings can change matching
inputs, including the siglum hint. Review regenerated matches before deployment.
The tests project tracked export columns but do not replay OpenRefine or its
reconciliation service.

## RDF behavior and compatibility

Archive `name`, `siglum`, `website`, `rism_id` and `source_identifiers` use text converters.
Other archive columns retain default pandas inference. Local subjects
remain `https://www.diamm.ac.uk/archives/{id}` with type
`https://linkedmusic.ca/graphs/diamm/Archive`.

| Source cell | RDF property | Behavior |
| --- | --- | --- |
| `name` | `rdfs:label` | Nonempty source name as a string literal |
| `siglum` | `wdt:P11550` (RISM siglum) | Nonempty source siglum as a string literal; no syntax or identity validation |
| Empty name or siglum | Corresponding property above | No statement for that cell; the archive subject and its other statements remain |

Names and sigla use plain string literals, serialized as quoted strings in
Turtle. Numeric-looking values now become strings rather
than numeric RDF objects. `00123`, `9007199254740993`, `1e3`, `NA`, `None`, QIDs,
URLs, Unicode, punctuation and whitespace retain their supplied spelling.
Whitespace-only strings are nonempty and survive; no trimming is performed.

An empty name no longer fabricates the literal `"None"`. An empty siglum still
emits no statement. A supplied string `"None"` is distinct from a null and is
preserved. No name or siglum is inferred from a QID, RISM ID, website or the
upstream model's default. Do not delete every old `"None"` label without its
source evidence: that spelling may have been supplied literally.

P2888 still uses only the dedicated `name_@id` column and its existing complete
bare-QID rule. A QID/URL appearing only in `name` or `siglum` remains literal.
The export's `blankUnmatchedCells: false` setting can also copy an unmatched
name such as `Q42` into `name_@id`, where it still passes the existing syntax
check. This pre-existing reconciliation ambiguity is explicitly tested and is
not resolved by text preservation. A syntactically valid ID is not verified
identity. Supplied matches, city links (P131), source-to-archive links (P276)
and external-identifier handling retain their existing roles.

Duplicate rows collapse identical RDF assertions. Conflicting rows for one
archive retain all distinct names and sigla as sets; these direct triples do
not encode which name and siglum appeared together in a particular CSV row.
Former archive names and former sigla are outside this mapping.

Exact-string queries can now use the supplied spelling, for example:

```sparql
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?archive ?name ?source WHERE {
  ?archive wdt:P11550 "00123" .
  OPTIONAL { ?archive rdfs:label ?name }
  OPTIONAL { ?source wdt:P276 ?archive }
}
```

Scope the query to the DIAMM named graph in a shared endpoint. Numeric-literal
filters for formerly coerced values need updating. Optional labels accommodate
archives whose exported name is empty.

## Archive websites

The converter preserves an absolute HTTP or HTTPS website IRI with a host and
a valid port (if supplied) as a `wdt:P856` link, with the original spelling.
For any other nonempty `website` cell, it records the exact string on
`diamm:sourceWebsite` (`https://linkedmusic.ca/graphs/diamm/sourceWebsite`).
An empty cell omits both properties.

For example, `https://www.rijksmuseum.nl/` produces a P856 link.
`www.rijksmuseum.nl/` produces the literal `"www.rijksmuseum.nl/"` on
`diamm:sourceWebsite`. To find archives whose website address needs review,
query this property. Resolving older relative P856 values against a Turtle
file path or dataset base can give them an unrelated destination.

## Validation and regeneration

The [archive tests](../tests/test_archive_text.py) cover real CSV loading, extraction and
RDF CLIs, tracked export projection, independently specified full graphs,
Turtle round trips and an exact-string SPARQL join through supplied name matches
and source/location relationships. Cases include numeric-only columns,
precision loss, NA-like strings, null/empty/whitespace-only cells, Unicode,
quotes/newlines, QIDs/URLs, invalid match candidates and duplicate/conflicting
rows. The website regression loads the converter's Turtle bytes in PyOxigraph
without a base IRI and compares the parsed triples with the expected archive
subjects, links and literals. Run from the repository root:

```sh
poetry run python scripts/check_offline.py
```

Synthetic export projection does not establish OpenRefine project settings,
historical source fidelity or identity accuracy.

When snapshot access resumes, record the source checksums and conversion
revision, compare these two raw fields with extracted and reconciled cells,
and count changed/empty values with explicit denominators. Re-extract where
old exports already lost text; lost zeros or rounded digits cannot be recovered
reliably from those exports or old RDF. Regenerate into a separate directory,
verify literal datatypes and text alongside name matches and archive links,
then stage queries before replacing the graph with a backup available.
Appending would retain old numeric objects and fabricated labels.

Historical affected counts, actual export fidelity and deployed source version
require matching source snapshots and separate deployment evidence.
