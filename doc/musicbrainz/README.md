# MusicBrainz Data Conversion Documentation

This guide outlines the steps required for the entire data pipeline of translating raw data from MusicBrainz into an RDF graph.

Follow the steps below to ensure a smooth data conversion and upload process.

## Characteristics of MusicBrainz Dataset

- Given that MusicBrainz data is based on a Relational Database (RDB) model, most entities (e.g. artists and recordings) are already carefully linked with one another. In fact, there are over 800 defined relationship types connecting these entities!
- Please read the [official documentation on Basic MusicBrainz Entities](//http://musicbrainz.org/doc/Terminology) as well as the [official table of MusicBrainz Relationships](https://musicbrainz.org/relationships)
- Luckily, most Musicbrainz entities are already reconciled with Wikidata (i.e. they have a field containing the matching Wikidata QID). This removes the need for reconciliation with OpenRefine.

## Data Processing Pipeline

### Process Overview

Below are the steps you must execute from your console once you have cloned the linkedmusic-datalake repository.

1. **Navigate to the Target Folder**

    - Change directory to `linkedmusic-datalake/`.
    - This helps all the scripts locate their default input and output directories. Additionally, all the scripts accept  --input_folder and/or --output_folder argument(s).

2. **Fetching the Latest Data**

    - Run the command below to download the latest `.tar.xz` dumps from the MusicBrainz public data sources (see [official documentation](https://musicbrainz.org/doc/Development/JSON_Data_Dumps)):

        ```bash
        python code/musicbrainz/fetch.py --output_folder data/musicbrainz/raw/archived/
        ```

    - The downloaded files are stored at:
        `data/musicbrainz/raw/archived/`
    - A tar.gz exists for each of the 13 MusicBrainz entity types, except "genre" and "url". Therefore, you should have downloaded the following 11 files:

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

3. **Extracting JSON Lines files From tar.xz files**

    - Each downloaded `.tar.xz` files contain a `mbdump` folder.
    - Each `mbdump` folder contain a single JSON Lines file
   - Each JSON Lines (JSONL) file contain all the MusicBrainz entities of that type (e.g. area.jsonl contain all the artists) : each line of the file is a JSON record for an entity.

    - Execute the following command to extract JSON Lines files from the tar.xz:

        ```bash
        python code/musicbrainz/untar.py --input_folder data/musicbrainz/raw/archived/ --output_folder data/musicbrainz/raw/extracted_jsonl/
        ```

    - The extracted files are located at:
        `data/musicbrainz/raw/extracted_jsonl/mbdump/`

    - Note: There are other files in the `.tar.xz`. However, they  are timestamps and data licenses, which are not useful to our project.


    

4. **Extracting and Reconciling Unreconciled Fields**

Note:
  - You can consult `doc/musicbrainz/layout.json` to see a list of fields that exist for each entity type.

    - Each entity in MusicBrainz has an additional `type` field on top of their basic entity-type. You can understand `type` as a subclass of `entity-type`. For example, Berlin Philharmoniker has `"artist"` as its `entity-type` (general), and `"orchestra"` as its `type` (specific).

        - EXCEPTION 1: `release-group` entities do not have a `type` field. Instead, they have both a `primary-type` and a `secondary-types`field.
        - EXCEPTION 2: `recording` and `release` entities do not have a `type` field.
  
- `types` are not yet reconciled with Wikidata. We must therefore extract a list of all available types and reconcile them ourselves (e.g. match the type `orchestra` to `Q42998`) 

  
  - Execute the following command to extract `type` and other unreconciled fields. 

            ```bash
            python code/musicbrainz/extract_for_reconciliation.py --input_folder data/musicbrainz/raw/extracted_jsonl/mbdump/ --output_folder data/musicbrainz/raw/unreconciled/
            ```

     - The script extract values from all unreconciled fields into CSV files. All CSV files are stored at:
            `data/musicbrainz/raw/unreconciled`
        
        - In that folder, you should find:
            - `f"{entity-type}_types.csv"` for each entity_type except `release-group` `recording`, `release` (see above).
            - `keys.csv` for `key` field of all `work` entities (`key` == tonality; `work` == composition).
            - `genders.csv` for `gender` field of all `artist` entities. 
            - `languages.csv` for `language` field of all `work` entities. The CSV includes an additional column, `full_language`, containing the full language name resolved from the ISO 639-3 code, using the pycountry library
        - Follow the steps in `doc/musicbrainz/reconciliation.md` to reconcile the CSVs against Wikidata. 
        - Put the reconciled CSVs in the `data/musicbrainz/raw/reconciled` folder. Name them according to the following conventions:
         `f"{entity_type}-types-csv.csv"`, `"keys-csv.csv"`, `"genders-csv.csv"`, or `"languages-csv.csv"`.
5. **Converting Data to RDF (Turtle Format)**

    - For each JSON Lines file, convert the data using:

        ```bash
        python code/musicbrainz/convert_to_rdf.py --input_folder data/musicbrainz/raw/extracted_jsonl/mbdump/ --reconciled_folder data/musicbrainz/raw/reconciled/ --config_folder code/musicbrainz/rdf_conversion_config/ --output_folder data/musicbrainz/rdf/
        ```

    - Notes on the script:

        - The script is optimized to be memory-efficient, but there's only so much you can do when one of the input files is >250GB.
        - The script uses disk storage to store the graph as it builds it to save on memory space. By default, this folder is `./store`, from the working directory. The script automatically deletes the folder when it finishes. However, if the script crashes, it is recommended to delete the folder before running it again.
        - By default, the script will ignore any data types that already have a corresponding file in the output directory. This is useful in the event that the program crashes and you only need to rerun the RDF conversion on the data that wasn't processed instead of the entire input directory.
        - Settings for queue sizes, as well as the number of parallel processes are in global variables at the beginning of the script
        - For ease of reading, the fields are processed in alphabetical order in the `process_line` function.
        - If you call `Literal(...)` with `XSD.date` as datatype, it will eventually call the `parse_date` isodate function to validate the format. However, `parse_date` is called after the construction of the `Literal`, making any exception it raises impossible to catch. This is why I made `convert_date` function to call the call the `Literal` constructor.
        - The same situation applies to the `convert_datetime` function with the `XSD.dateTime` datatype and the `parse_datetime` isodate function
        - The dictionary containing regex patterns for URLs has been moved to a separate module, `code/musicbrainz/url_regex.py`, to reduce clutter in the main script. 
        - The class definition for the `MappingSchema` class was moved to a separate module, `code/musicbrainz/mapping_schema.py`, to reduce clutter in the main script
        - The dictionary containing property mappings for the data fields and URLs was moved into a JSON file, located in `code/musicbrainz/rdf_conversion_config/mappings.json`. The dictionary contains the internal dictionary of a `MappingSchema` object serialized into JSON by Python's built-in JSON module. As such, the outermost dictionary's keys are the target types, the second one's keys are source types, and the third one's keys are properties, with the values being the full URIs for the properties.
        - To update this dictionary, either modify the JSON file, or modify the `MB_SCHEMA` and then use `json.dump(MB_SCHEMA.schema, file, indent=4)` to export it.

    - The generated RDF files are saved in the `data/musicbrainz/rdf/` directory.
    - Further documentation on the RDF conversion process is located in the `doc/musicbrainz/rdf_conversion.md` file
    - Documentation regarding the `relations` field can be found in the `doc/musicbrainz/relations.md` file

6. **Retrieving Genre Information**

    - Run the following script to scrape genres along with their reconciled WikiData IDs:

        ```bash
        python code/musicbrainz/get_genre.py --output data/musicbrainz/rdf/
        ```

    - The script is rate-limited to 1 request every 1.375 seconds following MusicBrainz' [rate limit guides](https://musicbrainz.org/doc/MusicBrainz_API/Rate_Limiting#How_throttling_works), it was increased from 1 second to 1.375 second because we were still getting rate limited even with a 1 second delay
    - The script also provides a user-agent header, following the same guidelines
    - The RDF is stored in `data/musicbrainz/rdf/`
    - The genres are handled this way because they are stored and treated differently by MusicBrainz compared to the other core entity types, and they are not available in the [main database dumps](https://data.metabrainz.org/pub/musicbrainz/data/json-dumps/). This is why we use the [API](https://musicbrainz.org/doc/MusicBrainz_API/#Introduction) to fetch the list of genres, and scrape the webpages to get the wikidata links.

### Recommendation: Script Testing

If you're experimenting on the scripts, it's recommended to take a small subset of the data, to save time. As an example, to get the first 100000 lines from the `area` file, run the following command in a terminal:

```bash
head -n 100000 area.jsonl > small_area.jsonl
```

This greatly speeds up the processing, because some files have up to 5 million lines, and it is unnecessary to test against the entire dataset when making minor changes



## Data Upload

- Upload all converted RDF files to Virtuoso for further use. 
(This section is yet completed)

