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

Besides, we really wish to avoid referencing this URI pattern (https://thesession.org/recordings/artists/{number}) in our RDF, since it is really confusing. 

Considering additionally that thesession.org may not be set up to handle too many of concurrent request,  we recommend not to scrape the websitesite for artists or composers id.

#### Question 3: What additional data exists the thesession.org, but is not included in our dataset?
Apart from artists and composers id, the dataset omits various memeber-related statistics that could be retrieved from scraping thesession.org. Thankfully, most of these data do not seem relevant to the LinkedMusic project.


|data | description | additional remarks|
|------|-------------|------------------|
|member | 
|trip |
|discussions|
|tunebook
|tune set
|bookmark
|tag


## 3.2 events.csv
events.csv contains all the live traditional Irish music events that thesession.org keeps track of. In this section 

Here is an explanation of each of the columns of event csv

| Column         | Description                                             | Example                                                       | Predicate                 | Additional Remarks                                  |
|----------------|---------------------------------------------------------|----------------------------------------------------------------|---------------------------|-----------------------------------------------------|
| events_id      | The session URI for an event                            | https://thesession.org/events/11                              | None (subject)            |                                                     |
| event          | Name of the event                                       | Colm Gannon, Sean Mckeon And John Blake                      | `rdfs:label`              | Mostly in English, occasionally in Irish Gaelic     |
| dtstart        | Event start date and time (ISO 8601 format)             | 2006-06-07T09:30:00                                           | `wdt:P580`                |                                                     |
| dtend          | Event end date and time (ISO 8601 format)               | 2006-06-07T12:00:00                                           | `wdt:P582`                |                                                     |
| venue          | Name of the venue                                       | The Goalpost                                                  | `wdt:P276`                | We will create a blank node                         |
| address        | Street address of the venue                             | 226 Water Street                                              | `wdt:6375`                | Not reconciled                                      |
| town           | Name of the town or city                                | Quincy                                                        | `wdt:P276`                |                                                     |
| area           | State, province, or regional area                       | Massachusetts                                                 | Not stored                | Only stored if town is unreconciled                 |
| country        | Country of the event location                           | United States                                                 | `wdt:P37`                 |                                                     |
| latitude       | Latitude of the event location                          | 42.24073792                                                   | Not stored                | Not stored because redundant with "coordinate"      |
| coordinate     | Full geospatial point (latitude and longitude)          | Point(42.24073792 -71.00814819)                               | `wdt:P625`                |                                                     |
| longitude      | Longitude of the event location                         | -71.00814819                                                  | Not stored                | Not stored because redundant with "coordinate"      |




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

