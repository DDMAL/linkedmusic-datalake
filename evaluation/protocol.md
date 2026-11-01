# Pilot protocol — version 1.0, 20 October 2026

Freeze this protocol, manifests, queries, sampling seed and source/configuration
hashes before interpreting a measurement. Record deviations with their reason.
The protocol is independent of SESEMMI and model-generated answers.

## Scope and evidence boundaries

The six sources are Weimar, MusicBrainz, RISM, musiconn, Detmold and APSearch.
They cover three tasks: jazz recording discovery, historical person/source
lookup, and role/date preservation. This pilot does not inventory every
LinkedMusic dataset.

Keep four evidence groups separate:

1. Synthetic query/converter controls: exact known answers, no population claim.
2. Current API or source-web evidence: dated retrieval, original response,
   URL/parameters and checksum; not the historical imported snapshot.
3. Live-graph observations: endpoint, graph, query, timestamp, result and status;
   graph provenance and source fidelity may remain unknown.
4. Matched historical source and converted graph: input snapshot/checksum,
   intermediate reconciliation export, code/configuration revision, output
   checksum and staging/deployment manifest. Only this group supports historical
   conversion-fidelity measurements.

The [manifests](manifests.json) are an inventory with explicit unknowns. Fill
snapshot date independently of retrieval time. Record source entity counts,
counts by RDF class and triple counts with their measurement time, query or
script, evidence file and completeness status. Count each entity once per stated
class; class totals can overlap. RDF triples, source records, relationship
occurrences and distinct observations are different denominators.

Licence entries are discovery references requiring snapshot-specific review.
Capture the actual metadata licence and any exceptions; media-file rights are
separate. A URL to a source homepage is not a verified licence.

## Conversion fidelity

Use [one review record](templates/fidelity-review.json) per source assertion or
field occurrence. Retain an occurrence ID, source file/hash and record locator,
original value/term, normalized or reconciled intermediate, mapped RDF terms,
converter/configuration hashes, and reviewer evidence. Include rows whose
mapping omits a value, not only RDF statements that survived conversion.

Start with these field strata:

| Source | Fields and necessary negative checks |
| --- | --- |
| Weimar | Performer identity; solo→track; track MBID; source date precision. Shared titles must not be treated as identity. |
| MusicBrainz | Recording/release role UUID, endpoints/direction, dates, attributes, missing IDs, repeated and inverse observations. Photography/generic contribution must not imply engineering. |
| RISM | Item-IRI variants, literal preservation, P2888 pivots and source role behind mapped P86. Canonical syntax does not prove identity or composer role. |
| musiconn/Detmold | Source related-person predicate, authority crosswalk, local entity class, creation versus performance date. Trace the two documented Person/opera cases separately. |
| APSearch | Original creation-period term, each bound, ordering/precision, unresolved values, `9009`, media classification and start-year projection. |

Assign one fidelity outcome per reviewed occurrence:

- `preserved`: supplied meaning/evidence retained, including qualifiers when
  relevant. A retained exact assertion plus a documented broad projection is
  counted here; the projection is recorded separately.
- `deliberately_generalized`: a documented, reviewed broader representation
  replaces the selected detail. Record what is lost; authorization does not make
  it exact preservation.
- `omitted`: supplied in-scope evidence has no output representation.
- `incorrectly_transformed`: wrong value, role, direction, precision or identity
  introduced by the pipeline.
- `unresolved`: required evidence is unavailable or the adjudication is pending.

Report the mutually exclusive counts over **all selected source occurrences**,
including unresolved cases. Also report distinct source assertion keys, output
observation nodes and output direct assertions to explain deduplication.
Identical duplicate inputs and inverse relationship observations can collapse;
neither occurrence count nor triple expansion is automatically information loss.

Classify each established finding separately as `source_limitation`,
`conversion_loss`, `conversion_error` or `reconciliation_error`. Leave category
`pending_trace` until the first stage introducing the discrepancy is established.
Preserve questionable source values and record anomalies without inventing
corrections. A source limitation can accompany a faithfully preserved field.
Retain authorisation/evidence for deliberate omissions or generalisations.

Use purposive edge cases first to test the machinery. For an estimated fidelity
rate, build a complete occurrence frame for each selected field/source stratum
and sample independently of outcomes. Do not treat converter fixtures or selected
bugs as an accuracy sample.

## Reconciliation: initial 60-case design

The unit is a source entity with its whole accepted target set, including an
empty set. Freeze a complete frame from the source/reconciliation export, not
from an ordered `LIMIT` over linked RDF. Record the extraction procedure,
source hash, frame hash and source-record locator. Deduplicate by a documented
stable source-entity key. A direct QID is still an accepted reconciliation
outcome and must not disappear from the frame.

Provisional allocation (60 total):

| Source/entity group | Linked | Unlinked | Method to recover from provenance |
| --- | ---: | ---: | --- |
| Weimar performer | 7 | 3 | OpenRefine/manual decision |
| MusicBrainz artist | 7 | 3 | Source-supplied Wikidata URL |
| RISM person | 7 | 3 | OpenRefine/manual decision |
| musiconn person | 7 | 3 | Authority crosswalk or residual manual match |
| Detmold person | 7 | 3 | Authority crosswalk or residual manual match |
| Detmold place | 7 | 3 | GeoNames crosswalk or residual manual match |

These are planning quotas, not known frame sizes. Split mixed matching methods
into separate strata before selection. Do not infer a matching method solely
from the final P2888 triple. Keep unknown methods explicit. If a stratum is empty,
record zero population; if it has fewer units than its quota, review all of them.
Redistribute the remaining allocation among nonempty strata before reviewing
any outcomes and retain the revised quotas. Keep the total between 50 and 100
when the available population permits. If it does not, report a smaller census.

The [sampler](sample_review.py) requires the complete-frame declaration and
positive quotas for all nonempty strata. Record a randomly chosen seed before
review, never search seeds for desirable cases. Save selected IDs and inclusion
probabilities. If manual sampling is used instead, record the exact selection
procedure and seed with equivalent evidence.

For each selected entity review independently:

- Identifier agreement: exact authority ID present, redirected/merged ID,
  disagreement, unavailable evidence or no ID. Archive the external response
  with retrieval time/checksum; one failed lookup establishes nothing.
- Identity: `correct`, `incorrect`, `uncertain` or `unreviewed`, with evidence
  about entity kind, names, dates, associated works and source context.
  Agreement is evidence, not automatically identity verification.
- For unlinked units: a verified candidate, no candidate found under the
  recorded search, or unresolved evidence. A failed search does not establish
  that Wikidata contains no matching entity.

Review source entity kinds as well as target identity. An opera typed locally
as a Person may originate in source typing, preprocessing or reconciliation;
trace it before assigning responsibility. Record reviewer and date. Have a
second reviewer adjudicate uncertain/error cases when available; otherwise
state explicitly that the review has one reviewer.

Report selected/reviewed/uncertain counts per stratum. Separate accepted-link
correctness, source-entity linking coverage and missed opportunities in unlinked
units. For linked correctness, include all selected linked units in the
denominator and give sensitivity bounds with uncertain units counted as wrong
versus correct. Do not silently exclude them. For stratum-weighted estimates,
weight by actual frame sizes and use design-appropriate uncertainty intervals;
report the method, finite-population treatment and assumptions. With sparse
strata, report counts and uncertainty instead of a precise-looking pooled rate.
No population recall estimate follows from accepted links alone.

Keep purposive anomaly cases (RISM protocol variants, APSearch `9009`, Detmold
Person/opera records) in a separate list, even if also encountered in the random
sample. A randomly selected anomaly still counts in that sample once; do not add
purposive cases to its denominator.

## Competency questions and independent answers

The [14-case catalogue](cases.json) fixes each question's meaning, manually
written SPARQL and evidence needed for review. Bindings for historical people
use canonical QIDs; Charlie Parker's lookup uses
[Q103767](https://www.wikidata.org/wiki/Q103767), and Clara Schumann's Q132232 is
documented in the earlier reliability review. Do not choose replacement people
only because their queries return rows.

Freeze expected answers from source evidence before executing the corresponding
measured query, or explicitly label a post-hoc investigation exploratory.
Record source locators, reasoning about roles/identity, expected inclusions and
exclusions, reviewer/date, and source/query version. The synthetic expected
bindings validate query logic; they are not independent expected live answers.

For bounded answer sets, distinguish a complete expectation within a defined
source-record set from a few known positive witnesses. A positive witness
validates only that row, not the completeness of an ordered 25-row result.
Compare RDF terms, not only displayed strings. Preserve multivalued attributes
and avoid counting projected rows as distinct source observations.

Record each case as supported, partly supported, unsupported by the imported
fields, or unavailable because execution/evidence failed. CQ12 deliberately
retains the unsupported Arabic/vocal/field-recording question. Its audio/date
probe is a necessary-condition diagnostic; even a nonempty result cannot answer
the full question. CQ06's negative control establishes absence of an explicit
composer assertion within the chosen graph, not historical non-composition.

CQ03 joins a track's explicit MusicBrainz UUID; a shared title, person or date
cannot replace that identifier. CQ05 joins people across RISM and musiconn
without claiming that the two sources describe the same work or that a generic
CKG person association means composer.

## Reporting and completion

Archive query/result/status files, manifests, matched source excerpts and
checksums, independent judgments, sampling frames/seeds and external responses
outside Git. Record the durable archive location in the findings report. Keep
server failures, partial results, row caps and unsupported questions visible.
The runner hashes working-tree files because Git HEAD alone does not describe
uncommitted converters.

#472 remains open until the matched source traces, 50–100-case reconciliation
review, independently checked competency answers and bounded findings exist.
The present implementation completes the protocol and query/tooling foundation.
It does not deploy RDF, establish the final paper's contribution, or replace the
pending review of the final DLfM manuscript.
