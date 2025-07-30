## Instructions

VERY IMPORTANT:
"Relevant Ontology" must be extracted from ## Context - Full Ontology. The Wikidata properties in the full ontology with the closest matching semantic meaning must be selected.
"SPARQL Query" must be as simple as possible. It must be beautiful, elegant, and perfect.

- Ensure all spaces are standard spaces (ASCII 32).
- Don't use an alias in ORDER BY—repeat the full aggregate expression instead.

THANK YOU FOR YOUR ATTENTION

## Example 1

Natural Language Question: Find all compositions in DIAMM that were composed by Antonio il Verso

Graph: Single Graph (diamm:)
All ontology must belong in diamm: subgraph.
Federated query is not needed because all information can be retrieved from diamm: subgraph.

Relevant Ontology:

```ttl
diamm:Composition
  wdt:P86 diamm:Person ; # object is a diamm:Person
diamm:Person
  wdt:P2888 "exact match" . # object is a Wikidata Entity
```

SPARQL Query:

```SPARQL
SELECT DISTINCT ?composition
WHERE {
  GRAPH diamm: {
    ?composer wdt:P2888 wd:Q2857523 . # QID for Antonio il Verso
    ?composition wdt:P86 ?composer .
  }
}
```

## Example 2

Natural Language Question: Find all solos in Dig That Lick that were recorded in New York City in 1929

Graph: Single Graph (dtl:)
All ontology must belong in dtl: subgraph.
Federated query is not needed because all information can be retrieved from dtl: subgraph.

Relevant Ontology:

```ttl
dtl:Track
  wdt:P8546 "recording location" ; # object is a Wikidata Entity
  wdt:P10135 "recording date" . # object is a xsd:date
dtl:Solo
  wdt:P361 dtl:Track . # object is a dtl:Track
```

SPARQL Query

```SPARQL
SELECT DISTINCT ?solo
WHERE {
  GRAPH dtl: {
    ?track a dtl:Track ;
           wdt:P8546 wd:Q60 ; # QID for New York City
           wdt:P10135 ?recordingDate .
    ?solo wdt:P361 ?track .
    FILTER (SUBSTR(STR(?recordingDate), 1, 4) = "1929")
  }
}
```

## Example 3

Natural Language Question: Return all the different instruments used by ensembles in the Global Jukebox

Graph: Single Graph (gj:)
All ontology must belong in gj: subgraph.
Federated query is not needed because all information can be retrieved from gj: subgraph.

Relevant Ontology:

```ttl
gj:Ensemble
  wdt:P870 "instrumentation" . # object is a Wikidata Entity
```

SPARQL Query:

```SPARQL
SELECT DISTINCT ?instrument WHERE {
 ?ensemble a gj:Ensemble.
 ?ensemble wdt:P870 ?instrument.
}
```

## Example 4

Natural Language Question: Find all Global Jukebox cultures from Africa

Graph: Single Graph (gj:) + Federated Query to Wikidata
All ontology must belong in gj: subgraph.
Federated query is needed to retrieve additional information from Wikidata.

Relevant Ontology:

```ttl
gj:Culture
  wdt:P17 "country" . # object is a Wikidata Entity
```

SPARQL Query:

```SPARQL
SELECT ?culture ?country
WHERE {
  ?culture a gj:Culture .
  ?culture wdt:P17 ?country .

  SERVICE <https://query.wikidata.org/sparql> {
    ?country wdt:P30 wd:Q15 . # QID for Africa
  }
}
```

## Example 5

Natural Language Question: Find all The Session recordings that contain a tune that has a setting in A major

Graph: Single Graph (ts:)
All ontology must belong in ts: subgraph.
Federated query is not needed because all information can be retrieved from ts: subgraph.

Relevant Ontology:

```ttl
ts:Recording
  wdt:P658 ts:Tune . # object is a ts:Tune
ts:Tune
  wdt:P747 ts:TuneSetting . # object is a ts:TuneSetting
ts:TuneSetting
  wdt:P826 "tonality" . # object is a Wikidata Entity
```

SPARQL Query:

```SPARQL
SELECT DISTINCT ?recording ?recordingLabel
WHERE {
    ?recording rdf:type ts:Recording .
    ?recording wdt:P658 ?tune .
    ?tune wdt:P747 ?tuneSetting .
    ?tuneSetting wdt:P826 wd:Q277793 . # QID for A Major
    ?recording rdfs:label ?recordingLabel .
}
```

## Example 6

Natural Language Question: On MusicBrainz, what's the average number of releases per decade for jazz pianists born in New York City?

Graph: Single Graph (mb:) + Wikidata Federated Query (SERVICE)
All ontology must belong in mb: subgraph.
Federated query to Wikidata is needed because mb: subgraph does not contain all needed information.

Relevant Ontology:

```ttl
mb:Artist
  rdf:type mb:Artist ;
  wdt:P19 mb:Area ; # object is a mb:Area
  wdt:P136 mb:Genre ; # object is a mb:Genre
  wdt:P2888 "exact match" . # object is a Wikidata Entity

mb:Genre
  wdt:P2888 "exact match" . # object is a Wikidata Entity

mb:Area
  wdt:P2888 "exact match" . # object is a Wikidata Entity

mb:Release
  rdf:type mb:Release ;
  wdt:P175 mb:Artist ; # object is a mb:Artist
  wdt:P577 "publication date" . # object is a xsd:date
```

SPARQL Query:

```SPARQL
SELECT (AVG(?decadeReleaseCount) AS ?avgReleasesPerDecade)
WHERE {
  {
    SELECT ?decade (COUNT(DISTINCT ?release) AS ?decadeReleaseCount)
    WHERE {
      {
        SELECT DISTINCT ?artist ?artistWikidata WHERE {
            GRAPH mb: {
                ?artist rdf:type mb:Artist .
                ?artist wdt:P19 ?birthplace .
                ?birthplace rdf:type mb:Area .
                ?birthplace wdt:P2888 wd:Q60 . # QID for New York City

                ?artist wdt:P136 ?genre .
                ?genre rdf:type mb:Genre .
                ?genre wdt:P2888 wd:Q8341 . # QID for Jazz

                ?artist wdt:P2888 ?artistWikidata .
            }
        }
      }
      SERVICE <https://query.wikidata.org/sparql> {
        ?artistWikidata wdt:P106 wd:Q486748 . # QID for Pianist
      }

      # Find all releases by these artists
      GRAPH mb: {
        ?release rdf:type mb:Release .
        ?release wdt:P175 ?artist .
        ?release wdt:P577 ?publicationDate .
      }

      # Calculate the decade from the publication date
      BIND(FLOOR(YEAR(?publicationDate) / 10) * 10 AS ?decade)
    }
    GROUP BY ?decade
  }
}
```

## You must complete the output below

Natural Language Question: Count how many session each country has in the Session.

Graph:

Relevant Ontology:

SPARQL Query:

## Context - Full Ontology

```
@prefix rdfs:        <http://www.w3.org/2000/01/rdf-schema#> .
@prefix mb:        <https://linkedmusic.ca/graphs/musicbrainz/> .
@prefix wdt:        <http://www.wikidata.org/prop/direct/> .
@prefix skos:        <http://www.w3.org/2004/02/skos/core#> .
@prefix dtl:        <https://linkedmusic.ca/graphs/dig-that-lick/> .
@prefix gj:        <https://linkedmusic.ca/graphs/theglobaljukebox/> .
@prefix ts:        <https://linkedmusic.ca/graphs/thesession/> .
@prefix diamm:        <https://linkedmusic.ca/graphs/diamm/> .

mb:Area
        rdfs:label        "label" ;
        wdt:P136        mb:Genre ;
        wdt:P2888        "exact match" ;
        wdt:P31        "instance of" ;
        wdt:P571        "inception" ;
        wdt:P576        "dissolved, abolished or demolished date" ;
        wdt:P131        mb:Area ;
        wdt:P85        mb:Work ;
        skos:altLabel        "alt label" .
mb:Artist
        rdfs:label        "label" ;
        wdt:P1066        mb:Artist ;
        wdt:P108        mb:Artist , mb:Label , mb:Place ;
        wdt:P123        mb:Label ;
        wdt:P127        mb:Place ;
        wdt:P1344        mb:Event ;
        wdt:P136        mb:Genre ;
        wdt:P138        mb:Artist , mb:Label , mb:Place , mb:ReleaseGroup , mb:Work ;
        wdt:P1416        mb:Place ;
        wdt:P21        "sex or gender" ;
        wdt:P26        mb:Artist ;
        wdt:P264        mb:Label ;
        wdt:P2652        mb:Artist ;
        wdt:P27        mb:Area ;
        wdt:P2888        "exact match" ;
        wdt:P31        "instance of" ;
        wdt:P3174        mb:Artist ;
        wdt:P3300        mb:Artist ;
        wdt:P3373        mb:Artist ;
        wdt:P361        mb:Artist , mb:Series ;
        wdt:P40        mb:Artist ;
        wdt:P451        mb:Artist ;
        wdt:P521        mb:Artist ;
        wdt:P527        mb:Artist ;
        wdt:P569        "date of birth" ;
        wdt:P570        "date of death" ;
        wdt:P571        "inception" ;
        wdt:P576        "dissolved, abolished or demolished date" ;
        wdt:P69        mb:Place ;
        wdt:P725        mb:Artist ;
        wdt:P742        mb:Artist ;
        wdt:P825        mb:Artist ;
        wdt:P8810        mb:Artist ;
        wdt:P972        mb:Series ;
        wdt:P57        mb:Place ;
        wdt:P19        mb:Area ;
        wdt:P20        mb:Area ;
        wdt:P740        mb:Area ;
        skos:altLabel        "alt label" .
mb:Event
        rdfs:label        "label" ;
        wdt:P136        mb:Genre ;
        wdt:P2888        "exact match" ;
        wdt:P31        "instance of" ;
        wdt:P3300        mb:Artist ;
        wdt:P527        mb:Event ;
        wdt:P1365        mb:Event ;
        wdt:P1366        mb:Event ;
        wdt:P110        mb:Artist ;
        wdt:P12484        mb:Artist ;
        wdt:P144        mb:Recording , mb:Release , mb:ReleaseGroup ;
        wdt:P170        mb:Artist ;
        wdt:P175        mb:Artist ;
        wdt:P179        mb:Series ;
        wdt:P2550        mb:ReleaseGroup ;
        wdt:P276        mb:Area , mb:Place ;
        wdt:P287        mb:Artist ;
        wdt:P371        mb:Artist ;
        wdt:P5028        mb:Artist ;
        wdt:P580        "start time" ;
        wdt:P582        "end time" ;
        wdt:P585        "point in time" ;
        wdt:P664        mb:Label ;
        wdt:P710        mb:Artist ;
        wdt:P915        mb:Recording ;
        skos:altLabel        "alt label" .
mb:Genre
        rdfs:label        "label" ;
        wdt:P138        mb:Artist , mb:Area , mb:Label , mb:Place , mb:ReleaseGroup ;
        wdt:P2888        "exact match" ;
        wdt:P495        mb:Area .
mb:Instrument
        rdfs:label        "label" ;
        wdt:P136        mb:Genre ;
        wdt:P2888        "exact match" ;
        wdt:P31        "instance of" ;
        wdt:P527        mb:Instrument ;
        wdt:P1531        mb:Instrument ;
        wdt:P155        mb:Instrument ;
        wdt:P156        mb:Instrument ;
        wdt:P279        mb:Instrument ;
        wdt:P61        mb:Artist , mb:Label ;
        wdt:P7084        mb:Instrument ;
        wdt:P495        mb:Area ;
        skos:altLabel        "alt label" .
mb:Label
        rdfs:label        "label" ;
        wdt:P127        mb:Artist ;
        wdt:P136        mb:Genre ;
        wdt:P138        mb:Work ;
        wdt:P2888        "exact match" ;
        wdt:P31        "instance of" ;
        wdt:P571        "inception" ;
        wdt:P576        "dissolved, abolished or demolished date" ;
        wdt:P112        mb:Artist ;
        wdt:P159        mb:Area ;
        wdt:P17        mb:Area ;
        wdt:P750        mb:Label ;
        wdt:P9237        mb:Label ;
        wdt:P1365        mb:Label ;
        wdt:P1366        mb:Label ;
        wdt:P355        mb:Label ;
        wdt:P749        mb:Label ;
        skos:altLabel        "alt label" .
mb:Place
        rdfs:label        "label" ;
        wdt:P127        mb:Artist , mb:Label ;
        wdt:P136        mb:Genre ;
        wdt:P138        mb:Artist ;
        wdt:P2888        "exact match" ;
        wdt:P31        "instance of" ;
        wdt:P361        mb:Place ;
        wdt:P527        mb:Place ;
        wdt:P571        "inception" ;
        wdt:P576        "dissolved, abolished or demolished date" ;
        wdt:P825        mb:Work ;
        wdt:P131        mb:Area ;
        wdt:P112        mb:Artist ;
        wdt:P1365        mb:Place ;
        wdt:P1366        mb:Place ;
        wdt:P915        mb:Recording ;
        wdt:P1037        mb:Artist ;
        wdt:P625        "coordinate location" ;
        wdt:P6375        "street address" ;
        skos:altLabel        "alt label" .
mb:Recording
        rdfs:label        "label" ;
        wdt:P123        mb:Label ;
        wdt:P136        mb:Genre ;
        wdt:P2888        "exact match" ;
        wdt:P3174        mb:Artist ;
        wdt:P3300        mb:Artist ;
        wdt:P361        mb:Recording ;
        wdt:P527        mb:Recording ;
        wdt:P57        mb:Artist ;
        wdt:P1071        mb:Area , mb:Place ;
        wdt:P10806        mb:Artist ;
        wdt:P12617        mb:Artist ;
        wdt:P161        mb:Artist ;
        wdt:P162        mb:Artist , mb:Label ;
        wdt:P1809        mb:Artist ;
        wdt:P2047        "duration" ;
        wdt:P272        mb:Label ;
        wdt:P3301        mb:Label ;
        wdt:P344        mb:Artist ;
        wdt:P3931        mb:Artist , mb:Label ;
        wdt:P4969        mb:Recording ;
        wdt:P5024        mb:Artist ;
        wdt:P5202        mb:Artist , mb:Label ;
        wdt:P5707        mb:Artist , mb:Recording , mb:Release ;
        wdt:P6275        mb:Artist ;
        wdt:P6718        mb:Recording ;
        wdt:P6942        mb:Artist ;
        wdt:P736        mb:Artist ;
        wdt:P767        mb:Artist ;
        wdt:P8546        mb:Area , mb:Place ;
        wdt:P943        mb:Artist ;
        wdt:P9767        mb:Recording ;
        wdt:P98        mb:Artist , mb:Label ;
        wdt:P9810        mb:Recording ;
        wdt:P110        mb:Artist ;
        wdt:P144        mb:Recording ;
        wdt:P175        mb:Artist ;
        wdt:P179        mb:Series ;
        wdt:P2550        mb:Work ;
        wdt:P287        mb:Artist ;
        wdt:P5028        mb:Artist ;
        wdt:P915        mb:Area , mb:Event , mb:Place ;
        skos:altLabel        "alt label" .
mb:Release
        rdfs:label        "label" ;
        wdt:P123        mb:Artist , mb:Label ;
        wdt:P136        mb:Genre ;
        wdt:P264        mb:Label ;
        wdt:P2888        "exact match" ;
        wdt:P31        "instance of" ;
        wdt:P3174        mb:Artist , mb:Label ;
        wdt:P3300        mb:Artist ;
        wdt:P361        mb:ReleaseGroup ;
        wdt:P57        mb:Artist ;
        wdt:P1534        "end cause" ;
        wdt:P655        mb:Artist ;
        wdt:P155        mb:Release ;
        wdt:P156        mb:Release ;
        wdt:P750        mb:Label ;
        wdt:P1071        mb:Area , mb:Place ;
        wdt:P10806        mb:Artist ;
        wdt:P162        mb:Artist ;
        wdt:P272        mb:Label ;
        wdt:P344        mb:Artist , mb:Label ;
        wdt:P3931        mb:Artist , mb:Label ;
        wdt:P5024        mb:Artist ;
        wdt:P5202        mb:Artist , mb:Label ;
        wdt:P5707        mb:Artist ;
        wdt:P6275        mb:Artist , mb:Label ;
        wdt:P767        mb:Artist ;
        wdt:P8546        mb:Area , mb:Place ;
        wdt:P943        mb:Artist ;
        wdt:P9767        mb:Release ;
        wdt:P98        mb:Artist , mb:Label ;
        wdt:P1365        mb:Release ;
        wdt:P1366        mb:Release ;
        wdt:P87        mb:Artist ;
        wdt:P110        mb:Artist , mb:Label ;
        wdt:P144        mb:Event ;
        wdt:P175        mb:Artist ;
        wdt:P287        mb:Artist , mb:Label ;
        wdt:P5028        mb:Artist ;
        wdt:P176        mb:Label ;
        wdt:P50        mb:Artist ;
        wdt:P577        "publication date" ;
        wdt:P629        mb:Release ;
        wdt:P676        mb:Artist ;
        wdt:P86        mb:Artist ;
        wdt:P872        mb:Label ;
        wdt:P9813        "container" ;
        wdt:P495        mb:Area ;
        skos:altLabel        "alt label" ;
        wdt:P1081        mb:Area .
mb:ReleaseGroup
        rdfs:label        "label" ;
        wdt:P136        mb:Genre ;
        wdt:P2888        "exact match" ;
        wdt:P31        "instance of" ;
        wdt:P361        mb:ReleaseGroup ;
        wdt:P527        mb:ReleaseGroup ;
        wdt:P825        mb:Artist , mb:Label ;
        wdt:P12617        mb:Artist ;
        wdt:P9810        mb:ReleaseGroup ;
        wdt:P144        mb:Series , mb:ReleaseGroup ;
        wdt:P175        mb:Artist ;
        wdt:P179        mb:Series ;
        wdt:P2550        mb:ReleaseGroup ;
        wdt:P577        "publication date" ;
        wdt:P629        mb:ReleaseGroup ;
        wdt:P658        mb:ReleaseGroup ;
        skos:altLabel        "alt label" .
mb:Series
        rdfs:label        "label" ;
        wdt:P123        mb:Label ;
        wdt:P136        mb:Genre ;
        wdt:P138        mb:Artist , mb:ReleaseGroup ;
        wdt:P2888        "exact match" ;
        wdt:P31        "instance of" ;
        wdt:P361        mb:Series ;
        wdt:P527        mb:Series ;
        wdt:P112        mb:Artist ;
        wdt:P175        mb:Artist ;
        wdt:P179        mb:Release , mb:ReleaseGroup ;
        wdt:P276        mb:Area , mb:Place ;
        wdt:P50        mb:Artist ;
        skos:altLabel        "alt label" .
mb:Work
        rdfs:label        "label" ;
        wdt:P123        mb:Artist , mb:Label ;
        wdt:P136        mb:Genre ;
        wdt:P138        mb:Artist , mb:Work ;
        wdt:P2888        "exact match" ;
        wdt:P31        "instance of" ;
        wdt:P361        mb:Work ;
        wdt:P527        mb:Work ;
        wdt:P825        mb:Artist , mb:Area , mb:Label , mb:Place ;
        wdt:P655        mb:Artist ;
        wdt:P1071        mb:Area , mb:Place ;
        wdt:P10806        mb:Artist ;
        wdt:P4969        mb:Work ;
        wdt:P5202        mb:Artist ;
        wdt:P87        mb:Artist ;
        wdt:P144        mb:Work ;
        wdt:P179        mb:Series ;
        wdt:P50        mb:Artist ;
        wdt:P629        mb:Work ;
        wdt:P676        mb:Artist ;
        wdt:P86        mb:Artist ;
        wdt:P11849        mb:Artist ;
        skos:altLabel        "alt label" ;
        wdt:P1701        mb:Area ;
        wdt:P2567        mb:Artist ;
        wdt:P407        "language of work or name" ;
        wdt:P4647        mb:Area , mb:Event , mb:Place ;
        wdt:P5059        mb:Work ;
        wdt:P6166        mb:Work ;
        wdt:P826        "tonality" ;
        wdt:P8535        "tala" ;
        wdt:P8536        "raga" ;
        wdt:P88        mb:Artist , mb:Area , mb:Label , mb:Place , mb:Series .
dtl:Solo
        wdt:P361        dtl:Track ;
        wdt:P175        "performer" ;
        wdt:P870        "instrumentation" .
dtl:Track
        rdfs:label        "label" ;
        wdt:P2888        "exact match" ;
        wdt:P361        "part of" ;
        wdt:P8546        "recording location" ;
        wdt:P175        "performer" ;
        wdt:P10135        "recording date" .
gj:Culture
        rdfs:label        "label" ;
        wdt:P2888        "exact match" ;
        wdt:P361        "part of" ;
        wdt:P4970        "alternative name" ;
        wdt:P17        "country" ;
        skos:altLabel        "alt label" ;
        wdt:P2341        "indigenous to" ;
        wdt:P2936        "language used" .
gj:Ensemble
        wdt:P136        "genre" ;
        wdt:P870        "instrumentation" ;
        wdt:P2596        gj:Culture .
gj:Instrument
        rdfs:label        "label" ;
        wdt:P2888        "exact match" ;
        wdt:P2341        gj:Culture , "indigenous to" ;
        wdt:P248        "stated in" .
gj:Minutage
        rdfs:label        "label" ;
        wdt:P2596        gj:Culture ;
        wdt:P921        gj:Song .
gj:Parlametrics
        rdfs:label        "label" ;
        wdt:P31        "instance of" ;
        wdt:P8546        "recording location" ;
        wdt:P585        "point in time" ;
        wdt:P1840        "investigated by" ;
        wdt:P407        "language of work or name" .
gj:Phonotactics
        wdt:P921        gj:Song .
gj:Song
        rdfs:label        "label" ;
        wdt:P136        "genre" ;
        wdt:P175        "performer" ;
        wdt:P585        "point in time" ;
        wdt:P495        "country of origin" ;
        wdt:P870        "instrumentation" ;
        wdt:P10893        "recordist" ;
        wdt:P2341        "indigenous to" ;
        wdt:P2596        gj:Culture .
gj:Source
        rdfs:label        "label" ;
        wdt:P50        "author" ;
        wdt:P577        "publication date" ;
        wdt:P921        gj:Culture .
diamm:Country
        rdfs:label        "label" ;
        wdt:P2888        "exact match" .
diamm:Organization
        rdfs:label        "label" ;
        wdt:P2888        "exact match" ;
        wdt:P31        "instance of" ;
        wdt:P131        diamm:City ;
        wdt:P17        diamm:Country ;
        wdt:P1343        diamm:Source .
diamm:Person
        rdfs:label        "label" ;
        wdt:P214        "VIAF cluster ID" ;
        wdt:P2888        "exact match" ;
        wdt:P569        "date of birth" ;
        wdt:P570        "date of death" ;
        wdt:P5504        "RISM ID" ;
        skos:altLabel        "alt label" ;
        wdt:P1343        diamm:Source .
diamm:Region
        rdfs:label        "label" ;
        wdt:P2888        "exact match" ;
        wdt:P17        diamm:Country .
diamm:Set
        wdt:P31        "instance of" ;
        wdt:P217        "inventory number" .
diamm:Source
        rdfs:label        "label" ;
        wdt:P123        diamm:Organization , diamm:Person ;
        wdt:P127        diamm:Organization , diamm:Person ;
        wdt:P31        "instance of" ;
        wdt:P361        diamm:Set ;
        wdt:P825        diamm:Organization , diamm:Person ;
        wdt:P131        diamm:City ;
        wdt:P655        diamm:Person ;
        wdt:P61        diamm:Person ;
        wdt:P1071        diamm:Organization ;
        wdt:P767        diamm:Person ;
        wdt:P98        diamm:Person ;
        wdt:P276        diamm:Organization , diamm:Archive ;
        wdt:P50        diamm:Organization , diamm:Person ;
        wdt:P872        diamm:Person ;
        wdt:P88        diamm:Organization , diamm:Person ;
        wdt:P11603        diamm:Person ;
        wdt:P1535        diamm:Organization , diamm:Person ;
        wdt:P2679        diamm:Person ;
        wdt:P547        diamm:Person ;
        wdt:P859        diamm:Organization , diamm:Person ;
        wdt:P941        diamm:Organization , diamm:Person .
diamm:Archive
        rdfs:label        "label" ;
        wdt:P2888        "exact match" ;
        wdt:P5504        "RISM ID" ;
        wdt:P131        diamm:City ;
        wdt:P11550        "RISM siglum" .
diamm:City
        rdfs:label        "label" ;
        wdt:P2888        "exact match" ;
        wdt:P131        diamm:Region ;
        wdt:P17        diamm:Country .
diamm:Composition
        rdfs:label        "label" ;
        wdt:P136        "genre" ;
        wdt:P361        diamm:Source ;
        wdt:P86        diamm:Person , "composer" .
ts:Events
        rdfs:label        "label" ;
        wdt:P131        "located in the administrative territorial entity" ;
        wdt:P17        "country" ;
        wdt:P276        "location" ;
        wdt:P580        "start time" ;
        wdt:P582        "end time" ;
        wdt:P625        "coordinate location" .
ts:Member
        rdfs:label        "label" .
ts:Recording
        rdfs:label        "label" ;
        wdt:P2888        "exact match" ;
        wdt:P175        "performer" ;
        wdt:P658        ts:Tune .
ts:Session
        wdt:P131        "located in the administrative territorial entity" ;
        wdt:P17        "country" ;
        wdt:P276        "location" ;
        wdt:P625        "coordinate location" .
ts:Tune
        rdfs:label        "label" ;
        skos:altLabel        "alt label" ;
        wdt:P747        ts:TuneSetting .
ts:Tuneset
        wdt:P527        ts:Tune ;
        wdt:P571        "inception" ;
        wdt:P170        ts:Member .
ts:TuneSetting
        wdt:P136        "genre" ;
        wdt:P826        "tonality" ;
        wdt:P3440        "time signature" .
```
