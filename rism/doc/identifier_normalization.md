# RISM identifier normalization

## Conversion contract

The converter normalizes complete HTTP/HTTPS × www/non-www × wiki/entity
Wikidata item IRIs to `http://www.wikidata.org/entity/Q…`. Only positive ASCII
IDs matching `Q[1-9][0-9]*` are recognized. Literal text/language/datatypes,
unrelated URLs, source-record identifiers and malformed/suffixed IDs remain
unchanged. A URL-shaped CSV field without literal metadata follows the existing
IRI convention. See [#462](https://github.com/DDMAL/linkedmusic-datalake/issues/462).

Topic traversal accepts four explicit P2888 predicate spellings and retains all
supplied matches. It falls back to `rdf:value` only when no match exists. This
is separate from item normalization and does not rewrite arbitrary predicates.
HTTP/HTTPS and optional www aliases are supported input forms, not assertions
about which forms occur in a stored or deployed population.

Run `poetry run python -m unittest discover -s rism/tests -v` from the repository
root. Synthetic controls cover the eight item forms, full-match rejection,
idempotence, literal preservation, topic aliases and a serialized canonical-ID
join through a local source/person node. They do not validate reconciliation
identity or the existing P50 (author) to P86 (composer) role mapping.

## Bounded identifier evidence

Classify an already archived SPARQL JSON response without network access:

```sh
poetry run python rism/src/audit_identifiers.py \
  --response path/to/response.json --output-dir path/to/new-audit
```

The response must project and bind `s`, `p` and `o`. A saved response establishes
only its supplied RDF terms; its endpoint, graph, original query, observation
time and completeness need separate archived evidence. The classification time
is not a replacement for its original retrieval time. Keep the source response.

For an explicitly authorized endpoint observation, supply the endpoint:

```sh
poetry run python rism/src/audit_identifiers.py \
  --endpoint https://example.org/sparql --output-dir path/to/new-observation
```

There is no default endpoint. The request uses the RISM named graph
`https://linkedmusic.ca/graphs/rism/`, at most 200 P2888 triples by default
(maximum 1,000), and a 15-second server timeout. Endpoint query options include
`--predicate P86` or `P136`, `--limit`, and `--noncanonical` (IRIs outside the
complete canonical item form). They do not filter an archived response.

Each fresh output directory retains exact response bytes, a report, and the
rendered query for endpoint mode. Reports include hashes, runtime/code identity,
normalizable/other-term counts and URI-form counts. Execution failures, partial
responses and read timeouts retain available diagnostic evidence and exit
nonzero. The shared [query runner](../../evaluation/README.md) defines timeout
and response limits. Existing output directories are refused before a request.

This is an unordered convenience sample, not an error-rate estimate or full
count. A result reaching the limit is flagged; fewer rows or an `ok` status do
not prove completeness. Local-person links may fill the sample and hide item
variants under the same predicate. Do not interpret an empty or timed-out
sample as evidence of absence. This classifier does not create population
measurements in the manifest or prove correspondence with stored RDF.

## Separate migration procedure

No live data migration has been performed. First establish which stored output
or live predicates actually contain variants; do not replace a graph merely
because the converter was repaired.

For an identifier-only migration:

1. Export the exact RISM named graph to a local RDF snapshot. Record its graph
   IRI, export time, triple count, checksum, and server/converter versions.
   Keep the unchanged export as the rollback artifact.
2. Produce a separate output by applying `WIKIDATA_PATTERN.fullmatch(str(o))`
   **only when `o` is an RDF `URIRef`**. On a match, substitute `WD[match.group(1)]`;
   keep subject and predicate unchanged. Never use text replacement on a Turtle
   file, and never call the CSV object parser on RDF literal text.
3. Save each distinct changed triple and its replacement to a local audit.
   Count both changed input triples and collisions where replacements collapse
   to one RDF triple. The expected total is the cardinality of the complete
   transformed triple set, not necessarily the original triple count.
4. Load the transformed output into a **new staging graph**, with no production
   replacement. Check exact transformed-set equality locally or by an exported
   staging snapshot. Verify unchanged subject/predicate pairs, literal values,
   language tags and datatypes, unrelated IRIs, and source URLs. Verify no
   recognized noncanonical item objects remain in a complete staging scan.
5. Run canonical-ID joins against the staging graph for sampled changed
   objects. Check both direct-QID paths and local-node/P2888 paths, retaining
   query text and expected/actual result sets. Record intentional duplicate
   collapse separately from lost triples.
6. Review the stage, affected-predicate counts, and rollback plan before a
   separately scheduled production replacement. Repeat the same checks after
   replacement and retain the original export until accepted.

Alternatively, regenerate from the reconciled CSV snapshot into a **new,
empty output directory** using the README command. Reusing an output directory
can trigger the converter's skip-existing behavior. Regeneration includes the
topic/P2888 mapping fixes as well as item normalization, so compare those added
assertions separately from the identifier-only transform. Neither route repairs
source values or changes reconciliation decisions.

`row_cap_reached` compares returned rows with the requested cap only in endpoint
mode. For an archived response it is `not_established`: its original query and
limit are unknown. `--noncanonical` samples IRIs only; literal terms are excluded.
