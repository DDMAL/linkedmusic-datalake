# Approximate dates across databases

If a catalogue says **“c. 1850”**, a user should be able to search for the year
1850 and still see **“around 1850”** in the answer. Keep the source wording, a
searchable year and the approximation flag together on the observation for
that particular date. A person's birth and death can have different flags.

The Boolean property is `lm:dateApproximate`, where `lm:` expands to
`https://linkedmusic.ca/terms/preservation/`. A dataset can use the property
directly or align an existing property with `rdfs:subPropertyOf`, as DIAMM
does. Each dataset documents how to reach the observation and identify the
event, the original evidence and the typed value. See the
[RDF definition](preservation.ttl) and [RDFS subproperty semantics](https://www.w3.org/TR/rdf-schema/#ch_subpropertyof).

| What the source supplies | RDF on the observation | What an answer can say |
| --- | --- | --- |
| `c. 1850` in a field where `c.` means “circa”, or year `1850` and an explicit approximate flag | Original evidence, `"1850"^^xsd:gYear`, Boolean `true` | “The catalogue gives the birth year as around 1850.” |
| Year `1850` and an explicit non-approximate flag | Original evidence, the same typed year, Boolean `false` | “The catalogue gives 1850 as the birth year.” The precision is one year. |
| Year `1850` with no interpretable flag or convention for unmarked values | Original evidence and the typed year. Omit the Boolean. | “The catalogue lists 1850. It does not say whether that year is approximate.” |

A documented source convention may establish the meaning of an unmarked year.
Without one, preserve its unknown status. For free text, document the accepted
whole-field forms and their meanings before parsing them. Preserve unrecognised
text for display. Expressions such as `before 1850`, `1850–1860` and
`1850?` need their own interpretation. Keep bounds where the source supplies
them. A circa marker alone supplies no earliest year, latest year, day of the
month or confidence percentage. PROV-O can identify where evidence came from.

## A catalogue with a free-text birth year

This illustrative catalogue recognises `c. YYYY` in its birth-year column.
Its example IRIs stand for the catalogue's own fields. In its named graph
`ex:catalogue`, it could emit the following Turtle.

```turtle
@prefix ex: <https://example.org/> .
@prefix lm: <https://linkedmusic.ca/terms/preservation/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

ex:person7 ex:birthDateObservation ex:birth7 .
ex:birth7 a lm:EvidenceObservation ;
    ex:sourceText "c. 1850" ;
    ex:year "1850"^^xsd:gYear ;
    lm:dateApproximate true .
```

DIAMM has two source cells for this purpose. Its candidate converter keeps
the original year and flag on a `diamm:PersonYearObservation` and emits
`diamm:approximate` when it can interpret the flag. Query the observation to
include approximate and unknown-status years. The direct person birth/death
triples cover only years explicitly flagged non-approximate.
[DIAMM source fields and conversion rules](../../diamm/doc/person_years.md)

## A query across both catalogues

This example retrieves each source's recorded birth years, including those
with an unknown approximation status. It names the predicates emitted in each
graph, so it works with inference disabled and the default graph empty.
Substitute the graph and field names from each enabled dataset's profile.

```sparql
PREFIX diamm: <https://linkedmusic.ca/graphs/diamm/>
PREFIX ex: <https://example.org/>
PREFIX lm: <https://linkedmusic.ca/terms/preservation/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>

SELECT ?graph ?person ?obs ?raw ?year ?approximate WHERE {
  {
    GRAPH diamm: {
      ?person diamm:personYear ?obs .
      ?obs diamm:dateProperty wdt:P569 ; diamm:sourceValue ?raw ; diamm:year ?year .
      OPTIONAL { ?obs diamm:approximate ?approximate }
    }
    BIND(diamm: AS ?graph)
  } UNION {
    GRAPH ex:catalogue {
      ?person ex:birthDateObservation ?obs .
      ?obs ex:sourceText ?raw ; ex:year ?year .
      OPTIONAL { ?obs lm:dateApproximate ?approximate }
    }
    BIND(ex:catalogue AS ?graph)
  }
}
```

For “which birth years does the catalogue mark approximate?”, add
`FILTER(?approximate = true)` after the `UNION`, inside the outer `WHERE`.
Use `= false` for explicitly non-approximate years and `!BOUND(?approximate)`
for unknown status. To answer “Who was born near 1850?”, the search needs
a defined year range regardless of which years carry a
circa flag. Preserve conflicting observations and attribute each to its source.

## Using the property in SESEMMI

SESEMMI selects a database and passes a subset of its schema to the model.
When enabling a graph version with person-year observations, merge the
[DIAMM context fragment](date_approximation_nlq.txt) into its
`ONTOLOGY_CHUNKS["diamm"]` entry. Append the query notes to the existing notes,
add the `personYear` edge to the existing Person block and add the observation
class to the same ontology block. Retrieve both classes for person-date
questions so the model sees the stored predicates and their meanings.
For each additional database, supply its own field paths and graph version.
The example.org catalogue above is a teaching example.
[SESEMMI schema corpus](https://github.com/DDMAL/SESEMMI/blob/94037d3db5c322908aa27e681602b7cfa57d2a51/llm-service/app/graph/schema_corpus.py)
and [class selection and retrieval](https://github.com/DDMAL/SESEMMI/blob/94037d3db5c322908aa27e681602b7cfa57d2a51/llm-service/app/graph/nodes/retrieve.py).

For acceptance, ask for birth years in a fixture with all three flag states
and a separate death year. Check that the query returns the three birth rows,
keeps the flag optional and excludes the death year. In the answer, the
approximate row should say “around”, the false row should keep year precision,
and the missing flag should remain unknown. A second question restricted to
source-marked approximate years should return only the true row.
