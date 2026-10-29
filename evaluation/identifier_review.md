# Cross-dataset identifier review

Reviewed 21 October 2026 for the design questions behind #419/#432.
**Keep source entity nodes and query explicit identifier links. Do not globally
replace them with Wikidata nodes or enable identity inference.** Use canonical
QID IRIs for joins, retaining the source node, graph and matching route when
reporting evidence. This decision is supported by local code/configuration
inspection and synthetic controls; it makes no claim about deployed link
accuracy, completeness or query latency.

A subsequent [shared-converter repair](../shared/rdf_conversion/identifier_preservation.md)
now addresses the first conversion finding below, with ten additional tests.
The findings and probe commands here describe the pre-repair baseline; the
MusicBrainz URL finding is now addressed by the
[URL recognition repair](../musicbrainz/doc/url_recognition.md). DIAMM’s helper is now repaired under its
[bare-ID export contract](../diamm/doc/identifier_validation.md). SIMSSA’s person
P2888 mapping is repaired under its
[person export contract](../simssa/doc/person_identifier_mapping.md). Global Jukebox’s separate mapping conflict is also
[repaired](../theglobaljukebox/doc/alternative_names_mapping.md).
MusicBrainz's auxiliary CSV helper and missing-value fallbacks were subsequently
[repaired on 26 October](../musicbrainz/doc/auxiliary_identifier_validation.md).
The same-day follow-up also preserves CSV text during parsing and isolates
reconciliation tables after Claude's review identified loader defects.
DIAMM's separate [person-year repair](../diamm/doc/person_years.md) now validates
year IDs, retains original year/flag evidence, and limits direct birth/death
years to values explicitly marked non-approximate.
Its [name/floruit follow-up](../diamm/doc/person_name_preservation.md) also keeps
the original person display name and optional separate floruit text through
extraction/export/conversion, without inferring dates from that text.
Later DIAMM repairs preserve [external identifier text](../diamm/doc/external_identifier_text.md),
[complete archive/person identifier lists](../diamm/doc/external_identifier_selection.md)
and [archive names/sigla](../diamm/doc/archive_text.md). Geographic name parsing
remains the next bounded review; the unmatched whole-QID export ambiguity and
historical prevalence remain unresolved.

## Scope and versions

The converters/configurations reviewed are those at
`9bbb4c7d` (the completed preservation handoff), unchanged during this review.
The local copies of issues #419/#432 and the sibling wiki's
`RDF-Conversion-Guidelines.md` supplied the existing questions and policy.
Their live issue status was not rechecked or changed. No snapshots, source API
responses or production graph queries were needed.

The review covers the bespoke MusicBrainz, RISM and DIAMM converters, shared
CKG conversion, and the shared CSV converter/configurations named below. It
does not establish which converter revision produced any existing live graph.

| Dataset / route | Observed representation in code/configuration | Query implication |
| --- | --- | --- |
| [MusicBrainz](../musicbrainz/src/convert_to_rdf.py), [field mappings](../musicbrainz/src/rdf_conversion_config/mappings.json) | Entities retain MusicBrainz URLs. Recognized Wikidata page links become canonical QID objects of P2888. Artist/area and other entity relationships generally retain the MusicBrainz target. | Traverse the relationship and the target's explicit P2888 link. The URL boundary at review time was narrower than RISM’s; the subsequent repair accepts complete item-URL variants (see findings). |
| [RISM](../rism/src/convert_to_rdf.py) | Source IRIs remain subjects. Exact item-URL variants are normalized in RDF objects. Relationship targets follow the reconciled input; some topic nodes are deliberately projected through a match/value lookup. | Handle direct QIDs and local targets. Do not assume all intermediate source nodes survive every mapping. |
| [CKG musiconn/Detmold](../ckg-musiconn/src/convert_to_rdf.py) | Authority blank nodes become GND/VIAF/GeoNames IRIs; a successful crosswalk adds P2888. Source residue IRIs remain local/authority nodes. | Authority IRIs are source entities for this query purpose. A person link remains role-unspecified unless the source supplied a role. |
| [CKG APSearch](../ckg-apsearch/src/convert_to_rdf.py) | Explicit publisher/license links may receive P2888 crosswalks. The feed has no comparable person-reconciliation backbone. | Do not treat all P2888 subjects as people or the generic CKG person query as applicable to this feed. |
| [DIAMM](../diamm/src/convert_rdf.py) | DIAMM subjects and relation endpoints remain source URLs; reconciled entity names add P2888. Reconciled fields can directly contain QID objects. | Both paths are needed; the repaired bare-QID helper now requires a complete ID under the tracked export contract. |
| [DTL](../shared/rdf_config/digthatlick.toml), [Weimar](../shared/rdf_config/wjazzd.toml) | Local tracks/solos remain. Performer/composer fields can become direct QIDs or unmatched literals. DTL track titles can supply P2888; Weimar's MusicBrainz recording identifier is P4404. | Entity resolution and recording-ID joins are different operations. Do not replace P4404 or match recordings by title. |
| [Global Jukebox](../shared/rdf_config/theglobaljukebox.toml) | Local culture/song/instrument and other nodes use configured prefixes. Several reconciled entity-name fields add P2888 only when converted to IRIs; other fields carry direct values. | Scope joins by entity kind and relation; an IRI-valued P2888 target need not be a QID. |
| [The Session](../shared/rdf_config/thesession.toml) | Recording subjects have P2888 from `recording_wiki`; the `artist` field supplies P175, and local IDs/URLs depend on the input columns. | Do not assume every relationship target is already a QID. Input histories distinguish reconciliation URLs from source URLs. |
| [SIMSSA TOML route](../shared/rdf_config/simssadb.toml) | Local person/work/file/source nodes. Works reference local composer/author IDs; person matches now require canonical Wikidata item IRIs, while work-title P2888 retains its IRI guard. | The person repair preserves original names as explicit string labels and omits P2888 for unmatched values. This review of the TOML route does not establish deployment of that route. |
| [Cantus DB](../shared/rdf_config/cantusdb.toml), [Cantus Index](../shared/rdf_config/cantusindex.toml) | Cantus DB chant instances link through P2888 to Cantus Index IDs; these are not Wikidata URLs. Cantus Index keeps its own chant IDs. | Restrict QID resolution by the complete target namespace. Whether instance-to-index links express identity needs source-model review. |

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

## Concrete conversion findings

The following are reproducible local behaviors, not claims that the historical
inputs contain these values. The broader extraction helper is also used by
reconciliation tools, so replacing it globally would change their contract.

| Finding | Local evidence | Consequence and next repair scope |
| --- | --- | --- |
| Shared CSV conversion guessed identifiers inside text and unrelated URLs | At the review baseline, `to_rdf_node` called `extract_wd_id` before URI/literal handling. `https://example.org/Q42` and `Study Q42 (draft)` became `wd:Q42`; `Q42 / Q43` became `wd:Q43`. Even `datatype="xsd:string"` with `Q42` yielded an IRI. | Fixed locally on 21 October: whole-identifier recognition, literal declarations and local prefixes take their documented precedence, and external IRIs retain their identity. Ten new tests cover the input contract; the general-purpose search helper and existing CSV missing-value parsing are unchanged. |
| MusicBrainz's URL branch recognizes fewer valid item-URL forms than RISM | A synthetic artist `wikidata` URL relationship using `https://www.wikidata.org/wiki/Q42` produces canonical P2888; using `https://www.wikidata.org/entity/Q42` produces a literal target. RISM normalizes both complete URLs. | Fixed locally on 21 October: complete HTTP/HTTPS item URLs on the two accepted hosts and paths now normalize; malformed IDs and unrelated values stay literal. Four regression tests cover conversion and canonical joins. Historical prevalence remains unknown; query audit fixtures intentionally retain literal-target controls. |
| MusicBrainz's auxiliary CSV helper accepts partial IDs and fails on missing cells | At `5f23d0a4`, `matched_wikidata` uses a prefix match; `Q42suffix` becomes an invalid item IRI and pandas `NaN` raises an exception. Missing type mappings omit the source type. | Fixed locally on 26 October after reviewing all 14 export/history pairs: complete bare-QID validation, safe missing-value handling, original type/field fallbacks and retained unmatched language names. Seven regression tests cover every helper call site, export-shaped CSV parsing and Turtle round trips. Full URLs remain outside the auxiliary contract; historical impact is unmeasured. |
| MusicBrainz CSV parsing drops textual keys and merged lookups mix field meanings | At `1a089373`, a synthetic `nan` language key is parsed as missing; shared `Other` entries let later auxiliary tables overwrite earlier matches and entity types. The actual CLI reproduces both failures. | Fixed locally on 26 October: read CSV cells as text with default NA detection disabled, isolate all five auxiliary fields and scope type matches by entity kind. Four added tests cover loader/main wiring, missing files and a complete CLI-to-Turtle run. Historical affected counts remain unknown. |
| DIAMM's bare-QID check accepts suffixes | The actual `matched_wikidata` helper uses a prefix match: both `Q42suffix` and `Q42 / Q43` are accepted. Full item URLs are not accepted by that helper. | Fixed locally on 21 October: full bare-QID validation and safe rejection of missing/non-string values, with all nine CSV tables exercised synthetically. Full URLs remain outside this export contract. The separate people year-ID branches were repaired on 26 October as described below. |
| DIAMM person years construct IRIs from unmatched text and discard approximation | At `bec388d8`, the two year-ID branches concatenate any non-null value and omit source years/flags. The tracked export retains those cells; upstream Person guidance distinguishes lifespan years from floruit. | Fixed locally on 26 October: validate bare QIDs, preserve all three cells in each year observation, and emit direct P569/P570 year literals only when explicitly non-approximate. Seven regressions cover both branches, CSV/CLI conversion, invalid/blank/approximate values, stable evidence grouping and query behavior. The subsequent name/floruit repair preserves display text through extraction/export/RDF and adds four tests. Historical prevalence remains unverified. |
| P2888 object constraints differ between configurations | A one-row synthetic CSV using the SIMSSA `person` table produces `<https://db.simssa.ca/persons/1> wdt:P2888 "Unmatched name"`. Its work-title mapping, and several DTL/Global Jukebox mappings, have IRI guards. | Fixed locally on 21 October for SIMSSA persons: retain explicit original-name literals and accept only canonical Wikidata item IRIs for P2888. Three actual-mapping CSV regressions cover matched/unmatched cases and local work links. Other tables and historical export/deployment verification remain separate. |
| A source-record link is not necessarily an entity-identity link | Cantus DB explicitly maps `cantus_id` to P2888 pointing at Cantus Index. The local documentation describes manuscript chants and index entries as different source structures. | This needs source-model review before any identity rule or flattening proposal. No error rate or universal replacement predicate is asserted here. |

These findings are recorded as bounded follow-ups, not silently fixed by this
query/design review. None requires inventing a new match. Code-level repairs
can be pursued with confirmed input contracts and fixtures; historical impact
and regeneration still require the snapshots. No converter, mapping, stored
RDF or production inference setting changed in this review.

The synthetic conversion probes are retained locally in
`evaluation/audits/identifier-review-2026-10-21/conversion-probes.json`, including
reviewed file hashes and original inputs/outputs. DIAMM's helper was compiled
from its function AST in isolation because importing that script reads source
files and starts conversion. The other probes call the actual conversion
functions; the SIMSSA probe runs the real shared graph builder with a temporary
CSV and the existing person-table configuration. These artifacts are ignored
and not transferred with Git.

The following command probes the shared-converter behavior without those
artifacts, from the repository root. At the review baseline it returned QID IRIs;
after the repair it preserves the external IRI and the two literal strings:

```bash
poetry run python - <<'PY'
import sys
sys.path.insert(0, "shared")
from rdfconv.convert import to_rdf_node
ns = {"wd": "http://www.wikidata.org/entity/"}
for value in ("https://example.org/Q42", "Study Q42 (draft)", "Q42 / Q43"):
    print(repr(value), to_rdf_node(value, ns).n3())
PY
```

The old output was the defect. The shared-converter regression tests now
require preservation of the external IRI and original literal meanings.

## Query verification and completion

The [synthetic fixture](fixtures/identifiers.trig) contains direct and local
references, multiple source nodes with one QID, competing QIDs, unmatched names,
external targets, HTTPS variants, literal targets, two-hop chains and unrelated
graph matches. It also deliberately contains a questionable catalogue-record
match: the query returns the asserted agreement, illustrating that query
success cannot verify identity.

Six [regression tests](tests/test_identifier_queries.py) check independently
specified bindings: six source-preserving entity rows, five distinct
record/QID pairs, and six cross-graph evidence rows. They also check graph
isolation, audit classifications and retention of original node descriptions.
They run automatically through the evaluation suite and
`poetry run python scripts/check_offline.py`. The original 14 competency cases
and their expected answers remain unchanged; these three query examples are
additional controls, not new measured user questions.

The review baseline on 21 October was **54 tests and 14 competency fixture
queries**, using Python 3.12.11 / RDFLib 7.6.0 locally. Later repair counts are
recorded by task in the [handoff](../LINKEDMUSIC-HANDOFF.md). The complete command
was rerun on 29 October and passed **117 tests and 14 competency fixture queries**;
see the [current baseline](../README.md#preservation-and-evaluation-status).
The hosted CI result recorded for draft PR #473 covers only the earlier
69-test revision, not the subsequent local repairs.

This local identifier design review is complete. It does not settle live
reconciliation accuracy, the proportion of affected identifiers, source-record
versus entity identity in every dataset, or Virtuoso performance. Keep those
questions separate from the verified query semantics and the concrete code
follow-ups above. SESEMMI and production graphs remain unchanged.
