# MusicBrainz Data Pipeline Documentation

This guide details all the steps required to translate raw data from MusicBrainz into an RDF graph reconciled with Wikidata.

## Characteristics of the MusicBrainz Dataset

- Given that MusicBrainz data is based on a Relational Database (RDB) model, most entities (e.g. artists and recordings) are already carefully linked with one another. In fact, there are over 800 defined relationship types connecting these entities!
- Luckily, most Musicbrainz entities are already reconciled with Wikidata (i.e. they have a field containing the matching Wikidata QID). This removes the need for us to reconcile the data with OpenRefine (Ichiro confimed).
- Please take a look the [official documentation on basic MusicBrainz entities](https://musicbrainz.org/doc/Terminology) and the [official table of MusicBrainz relationships](https://musicbrainz.org/relationships) before you continue.

## Data Processing Pipeline

### Overview of the Pipeline

Below are the steps you must execute from your console once you have cloned the `linkedmusic-datalake` repository.

#### 1. **Navigate to the Target Folder**

- Change your working directory to `linkedmusic-datalake/`.
- All the commands written in this guide expect the working directory to be the project root directory.
- If you want the scripts' default arguments be pointing to the correct folders, you can run the scripts directly from the directory they are in: `code/musicbrainz/`. This can be especially useful when using VSCode's run script feature.

#### 2. **Fetch the Latest Data**

- Run the command below to download the latest `.tar.xz` dumps from the MusicBrainz public data sources (see [official documentation](https://musicbrainz.org/doc/Development/JSON_Data_Dumps)):

  ```bash
  python code/musicbrainz/fetch.py --output_folder data/musicbrainz/raw/archived/
  ```

- The downloaded files are stored at:
  `data/musicbrainz/raw/archived/`
- A tar.xz exists for 11 of the 13 MusicBrainz entity types (all of them except `genre` and `url`). Therefore, you should have downloaded the following 11 files:

  1. area.tar.xz
  2. artist.tar.xz
  3. event.tar.xz
  4. instrument.tar.xz
  5. label.tar.xz
  6. place.tar.xz
  7. recording.tar.xz
  8. release-group.tar.xz
  9. release.tar.xz
  10. series.tar.xz
  11. work.tar.xz

#### 3. **Untar the dump**

- Execute the following command to extract JSON Lines files from the tar.xz:

  ```bash
  python code/musicbrainz/untar.py --input_folder data/musicbrainz/raw/archived/ --output_folder data/musicbrainz/raw/extracted_jsonl/
  ```

- Each downloaded `.tar.xz` files contain a `mbdump` folder, in which is a single JSON Lines file
- JSON Lines (JSONL) is a format in which each line is a JSON object. Each of the MusicBrainz JSONL files contain all MusicBrainz entities of that particular `entity-type`. For example, `artist.jsonl` contains all MusicBrainz artist entities; each entity is a JSON object who occupies a entire line.

- The extracted JSONL files are located at:
  `data/musicbrainz/raw/extracted_jsonl/mbdump/`

- Note: There are other files in the `.tar.xz`. However, they are timestamps and data licenses, which are not useful to our project.

#### 4. **Extract and Reconcile Unreconciled Fields**

- Note that you can consult [`doc/musicbrainz/layout.json`](/doc/musicbrainz/layout.json) to see a list of fields that exist for each entity type.

- Each entity in MusicBrainz has an additional `type` field on top of their basic entity-type. You can understand `type` as a subclass of `entity-type`. For example, Berlin Philharmoniker has `"artist"` as its `entity-type` (general), and `"orchestra"` as its `type` (specific).

  - EXCEPTION 1: `release-group` entities do not have just a `type` field. Instead, they have both a `primary-type` and a `secondary-types`field.
  - EXCEPTION 2: `recording` and `release` entities do not have a `type` field.

- `types` are not yet reconciled with Wikidata. We must therefore extract a list of all available types and reconcile them ourselves (e.g. match the type `orchestra` to [`Q42998`](https://www.wikidata.org/wiki/Q42998)).

- Execute the following command to extract `type` and other unreconciled fields.

  ```bash
  python code/musicbrainz/extract_for_reconciliation.py --input_folder data/musicbrainz/raw/extracted_jsonl/mbdump/ --output_folder data/musicbrainz/raw/unreconciled/
  ```

- The script extracts values from all unreconciled fields into CSV files. All CSV files are stored at:
  `data/musicbrainz/raw/unreconciled/`

- In that folder, you should find:
  - `f"{entity-type}_types.csv"` for each entity_type except `recording` and `release` (see above).
  - `keys.csv` for `key` field of all `work` entities (`key` == tonality; `work` == composition).
  - `genders.csv` for `gender` field of all `artist` entities.
  - `languages.csv` for `language` field of all `work` entities. The CSV includes an additional column, `full_language`, containing the full language name resolved from the ISO 639-3 code, using the `pycountry` library.
- Follow the steps in [miscellanous_reconciliation.md](./miscellanous_reconciliation.md) to reconcile the CSVs against Wikidata.
- Put the reconciled CSVs in the `data/musicbrainz/raw/reconciled` folder. Name them according to the following conventions:
  `f"{entity_type}-types-csv.csv"`, `"keys-csv.csv"`, `"genders-csv.csv"`, or `"languages-csv.csv"`.

#### **5. Reconcile Relationships**

- In addition to the above mentionned fields, the field `relationships` is also unreconciled in the raw MusicBrainz data.

- Please consult [relationships_reconciliation.md](./relationships_reconciliation.md) to learn how to reconcile relationships against Wikidata.

#### **6. Converting Data to RDF (Turtle Format)**

- For each JSON Lines file, convert the data using:

  ```bash
  python code/musicbrainz/convert_to_rdf.py --input_folder data/musicbrainz/raw/extracted_jsonl/mbdump/ --reconciled_folder data/musicbrainz/raw/reconciled/ --config_folder code/musicbrainz/rdf_conversion_config/ --output_folder data/musicbrainz/rdf/
  ```

- The generated RDF files are saved in the `data/musicbrainz/rdf/` directory.
- Please consult [rdf_conversion.md](./rdf_conversion.md) to learn more about our RDF conversion for MusicBrainz.

#### **7. Retrieving Genre Information**

- Run the following script to scrape genres along with their reconciled Wikidata IDs:

  ```bash
  python code/musicbrainz/get_genre.py --output data/musicbrainz/rdf/
  ```

- The script outputs an RDF file, which is stored in `data/musicbrainz/rdf/`, along the other RDF files.
- The script is rate-limited to 1 request every 1.375 seconds following MusicBrainz' [rate limit guides](https://musicbrainz.org/doc/MusicBrainz_API/Rate_Limiting#How_throttling_works). It was increased from 1 second to 1.375 second because we were still getting rate limited even with a 1 second delay.
- The script also provides a user-agent header, following the same guidelines.

- The genres are handled this way because they are stored and treated differently by MusicBrainz compared to the other core entity types, and they are not available in the [main database dumps](https://data.metabrainz.org/pub/musicbrainz/data/json-dumps/). This is why we use the [API](https://musicbrainz.org/doc/MusicBrainz_API/#Introduction) to fetch the list of genres, and scrape the webpages to get the wikidata links.

### Recommendation: Script Testing

- If you're experimenting on the scripts, we recommend you to test on a small subset of the data.

- For example, you can get the first 100000 lines of the `area.jsonl` file, by running the following command:

```bash
head -n 100000 area.jsonl > small_area.jsonl
```

- This greatly speeds up the processing. Some files have up to 5 million lines: it is unnecessary to test them all for minor changes.

## Data Upload

- Upload all converted RDF files to Virtuoso for further use.
  (This section is not yet completed.)
