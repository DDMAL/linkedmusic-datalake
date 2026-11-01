# Shared evidence and lineage contract

Version 1, 1 November 2026. This contract resolves the shared-model prerequisite
from the [DIAMM design review](../../diamm/doc/source_provenance.md#design-review--29-october-2026).
It describes the existing observations and provides an optional lineage profile.
The schema is a maintained local artifact; its namespace is not a claim that a
web resolver, production schema graph or application migration has been deployed.

- [preservation.ttl](preservation.ttl): labels, definitions and conservative RDFS
  alignments, using `lm: <https://linkedmusic.ca/terms/preservation/>`.
- [shapes.ttl](shapes.ttl): executable SHACL constraints for DIAMM geographic
  provenance and the optional versioned-lineage profile.
- [DIAMM query templates](../../diamm/doc/source_provenance.md#query-and-answer-contract):
  named-graph discovery, uncertainty selection, qualifier disagreements and counts.

## Decision and scope

Keep named evidence observations and their source-specific qualifiers. Use
`lm:EvidenceObservation`, a `prov:Entity` subclass, as the shared superclass of
DIAMM provenance/person-year observations, MusicBrainz relationship observations
and APSearch creation periods. Schema loading does not rewrite data or imply
that current converters emit the shared superclass explicitly. Cross-dataset
discovery must either join the separately loaded schema's `rdfs:subClassOf*`
path or deliberately enable the tested entailment regime.

An observation is retained evidence plus a bounded interpretation. It can be
incomplete, uncertain or disagree with other evidence. It is not necessarily a
complete RDF statement. MusicBrainz's mapped observations retain their existing
`rdf:Statement` endpoints; unresolved records do not acquire guessed endpoints.
No universal subject/predicate/object fields are imposed on incomplete evidence.
The [RDF reification vocabulary](https://www.w3.org/TR/rdf-schema/#ch_reificationvocab)
describes statements; it does not remove the need for application-specific
qualification and projection rules.

| Quantity | Shared interpretation | Existing source meaning |
| --- | --- | --- |
| Source uncertainty | `lm:sourceUncertain` | DIAMM `uncertain` is a subproperty. True explicitly flags an association; false means source-unflagged. Missing is unknown. |
| Date approximation | `lm:dateApproximate` | DIAMM `approximate` qualifies a person year. It does not measure geographic association uncertainty. |
| Conversion/review flags | `lm:validationFlag` | DIAMM `validationFlag` and CKG `reviewFlag` are subproperties. They report processing limitations or review conditions. |
| Mapping/parse status | Source-specific | MusicBrainz `mappingStatus` and APSearch `parseStatus` retain their definitions. Successful processing does not establish certainty or independent correctness. |
| Reconciliation quality | Separate evaluation | A QID match or syntactically valid identifier supplies no confidence score. |
| Answer confidence | Separate application evaluation | None of these source fields measures an LLM answer's accuracy. |

There is no equivalence between uncertainty and approximation, no blanket
confidence score, and no subproperty alignment to P131/P276 for manuscript
provenance. Raw evidence and supported bounds remain attached to the same
observation. Direct projection rules remain dataset-specific: for example,
DIAMM person dates require explicit non-approximation; geographic provenance
does not produce unqualified location assertions. CRMinf is not adopted because
the available fields do not supply scholarly agents, arguments or belief values.

## Historical provenance versus data lineage

Manuscript provenance describes a historical association. Data lineage identifies
the source artifact and transformation that produced an RDF representation.
The existing DIAMM `dcterms:source` place link is only a coarse origin reference,
including on legacy rows. It is not a versioned source document, retrieval
record or conversion identity. Passing the evidence shape does not upgrade it.

Use the [PROV-O](https://www.w3.org/TR/prov-o/) Entity/Activity pattern for
lineage when actual metadata exists. The optional profile specifies:

1. `lm:SourceSnapshot`: immutable retained source artifact with `lm:sha256` of
   its exact bytes. Retain the artifact; a checksum alone cannot recover it.
2. `lm:SourceRecordVersion`: `prov:wasDerivedFrom` one snapshot, with a nonempty
   `lm:recordSelector` resolving unambiguously inside it. Document the selector
   convention (e.g. archive member plus JSON pointer). This resource describes
   a source record, not the person, manuscript or place mentioned in it.
3. `lm:Conversion`: one execution with a unique run IRI, `prov:used` the relevant
   record versions, and `lm:runManifest` identifying an immutable `lm:RunManifest`
   with its own exact-byte hash. The manifest must record code and configuration
   hashes, dirty-working-tree content, dependency/runtime identity, all inputs,
   actual execution identity and output checksums. An output checksum lives in
   the separate manifest to avoid an RDF file containing its own checksum.
4. `lm:ObservationOccurrence`: a run-specific resource with
   `prov:specializationOf` the content observation, `prov:wasDerivedFrom` its
   record version and `prov:wasGeneratedBy` one conversion. That conversion must
   explicitly `prov:used` the same record. Qualifiers are read from the linked
   content observation; specialization does not copy triples in ordinary SPARQL.

Keep different executions' occurrences separate even when their content hashes
match. Existing observation hashes do not identify retrievals or historical
events. When source occurrences have reliable positions/IDs, include them in
occurrence identity; when identical entries have already collapsed, their
multiplicity cannot be reconstructed. Different city/region listings still
cannot establish one shared provenance event without evidence.

This profile deliberately does not require timestamps: absent retrieval or
snapshot dates must stay absent. If known, record retrieval as its own activity;
do not substitute conversion time for source snapshot time. Never backfill
versioned lineage from a website URL or current source-code revision. Existing
converters do not emit this optional profile; wiring real run metadata into
conversion awaits retained inputs and remains a separate task.

## Shapes and verification

[SHACL](https://www.w3.org/TR/shacl/) checks representation constraints, not
historical accuracy. The DIAMM shape checks named identities, one manuscript and
place per observation, the source field, supported RDF datatypes/cardinalities,
and the mutually exclusive retained-JSON versus legacy-unqualified forms.
Raw invalid/null/missing qualifiers and reversed bounds remain allowed evidence;
their extraction/projection rules are checked by converter regression tests.
The shapes are open, allowing other evidence fields. They do not parse embedded
JSON, verify an endpoint against the source, or replace conversion tests.

Optional lineage shapes reject missing hashes/selectors, missing manifests,
multiple generating executions for one occurrence and a generating execution
that did not use the stated record. They check structure and hash syntax, not
artifact availability, checksum correctness or manifest contents. They must not
be reported as evidence that lineage has been measured in real snapshots.

Run the normal offline suite after `poetry install` (pySHACL is a locked
development dependency):

```bash
poetry run python scripts/check_offline.py
```

Tests load the local ontology explicitly and disable general inference; SHACL
still recognizes declared subclass relationships. They validate real DIAMM
converter output, malformed graph mutations, separate synthetic run occurrences
and query results with deliberately disagreeing, unknown and legacy evidence.
No remote imports, source API requests or triplestore are needed. Schema and
shapes stay separate from instance output, avoiding extra vocabulary triples
being counted as dataset records.

## Application and deployment boundary

SESEMMI currently uses its static schema corpus and still describes the old
Source/P131/City route. Loading this Turtle into Virtuoso does not update that
corpus. The [candidate context fragment](../../diamm/doc/source_provenance_nlq.txt)
and tested queries prepare its migration; they are not activated application
configuration. Update the complete corpus, examples and graph-version selection
together when a candidate graph is available.

Retrieval must include the observation block and its qualifier notes whenever
it selects geographic provenance. Source-only context is insufficient. Tests
must check generated SPARQL, returned evidence columns and answer wording for
uncertain, source-unflagged, unknown and disagreeing cases. Measure accuracy and
query cost separately; deterministic parser checks do not establish either.

The next converter repair remains geographic parent evidence/type routing.
The shared contract supplies representation rules; it does not establish that
a country URL identifies the true parent type or justify administrative P131.
