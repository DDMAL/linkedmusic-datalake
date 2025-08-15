# Data Schema of Databases Within Dig That Lick

This document explains the schema of the datasets provided by the Dig That Lick project.

So far, we have only ingested DTL1000, an original dataset the Dig That Lick team has compiled for their project. Dig That Lick also incorporates three non-original music datasets (see the [section below](#12-dig-that-lick-similarity-search-website))

## 1. Very Brief Introduction to Dig that Lick

## 1.1 What is Dig That Lick?

See ["About" page](https://dig-that-lick.eecs.qmul.ac.uk/Dig%20That%20Lick_About.html).

Dig That Lick is a scholarly effort to analyze melodic patterns in jazz (i.e. licks). The project's main emphasis is melody, with music metadata being of secondary importance.

### 1.2 Dig That Lick Similarity Search Website

https://dig-that-lick.hfm-weimar.de/similarity_search/documentation

This website is one of the main deliverables (i.e. final products) of the Dig That Lick project. Its primary function is to enable searching for a jazz solo or folk song by inputting a melodic fragment, with metadata filtering available.

Its [homepage](https://dig-that-lick.eecs.qmul.ac.uk/index.html) indicates that the site currently supports four databases:

1. The new DTL1000 database, comprising 300000 tone events in 1736 monophonic solos from over 600 jazz tunes spanning the 100 years of jazz history. The solos have been extracted automatically from audio using a newly developed CRNN-based algorithm specialised for jazz.
2. The well-known Weimar Jazz Database with about 200000 tone events from 456 monophonic solos by 78 jazz masters.
3. The Charlie Parker Omnibook with about 18000 tones taken from 52 solos by the co-inventor of bebop.
4. The Essen Folk Song Collection, comprising about 350000 notes from 7352 folk songs.

All four CSV files can be downloaded from the bottom of [the documentation page](https://dig-that-lick.hfm-weimar.de/similarity_search/documentation). This is how we obtained our raw data.

### 1.3 Current Progress

Currently, DTL1000 has been reconciled against Wikidata and has been converted to RDF.

However, we are still deciding whether it is worthwhile to ingest the Essen Folksong Collection and the Weimar Jazz Database, as they mostly contain metadata which already exists in the bigger databases (e.g. RISM, MusicBrainz).

The Charlie Parker Omnibook stores mostly harmonic information and contains very little metadata. It may not be worth ingesting.

## 2. Data Schema of DTL1000

DTL1000 is contained within one CSV file: dtl_metadata_v0.9.csv. The CSV consists of 15 columns:

| column name                   | description                                                                 | example                                                                                                      |
| ----------------------------- | --------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| solo_id                       | unique identifier for each solo                                             | AQAD-EqXKIqegOmiDWIyCXeWCecPP0cR_0.00.46.043990-0.01.25.005469                                               |
| possible_solo_performer_names | list of musicians that could have performed on the solo                     | Elmer 'Skippy' Williams, Wayman Carver                                                                       |
| performer_names               | list of musicians performing on the track                                   | Horace Silver (p), Joe Calloway (b), Stan Getz (ts), Walter Bolden (dr)                                      |
| solo_performer_name           | musician who is certainly performing on the solo                            | Stan Getz                                                                                                    |
| band_name                     | name of the band recording this track                                       | Stan Getz Quartet                                                                                            |
| leader_name                   | name of the band leader                                                     | Stan Getz                                                                                                    |
| medium_title                  | volume (part of the compilation album) from which the track is taken        | White Bebop Boys Vol. 6 (1949-50) Terry Gibbs - Al Cohn – Zoot Sims - George Wallington - Stan Getz          |
| medium_record_number          | the position of the volume on the compilation album                         | 82                                                                                                           |
| disk_title                    | name of the album (often a compilation album) from which the track is taken | The Encyclopedia of Jazz, Part 4: Bebop Story - A Musical Revolution That Radically Changed the Road of Jazz |
| track_title                   | name of the track from which the solo was taken                             | Tootsie Roll                                                                                                 |
| session_date                  | track recording date (yyyy-mm-dd)                                           | 1950-12-10                                                                                                   |
| area                          | location of recording                                                       | New York                                                                                                     |
| instrument_label              | abbreviated label for soloist's instrument                                  | ts                                                                                                           |
| solo_start                    | start time of the solo in the recording                                     | 0:00:46.043990                                                                                               |
| solo_end                      | end time of solo in the recording                                           | 0:01:25.005469                                                                                               |

### 2.1 Solo vs Track vs Medium vs Disk

From largest to smallest:

- Disk: album containing multiple CDs/volumes (e.g. [The Encyclopedia of Jazz](https://musicbrainz.org/release/2afeb957-bee2-4a92-85ba-943a542437db/disc/78))

- Medium: a CD/volume on the compilation album (e.g. "Miles Davis, Vol. 1 (1945–48)" is one of the CDs in [The Encyclopedia of Jazz](https://musicbrainz.org/release/2afeb957-bee2-4a92-85ba-943a542437db/disc/78))

- Track: a track/song/recording on a CD/volume (e.g. "Deep Sea Blues" is a track on the CD "Miles Davis, Vol. 1 (1945–48)")

- Solo: a section within a track featuring a single jazz musician improvising a melody (see [Jazz improvisation Wikipedia page](https://en.wikipedia.org/wiki/Jazz_improvisation)). Dig That Lick participants were the ones who decided which parts of the song constitute solos (e.g. "1:15-2:20" is a solo section in "Deep Sea Blues")

### Additional info:

1. solo_id:
   The first 32 characters are not unique per solo, but are unique per track which the solo is on (e.g. `AQAD-EqXKIqegOmiDWIyCXeWCecPP0cR`). The subsequent characters are the start and end times of the solo within the track (e.g. `_0.00.46.043990-0.01.25.005469`).

   - Each DTL1000 solo has a webpage, which can be accessed by adding the `solo_id` after `https://dig-that-lick.hfm-weimar.de/similarity_search/details?melid=`.
   - To be precise, before appending `solo_id` to build the URL, you must remove two zeros from the millisecond position (this is simply an inconsistency within the dataset). For example, `AQAD-EqXKIqegOmiDWIyCXeWCecPP0cR_0.00.46.043990-0.01.25.005469` needs to become `AQAD-EqXKIqegOmiDWIyCXeWCecPP0cR_0.00.46.43990-0.01.25.05469`.
   - The splitting script should handle the removal of zeros.

2. possible_solo_performer_names:
   This column only has a value if there is no value in `solo_performer_name`.

3. area:
   This column specifies where a solo (or rather the track containing the solo) was recorded. However, the values in this column vary a lot in terms of format. They can be formatted as:

   - Individual city: `Chicago`
   - "City, Country": `Milan, Italy`
   - "City, State": `Camden, N.J`
   - List of cities + dates: `New York, Mumbai & Chennai, India, Saylorsburg, PA, Encino, CA, & Chicago, IL, November 2006-`
   - "Venue, City, Country": `Live "Jazzhus Montmartre", Copenhagen, Denmark`
