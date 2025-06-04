# MusicBrainz Data Conversion Documentation

This guide outlines the steps required for the entire MusicBrainz data pipeline. Follow the steps below to ensure a smooth data conversion and upload process.

## Prerequisites/What is already completed

- Given Musicbrainz is based on Relational Database (RDB) model, most of the entities (as distinct from relations and attributes, in RDB terms) are already reconciled during the conversion process, negating the need for OpenRefine.

## Data Processing

### Process Overview

1. **Navigate to the Target Folder**
    - Change directory to `linkedmusic-datalake/`. This will ensure that all the paths provided in this guide point to the correct locations. For each script, you can also run them without any arguments directly from the directory containing the scripts and the default argument values will point to the correct folders.

2. **Fetching the Latest Data**
    - Run the command below to download the latest `.tar.xz` dumps from the MusicBrainz public data sources:

        ```bash
        python code/musicbrainz/fetch.py --output_folder data/musicbrainz/raw/archived
        ```

    - The downloaded files are stored in:
        `data/musicbrainz/raw/archived/`
    - The script downloads the data from MusicBrainz, always choosing the latest dump.
    - The downloaded `.tar.xz` files include a `mbdump` folder with a single file containing all entities of that type. Each file is formatted with JSON Lines, where each line is a separate JSON record. The other files in the `.tar.xz` files aren't useful for data processing, they contain things like the timestamp of the dump and the data license.

3. **Extracting JSON Lines Files**
    - Execute the following command to extract JSON Lines files from the archives:

        ```bash
        python code/musicbrainz/untar.py --input_folder data/musicbrainz/raw/archived/ --output_folder data/musicbrainz/raw/extracted_jsonl/
        ```

    - The extracted files are located at:
        `data/musicbrainz/raw/extracted_jsonl/mbdump/`
    - The `doc/musicbrainz/layout.json` is a JSON file showing the list of fields for each entity type.

4. **Extracting Specific Unreconciled Fields and Reconciling them**
    - Execute the following command to extract specific unreconciled fields into CSV files for reconciliation. The fields are detailed below.

        ```bash
        python code/musicbrainz/extract_for_reconciliation.py --input_folder data/musicbrainz/raw/extracted_jsonl/mbdump/ --output_folder data/musicbrainz/raw/unreconciled/
        ```

    - It will extract the types for each entity type, except for those contained in the `IGNORE_TYPES` list. Those entity types don't have any `type` fields, so it's pointless to parse them.
    - Each entity type that has types except for `release-group` stores the types in the `type` field. For `release-group` they are stored in the `primary-type` and `secondary-types` fields.
    - Each type CSV will be named `f"{entity-type}_types.csv"`, and will be located in the `data/musicbrainz/raw/unreconciled` folder.
    - The script will also extract the tonality (called "key" in the MusicBrainz database) for the `work` entity type and will output them to a CSV named "keys.csv", and will be located in the same folder.
    - The script will also extract the genders for the `artist` entity type and will output them to a CSV named "genders.csv", and will be located in the same folder.
    - The script will also extract the languages for the `work` entity type and will output them to a CSV named "languages.csv", and will be located in the same folder. The languages are stored by MusicBrainz in the [ISO 639-3 format](https://en.wikipedia.org/wiki/ISO_639-3) ([full list](https://en.wikipedia.org/wiki/List_of_ISO_639-3_codes)), but to enable reconciliation, the CSV will have an additional column named "full_language" which will hold the full name corresponding to the ISO 639-3 code, using the `pycountry` library.
    - Follow the steps in `doc/musicbrainz/reconciliation.md` to reconcile the CSVs against Wikidata, and put the reconciled CSVs in the `data/musicbrainz/raw/reconciled` folder, naming each one `f"{entity_type}-types-csv.csv"`, `"keys-csv.csv"`, `"genders-csv.csv"`, or `"languages-csv.csv"`.

5. **Converting Data to RDF (Turtle Format)**
    - For each JSON Lines file, convert the data using:

        ```bash
        python code/musicbrainz/convert_to_rdf.py --input_folder data/musicbrainz/raw/extracted_jsonl/mbdump/ --reconciled_folder data/musicbrainz/raw/reconciled/ --config_folder code/musicbrainz/rdf_conversion_config/ --output_folder data/musicbrainz/rdf/
        ```

    - Notes on the script:
        - The script is optimized to be memory-efficient, but there's only so much you can do when one of the input files is >250GB.
        - The script uses disk storage to store the graph as it builds it to save on memory space. By default, this folder is `./store` from the script's working directory. The script will automatically delete the folder when it finishes, but if it crashes, it is recommended to delete the folder before running the script again.
        - By default, the script will ignore any data types that already have a corresponding file in the output directory. This is useful in the event that the program crashes and you only need to rerun the RDF conversion on the data that wasn't processed instead of the entire input directory.
        - Settings for queue sizes, as well as the number of parallel processes are in global variables at the beginning of the script
        - For ease of reading, the fields are processed in alphabetical order in `process_line`
        - For the `convert_date` function, if you call `Literal(...)` with `XSD.date` as datatype, it will eventually call the `parse_date` isodate function, but not during the constructor, making any exceptions it raises impossible to catch, which is why I manually call it and pass its value to the constructor
        - The same thing applies to the `convert_datetime` function with the `XSD.dateTime` datatype and the `parse_datetime` isodate function
        - The dictionary containing regex patterns for URLs has been moved to a separate module, `code/musicbrainz/url_regex.py` to reduce clutter in the main script
        - The class definition for the `MappingSchema` class was moved to a separate module, `code/musicbrainz/mapping_schema.py` to further reduce clutter in the main script
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

7. **Key Properties Extracted**
    - The conversion process extracts as many properties as it can from each entity type, searching the fields of the JSON file, as well as all relations in the `relations` field, and all attributes in the `attributes` field.

## Data Upload

- Upload all converted RDF files to Virtuoso for further use.

## Script Testing

If you're experimenting on the scripts, it's recommended to take a small subset of the data, to save time. As an example, to get the first 100000 lines from the `area` file, run the following command in a terminal:

```bash
head -n 100000 area.jsonl > small_area.jsonl
```

This greatly speeds up the processing, because some files have up to 5 million lines, and it is unnecessary to test against the entire dataset when making minor changes
