# Data Schema of Databases Within Dig That Lick

This document is intended to explain the schema of the raw data within DTL1000, the database created as part of the Dig that Lick project. 

In the near future, I will write a separate document explaining the schema of the RDF we create from DTL1000.  

## 1. Very Brief Introduction to Dig that Lick

## 1.1 What is Dig That Lick?

See its ["About" page](https://dig-that-lick.eecs.qmul.ac.uk/Dig%20That%20Lick_About.html).

Dig That Lick is a scholarly effort to analyze melodic patterns in jazz (i.e. licks). 

### 1.2 Dig That Lick Similarity Search Website
https://dig-that-lick.hfm-weimar.de/similarity_search/documentation

This website is one of the main deliverables (i.e. final products) of the Dig That Lick project. Its [homepage](https://dig-that-lick.eecs.qmul.ac.uk/index.html) indicates that the site currently supports four databases:

1. The new DTL1000 database, comprising 300000 tone events in 1736 monophonic solos from over 600 jazz tunes spanning the 100 years of jazz history. The solos have been extracted automatically from audio using a newly developed CRNN-based algorithm specialised for jazz.
2. The well-known Weimar Jazz Database with about 200000 tone events from 456 monophonic solos by 78 jazz masters.
3. The Charlie Parker Omnibook with about 18000 tones taken from 52 solos by the co-inventor of bebop.
4. The Essen Folk Song Collection, comprising about 350000 notes from 7352 folk songs.

All four csv files can be downloadaded from the bottom of [the documentation page](https://dig-that-lick.hfm-weimar.de/similarity_search/documentation). This is how we obtain our raw data.

### 1.3 The current progress
As for now, we have reconciled DTL1000 and have converted it to RDF 

However, we decided to finish reconciling RISM and MusicBrainz before processing The Essen Folksong Collection and the Weimar Jazz Database, as they mostly contain metadata which already exists in the bigger databases.

The Charlie Parker Omnibook store mostly melodic and harmonic information, and contain very little metadata. It may not be worth ingesting.  

## 2. Data Schema of DTL1000:


DTL1000 is contained within the one csv:  dtl_metadata_v0.9.csv. The csv consists of 15 columns:

|column name     | description | example|
|----------------------------|-------------|--------|
|solo_id |unique identifier for each solo | AQAD-EqXKIqegOmiDWIyCXeWCecPP0cR_0.00.46.043990-0.01.25.005469|
|possible_solo_performer_names | list of musicians that could have performed on the solo| Elmer  'Skippy' Williams, Wayman Carver|
|performer_names | list of musicians performing on the track| 	Horace Silver (p), Joe Calloway (b), Stan Getz (ts), Walter Bolden (dr)|
|solo_performer_name | musician who is certainly performing on the solo| Stan Getz |
|band_name | name of the band recording this track| Stan Getz Quartet|
|leader_name | name of the band leader| Stan Getz|
|medium_title | volume of the compilation album from the track is taken| White Bebop Boys Vol. 6 (1949-50) Terry Gibbs - Al Cohn – Zoot Sims - George Wallington - Stan Getz |
|medium_record_number | Not sure what this is| 82|
|disk_title | name of the album (often a compilation album) from which the track is taken| The Encyclopedia of Jazz, Part 4: Bebop Story - A Musical Revolution That Radically Changed the Road of Jazz|
|track_title | name of the track from which the solo was taken | Tootsie Roll|
|session_date | track recording date (yyyy-mm-dd)| 1950-12-10| 
|area | location of recording| New York| 
|instrument_label | abbreviateed label for soloist's instrument| ts|
|solo_start | start time of the solo in the recording| 0:00:46.043990|
|solo_end | end time of solo in the recording| 0:01:25.005469|

Additional info:
1. solo_id: looks like: AQAD-EqXKIqegOmiDWIyCXeWCecPP0cR_0.00.46.043990-0.01.25.005469, a unique id for each solo
    the first 32 characters are not unique per solo, but are unique per track which the solo is on, the rest are jsut the time stamps of the recorded solo.
    odd thing is that in the time stamps, the miliseconds part has an extra 0 in front, which does not show up when u use this as url and doesnt work must be removed ie

2. possible_solo_performer_names:
    In each row (for each solo), only one of this column and the solo_performer_name column will be filled

3. performer_names:
    list of all the musicians performing on the track/recording

4. solo_performer_name:
    musician who is for sure performing the solo at the time on this recording

12.  area: could be city, could be more general, could also be multiple places, could also be more specific like a venue: for example:
    most are like New York, Chicago, blah
    but some are like: Milan, Italy
    or Camden, N.j.
    theres also Chicago, and then Chicago, IL
    and then venue: Live "Jazzhus Montmartre", Copenhagen, Denmark


13. instrument_label:, abbreviated, note for reconciliation, expanded to match with wikidata, also used as property instrument for reconcile solo performer, but ts becomes saxophone because whenever someone plays tenor sax, for some reason in wikidata they just put saxophone
put back to tenor saxophone after



