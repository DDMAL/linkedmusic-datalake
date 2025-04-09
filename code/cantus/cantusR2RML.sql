--the Name of the R2RML Graph:
SPARQL CLEAR GRAPH <http://temp/product>;
--the Name of the Graph:
SPARQL CLEAR GRAPH <http://example.com/trial>;

DB.DBA.TTLP ('
@prefix rr: <http://www.w3.org/ns/r2rml#> .
@prefix cantusDB: <https://cantusdatabase.org/> .
@prefix schema: <http://schema.org/> .
@prefix wdt: <http://www.wikidata.org/prop/direct/> .

<http://example.com/ns#TriplesMap1>
    a rr:TriplesMap;

    rr:logicalTable
    [
      rr:tableSchema "CSV2RDF_Sample";
      rr:tableOwner "DBA";
      rr:tableName "sampleCantusChant_csv"
    ];

    rr:subjectMap
    [
      rr:template "https://cantusdatabase.org/chant/{Chant_ID}";
      rr:class cantusDB:chant;
      rr:graph <http://example.com/trial>;
    ];

    rr:predicateObjectMap
    [
      rr:predicate wdt:P1922;
      rr:objectMap [ rr:column "incipit" ];
    ];

    rr:predicateObjectMap
    [
      rr:predicate wdt:P136;
      rr:objectMap [ rr:column "genre" ];
    ];

    rr:predicateObjectMap
    [
      rr:predicate cantusDB:sources;
      rr:objectMap [ rr:column "src_link" ];
    ];
.
', 'http://temp/product', 'http://temp/product' )
;


exec ('sparql ' || DB.DBA.R2RML_MAKE_QM_FROM_G ('http://temp/product'));

--sparql select distinct ?g where { graph ?g { ?s a ?t }};

SPARQL
SELECT * FROM <http://example.com/trial>
WHERE {?s ?p ?o .};