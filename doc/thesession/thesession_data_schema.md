# Explanation of The Session's Data Schema

This document explains the schema of the raw data that can be extracted from thesession.org.
 
In the near future, I plan on completing two additional documents: one will explain our entire data processing workflow for thesession.org (an update to the existing reconcile_procedures.md); the other will explain the schema of the RDF graph we create from the The Session's data (perhaps I can merge that document with this one). 




# 3. Schema of The Session Dataset

## 3.1 General Structure of The Dataset
We have obtained 7 files from [the Session's official Github repository](https://github.com/adactio/TheSession-data). 

The files are:

|file | description | additional remarks|
|------|-------------|------------------|
|events.csv | concerts featuring Irish traditional music |
|tunes.csv | traditional Irish compositions | 
|recordings.csv | Irish traditional music recordings/albums | A recording usually features multiple tunes|
|sessions.csv | periodic gatherings where attendees play Irish music together, like a "jam session" | See [Irish traditional music session](https://en.wikipedia.org/wiki/Irish_traditional_music_session)
|aliases.csv |alternative names by which a tune/composition is known| 
|sets.csv | User-curated collections of tunes, like playlists| This metadata is not the most relevant to our project | 
|tunes-popularity.csv | number of times which a user has added a tune/composition into a "tunebook" | This metadata is not the most relevant to our project




## 3.2 events.csv
This file includes all the Irish Traditional music events on thesession.org. Remember that events = concerts.

Here is an explanation of each of the columns in events.csv

| Column     | Description                  | Example                          |
|------------|------------------------------|----------------------------------|
| events_id  | Event URI                    | https://thesession.org/events/11 |
| event      | Event name                   | Colm Gannon, Sean Mckeon         |
| dtstart    | Start datetime (ISO 8601)    | 2006-06-07T09:30:00              |
| dtend      | End datetime (ISO 8601)      | 2006-06-07T12:00:00              |
| venue      | Venue name                   | The Goalpost                     |
| address    | Venue address               | 226 Water Street                 |
| town       | Location: town or city       | Quincy                           |
| area       | Location: Province, region, or state| Massachusetts                    |
| country    | Location: Country       | United States                    |
| latitude   | Location: Latitude                  | 42.24073792                      |
| coordinate | Location: Coordinate point (WKT format)   | Point(42.24073792 -71.00814819)  |
| longitude  | Location: Longitude              | -71.00814819                     |

The Session dataset does not include the organizers or the performers of an event. As discussed [here](#question-2-why-is-there-not-an-artistscsv-nor-a-composerscsv), it is not a artist-centered database.

### 3.2.1 Mapping events.csv to RDF
will complete

## 3.3 recordings.csv
recordings.csv contain all Irish traditional music recordings/albums in thesession.org. 

| Column         | Description             | Example                                         |
|----------------|-------------------------|-------------------------------------------------|
| id   | Recording URI           | https://thesession.org/recordings/6584         |
| artist         | Artist name            | 3sticks                                         |
| recording      | Recording title         | Crossing Currents                               |
| track          | Track position on which the tune is|6                  |
| number         | Tune position on the track | 1                                               |
| tune           | Tune name               | St. Patrick's Day                               |
| tune_id        | Tune URI                | https://thesession.org/tunes/385.0             |


The primary key in recordings.csv is, in fact, "tune_id". In Irish traditional music, it common to feature many tunes on each track of the recording. For example, on the album [The Twisted Tree](https://floatingcrowbar.bandcamp.com/album/the-twisted-tree), the fourth track is called _The Coachman’s Whip / Scartaglen / The Shaskeen_. In this example, the tune "The Shaskeen" would have "4" in the "track" column, and "3" in the "number" column, because it is the third tune on the fourth track.

## 3.4 sessions.csv

| Column        | Description              | Example                                         |
|---------------|--------------------------|-------------------------------------------------|
| sessions_id   | Session URI              | https://thesession.org/sessions/7567           |
| name          | Venue name             | Clarke's Irish Bar                              |
| address       | Street address of the venue        | Derqui 225 B° Nueva                             |
| town          | Location: Town or city             | Córdoba                                         |
| area          | Location: Region or province       | Córdoba                                         |
| country       | Location:Country                  | Argentina                                       |
| latitude      | Latitude                 | -31.42639351                                    |
| longitude     | Longitude                | -64.18499756                                    |
| coordinate    |           | Point(-64.18499756 -31.42639351)               |
| date          | Date added to the Session (ISO 8601)    | 2022-09-18T08:19:38                             |

Sessions don't have a name by themselves. They are identified by the venue at which they are periodically held. Though it is not in the dataset, we can find when this session reccurs (Thursday) on https://thesession.org/sessions/7567, as well as an [Instagram link](https://www.instagram.com/accounts/login/?next=https%3A%2F%2Fwww.instagram.com%2Firish.session.cordoba%2F&is_from_rle)

## 3.5 tunes.csv

| Column      | Description              | Example                                                |
|-------------|--------------------------|--------------------------------------------------------|
| tune_id     | Tune URI                 | https://thesession.org/tunes/18105                     |
| setting_id  | Tune setting URI         | https://thesession.org/tunes/18105#setting35234        |
| name        | Tune setting name        | "$150 Boot, The"                                       |
| type        | Musical form of the tune                | polka                                          |
| meter       | Time signature           | 2/4                                                    |
| mode        | Mode or Tonality             | Gmajor                                                |
| date        | Date added to thesession.org  | 2019-07-06 04:39:09                                   |
| username    | Username of contributor  | NfldWhistler                                           |

The "mode" almost always include the tonic (e.g. E mixolydian). Each tune can have multiple settings (i.e. versions). Settings don't have a name of their own ("name" belong to tunes, but they are the primary key of this csv.

## 3.7 aliases.csv

| Column   | Description          | Example         |
|----------|----------------------|-----------------|
| tune_id  | Tune ID number       | 4               |
| alias    | Alternative tune name  | Great Eastern   |
| name     | Primary tune name    | Belfast, The    |

A tune, which includes many settings, can be known by many aliases. 

## 3.6 sets.csv, tunes-popularity.csv

These csv include data on user activity. They don't not seem the most relevant to our project. Although, I can see how tunes popularity on The Session may be an interesting data to store.

## 3.7 Some Questions and Answers

### Question 1:  How are Events Different from Sessions?
In short, events are concerts. Concert attendees usually listen to performers without making music themselves. Events have a fixed start date and end date (e.g. June 10th, 2006, 9:30pm – 11pm).

On the other hand, sessions are like "jam sessions", in which attendees are expected to bring an instrument and play with others. Sessions occur periodically at a same location (e.g. Wednesday at Lapa Irish Pub ): thesession.org would remove a session if it is no longer active!

### Question 2: Why is there not an artists.csv, nor a composers.csv?
Good question! You may have noticed on thesession.org that recordings have artists (https://thesession.org/recordings/artists/2983) and that tunes sometimes have composers (https://thesession.org/tunes/composers/2). However, thesession.org was not designed to be artist-centered, and artist profile contains almost no information on the artists, apart from an occasional Bandcamp or Soundcloud link. 

Besides, we really wish to avoid referencing this URI pattern (https://thesession.org/recordings/artists/{number}) in our RDF, since it is really confusing. 

Considering additionally that thesession.org may not be set up to handle too many of concurrent request,  we recommend not to scrape the website for artists or composers id.

### Question 3: What additional data exists the thesession.org, but is not included in our dataset?
Apart from artists and composers id, the dataset omits various memeber-related statistics that could be retrieved from scraping thesession.org. Thankfully, most of these data are related to user activity on thesession.org: they do not seem directly relevant to the LinkedMusic project. 



|data | description | example|
|------|-------------|------------------|
|member | users on thesession.org| https://thesession.org/members/1|
|trip | user travel itinerary (help users meet up) | https://thesession.org/trips/1777|
|discussions| user discussions | https://thesession.org/discussions/50261
|tunebook | user-made playlist (alternative to "tune set") | https://thesession.org/members/1/tunebook|
|bookmark| user tune bookmarks | https://thesession.org/members/1/bookmarks
|tag | user-made playlist (alternative to "tune set" and "tunebook" ) | https://thesession.org/members/1/tags/AncientMariner






