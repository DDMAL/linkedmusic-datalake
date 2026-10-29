# APSearch creation-period preservation

Implemented locally on 20 October 2026 for
[#471](https://github.com/DDMAL/linkedmusic-datalake/issues/471).
The stored dump has not been reconverted and Virtuoso has not been updated.
This is a conversion-fidelity repair; it does not repair source dates.

## Meaning and representation

The [official CTO definition](https://nfdi.fiz-karlsruhe.de/4culture/ontology/#CTO_0001073)
describes `CTO_0001073` as an approximate creation span associated with the item.
Keep that source meaning: a creation period does not independently establish
a performance date or the date of a field-recording session.

The converter now retains the original `cto:CTO_0001073` assertion, including
the literal's lexical form, datatype and language tag. A named observation
keeps each pair of year bounds together:

```turtle
@prefix ckgterm: <https://linkedmusic.ca/terms/ckg/> .
@prefix cto: <https://nfdi4culture.de/ontology/> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix wdt: <http://www.wikidata.org/prop/direct/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix ex: <https://example.org/synthetic/> .

ex:record
    cto:CTO_0001073 "1909-01-01/1950-01-01" ;
    ckgterm:creationPeriod ex:period ;
    wdt:P571 "1909"^^xsd:gYear .

ex:period a ckgterm:CreationPeriod ;
    rdf:value "1909-01-01/1950-01-01" ;
    ckgterm:startYear "1909"^^xsd:gYear ;
    ckgterm:endYear "1950"^^xsd:gYear ;
    ckgterm:parseStatus "parsed" .
```

The example shortens the actual observation IRI:
`https://linkedmusic.ca/graphs/ckg-apsearch/creation-period/{sha256}`.
Its digest covers the JSON-encoded array of normalized NT subject token,
source predicate token and complete object token, using Python `json.dumps`
with `ensure_ascii=False`, default separators, and UTF-8. Identical repeated
triples coalesce; different records, values or literal token spellings produce
different observations. These identify source assertions, not globally shared
time periods. Multiple periods on one record cannot mix their endpoints.

The `ckgterm:` vocabulary is local to LinkedMusic, not an official CTO extension.
Its terms are defined here; there is no separate schema graph to load for this
repair and no inference rule is required.

| Term and readable label | Direction / endpoints | Definition and interpretation |
| --- | --- | --- |
| `creationPeriod` — source creation period | source record → `CreationPeriod` observation | Links a record to one observed `CTO_0001073` value. Supports inspection of the source's creation span; does not assert a performance or recording-session date. |
| `CreationPeriod` — creation-period observation | class of named observations | Retained source evidence and derived year bounds. Not a claim that an activity continued throughout every year. |
| `startYear` — supplied start year | observation → `xsd:gYear` | Year extracted from the source's first endpoint. An unresolved observation can retain this alone; it does not establish a complete or ordered interval. |
| `endYear` — supplied end year | observation → `xsd:gYear` | Year extracted from the source's second endpoint. Same-year periods retain both bounds. Does not imply day precision. |
| `parseStatus` — period parse status | observation → string | `parsed`: supported form with ordered bounds at the mutually known precision. `unresolved`: unsupported, invalid, or reversed evidence. Neither is a historical accuracy judgment. |
| `reviewFlag` — source-period review flag | observation → string, repeatable | Identifies a parsing limitation or known anomaly without changing the source. See the table below. |
| `rdf:value` — retained source value | observation → original RDF term | Copies the object of the retained CTO assertion, including datatype/language. Does not replace it with a corrected date. |
| `wdt:P571` — compatibility start-year projection | source record → `xsd:gYear` | Emitted only for a `parsed` period. Summarizes its start year; cannot answer interval-overlap questions or distinguish multiple periods by itself. |

Both bounds use the source's year resolution. For overlap queries they are
inclusive. The historical APSearch profile found Jan-01 placeholders, not
evidence of precise January 1 creation dates. The raw source term still retains
every supplied component.

## Supported inputs and review flags

Supported forms are a bare positive four-digit year, or two endpoints separated
by `/`. Each endpoint can be a year, a Jan-01 date, or a Jan-01 date with the
observed `T00:00:00` start / `T23:59:59` end time. `YYYY-00-00` and valid
`YYYY-MM-00` preserve the known year without inventing month/day values.
A single year or supported date supplies the same year for both bounds.

| Input condition | Treatment |
| --- | --- |
| Valid non-placeholder dates/times | Preserve extractable years and raw evidence; mark `unexpected-precision-start` / `-end`, status `unresolved`, pending review of the changed source shape. |
| Missing year, free text, open end, timezone/fractional timestamp or other unsupported syntax | Keep the raw value and any independently supported endpoint; `unrecognized-start` / `-end`. A missing bound is not interpreted as infinity. |
| More than one slash | Raw value retained; `unrecognized-interval`; no guessed endpoints. |
| Invalid calendar date/time or year `0000` | Retain the raw value, withhold the invalid bound, mark `invalid-start` / `-end`. |
| Reversed bounds | Retain both years in source order, mark `reversed-interval`. Never swap them. Comparison includes mutually known month/day/time components. |
| Language-tagged literal / IRI object | Preserve the RDF term; mark `language-tagged` / `non-literal`; no year projection. Unexpected blank-node objects stop conversion for inspection. |
| Year `9009` | Keep `9009` and mark `year-9009`. An otherwise parseable, ordered period remains `parsed` and keeps its compatibility projection. The flag is a known source-tracing case, not a general anomaly detector or an inferred correction to 2009. |

Every unresolved period remains in RDF with its source evidence. It has no
P571 projection. This differs deliberately from the old permissive fallback,
which could turn a malformed or reversed interval into an apparently ordinary
inception year.

## Query and offline validation

Use [creation_period_overlap.rq](queries/creation_period_overlap.rq) for the full
interval. It casts the lexical `gYear` values to integers, selects `parsed`
periods, and returns review flags alongside evidence. Change its staging graph
IRI and the requested year for the deployment being tested.

An interval from 1909 through 1950 matches 1909, 1940 and 1950, and excludes
1960. Matching means the supplied creation span includes that year, not proof
that an event took place in that year. Unknown and reversed periods are excluded
from this particular query, but remain inspectable in the graph.

From the repository root:

```bash
poetry run python -m unittest discover -s ckg-apsearch/tests -v
```

Eleven offline tests cover source-term preservation, year precision, invalid
and reversed values, the `9009` flag, multiple periods and duplicate collapse,
named-graph overlap queries, audit denominators, legacy feed dates, and equality
of all three shared converter/configuration copies. Fixtures are synthetic;
generated NT/Turtle and audit files live in temporary directories.

A separate normal-CLI smoke test on 20 October 2026 emitted 78 triples for
9 synthetic creation-period occurrences: 8 distinct observations, 1 duplicate,
4 parsed and 4 unresolved observations, 6 retained start bounds, 6 retained end
bounds, and 5 flagged observations. Five musiconn and six Detmold synthetic
records produced byte-identical Turtle with the previous converter at
`c468e947`. This is bounded fixture evidence, not full-dump validation.
The smoke-test inputs, output, audit and comparison report were first saved to
`/tmp/linkedmusic-preservation-2026-10-20/apsearch/`, then copied and
checksum-verified under `evaluation/audits/handoff-2026-10-20/preservation/apsearch/`.
The handoff manifest records the copies. These ignored files are local evidence,
not a remote backup or a prerequisite for the synthetic tests.

## Audit denominators

Each APSearch conversion writes `apsearch.creation-period-audit.json` beside
the Turtle. It records a UTC generation timestamp, model version, hashes of the
normalized input, converter, runtime predicate map and generated Turtle, and:

- `input_occurrences`: creation-period triples encountered on non-blank-node
  subjects, including exact duplicates.
- `distinct_periods`, `duplicate_occurrences`: named source observations and
  duplicate input occurrences. Their sum equals `input_occurrences`.
- `parsed`, `unresolved`: distinct observations in each status; their sum equals
  `distinct_periods`.
- `startYear`, `endYear`: distinct observations retaining each bound, including
  bounds on unresolved periods. Each denominator is `distinct_periods`.
- `flagged_periods` and `review_flags`: observations with any flag and counts
  per flag. Several flags can apply to one observation, so flag counts need
  not sum to `flagged_periods`.

`source_snapshot_date` stays null because the converter cannot derive it from
the input. Record the actual source snapshot date in a separate run manifest;
do not substitute the conversion timestamp. Record the raw dump checksum and
all other conversion inputs there as well.

The historical 4,214 intervals / 128 multi-year intervals are prior snapshot
observations. They are not new measurements, current production counts, or
acceptance thresholds for another dump.

## Regeneration and reload

1. On the machine holding the E6304 snapshot, record its date and raw checksum,
   the Git revision and whether the checkout is clean, Python/dependency
   versions, and checksums of normalized NT, entity index, `crosswalk.json`,
   `record_types.json` and `ontology/mapping.json`. Retain the original source.
2. From `ckg-apsearch/src/`, convert to a **new** output directory:

   ```bash
   poetry run python convert_to_rdf.py apsearch \
     --extracted /absolute/path/to/extracted \
     --mappings /absolute/path/to/mappings \
     --outdir /absolute/path/to/new-apsearch-candidate
   ```

3. Check successful completion and the audit's output checksum. Parse the
   Turtle and compare the retained `CTO_0001073` assertions to normalized source
   terms. Review all unresolved/flagged observations; report actual source
   occurrences, distinct periods, preserved bounds and projections with dated
   denominators. Do not assume every future snapshot has Jan-01 placeholders.
   Verify record, type, URL and reconciliation counts against the same source.
   The old ~46,203-triple total excludes the new preservation triples.
4. Back up the production APSearch graph. Load the candidate into a separate
   staging graph, adapt the documented overlap query to that graph, and check
   both positive and negative answers against source examples. Inspect original
   literals, year bounds, flags, projection counts and zero blank nodes.
5. After staging review, replace the production APSearch graph using the wiki's
   Virtuoso procedure. Do not append blindly: old invalid P571 projections could
   otherwise survive. This change does not require reloading musiconn/Detmold.
6. Repeat the checks on production and record the deployment date, graph IRIs,
   source snapshot, conversion revision, audit and rollback snapshot in the
   handoff. Keep #471 open until the stored-snapshot check and deployment
   disposition are recorded (or explicitly tracked in a linked follow-up).

The three converter copies are intentionally identical. The new preservation
branch runs only for APSearch `CTO_0001073`; musiconn/Detmold retain their date
coercion and output shape. Later SESEMMI integration must explicitly ingest this
model and the overlap query; no SESEMMI changes are included here.
