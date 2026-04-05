# UT Song Database

The UT Song Database is a curated collection of song metadata maintained by the University of Tennessee Libraries. Its main website is `https://databases.lib.utk.edu/songdb/songdb.php`.

We have used the lowercase string `utsi` as the naming convention for this dataset. In the future, you may consider changing it to `utksi`, since "UTK" is a commonly used abbreviation for the University of Tennessee, Knoxville.

## How to Obtain the Database

The database is not publicly downloadable. A complete copy of the dataset was obtained directly from the maintainers of the University of Tennessee Libraries in spreadsheet format. A copy of the spreadsheet is uploaded to Arbutus Cloud, under the container `virtuoso` and its directory `raw_data_files`.

## Ingestion Workflow

1. Change the directory to the repository root.
2. Obtain a copy of the database CSV.
3. Reconcile and clean using OpenRefine (see [reconciliation procedures](./doc/reconciliation_procedures.md)).
4. Store the reconciled CSV under `/utsi/data/reconciled`.
5. Review `shared/rdf_config/utsi.toml` to ensure it matches the reconciled CSV structure.
6. After reviewing the TOML file, run the general RDF conversion script using the following command from the `/shared` directory:

```bash
python -m rdfconv.convert rdf_config/utsi.toml
```

7. The converted TTL file should be output to `/utsi/data/rdf`.

## Content of the Database

The main entity of the UT Song Database is the song.

Songs on the website do not have a dedicated webpage URL. Instead, each song is retrieved by query parameters in the main URL. For example, `http://databases.lib.utk.edu/songdb/songdb.php?word=0&title=%27S%20WONDERFUL` retrieves the song `'S Wonderful`. Unfortunately, these retrievals can be inaccurate — the link above retrieves 16 different entries, not all of which are relevant. I have not been able to retrieve entities using the `id` or `reference` column in the given CSV, so they are not included at all in the final TTL.

From the example of `'S Wonderful`, you may also notice that the same song by George Gershwin has many different entities — each time it appears in another anthology, another entity is created.

## Ingested Entity Types

- **song**: a musical work with lyrics. For each song, the dataset provides metadata information such as the composer, the author (i.e., lyricist/librettist), the genre, the language(s), etc. On top of that, each song is linked to the anthology from which it was taken.
- **anthology**: a book containing many songs. The dataset creates a distinct entity each time a song appears in a different anthology.
