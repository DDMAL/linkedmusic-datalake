# Identified CKG candidate validation

All three candidates were generated from the inputs below at commit
`5e47df31c29b16e2d25fdf54a8c5d03c9e9dde03`. The shared `convert_to_rdf.py`
had SHA-256 `c7c0799bbee8303cdf4a389eeb3146d8b7aaf9cc157fe3f110df9d7833937fdf`.
The measurements cover these candidate files and their stored comparators.
Source snapshot dates are unknown. The original files had matching checksums
before and after conversion.

| Feed | Raw N-Triples SHA-256 | Candidate Turtle SHA-256 |
| --- | --- | --- |
| apsearch | `4579a5cec820d87a7d3838e014176c85c6c6c68a863903134e3ee45cf663e891` | `30b6d00639b4dc2ab4324a1dee92ec465e43455aa1b98b3b50b3a673b01dbcc9` |
| detmold | `4caf2e43df638179edf46a1316842ed3457b3db9d4aaa40d05fa73e8f04180c6` | `2664a06733167d5a8f08b37c8d63eec76a35d9e15dedaf79f9590e86b2135bea` |
| musiconn | `f80b33b466b3f4cc9e62b0df002f662f492f81732608979dd345e9b02b40995d` | `3ea0108c9027723930510178d0e049885467050f2119d5290b67bf043c8b8d1a` |

APSearch's stored baseline has SHA-256
`553f835c2661eb31660adfb59c8e330178ac7232b4e7051862d2512ce11c1b28`.
The candidate preserves all 4,214 distinct source creation-period assertions and
has one paired observation for each. Its 75,702 distinct triples are exactly the
46,203 baseline triples plus 29,499 preservation triples: no baseline triple was
removed and no unrelated triple changed. The source period for “Sudan Situation”
has both bounds in `9009`. Its observation carries the `year-9009` review flag.
A query selecting only `wdt:P571` returns `9009` without the flag.

The independently parsed source intervals and the documented named-graph query
agree on these record sets:

| Requested year | Source-derived records | Candidate-query records |
| --- | ---: | ---: |
| 1909 | 111 | 111 |
| 1940 | 109 | 109 |
| 1950 | 108 | 108 |
| 1960 | 0 | 0 |
| 9009 | 1 | 1 |

This E6304 input contains no temporal-coverage (`CTO_0001070`) triples.
The comparison is specific to this source's January-01 creation-period syntax. It
checks inclusive year overlap, not events occurring in each year. Other syntax
is covered by synthetic tests rather than inferred from these measurements.

Detmold's candidate has 14,835 statements and equals its stored baseline as an
RDF set (serialization order differs). musiconn's 1,588,653-statement candidate
is byte-identical to its stored baseline. Both comparisons use the corresponding
raw input and candidate hashes above; source/classifier/crosswalk changes are
outside this result.

To reproduce, use the identified N-Triples files and matching mapping/name inputs,
run preprocessing and conversion into new directories as described in the
[creation-period contract](creation-period-preservation.md), and retain every
command and file hash. The converter audit records the normalized input, entity
index, crosswalk, record types, optional names, runtime and output identity.
Compare source `CTO_0001073` RDF terms with retained terms, match each observation's
`rdf:value` to its source record, check both bounds against the supplied endpoints,
and compare all other triples with the baseline as RDF sets. Load the candidate
only into a local named-graph dataset to run the [overlap query](queries/creation_period_overlap.rq).
A successful local query is not evidence about a production endpoint.

## Mapping and runtime identity

The original auxiliary inputs were unchanged from the preserved inventory.

| Feed | Crosswalk SHA-256 | Record-type map SHA-256 |
| --- | --- | --- |
| apsearch | `79f32b9146efce0b5a02268f327630ea25d5c349f3d4b0410e4adf2ee51828fd` | `53ff13d95191b7faaa604c62d0493a2befe9aa460b345e785b5bcb67cd2fb706` |
| detmold | `79f32b9146efce0b5a02268f327630ea25d5c349f3d4b0410e4adf2ee51828fd` | `53ff13d95191b7faaa604c62d0493a2befe9aa460b345e785b5bcb67cd2fb706` |
| musiconn | `79f32b9146efce0b5a02268f327630ea25d5c349f3d4b0410e4adf2ee51828fd` | `53ff13d95191b7faaa604c62d0493a2befe9aa460b345e785b5bcb67cd2fb706` |

The shared authority-name CSV has SHA-256 `6cc107c69fbab358d2951728cdc7e886fbb83a619c91185e3da376549c9ce9c7`.
Python 3.12.7, rdflib 7.1.4 and PyOxigraph 0.4.11
were used; the dependency lock SHA-256 is `666ce0ecf4f21d7430e1a684350273610c0cdc5ae25da739d26ab5220fbe6a2e`.
No authority lookups or live endpoint queries were needed for this comparison.
