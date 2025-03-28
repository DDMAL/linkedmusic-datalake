#   LinkedMusic Data Lake

This GitHub repo contains codes, documentations, and test files used to 
-   fetch the original data dumps from databases, 
-   convert them to CSV, 
-   reconcile, 
-   convert the reconciled CSV to RDF turtle, then upload them to the Virtuoso Staging. 

#   Virtual Environment

Open an terminal at the ```/linkedmusic-datalake``` folder.
Run ```poetry shell``` in the terminal. This will enter the virtual environment required for this project.
If some packages are still missing, run ```poetry add {the required package}``` to install.
(related documents: poetry.lock, pyproject.toml)

#   Database Intro

    ##  Cantus DB

    https://cantusdatabase.org/
    Cantus is a database of the Latin chants found in manuscripts and early printed books, primarily from medieval Europe. This searchable digital archive holds inventories of antiphoners and breviaries -- the main sources for the music sung in the Latin liturgical Office -- as well as graduals and other sources for music of the Mass.
    Find https://github.com/DDMAL/linkedmusic-datalake/blob/main/cantusdb/README.md for further manual.

    ##  ESEA(East-and-Southeast-Asian)&Chinese (traditional) Music Instrument
    (more details can be seen inside the .ttl files)

    ##  MusicBrainz

    https://musicbrainz.org/
    MusicBrainz is an open music encyclopedia that collects music metadata and makes it available to the public.

    MusicBrainz aims to be:

    The ultimate source of music information by allowing anyone to contribute and releasing the data under open licenses.
    The universal lingua franca for music by providing a reliable and unambiguous form of music identification, enabling both people and machines to have meaningful conversations about music.
    Find https://github.com/DDMAL/linkedmusic-datalake/blob/main/musicbrainz/README.md for further manual.

    ##  Simssa DB

    https://db.simssa.ca/
    The SIMSSA Database is designed as a repository and discovery tool for symbolic music files (e.g. MEI, Kern, MusicXML, and MIDI). Users can browse existing files or upload their own. The current site is a prototype that is still under development. It serves as part of the SIMSSA Project, a SSHRC Partnership Grant. The SIMSSA Database is the successor of an older database created as part of Julie Cumming’s Digging into Data grant, designed to gather symbolic music files in one place to do computer-aided counterpoint analysis. The new database has made improvements in several areas, explained below.
    Find https://github.com/DDMAL/linkedmusic-datalake/blob/main/simssadb/README.md for further manual.

    ##  The Session

    https://thesession.org/
    The Session is a community website dedicated to Irish traditional music.
    Find https://github.com/DDMAL/linkedmusic-datalake/blob/main/thesession/README.md for further manual.

    ##  AcousticBrainz

    https://acousticbrainz.org/
    Between 2015 and 2022, AcousticBrainz helped to crowd source acoustic information from music recordings. This acoustic information describes the acoustic characteristics of music and includes low-level spectral information and information for genres, moods, keys, scales and much more.
    Find https://github.com/DDMAL/linkedmusic-datalake/blob/main/acousticbrainz/README.md for further manual.

## csv2rdf
In this folder are corresponding files for different databases related to the procedures of csv2rdf (except for RSIM).

## ArchiveForReconciledEntries
In terms of reconciliation, OpenRefine primarily automate the matching of property values. However, perfect matches on Wikidata are not always guaranteed. To address this, we have been creating the "archive", storing those manually reconciled entries. This shared resource ensures that previously verified mappings can be reused, saving time and effort for others.