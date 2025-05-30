# Explanation of The Session's Data Structure and RDF Schema

This document is yet complete.


# 1. Namespaces Defined

@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .  
@prefix wd:   <http://www.wikidata.org/entity/> .  
@prefix wdt:  <http://www.wikidata.org/prop/direct/> .  
@prefix geo:  <http://www.opengis.net/ont/geosparql#> .  
@prefix ts:   <https://thesession.org/> .

xsd is the standard XML datatype definition which we help us define the literals we store (e.g. "this is a dateTime data").  
wd is for wikidata entities; wdt is for wikidata properties.  
ts is for the Session entities (e.g. recordings, sessions), who often don't have an equivalent in Wikidata.  
geo is for geographic coordinates (e.g. Point(42.24073792 -71.00814819))  

# 2. Workflow
pass

# 3. Schema of The Session Dataset

## 3.1 General Structure of The Dataset
We have obtained 7 files from [the Session's official Github repository](https://github.com/adactio/TheSession-data). 

The files are:

|file | description | additional remarks|
|------|-------------|------------------|
|events.csv | concerts featuring Irish traditional music |
|tunes.csv | traditional Irish compositions | 
|recordings.csv | Irish traditional music recordings/albums | A recording usually features multiple traditional tunes|
|sessions.csv | periodic gatherings where attendees can play Irish music together, like a "jam session" | See [Irish traditional music session](https://en.wikipedia.org/wiki/Irish_traditional_music_session)
|tunes-aliases.csv |alternative names by which a tune/composition is known| 
|sets.csv | User-curated collections of tunes, like playlists| This metadata is not the most relevant to our project | 
|tunes-popularity.csv | number of times which a user has added a tune/composition into a "tunebook" | This metadata is not the most relevant to our project


### 3.1.1 Some Questions and Answers

#### Question 1:  How are Events Different from Sessions?
In short, events are concerts. As you know, concert attendees usually listen to performers without making music themselves. Events have a fixed start date and end date (e.g. June 10th, 2006, 9:30pm – 11pm).

On the other hand, sessions are like "jam sessions", in which attendees are expected to bring an instrument and play with others. Sessions occur periodically at a same location (e.g. Wednesday at Lapa Irish Pub ): thesession.org would remove a session if it is no longer active!

#### Question 2: Why is there not an artists.csv, nor a composers.csv?
Good question! You may have noticed on thesession.org that recordings have artists (https://thesession.org/recordings/artists/2983) and that tunes sometimes have composers (https://thesession.org/tunes/composers/2). However, thesession.org was not designed to be artist-centered, and artist profile contains almost no information on the artists, apart from an occasional Bandcamp or Soundcloud link. 

Besides, we really should avoid referencing this URI pattern (https://thesession.org/recordings/artists/{number}) in our RDF, since it's really confusing. 

Considering additionally that thesession.org may not be set up to handle thousands of concurrent request,  we have decided not to scrape the site for artists or composers id. We at least have the artist's name as a string in recordings.csv.

#### Question 3: Tune Set vs Tunebook vs Tune Collection???


## 3.2 Schema of Events.CSV
events.csv contains all the live traditional Irish music events that thesession.org keeps track of. In this section I will explain the different columns in events.csv (so that you don't have to struggle as much!) and how we create our RDF graph from them.




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
- area: the province/territory (or equivalent administrative region). == P276 if town is unreconciled, otherwise not stored
- country == P17

In most cases the P276 (location) of the event returns the venue (literal) and the town (URI). This is ot ideal, but the best apparent solution.

Unreconciliable (stored as geo:wktLiteral (e.g. Point(40.52559280 141.45117188)^^geo:wktLiteral )):
- coordinate: longitude and latitude stored in WKT format (e.g. Point(40.52559280 141.45117188)) == P625

