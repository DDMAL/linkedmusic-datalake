# MusicBrainz URL relationships

In the JSON dumps, each external link has two parts. The relationship's
`type` describes why MusicBrainz links to the page, and `url.resource`
contains its address. A single host can serve pages about different subjects.
For example, Cher's artist record links to three Wikidata items:

| MusicBrainz relationship | Item | What the RDF says |
| --- | --- | --- |
| `wikidata` | Q12003, Cher | The MusicBrainz artist has this Wikidata exact match. |
| `discography page` | Q2604791, albums discography | The artist has an albums discography at this address. |
| `discography page` | Q5264608, singles discography | The artist has a singles discography at this address. |

These roles come from the artist's [MusicBrainz API record](https://musicbrainz.org/ws/2/artist/bfcc6d75-a6a5-4bc6-8282-47aec8531818?inc=url-rels&fmt=json).
MusicBrainz defines the [artist Wikidata relationship](https://musicbrainz.org/relationship/689870a4-a1e4-4912-b17f-7b2664215698)
and [discography page relationship](https://musicbrainz.org/relationship/4fb0eeec-a6eb-4ae3-ad52-b55765b94e8f) separately.

## Exact matches

The converter emits `wdt:P2888` on the original MusicBrainz entity when:

- The source relationship is named `wikidata` and MusicBrainz defines it
  for this kind of entity. If supplied, its type UUID and direction must
  agree with the definition. Older input can supply the name alone.
  A release group and its individual releases are distinct entity kinds.
  See the [MusicBrainz relationship definitions](https://musicbrainz.org/relationships).
- The relationship has no end date and is not marked as ended.
- The complete address matches `http` or `https`, host `wikidata.org` or
  `www.wikidata.org`, and path `/wiki/Q…` or `/entity/Q…`. The digits
  after Q must be ASCII, positive and free of leading zeros. Case matters.
  Ports, query strings, fragments and trailing slashes fall outside this rule.

The exact-match object uses the canonical spelling, for example
`http://www.wikidata.org/entity/Q12003`. Distinct qualifying items remain
separate claims. The converter performs no lookup or editorial reconciliation.

## Retrieving the original links

Every URL relationship has an observation with the original MusicBrainz JSON in
`mb:sourcePayload` and, when supplied as strings, its role in `mb:sourceTypeName`,
type UUID in `mb:sourceTypeId` and address in `mb:urlTarget`. The observation
identifier depends on the source entity and the complete relationship. Different
roles or qualifiers on the same address remain distinguishable after serialization.

An absolute HTTP(S) address becomes an RDF link when it has a host, a valid
port if supplied, no whitespace, and Oxigraph accepts the original spelling as
an IRI. Both in-memory and disk-backed conversion use this rule. For example,
`https://[::1]/catalog` remains a link, while `https://example.org/a[1]`
stays queryable as the original text in `mb:urlTarget`. Other schemes,
relative strings and malformed addresses are also retained as text. A
missing or non-string address remains available in the source JSON. Official
homepages, streaming links, discographies and unfamiliar roles are retrievable
by their MusicBrainz names. For example:

```sparql
PREFIX mb: <https://linkedmusic.ca/terms/musicbrainz/>
SELECT ?page WHERE {
  <https://musicbrainz.org/artist/bfcc6d75-a6a5-4bc6-8282-47aec8531818>
      mb:urlRelationship ?relation .
  ?relation mb:sourceTypeName "discography page" ; mb:urlTarget ?page .
}
```

The [regression tests](../tests/test_url_recognition.py) exercise the JSON
converter, Turtle serialization and the distinction between these query paths.
The separate [CSV contract](auxiliary_identifier_validation.md) covers bare
item IDs assigned during reconciliation of descriptive fields. Existing RDF
retains the behavior of the converter that generated it. Reproducing counts or
regenerating a graph requires the corresponding source snapshot.
