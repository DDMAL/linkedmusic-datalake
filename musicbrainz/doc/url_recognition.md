# Wikidata URL recognition

The URL-relationship branch of `process_entity` in `src/convert_to_rdf.py`
recognizes complete Wikidata item URLs. MusicBrainz subjects and entity-to-entity
relationships remain source IRIs; normalization adds no identity inference or
new reconciliation. See the [identifier guide](../../evaluation/identifier_review.md).

## Evidence and accepted input

The tracked converter reads `relations[].url.resource` when `target-type` is
`url` and a relationship `type` is present. The existing
[`mappings.json`](../src/rdf_conversion_config/mappings.json) assigns these URL
relationships to P2888. The [conversion guide](rdf_conversion.md#urls) specifies
that recognized Wikidata links are IRIs and other URL values remain literals.
That broader P2888 policy is unchanged by this narrowly scoped repair.

The project's canonical item namespace is
`http://www.wikidata.org/entity/`. Only complete recognized URL forms are
normalized; this checks syntax, not item existence or reconciliation identity.

| Input | Output object of P2888 |
| --- | --- |
| HTTP/HTTPS, `www.wikidata.org` or `wikidata.org`, `/wiki/Q42` or `/entity/Q42` | IRI `http://www.wikidata.org/entity/Q42` |
| Canonical entity IRI supplied again as a URL | Same canonical IRI |
| External URL, lookalike host, query/fragment, suffix or trailing slash | Literal containing the original value |
| `Q0`, `Q042`, non-ASCII digits, whitespace or newline in a URL | Original literal |
| Property URLs, Special:EntityData URLs, explicit ports or percent-encoded IDs | Original literal; not part of this item-URL contract |
| Bare `Q42`, `wd:Q42`, ambiguous lists or prose in the URL field | Original literal; no substring extraction |

Matching is case-sensitive and requires the entire value. The QID must contain
positive ASCII digits with no leading zero. No redirects, stripping, decoding,
network lookups or case folding occur. Ordinary name fields remain literal even
when their complete value is an accepted item URL. Multiple distinct P2888
targets survive; conversion does not resolve competing matches.

## Validation and limits

Four [regression tests](../tests/test_url_recognition.py) call the actual entity
converter using tracked field and relationship mappings. They check all eight
accepted URL combinations, idempotence, malformed/external values, unchanged
name literals, multiple targets and source-node retention. Exact expected
triples, a Turtle round trip and a SPARQL join to canonical Q42 are independently
specified. Run the controls from the repository root:

```sh
poetry run python -m unittest discover -s musicbrainz/tests -v
poetry run python scripts/check_offline.py
```

These synthetic controls do not measure URL forms or affected links in a
stored or deployed population. For a matched source snapshot, record checksums and converter versions,
count accepted/rejected forms against source cells, regenerate into a separate
directory, and verify canonical joins and preserved literal targets in staging.
Do not rewrite stored literal values globally or infer names from old IDs.

The auxiliary CSV `matched_wikidata` helper follows its separate
[bare-ID export contract](auxiliary_identifier_validation.md).
It serves reconciled types, keys, genders, languages, packaging and statuses;
full URLs remain outside that contract. Other URL-to-P2888 semantics,
relationship roles, SESEMMI and production inference settings remain unchanged.
