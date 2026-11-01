# RISM identifier normalization

## Change and evidence

Issue [#462](https://github.com/DDMAL/linkedmusic-datalake/issues/462) describes
Wikidata item IRIs emitted with HTTPS while LinkedMusic's canonical namespace
uses HTTP. This is a **conversion error**. A tiny synthetic CSV-to-Turtle fixture
reproduced a failed canonical-ID join before the fix; the same SPARQL now returns
the expected source through its local person node and `wdt:P2888`.

The converter accepts exactly HTTP/HTTPS × www/non-www × wiki/entity, with a
complete, positive ASCII QID. It preserves literal contents, malformed IDs,
unrelated IRIs, and source record identifiers. Non-www item forms are supported
as an explicit hostname alias; they were **not observed** in the bounded live
P2888 sample. Existing non-www predicate keys are independently evidenced by
`property_mapping.json` and the former P921 lookup. They are not evidence that
non-www item forms occur in the imported data.

Topic traversal accepts all four explicit P2888 predicate spellings and retains
all supplied matches; it falls back to `rdf:value` only when no match exists.
This does not introduce general predicate rewriting. Tests cover this lookup,
literal handling, malformed identifiers, idempotence, and serialized conversion.

## Read-only live checks

Run from the repository root, saving reports outside Git:

```bash
poetry run python rism/src/audit_identifiers.py \
  --output /tmp/rism-identifiers.json
poetry run python rism/src/audit_identifiers.py --noncanonical \
  --output /tmp/rism-noncanonical-identifiers.json
```

The script requests at most 200 P2888 triples by default (maximum 1,000), with a
15-second server timeout. `--predicate P86` or `--predicate P136` checks another
mapped property. It stores query text, graph/endpoint, retrieval timestamp,
response bindings, response hash, timeout headers, and URI-form counts.
`--noncanonical` selects IRIs outside the canonical namespace; malformed or
unrelated results remain in the report and are not counted as normalizable.

On **20 October 2026**, the first 200 P2888 bindings in
`https://linkedmusic.ca/graphs/rism/` all used canonical HTTP item IRIs. A separate
P2888 noncanonical query returned no rows and no partial-result header. These
checks do not establish an error rate, complete source coverage, or the state of
other predicates or stored files. An earlier broad graph scan timed out with no
rows; that response is **not evidence of absence**. Evidence was first saved to
`/tmp/linkedmusic-preservation-2026-10-20/`, then copied and checksum-verified
under `evaluation/audits/handoff-2026-10-20/preservation/`. The parent manifest
records the copies; these ignored local files are not transferred with Git.

Additional bounded checks returned 200 local RISM person IRIs for noncanonical-
namespace P86 objects (all outside the normalization rule), and no noncanonical-
namespace P136 IRIs. No timeout header was returned for either. The P86 sample
was filled by local-node links, so it does not exclude Wikidata variants
elsewhere under that predicate.

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
