# Understanding Dig That Lick

This is a temporary document, in which we note down what we learn about the Dig That Lick and its data. 
This will be helpful for making the final documentation

## What is Dig That Lick?

["About" page](https://dig-that-lick.eecs.qmul.ac.uk/Dig%20That%20Lick_About.html)

Dig That Lick is a scholarly effort to analyze melodic patterns in jazz (i.e. licks).

## Dig That Lick Similarity Search Website
https://dig-that-lick.hfm-weimar.de/similarity_search/documentation

This website is one of the main deliverables (i.e. final products) of the Dig That Lick project.

The [homepage](https://dig-that-lick.eecs.qmul.ac.uk/index.html) indicates that the site currently supports four databases:


1. The new DTL1000 database, comprising 300000 tone events in 1736 monophonic solos from over 600 jazz tunes spanning the 100 years of jazz history. The solos have been extracted automatically from audio using a newly developed CRNN-based algorithm specialised for jazz.
2. The well-known Weimar Jazz Database with about 200000 tone events from 456 monophonic solos by 78 jazz masters.
3. The Charlie Parker Omnibook with about 18000 tones taken from 52 solos by the co-inventor of bebop.
4. The Essen Folk Song Collection, comprising about 350000 notes from 7352 folk songs.

## Dig That Lick (DTL) Similarity Search Documentation
https://dig-that-lick.hfm-weimar.de/similarity_search/documentation


The section "Metadata Filters" may be of particular interest to us since we are only interested in its metadata, not it's tone analysis tool.


## Doing Some Searches Ourselves

AQAK60kSSkmSJImUKDiOGMfxgjnRxodV_0.01.59.032734-0.02.58.079365
AQAK60kSSkmSJImUKDiOGMfxgjnRxodV_0.01.59.32734-0.02.58.79365

The first 0 after the last dot must be removed

From [OSF](https://osf.io/bwg42/files/osfstorage?view_only=), we have obtained DTL1000.ttl. It is of much help to us except that it specifies the conventional space for DTL solos, which is http://www.DTL.org/JE/solo_performances/AQAF7EkVKUsW6MKVDz1lPHwErxL6b0hO_0.01.30.39528-0.03.10.37333 (not zero after dot).


## Other Databases
The RDF schema of DTL1000 has already been determined. Now I will establish work on the Weimar Jazz Database and the Essen Folksong Collection. I will ingest the Charlie Parker Omnibook as it contains too little metadata.

### Exploring the Essen Folksong Collection
[Github page](https://github.com/ccarh/essen-folksong-collection)
[ESAC page](https://www.esac-data.org/)

ESAC stands for Essen Associative Code. It is a computer way to notate melody developed by by Helmut Schaffrath in 1980's. This standard is pretty famous, it seems.

After some research, I am feeling that the Essen Folksong Collection does include enough linkable data. We should other database before returning to it.

### Exploring the Weimar Jazz Database
[Main Page](https://jazzomat.hfm-weimar.de/index.html)
[Content of the DB](https://jazzomat.hfm-weimar.de/dbformat/dbcontent.html)
[Glossary of the DB](https://jazzomat.hfm-weimar.de/dbformat/glossary.html)

The Weimar Jazz Database is a database of jazz solos (much like DTL1000) created by the Jazzomat Research Project, the same project behind Dig That Lick. The three above link comprise all the documentation we need to reconcile the database.

Since every track in the Weimar Jazz Database include a MusicBrainz id, it may not be necessary to save any of its track related metadata, as MusicBrainz contain them all.


