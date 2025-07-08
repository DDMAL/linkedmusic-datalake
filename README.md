# LinkedMusic Data Lake

This repository contains code, documentation, and sample data set files to:
- Fetch data dumps from various databases in various file formats.
- Reconcile entries in these databases against entities and properties in WikiData.
- Transform reconciled databases into RDF turtle format and upload it to Virtuoso Staging.
- Please refer to [OpenRefine Tips](https://github.com/DDMAL/linkedmusic-datalake/blob/main/doc/openrefine_tips/README.md) if you are not familiar with how OpenRefine works.

This GitHub repo contains codes, documentations, and test files are used to 
-   fetch the original data dumps from databases, 
-   convert them to CSV, 
-   reconcile, 
-   convert the reconciled CSV to RDF turtle, then upload them to the Virtuoso Staging. 

## Virtual Environment Setup

1. Open a terminal in the `/linkedmusic-datalake` folder.
2. Run `poetry install` to install the required packages.
3. Activate the virtual environment with `eval $(poetry env activate)`.

## Database Introductions

### Cantus DB  
[Cantus Database](https://cantusdatabase.org/) is a repository of Latin chants found in medieval manuscripts and early printed books.  
Cantus DB provides us their sample Data Sets in CSV format. The work is still in progress.
Refer to the [Cantus DB manual](https://github.com/DDMAL/linkedmusic-datalake/blob/main/doc/cantus/README.md) for details.

### ESEA (East-and-Southeast-Asian) & Chinese (Traditional) Music Instrument  
Detailed information is provided within the corresponding `.ttl` files.

### RISM
[RISM Database](https://www.rism.info/) is the Répertoire International des Sources Musicales, an international collaborative database that catalogues historical musical sources. It provides detailed information on manuscripts, prints, and other music-related documents, serving as a crucial resource for researchers, librarians, and musicologists seeking to study and reference historical musical materials.
RISM provides us their complete Data Sets in RDF format. We use OpenRefine to reconcile the database against WikiData.
Refer to the [RISM manual](https://github.com/DDMAL/linkedmusic-datalake/blob/main/doc/rism/README.md) for more details.

### MusicBrainz  
[MusicBrainz](https://musicbrainz.org/) is an open music encyclopedia that provides extensive music metadata and serves as a universal reference for music identification.  
MusicBrainz has a public Data Set downloading site. We retrieve those Data Sets in JSON Lines format and process them using RDFLib package from python.
See the [MusicBrainz manual](https://github.com/DDMAL/linkedmusic-datalake/blob/main/doc/musicbrainz/README.md) for more information.

### Simssa DB  
[SIMSSA Database](https://db.simssa.ca/) is a discovery tool for symbolic music files (MEI, Kern, MusicXML, MIDI). It evolved from a previous database developed under Julie Cumming’s Digging into Data grant, offering improved functionality.
The work is still in progress.
Refer to the [Simssa DB manual](https://github.com/DDMAL/linkedmusic-datalake/blob/main/doc/simssadb/README.md) for further instructions.

### The Session  
[The Session](https://thesession.org/) is a community website dedicated to Irish traditional music. 
The Session has a public GitHub repo that contains public Data Sets. We retrieve these in CSV format and reconcile them using OpenRefine.
Find the [Session manual](https://github.com/DDMAL/linkedmusic-datalake/blob/main/doc/thesession/README.md) for additional guidance.


## Additional Resources
    The definitive source of music information by allowing anyone to contribute and releasing the data under open licenses.
    The universal lingua franca for music by providing a reliable and unambiguous form of music identification, enabling both people and machines to have meaningful conversations about music.
    Find https://github.com/DDMAL/linkedmusic-datalake/blob/main/musicbrainz/README.md for further manual.

## Abandoned Work

### AcousticBrainz  
~~[AcousticBrainz](https://acousticbrainz.org/) collected acoustic information from music recordings between 2015 and 2022, providing insights into spectral data, genres, moods, keys, and scales.  
Consult the [AcousticBrainz manual](https://github.com/DDMAL/linkedmusic-datalake/blob/main/acousticbrainz/README.md) for more details.~~

## Previous Work by Van

- All located in the jsonld_approach folder. We share some test sample files.

## ArchiveForReconciledEntries
In terms of reconciliation, OpenRefine primarily automate the matching of property values. However, perfect matches on Wikidata are not always guaranteed. To address this, we have been creating the "archive", storing those manually reconciled entries. This shared resource ensures that previously verified mappings can be reused, saving time and effort for others.
Reconciliation with OpenRefine may not always yield perfect matches on Wikidata. The "archive" stores manually reconciled entries, allowing verified mappings to be reused and saving time and effort.

<img src="images/wikidata_stamp_light.svg" alt="wikidata_stamp" width="400"/>