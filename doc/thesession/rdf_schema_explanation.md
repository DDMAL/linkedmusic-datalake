# Explanation of The Session's Data Structure and RDF Schema

This document is yet complete.


## I. Namespaces Defined

@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .  
@prefix wd:   <http://www.wikidata.org/entity/> .  
@prefix wdt:  <http://www.wikidata.org/prop/direct/> .  
@prefix geo:  <http://www.opengis.net/ont/geosparql#> .  
@prefix ts:   <https://thesession.org/> .

xsd is the standard XML datatype definition which we help us define the literals we store (e.g. "this is a dateTime data").  
wd is for wikidata entities; wdt is for wikidata properties.  
ts is for the Session entities (e.g. recordings, sessions), who often don't have an equivalent in Wikidata.  
geo is for geographic coordinates (e.g. Point(42.24073792 -71.00814819))  


## III. Schema of Dataset

### Clarification 1:  How are Events different from Sessions?
Events are Irish music concert and festivals where the user is expected to listen. They have a fixed start date and end date (June 10th, 2006, 9:30pm – 11pm).

Sessions are "jam sessions", where the user is expected to bring an instrument and play along. Thesession.org usually indicates the day of the week when a session happens (e.g. Wednesday). It will remove the session once it is no longer active. 

### Schema of Events.CSV
events.csv contains all the live traditional Irish music events that thesession.org keeps track of. In this section I will explain the different columns in events.csv (so that you don't have to struggle as much!) and how we create our RDF graph from them.


country == P17 means that each value in the column "country" is linked to the primary key of the row with the Wikidata predicate "P17". 

Stored as literal means that we will not attempt to reconcile the column against Wikidata. 

#### Event Identifiers

- event_id: The primary key; URI in the format "https://thesession.org/events/{number}"

The following is unreconciliable (i.e. do not have equivalent entities in Wikidata). As of now, we are not adding new entries to Wikidata, so we will store unreconcilibale fields as Literals (e.g. "Irish Cultural Centre"@en):
- event: the name of the event (e.g. National Celtic Festival). == rdfs:label

#### Event Time

The following are stored as literals with the identifier xsd:dateTime, which is the standard datatype for dates.
- dtstart: start time of event == P580 
- dtend: end time of event == P582  

#### Event Location

Unreconciliable (stored as literals):
- venue == P276 
- address == P6375 of venue (i.e. \<venue\> \<P6375\> \<address\>)

Largely Reconciliable (if reconciled, stored as URI):
- town: the city (or equivalent administrative region) where the event took place. == P276
- area: the province/territory (or equivalent administrative region). == P276 if town is unreconciled
- country == P17

In most cases the P276 (location) of the event returns the venue (literal) and the town (URI). This is ot ideal, but the best apparent solution.

Unreconciliable (stored as geo:wktLiteral (e.g. Point(40.52559280 141.45117188)^^geo:wktLiteral )):
- coordinate: longitude and latitude stored in WKT format (e.g. Point(40.52559280 141.45117188)) == P625

