# LinkedMusic Data Lake

This repository contains code, documentation, and sample data set files to:
- Fetch data dumps from various databases in various file formats.
- Reconcile entries in these databases against entities and properties in WikiData.
- Transform reconciled databases into RDF turtle format
- Upload the RDF files to Virtuoso
- Generate visuals of the data lake ontology
- Test and validate the data lake through benchmark SPARQL queries
- Use LLMs to generate SPARQL through NLQ2SPARQL with the aid of a custom prompt engineering context

Refer to the wiki for a [general overview of our current pipeline for adding a new dataset](https://github.com/DDMAL/linkedmusic-datalake/wiki/Current-Pipeline-for-Adding-a-New-Dataset).

## Database Introductions

The following datasets are currently at least partially integrated into our data lake.

Refer to the wiki for [more details on the project status](https://github.com/DDMAL/linkedmusic-datalake/wiki/Project-Status), including completed work, work in progress, and future directions.

### DIAMM
The [Digital Image Archive of Medieval Music (DIAMM)](https://www.diamm.ac.uk/) is an archive of digital images of European medieval manuscripts. We use a web crawler to fetch metadata from the DIAMM site and use custom scripts to convert the JSON data to CSV, and then to RDF. See the [DIAMM manual](/diamm/doc/README.md) for more information.

### Dig That Lick (DTL1000)
[Dig That Lick](https://dig-that-lick.eecs.qmul.ac.uk/) is a project the extracts and analyses solos from jazz performances. See the [Dig That Lick documentation](/dtl) for more information.

### The Global Jukebox
[The Global Jukebox](theglobaljukebox.org/) focuses on traditional folk, indigenous, and popular songs from around the world. Its data can be found on [The Global Jukebox Github](https://github.com/theglobaljukebox). See [The Global Jukebox manual](theglobaljukebox/doc/README.md) for more information.

### MusicBrainz  
[MusicBrainz](https://musicbrainz.org/) is an open music encyclopedia that provides extensive music metadata and serves as a universal reference for music identification.  
MusicBrainz has a public Data Set downloading site. We retrieve those Data Sets in JSON Lines format and process them using RDFLib package from python.
See the [MusicBrainz manual](/musicbrainz/doc/README.md) for more information.

### The Session  
[The Session](https://thesession.org/) is a community website dedicated to Irish traditional music. 
The Session has a public GitHub repo that contains public Data Sets. We retrieve these in CSV format and reconcile them using OpenRefine.
Find the [Session manual](/thesession/doc/README.md) for additional guidance.

### RISM
[RISM Database](https://www.rism.info/) is the Répertoire International des Sources Musicales, an international collaborative database that catalogues historical musical sources. It provides detailed information on manuscripts, prints, and other music-related documents, serving as a crucial resource for researchers, librarians, and musicologists seeking to study and reference historical musical materials.
RISM provides us their complete Data Sets in RDF format. We use OpenRefine to reconcile the database against WikiData.
Refer to the [RISM manual](/rism/doc/README.md) for more details.

### Cantus DB  
[Cantus Database](https://cantusdatabase.org/) is a repository of Latin chants found in medieval manuscripts and early printed books.  
Cantus DB provides us their sample Data Sets in CSV format.
Refer to the [Cantus DB manual](/cantus/doc/README.md) for details.

### Simssa DB  
[SIMSSA Database](https://db.simssa.ca/) is a discovery tool for symbolic music files (MEI, Kern, MusicXML, MIDI). It evolved from a previous database developed under Julie Cumming’s Digging into Data grant, offering improved functionality.
The work is still in progress.
Refer to the [Simssa DB manual](/simssa/doc/README.md) for further instructions.

### ESEA (East-and-Southeast-Asian) & Chinese (Traditional) Music Instrument  
Detailed information is provided within [the corresponding `.ttl` files](https://github.com/DDMAL/linkedmusic-datalake/tree/main/esea/data).

<img src="images/wikidata_stamp_light.svg" alt="wikidata_stamp" width="400"/>
