# DTL1000 Workflow

## 1. Fetching Raw Data

The CSV containing the entire DTL1000 dataset (also referred to as the Dig That Lick Database) can be downloaded at the bottom of [this webpage](https://dig-that-lick.hfm-weimar.de/similarity_search/documentation).

It is named `dtl_metadata_v0.9.csv`. Please store it at `/data/digthatlick/raw`.

## 2. Splitting and Cleaning the CSV File

Change the working directory to `code/digthatlick`.

- To split and clean `dtl_metadata_v0.9.csv`, run the following command:

```python
python split_dtl1000.py [path to csv]
```

- The `[path to csv]` argument is not needed if the raw CSV is stored at `/data/digthatlick/raw`.
- The split CSVs will be outputted to `data/digthatlick`

### 2.1 Logic Behind Splitting

- Splitting the CSV file is not strictly mandatory, since reconciliation and RDF conversion can happen without it. However, it does make the data much easier to navigate.

- We split up the raw CSV into three files:

  - dtl1000_solos.csv
  - dtl1000_tracks.csv
  - dtl1000_performers.csv

- `solos.csv` contains all metadata unique to the solo (e.g., performers on the solo, instrument used in the solo).
- `track.csv` contains all metadata unique to the track from which the solo is taken (e.g., recording location). It does not include performers.
- `performers.csv` contains all track performers' data. It is a separate file because track performers are often in multi-valued cells (i.e., multiple performer names in a single cell). Splitting them into different cells creates many extra rows, which would make `tracks.csv` unnecessarily large and cumbersome.

### 2.2 Logic Behind Cleaning

Columns changed:

- solo_id:

  - We remove 0s within `solo_id` in order to build valid URIs (see [digthatlick_data_schema.md](./digthatlick_data_schema.md)).

- track_id:

  - We create `track_id` using the first 32 characters of `solo_id`, which is unique per track. `track_id` is not dereferenceable (i.e., there is no Dig That Lick webpage for tracks).
  - This is the only column present in all three CSVs; its values are used to link entities across files.

- instrument_label (in `solos.csv`):

In the raw dataset, instruments are stored as abbreviations. To help reconciliation, we expand the abbreviations with this mapping:

```
{
    "as": "alto saxophone",
    "bs": "baritone saxophone",
    "cl": "clarinet",
    "cor": "cornet",
    "fl": "flute",
    "flg": "flugelhorn",
    "ss": "soprano saxophone",
    "tb": "trombone",
    "tp": "trumpet",
    "ts": "saxophone",
    "vib": "vibraphone",
    "vln": "violin",
    "voc": "voice",
}
```

- Instrument labels can be used to more precisely reconcile performers (you specify in OpenRefine that the instrument is `instrument (P1303)` of the performer).

  - Note that "ts" is expanded to simply "saxophone" because it helps performer reconciliation. It should be changed to "tenor saxophone" once reconciliation is complete.

- start_time and end_time: removed from CSV since they are not needed (already in the URI).

- performer_names and possible_performer_names:
  - These columns contain a lot of cells that need to be split into multiple cells (e.g., "Charlie Parker, Stan Getz" needs to be split into "Charlie Parker" and "Stan Getz").
  - Some performers have instruments in parentheses (e.g., `Charlie Parker(as)`). These are removed during cleaning.

# Reconciling Against Wikidata

See [reconciliation_procedures.md](./reconciliation_procedures.md) for details.

# Converting DTL1000 to RDF

DTL1000 is converted to RDF using the General RDF Conversion script (please read through [General RDF Conversion Guide](../rdf_conversion/using_rdfconv_script.md)).

The TOML configuration for DTL1000 is `/code/rdf_config/digthatlick.toml`. You may need to update the configuration file if your column names differ from the expected.

Once the config is updated, you may convert the dataset to RDF by following the steps below:

- Change your working directory to `/code`.

- Run the following command:

```bash
python -m rdfconv.convert rdf_config/digthatlick.toml
```

- A TTL file should be outputted to `/data/digthatlick/rdf`, or whichever folder you specified in the config.

## Note about Namespace

The Dig That Lick project has [a page at OSF](https://osf.io/bwg42/files/osfstorage?view_only=), on which can be found DTL1000.ttl. In the official DTL1000.ttl, the namespace used for solos is `http://www.DTL.org`, a domain name that would bring to an unrelated website.

Thus, we have temporarily adopted the namespace `http://www.DTL.org` to maintain compatibility with the official DTL1000.ttl file, despite its drawbacks. We may consider using a redirection service eventually (see [Issue 373](https://github.com/DDMAL/linkedmusic-datalake/issues/373)).
