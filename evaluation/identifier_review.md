# Identifier query contracts

Keep source entity nodes and query explicit identifier links. Resolve canonical
QID IRIs within selected named graphs, retaining the source node, graph and
matching route as evidence. These controls support [#419](https://github.com/DDMAL/linkedmusic-datalake/issues/419)
and [#432](https://github.com/DDMAL/linkedmusic-datalake/issues/432); they do not
establish deployed link accuracy, completeness or latency.

## Current converter boundaries

These are code/configuration contracts, not claims about which revision produced
stored or deployed RDF. The query controls do not repair these converters.

| Route | Current behavior | Query consequence |
| --- | --- | --- |
| [MusicBrainz](../musicbrainz/src/convert_to_rdf.py) | Retains MusicBrainz entity URLs and configured contributor roles with source observations. Its JSON converter emits a canonical Wikidata exact match for a current entity-specific Wikidata relationship with a complete item URL. External links retain their MusicBrainz role and original address. Auxiliary CSV matches require complete bare IDs; text-preserving lookups are isolated by field and entity kind. Invalid/missing matches use documented literal fallbacks. | Older stored RDF can contain P2888 links from any URL role, including discography pages. Before counting even a canonical Wikidata target as an identity, verify the original MusicBrainz relationship was `wikidata` in the corresponding source snapshot. Broad contributor queries require the matching role schema, and qualifier-sensitive questions require the observations. |
| [RISM](../rism/src/convert_to_rdf.py) | Retains source IRIs; canonicalizes complete positive-ASCII item IDs across HTTP(S), www/non-www and wiki/entity forms. Topic traversal retains matches under four explicit P2888 predicate aliases, falling back to the source value only when no match exists. Literals and unrelated/malformed IRIs remain unchanged. | Support direct QIDs and local targets. Existing output may predate normalization; neither canonical IDs nor the P50-to-P86 mapping establish identity or composer-role correctness. |
| [CKG musiconn/Detmold](../ckg-musiconn/src/convert_to_rdf.py) | Authority blank nodes become GND/VIAF/GeoNames IRIs; successful crosswalks add P2888. Residual source nodes remain. | A generic related-person link does not assert a composer role. The link must be present in the selected graph. |
| [CKG APSearch](../ckg-apsearch/src/convert_to_rdf.py) | Publisher/licence links can receive P2888 crosswalks; this is not a person-reconciliation frame. Creation periods retain their source terms, paired year bounds and parse/review evidence. | Do not treat every P2888 subject as a person. Query parsed paired bounds for creation-span overlap; P571 is only a start-year projection, and no period asserts a performance date. |
| [DIAMM](../diamm/src/convert_rdf.py) | Retains local subjects and relationship endpoints; matches require complete positive-ASCII bare QIDs. Descriptive fields retain literal fallbacks. Archive/person identifiers preserve complete source lists and string values; year observations retain original cells and approximation. | Follow the [identifier contract](../diamm/doc/identifier_validation.md). Only supported years with a false source flag supply direct P569/P570 year literals. Geographic names remain strings; each organization's directly listed city, region or country uses `schema:location`. [Manuscript city, region and organization provenance](../diamm/doc/source_provenance.md) uses qualified observations for both current and legacy inputs. Syntax does not verify identity; parent routing and other provenance routes retain documented limits. |
| [Shared CSV conversion](../shared/rdfconv/convert.py) | Honors explicit literal declarations and local prefixes before complete structured Wikidata IDs; unrelated URLs stay external IRIs. | Use the [identifier contract](../shared/rdf_conversion/identifier_preservation.md). Existing CSV missing-value and fill-down rules still apply; historical outputs can predate this boundary. |
| [SIMSSA TOML route](../shared/rdf_config/simssadb.toml) | Person matches require canonical positive-ASCII Wikidata item IRIs; original names are explicit string labels. Work titles retain their IRI guard; composer/author links remain local. | Follow the [person export contract](../simssa/doc/person_identifier_mapping.md). This route does not establish historical use of the separate JSON-LD converter. |
| [Global Jukebox](../shared/rdf_config/theglobaljukebox.toml) | Six societies tables emit string `skos:altLabel` values on the same local societies. Parlametrics omits alternative names. | Names, including QID-like text and URLs, are lexical labels rather than entity matches. Other table mappings retain their contracts. |
| [Weimar](../shared/rdf_config/wjazzd.toml) | Local solos/tracks; performer fields can contain direct QIDs, and track MusicBrainz IDs use P4404. | Join recordings by the explicit UUID, not title or shared performer. |
| [Cantus DB](../shared/rdf_config/cantusdb.toml) | P2888 can point to Cantus Index identifiers. | Other-IRI targets are not automatically errors or Wikidata identities; source-record/entity meaning needs separate review. |

## Meaning and decision

P2888 expresses a claimed exact match to another identifier/concept; it is not
restricted to Wikidata targets. Its meaning is stronger than a mere shared
label. The queries below retain the supplied claim without independently
verifying it. [Wikidata's P2888 definition](https://www.wikidata.org/wiki/Property:P2888).

`owl:sameAs` identifies individuals and allows their facts to be interpreted
as facts about the same individual. A mistaken reconciliation, or confusing a
catalogue record with the person/work it describes, can therefore propagate
incorrect assertions. This review adds no equivalence, symmetry, transitivity
or inverse-functional rules to P2888.
[OWL identity semantics](https://www.w3.org/TR/owl-ref/#sameAs-def).

Retain both supported storage forms:

1. A relationship directly targets a canonical QID when the converted source
   field supplies that reconciled identifier.
2. A relationship targets a source entity, which has an explicit P2888 match.
   Keep the entity's source attributes and provenance attached to that node.

Canonical item objects use `http://www.wikidata.org/entity/Q…`; direct
predicates use `http://www.wikidata.org/prop/direct/P…`. These are exact RDF
terms. An HTTPS URL or a literal containing the same characters will not join
as that canonical IRI. Audit variants separately rather than changing strings
inside a query and hiding the evidence of conversion differences.

Keep multiple candidate targets visible. Selecting the first or last target,
or using `SAMPLE`/`COALESCE` to hide competing matches, does not resolve an
identity conflict. A shared QID can support an identifier-agreement join;
it does not establish that the linked source records describe the same work,
recording, edition or event.

Global replacement would detach relationships from source-specific entity
descriptions and obscure which match supported the answer. A derived query
view could be considered later for a demonstrated compatibility/performance
need, retaining its original nodes and derivation evidence separately. There
is no measured performance result here that justifies flattening base graphs.

## Reusable query patterns

Three runnable examples use synthetic graph IRIs. Replace those IRIs with
explicitly selected data graphs and P86 with the source-supported relationship
being asked about. They are not requests to run against production. In
particular, changing an unspecified CKG person relation to P86 would invent a
composer role.

- [Resolve entity references](queries/identifier_entities.rq): returns graph,
  record, original entity, canonical QID and `direct`/`P2888` route. It follows
  at most one supplied P2888 edge in that graph.
- [Join two source graphs](queries/identifier_cross_graph.rq): resolves each
  side in its own selected graph, joins canonical QIDs and returns both source
  records/entities. A matching edge in a third graph is not silently borrowed.
- [Inspect supplied links](queries/identifier_link_audit.rq): retains every
  P2888 target and classifies canonical QIDs, variant QID IRIs, other IRIs and
  non-IRIs. Other IRIs are not automatically errors; Cantus Index is an example.

For a compact query that only needs distinct record/QID pairs within one graph:

```sparql
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
SELECT DISTINCT ?record ?qid WHERE {
  GRAPH <urn:linkedmusic:identifier:a> {
    ?record wdt:P86/wdt:P2888? ?qid .
    FILTER(isIRI(?qid) && REGEX(STR(?qid),
      "^http://www[.]wikidata[.]org/entity/Q[1-9][0-9]*$"))
  }
}
```

The `?` path means zero or one edge, supporting direct QIDs and one-hop links;
`*` would traverse arbitrary chains and broaden the interpretation. The compact
form discards the original entity and route, so use the explicit UNION query
for evidence review. [SPARQL property paths](https://www.w3.org/TR/sparql11-query/#propertypaths).

If relationship assertions and identifier links intentionally live in different
graphs, bind each graph explicitly and document why both are authoritative for
that question. Do not rely on an endpoint's default union graph. A missing
link in the selected graph does not establish absence from Wikidata.

## Synthetic verification

The [identifier fixture](fixtures/identifiers.trig) includes direct and one-hop
links, competing QIDs, unmatched names, external targets, HTTPS variants,
literal targets, two-hop chains and matches in unrelated graphs. A deliberately
questionable catalogue-record match demonstrates that identifier agreement
can be returned even when identity requires adjudication.

[Tests](tests/test_identifier_queries.py) check complete source-preserving
bindings, distinct record/QID pairs, graph isolation, target classifications
and retention of original node descriptions. Run from the repository root:

```sh
poetry run python scripts/check_offline.py
```

The three identifier queries supplement the [14 competency controls](cases.json).
The role/period controls describe explicit synthetic models; they do not assert
that matching converter behavior or a schema graph has been deployed. No
historical conversion-probe result or data quality rate is established by these
fixtures. Use the [protocol](protocol.md) for source evidence and human review.
