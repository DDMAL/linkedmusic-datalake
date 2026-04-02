# Ingestion of SIMSSA DB

# 1. General Description

You can read more about SIMSSA DB on the [official webpage](https://db.simssa.ca/about/). A graphic of the SIMSSA DB database model can be found [on Cory McKay's SourceForge page](https://jmir.sourceforge.net/cmckay/papers/mckay17database.pdf)

The project is mainly maintained by [Cory McKay](https://jmir.sourceforge.net/cmckay/). According to Ich, it is unlikely for SIMSSA DB to see any future update.

# 2. Obtaining The Database Dump

Dylan has obtained a PostgreSQL dump of the SIMSSA DB. The dump can be found on [Arbutus Object Storage](https://arbutus.cloud.computecanada.ca/auth/login/?next=/project/containers/container/virtuoso/misc). Please refer to the Internal SIMSSA Wiki on how to set up your Arbutus account.

# 3. Export SQL Dump to CSV files

1. Install PostgreSQL, if it is not installed already.

2. Make sure that postgres is running using the following command:

```bash
sudo service postgresql status
```

Start postgresql if it is not running:

```bash
sudo service postgresql start
```

3. Start the postgres shell

```bash
sudo -u postgres psql
```

4. Inside the shell, create a new user and database, and exit the shell:

```bash
CREATE USER myuser WITH PASSWORD 'mypassword';
CREATE DATABASE simssadb OWNER myuser;
GRANT ALL PRIVILEGES ON DATABASE simssadb TO myuser;
\q
```

5. Load the SQL dump into your new database through the following command:

```bash
sudo -u postgres sh -c "gunzip -c <path/to/sql_gz/dump> | psql -d simssadb"
```

When prompted, enter "mypassword" as the password.

6. Grant read access to all loaded tables to "myuser"

First, start the shell again:

```bash
sudo -u postgres psql -d simssadb
```

Then, run the following commands:

```bash
-- Grant SELECT on all existing tables
GRANT SELECT ON ALL TABLES IN SCHEMA public TO myuser;

-- Grant SELECT on tables created in the future
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO myuser;

\q
```

7. Run `export_all_tables.py`

Run the following command from the repository root directory:

```bash
python simssa/src/export_all_tables.py
```

All nonempty tables should be output as CSV files in the subdirectories of `simssa/data/raw`

# 4. Overview of The Raw Dataset

After running `simssa/src/export_all_tables.py `, each nonempty table should be output as a CSV file in a subdirectory of `simssa/data/raw`

`export_all_tables.py` groups the CSV files into the following subdirectories:

1. `feature`: CSV related to audio/musical features (e.g., most frequent pitch, rhythmic variability).
2. `genre`: CSV files related to musical genres, including both "genre-as-in-style" (e.g., Renaissance) and "genre-as-in-type" (e.g., Madrigal).
3. `instance`: CSV files related to instances of musical works, which serve as intermediate links between works, sources, and files.
4. `musical_work`: CSV files related to musical works, including their titles, sections, and associated metadata. Musical works (i.e., compositions) are the central entities of SIMSSA DB.
5. `person`: CSV files containing data about authors and composers, including their roles and contributions.
6. `source`: CSV files describing the origins of scores and their relationships to musical works and sections.

Every other CSV file is placed in the `other` subdirectory: these do not seem to be pertinent to the datalake.

## 4.1 Feature Subdirectory

Contains CSV related to audio/musical features (e.g., most frequent pitch, rhythmic variability). These features were extracted from MIDI files. You can find a list of example features at `https://db.simssa.ca/files/2018`

Contains the following CSVs:

- extracted_features.csv: list of musical/audio features
- feature_file.csv: location of files containing extracted features
- feature.csv: another list of musical/audio features

Musical features are currently omitted from the RDF since it is very difficult/impractical to store them in Linked Data form. Anyone interested in these data should be redirected to the SIMSSA DB website.

## 4.2 Genre Subdirectory

Contains CSV files related to musical genres, including both "genre-as-in-style" and "genre-as-in-type."

Contains the following CSVs:

- genre_as_in_style.csv: "Renaissance" is the only genre_as_in_style in SIMSSA DB.
- genre_as_in_type.csv: Lists twelve different genre_as_in_type (e.g., Zibaldone, Madrigal).
- musical_work_genres_as_in_style.csv: Maps every musical work in SIMSSA DB to the genre "Renaissance."
- musical_work_genres_as_in_type.csv: Maps musical works to their genre_as_in_type.

Musical genres are an important aspect of SIMSSA DB, particularly "genre-as-in-type," which provides more detailed classifications. These data are suitable for Linked Data representation.

## 4.3 Instance Subdirectory

Contains CSV files related to instances of musical works, which serve as intermediate links between works, sources, and files.

Contains the following CSVs:

- files.csv: Points to files containing sheet music or MIDI scores.
- source_instantiation.csv: Links instances to a musical work and to a source.
- source_instantiation_sections.csv: Links instances to a section of a musical work. An instance is either linked to the entire musical work or to a section of it.

Instances are not stored as distinct entities in the data lake but are crucial for linking works, sources, and files in the raw dataset.

## 4.4 Musical Work Subdirectory

Contains CSV files related to musical works, including their titles, sections, and associated metadata.

Contains the following CSVs:

- geographic_area.csv: Only contains "Vienna."
- instruments.csv: Only contains "Voice."
- musical_works.csv: Links a musical work to its title and indicates whether it is sacred or secular.
- part.csv: Lists whenever a work has a part for voice.
- section.csv: Lists sections of the musical works (e.g., work 117 may have a "Sanctus (In nomine)" section).

Among these, only `musical_works.csv` and `section.csv` are ingested into the datalake. The other files were not part of the final RDF since they contained so little data.

## 4.5 Person Subdirectory

Contains CSV files related to authors and composers, including their roles and contributions.

Contains the following CSVs:

- person.csv: Lists all composers/authors, with their birth and death years.
- contribution_musical_work.csv: Links people to compositions. The "role" column describes whether the person was an "AUTHOR" or a "COMPOSER."

These files provide essential metadata about the creators of musical works and their contributions, making them suitable for Linked Data representation.

## 4.6 Source subdirectory

Contains the CSV file `source.csv, which specifies information on a source (i.e. a book/anthology from which a musical work is taken).

# 5. Type of Entities in the RDF

## 5.1 Persons

Prefix: `https://db.simssa.ca/persons/`

Identifies people who are either authors or composers of musical works. Each person is linked to a VIAF ID in the raw dataset.

## 5.2 Musical Works

Prefix: `https://db.simssa.ca/musicalworks/`

Identifies individual musical works (i.e., compositions). Each composition is linked to:

1. An author and a composer
2. A genre
3. Symbolic music files (MIDI & PDF score)
4. Sections (e.g., a mass may have an Introit section)
5. A source (a book or an anthology in which the work was found).

## 5.3 Sections

Prefix: `https://db.simssa.ca/sections/`

This namespace refers to _sections_ of musical works. A “section” may correspond to a movement, chant segment, or logical division within a work.

There can be a symbolic music file for a particular section instead of the whole composition.

## 5.4 Types

Prefix: `https://db.simssa.ca/types/`

This namespace identifies the genre of the musical work ("genre-as-in-type"). 

## 5.5 Sources

Prefix: `https://db.simssa.ca/sources/`

Identifies the book/anthology from which the chant was taken.

## 5.6 Files

Prefix: `https://db.simssa.ca/files/`

Identifies the symbolic music file (PDF or MIDI) attached to a work or a section.
