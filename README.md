# LinkedMusic Data Lake

[LinkedMusic](https://linkedmusic.ca/) is an open-source project that combines detailed music metadata from many independent databases into one searchable RDF graph. It brings together information about musical works, performances, recordings, composers, and performers, spanning repertoires from Irish traditional music to jazz solos to medieval chant, and links them through a common vocabulary so they can be explored together through a single endpoint.

Music metadata today is scattered across hundreds of databases, each with its own fields, identifiers, and access methods. Studying a single composer or work means juggling many interfaces and reconciling inconsistent naming by hand ("Mozart, W.A." vs. "Wolfgang Amadeus Mozart"?). LinkedMusic addresses this by reconciling every dataset's entities to [Wikidata](https://www.wikidata.org/), giving them shared, stable identifiers, and converting the result to [RDF](https://en.wikipedia.org/wiki/Resource_Description_Framework), loaded into a [Virtuoso](https://virtuoso.openlinksw.com/) triplestore that can be queried with SPARQL.

For the full project background, see the [wiki](https://github.com/DDMAL/linkedmusic-datalake/wiki).

## This repository

This repo is the **ingestion codebase** behind the data lake. For each source database it follows a common pipeline: fetch → reconcile against Wikidata (via OpenRefine) → convert to RDF → upload to Virtuoso (though the details vary by source). It also holds the supporting tooling around the graph: ontology visualizations, benchmark SPARQL queries, and the natural-language-to-SPARQL context used by SESEMMI (see [Querying the data](#querying-the-data)).

The generated data itself is **not** committed — most datasets are far too large, so the per-subproject `data/` folders only exist locally. See the [pipeline overview](https://github.com/DDMAL/linkedmusic-datalake/wiki/Current-Pipeline-for-Adding-a-New-Dataset) to learn about the ingestion process.

## Querying the data

The recommended way to explore the graph is [SESEMMI](https://sesemmi.linkedmusic.ca/) (Search Engine System for Enhancing Music Metadata Interoperability), our web front end for the data lake.


SESEMMI translates plain-language questions into SPARQL for you, and also provides a SPARQL input field if you'd rather write queries by hand. For developers, our Virtuoso SPARQL endpoint is available at [https://virtuoso.simssa.ca/sparql/](https://virtuoso.simssa.ca/sparql/).

## Repository structure

There is one folder per source database (listed under [Datasets](#datasets)). Most follow the same layout, though not every subproject uses every subdirectory:

- `data/` — data files, typically split into `archived/`, `extracted/`, `unreconciled/`, `reconciled/`, and `rdf/` stages. Almost none of these are committed, due to their size.
- `doc/` — documentation.
- `openrefine/` — OpenRefine history and export files.
- `src/` — scripts. Most scripts assume the current working directory is the subproject's `src/`.

The repository root also holds:

- `shared/` — code reused across subprojects: a config-driven RDF conversion tool (`rdfconv/`, with per-subproject configs in `rdf_config/`), a Wikidata API client (`wikidata_utils/`), and standalone utilities.
- `pyproject.toml` / `poetry.lock` — Python dependencies, managed with Poetry (one environment for the whole repo).

A few of the older subprojects also contain a `jsonld_approach/` folder, holding files from the now-discontinued JSON-LD approach.

## Datasets

The following databases are at least partially integrated into the data lake. Each links to its source and to its subproject documentation. See the wiki [Project Status](https://github.com/DDMAL/linkedmusic-datalake/wiki/Project-Status) page for what's complete, in progress, and planned.

| Dataset | Description |
| --- | --- |
| **[DIAMM](https://www.diamm.ac.uk/)** · [docs](/diamm/README.md) | Digital Image Archive of Medieval Music: digital images of European medieval music manuscripts. |
| **[Dig That Lick (DTL1000)](https://dig-that-lick.eecs.qmul.ac.uk/)** · [docs](/dtl/README.md) | Solos extracted and analyzed from jazz recordings. |
| **[Weimar Jazz Database](https://jazzomat.hfm-weimar.de/)** · [docs](/wjazzd/README.md) | Detailed transcriptions and annotations of jazz solos (Jazzomat project, HfM Weimar). |
| **[The Global Jukebox](https://theglobaljukebox.org/)** · [docs](/theglobaljukebox/README.md) | Traditional folk, Indigenous, and popular songs from around the world. |
| **[UT Song Index](https://databases.lib.utk.edu/songdb/)** · [docs](/utsi/README.md) | Songs indexed from anthologies held at the University of Tennessee's DeVine Music Library. |
| **[MusicBrainz](https://musicbrainz.org/)** · [docs](/musicbrainz/README.md) | Open music encyclopedia and universal reference for music identification. |
| **[The Session](https://thesession.org/)** · [docs](/thesession/README.md) | Community database dedicated to Irish traditional music. |
| **[RISM](https://rism.info/)** · [docs](/rism/README.md) | Répertoire International des Sources Musicales: historical musical sources (manuscripts, prints). |
| **[Cantus DB](https://cantusdatabase.org/)** · [docs](/cantus/README.md) | Latin chants found in medieval manuscripts and early printed books. |
| **[Cantus Index](https://cantusindex.org/)** · [docs](/cantusindex/README.md) | Cross-database catalogue of Latin chant, keyed by Cantus ID. |
| **[SIMSSA DB](https://db.simssa.ca/)** · [docs](/simssa/README.md) | Discovery tool for symbolic music files (MEI, Kern, MusicXML, MIDI). |
| **[CKG · musiconn.performance](https://nfdi4culture.de/)** · [docs](/ckg-musiconn/README.md) | German concert and opera performances, and the works performed at them. |
| **[CKG · Hoftheater Detmold](https://nfdi4culture.de/)** · [docs](/ckg-detmold/README.md) | Repertoire of the Detmold court theatre (operas, plays, Singspiele). |
| **[CKG · APSearch](https://nfdi4culture.de/)** · [docs](/ckg-apsearch/README.md) | ELAR (Endangered Languages Archive) field recordings — audio, image, video, text. |

The three CKG feeds come from the [NFDI4Culture](https://nfdi4culture.de/) Culture Knowledge Graph. Unlike most sources, they are delivered RDF-native and reconciled via a deterministic authority-ID → Wikidata crosswalk (GND / VIAF / GeoNames) rather than column-by-column in OpenRefine. Each loads as its own named graph in Virtuoso, which is why they are kept as separate sibling subprojects. (The CKG's RISM feed is excluded by design, since LinkedMusic ingests RISM separately.)

## Getting started

Setup and the full ingestion workflow are documented in the wiki. In brief: the repo uses Python 3.12 with Poetry (`poetry install` at the root creates one environment for everything), and most scripts run from a subproject's `src/` folder.

- [Current pipeline for adding a new dataset](https://github.com/DDMAL/linkedmusic-datalake/wiki/Current-Pipeline-for-Adding-a-New-Dataset)
- [Working with Virtuoso](https://github.com/DDMAL/linkedmusic-datalake/wiki/Working-with-Virtuoso) · [Accessing the SPARQL endpoint](https://github.com/DDMAL/linkedmusic-datalake/wiki/Accessing-the-Virtuoso-SPARQL-Endpoint)
- [Project status](https://github.com/DDMAL/linkedmusic-datalake/wiki/Project-Status)

## Team & contact

LinkedMusic is developed at the [Distributed Digital Music Archives and Libraries Lab (DDMAL)](https://ddmal.ca/) at McGill University.

Questions, corrections, and dataset suggestions are welcome! Feel free to [open an issue](https://github.com/DDMAL/linkedmusic-datalake/issues) or contact Liam Pond at [liam.pond@mail.mcgill.ca](mailto:liam.pond@mail.mcgill.ca).

<img src="images/wikidata_stamp_light.svg" alt="Reconciled against Wikidata" width="400"/>
