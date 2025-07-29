## Instructions

- wdt:2888 is used 

## Example 1

Natural Language Question: Find all compositions in DIAMM that were composed by Antonio il Verso

SPARQL Query

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

SPARQL Query:

```SPARQL
SELECT DISTINCT ?instrument WHERE {
 ?ensemble a gj:Ensemble.
 ?ensemble wdt:P870 ?instrument.
}
```

## Example 4

Natural Language Question: Find all Global Jukebox cultures from Africa

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

Input: Find all Global Jukebox cultures that have at least one song with flute instrumentation

Output: 


## Context - Full Ontology

```
@prefix rdfs:        <http://www.w3.org/2000/01/rdf-schema#> .
@prefix mb:        <https://linkedmusic.ca/graphs/musicbrainz/> .
@prefix wdt:        <http://www.wikidata.org/prop/direct/> .
@prefix dtl:        <https://linkedmusic.ca/graphs/dig-that-lick/> .
@prefix gj:        <https://linkedmusic.ca/graphs/theglobaljukebox/> .
@prefix skos:        <http://www.w3.org/2004/02/skos/core#> .
@prefix ts:        <https://linkedmusic.ca/graphs/thesession/> .
@prefix diamm:        <https://linkedmusic.ca/graphs/diamm/> .

mb:Area
        rdfs:label        "label" ;
        wdt:P136        mb:Genre ;
        wdt:P2888        "exact match"@en ;
        wdt:P31        "instance of"@en ;
        wdt:P4970        "alternative name"@en ;
        wdt:P571        "inception"@en ;
        wdt:P576        "dissolved, abolished or demolished date"@en ;
        wdt:P131        mb:Area ;
        wdt:P85        mb:Work .
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
        wdt:P21        "sex or gender"@en ;
        wdt:P26        mb:Artist ;
        wdt:P264        mb:Label ;
        wdt:P2652        mb:Artist ;
        wdt:P27        mb:Area ;
        wdt:P2888        "exact match"@en ;
        wdt:P31        "instance of"@en ;
        wdt:P3174        mb:Artist ;
        wdt:P3300        mb:Artist ;
        wdt:P3373        mb:Artist ;
        wdt:P361        mb:Artist , mb:Series ;
        wdt:P40        mb:Artist ;
        wdt:P451        mb:Artist ;
        wdt:P4970        "alternative name"@en ;
        wdt:P521        mb:Artist ;
        wdt:P527        mb:Artist ;
        wdt:P569        "date of birth"@en ;
        wdt:P570        "date of death"@en ;
        wdt:P571        "inception"@en ;
        wdt:P576        "dissolved, abolished or demolished date"@en ;
        wdt:P69        mb:Place ;
        wdt:P725        mb:Artist ;
        wdt:P742        mb:Artist ;
        wdt:P825        mb:Artist ;
        wdt:P8810        mb:Artist ;
        wdt:P972        mb:Series ;
        wdt:P57        mb:Place .
mb:Event
        rdfs:label        "label" ;
        wdt:P136        mb:Genre ;
        wdt:P2888        "exact match"@en ;
        wdt:P31        "instance of"@en ;
        wdt:P3300        mb:Artist ;
        wdt:P4970        "alternative name"@en ;
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
        wdt:P580        "start time"@en ;
        wdt:P582        "end time"@en ;
        wdt:P585        "point in time"@en ;
        wdt:P664        mb:Label ;
        wdt:P710        mb:Artist ;
        wdt:P915        mb:Recording .
mb:Genre
        rdfs:label        "label" ;
        wdt:P138        mb:Artist , mb:Area , mb:Label , mb:Place , mb:ReleaseGroup ;
        wdt:P2888        "exact match"@en ;
        wdt:P495        mb:Area .
mb:Instrument
        rdfs:label        "label" ;
        wdt:P136        mb:Genre ;
        wdt:P2888        "exact match"@en ;
        wdt:P31        "instance of"@en ;
        wdt:P4970        "alternative name"@en ;
        wdt:P527        mb:Instrument ;
        wdt:P1531        mb:Instrument ;
        wdt:P155        mb:Instrument ;
        wdt:P156        mb:Instrument ;
        wdt:P279        mb:Instrument ;
        wdt:P61        mb:Artist , mb:Label ;
        wdt:P7084        mb:Instrument ;
        wdt:P495        mb:Area .
mb:Label
        rdfs:label        "label" ;
        wdt:P127        mb:Artist ;
        wdt:P136        mb:Genre ;
        wdt:P138        mb:Work ;
        wdt:P2888        "exact match"@en ;
        wdt:P31        "instance of"@en ;
        wdt:P4970        "alternative name"@en ;
        wdt:P571        "inception"@en ;
        wdt:P576        "dissolved, abolished or demolished date"@en ;
        wdt:P112        mb:Artist ;
        wdt:P159        mb:Area ;
        wdt:P17        mb:Area ;
        wdt:P750        mb:Label ;
        wdt:P9237        mb:Label ;
        wdt:P1365        mb:Label ;
        wdt:P1366        mb:Label ;
        wdt:P355        mb:Label ;
        wdt:P749        mb:Label .
mb:Place
        rdfs:label        "label" ;
        wdt:P127        mb:Artist , mb:Label ;
        wdt:P136        mb:Genre ;
        wdt:P138        mb:Artist ;
        wdt:P2888        "exact match"@en ;
        wdt:P31        "instance of"@en ;
        wdt:P361        mb:Place ;
        wdt:P4970        "alternative name"@en ;
        wdt:P527        mb:Place ;
        wdt:P571        "inception"@en ;
        wdt:P576        "dissolved, abolished or demolished date"@en ;
        wdt:P825        mb:Work ;
        wdt:P131        mb:Area ;
        wdt:P112        mb:Artist ;
        wdt:P1365        mb:Place ;
        wdt:P1366        mb:Place ;
        wdt:P915        mb:Recording ;
        wdt:P1037        mb:Artist ;
        wdt:P625        "coordinate location"@en ;
        wdt:P6375        "street address"@en .
mb:Recording
        wdt:P123        mb:Label ;
        wdt:P136        mb:Genre ;
        wdt:P2888        "exact match"@en ;
        wdt:P3174        mb:Artist ;
        wdt:P3300        mb:Artist ;
        wdt:P361        mb:Recording ;
        wdt:P4970        "alternative name"@en ;
        wdt:P527        mb:Recording ;
        wdt:P57        mb:Artist ;
        wdt:P1071        mb:Area , mb:Place ;
        wdt:P10806        mb:Artist ;
        wdt:P12617        mb:Artist ;
        wdt:P1476        "title"@en ;
        wdt:P161        mb:Artist ;
        wdt:P162        mb:Artist , mb:Label ;
        wdt:P1809        mb:Artist ;
        wdt:P2047        "duration"@en ;
        wdt:P272        mb:Label ;
        wdt:P3301        mb:Label ;
        wdt:P344        mb:Artist ;
        wdt:P3931        mb:Artist , mb:Label ;
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
        wdt:P915        mb:Area , mb:Event , mb:Place .
mb:Release
        wdt:P123        mb:Artist , mb:Label ;
        wdt:P136        mb:Genre ;
        wdt:P264        mb:Label ;
        wdt:P2888        "exact match"@en ;
        wdt:P31        "instance of"@en ;
        wdt:P3174        mb:Artist , mb:Label ;
        wdt:P3300        mb:Artist ;
        wdt:P361        mb:ReleaseGroup ;
        wdt:P4970        "alternative name"@en ;
        wdt:P57        mb:Artist ;
        wdt:P655        mb:Artist ;
        wdt:P155        mb:Release ;
        wdt:P156        mb:Release ;
        wdt:P750        mb:Label ;
        wdt:P1071        mb:Area , mb:Place ;
        wdt:P10806        mb:Artist ;
        wdt:P1476        "title"@en ;
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
        wdt:P577        "publication date"@en ;
        wdt:P629        mb:Release ;
        wdt:P676        mb:Artist ;
        wdt:P86        mb:Artist ;
        wdt:P872        mb:Label ;
        wdt:P9813        "container"@en ;
        wdt:P495        mb:Area ;
        wdt:P1081        mb:Area .
mb:ReleaseGroup
        wdt:P136        mb:Genre ;
        wdt:P2888        "exact match"@en ;
        wdt:P31        "instance of"@en ;
        wdt:P361        mb:ReleaseGroup ;
        wdt:P4970        "alternative name"@en ;
        wdt:P527        mb:ReleaseGroup ;
        wdt:P825        mb:Artist , mb:Label ;
        wdt:P12617        mb:Artist ;
        wdt:P1476        "title"@en ;
        wdt:P9810        mb:ReleaseGroup ;
        wdt:P144        mb:Series , mb:ReleaseGroup ;
        wdt:P175        mb:Artist ;
        wdt:P179        mb:Series ;
        wdt:P2550        mb:ReleaseGroup ;
        wdt:P577        "publication date"@en ;
        wdt:P629        mb:ReleaseGroup ;
        wdt:P658        mb:ReleaseGroup .
mb:Series
        rdfs:label        "label" ;
        wdt:P123        mb:Label ;
        wdt:P136        mb:Genre ;
        wdt:P138        mb:Artist , mb:ReleaseGroup ;
        wdt:P2888        "exact match"@en ;
        wdt:P31        "instance of"@en ;
        wdt:P361        mb:Series ;
        wdt:P4970        "alternative name"@en ;
        wdt:P527        mb:Series ;
        wdt:P112        mb:Artist ;
        wdt:P175        mb:Artist ;
        wdt:P179        mb:Release , mb:ReleaseGroup ;
        wdt:P276        mb:Area , mb:Place ;
        wdt:P50        mb:Artist .
mb:Work
        wdt:P123        mb:Artist , mb:Label ;
        wdt:P136        mb:Genre ;
        wdt:P138        mb:Artist , mb:Work ;
        wdt:P2888        "exact match"@en ;
        wdt:P31        "instance of"@en ;
        wdt:P361        mb:Work ;
        wdt:P4970        "alternative name"@en ;
        wdt:P527        mb:Work ;
        wdt:P825        mb:Artist , mb:Area , mb:Label , mb:Place ;
        wdt:P655        mb:Artist ;
        wdt:P1071        mb:Area , mb:Place ;
        wdt:P10806        mb:Artist ;
        wdt:P1476        "title"@en ;
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
        wdt:P1701        mb:Area ;
        wdt:P2567        mb:Artist ;
        wdt:P407        "language of work or name"@en ;
        wdt:P4647        mb:Area , mb:Event , mb:Place ;
        wdt:P5059        mb:Work ;
        wdt:P6166        mb:Work ;
        wdt:P826        "tonality"@en ;
        wdt:P8535        "tala"@en ;
        wdt:P8536        "raga"@en ;
        wdt:P88        mb:Artist , mb:Area , mb:Label , mb:Place , mb:Series .
dtl:Solo
        wdt:P361        dtl:Track ;
        wdt:P175        "performer"@en ;
        wdt:P870        "instrumentation"@en .
dtl:Track
        rdfs:label        "label" ;
        wdt:P2888        "exact match"@en ;
        wdt:P361        "part of"@en ;
        wdt:P8546        "recording location"@en ;
        wdt:P175        "performer"@en ;
        wdt:P10135        "recording date"@en .
gj:Culture
        rdfs:label        "label" ;
        wdt:P2888        "exact match"@en ;
        wdt:P361        "part of"@en ;
        wdt:P4970        "alternative name"@en ;
        wdt:P17        "country"@en ;
        skos:altLabel        "alt label" ;
        wdt:P2341        "indigenous to"@en ;
        wdt:P2936        "language used"@en .
gj:Ensemble
        wdt:P136        "genre"@en ;
        wdt:P870        "instrumentation"@en ;
        wdt:P2596        gj:Culture .
gj:Instrument
        rdfs:label        "label" ;
        wdt:P2888        "exact match"@en ;
        wdt:P2341        gj:Culture , "indigenous to"@en ;
        wdt:P248        "stated in"@en .
gj:Minutage
        rdfs:label        "label" ;
        wdt:P2596        gj:Culture ;
        wdt:P921        gj:Song .
gj:Parlametrics
        rdfs:label        "label" ;
        wdt:P31        "instance of"@en ;
        wdt:P8546        "recording location"@en ;
        wdt:P585        "point in time"@en ;
        wdt:P1840        "investigated by"@en ;
        wdt:P407        "language of work or name"@en .
gj:Phonotactics
        wdt:P921        gj:Song .
gj:Song
        rdfs:label        "label" ;
        wdt:P136        "genre"@en ;
        wdt:P175        "performer"@en ;
        wdt:P585        "point in time"@en ;
        wdt:P495        "country of origin"@en ;
        wdt:P870        "instrumentation"@en ;
        wdt:P10893        "recordist"@en ;
        wdt:P2341        "indigenous to"@en ;
        wdt:P2596        gj:Culture .
gj:Source
        rdfs:label        "label" ;
        wdt:P50        "author"@en ;
        wdt:P577        "publication date"@en ;
        wdt:P921        gj:Culture .
ts:Events
        rdfs:label        "label" ;
        wdt:P131        "located in the administrative territorial entity"@en ;
        wdt:P17        "country"@en ;
        wdt:P276        "location"@en ;
        wdt:P580        "start time"@en ;
        wdt:P582        "end time"@en ;
        wdt:P625        "coordinate location"@en .
ts:Member
        rdfs:label        "label" .
ts:Recording
        rdfs:label        "label" ;
        wdt:P2888        "exact match"@en ;
        wdt:P175        "performer"@en ;
        wdt:P658        ts:Tune .
ts:Session
        wdt:P131        "located in the administrative territorial entity"@en ;
        wdt:P17        "country"@en ;
        wdt:P276        "location"@en ;
        wdt:P625        "coordinate location"@en .
ts:Tune
        rdfs:label        "label" ;
        skos:altLabel        "alt label" ;
        wdt:P747        ts:TuneSetting .
ts:Tuneset
        wdt:P527        ts:Tune ;
        wdt:P571        "inception"@en ;
        wdt:P170        ts:Member .
ts:TuneSetting
        wdt:P136        "genre"@en ;
        wdt:P826        "tonality"@en ;
        wdt:P3440        "time signature"@en .
diamm:Archive
        rdfs:label        "label" ;
        wdt:P2888        "exact match"@en ;
        wdt:P5504        "RISM ID"@en ;
        wdt:P131        diamm:City ;
        wdt:P11550        "RISM siglum"@en .
diamm:City
        rdfs:label        "label" ;
        wdt:P2888        "exact match"@en ;
        wdt:P131        diamm:Region ;
        wdt:P17        diamm:Country .
diamm:Composition
        rdfs:label        "label" ;
        wdt:P136        "genre"@en ;
        wdt:P361        diamm:Source ;
        wdt:P86        diamm:Person , "composer"@en .
diamm:Country
        rdfs:label        "label" ;
        wdt:P2888        "exact match"@en .
diamm:Organization
        rdfs:label        "label" ;
        wdt:P2888        "exact match"@en ;
        wdt:P31        "instance of"@en ;
        wdt:P131        diamm:City ;
        wdt:P17        diamm:Country ;
        wdt:P1343        diamm:Source .
diamm:Person
        rdfs:label        "label" ;
        wdt:P2888        "exact match"@en ;
        wdt:P569        "date of birth"@en ;
        wdt:P570        "date of death"@en ;
        wdt:P5504        "RISM ID"@en ;
        skos:altLabel        "alt label" ;
        wdt:P1343        diamm:Source .
diamm:Region
        rdfs:label        "label" ;
        wdt:P2888        "exact match"@en ;
        wdt:P17        diamm:Country .
diamm:Set
        wdt:P31        "instance of"@en ;
        wdt:P217        "inventory number"@en .
diamm:Source
        rdfs:label        "label" ;
        wdt:P123        diamm:Organization , diamm:Person ;
        wdt:P127        diamm:Organization , diamm:Person ;
        wdt:P31        "instance of"@en ;
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
```