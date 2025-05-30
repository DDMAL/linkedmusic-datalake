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
        `linkedmusic-datalake/data/musicbrainz/raw/archived/`
    - The script downloads the data from MusicBrainz, always choosing the latest dump.
    - The downloaded `.tar.xz` files include a `mbdump` folder with a single file containing all entities of that type. Each file is formatted with JSON Lines, where each line is a separate JSON record. The other files in the `.tar.xz` files aren't useful for data processing, they contain things like the timestamp of the dump and the data license.

3. **Extracting JSON Lines Files**
    - Execute the following command to extract JSON Lines files from the archives:

        ```bash
        python code/musicbrainz/untar.py --input_folder data/musicbrainz/raw/archived --output_folder data/musicbrainz/raw/extracted_jsonl
        ```

    - The extracted files are located at:
        `linkedmusic-datalake/data/musicbrainz/raw/extracted_jsonl/mbdump/`

4. **Extracting Types and Reconciling them**
    - Execute the following command to extract the types for each entity type into CSV files for reconciliation:

        ```bash
        python code/musicbrainz/extract_types.py --input_folder data/musicbrainz/raw/extracted_jsonl/mbdump --output_folder data/musicbrainz/raw/types
        ```

    - It will extract the types for each entity type, except for those contained in the `IGNORE_TYPES` list, those don't have any types, so it's pointless to parse them.
    - Each CSV will be named "{entity-type}_types.csv", and will be located in the `data/musicbrainz/raw/types` folder
    - Follow the steps in `doc/musicbrainz/reconciliation.md` to reconcile the types against Wikidata, and put the reconciled CSVs in the `data/musicbrainz/raw/types-reconciled` folder, naming each one `f"{entity_type}-types-csv.csv"`

5. **Converting Data to RDF (Turtle Format)**
    - For each JSON Lines file, convert the data using:

        ```bash
        python code/musicbrainz/convert_to_rdf.py --input_folder data/musicbrainz/raw/extracted_jsonl/mbdump/ --type_folder data/musicbrainz/raw/types_reconciled --config_folder doc/musicbrainz/rdf_conversion_config --output_folder data/musicbrainz/rdf/
        ```

    - Note on the script:
        - The script is optimized to be memory-efficient, but there's only so much you can do when one of the input files is >250GB.
        - The script uses disk storage to store the graph as it builds it to save on memory space. By default, this folder is `./store` from the script's working directory. The script will automatically delete the folder when it finishes, but if it crashes, it is recommended to delete the folder before running the script again.
        - By default, the script will ignore any data types that already have a corresponding file in the output directory. This is useful in the event that the program crashes and you only need to rerun the RDF conversion on the data that wasn't processed instead of the entire input directory.
        - Settings for queue sizes, as well as the number of parallel processes are in global variables at the beginning of the script
        - For ease of reading, the fields are processed in alphabetical order in `process_line`
        - For the `convert_date` function, if you call `Literal(...)` with `XSD.date` as datatype, it will eventually call the `parse_date` isodate function, but not during the constructor, making any exceptions it raises impossible to catch, which is why I manually call it and pass its value to the constructor
        - The same thing applies to the `convert_datetime` function with the `XSD.dateTime` datatype and the `parse_datetime` isodate function
        - The dictionary containing regex patterns for URLs has been moved to a separate module, `code/musicbrainz/url_regex.py` to reduce clutter in the main script
    - The generated RDF files are saved in the `linkedmusic-datalake/data/musicbrainz/rdf/` directory.
    - Documentation regarding decisions made for properties is located in the `doc/musicbrainz/rdf_conversion.md` file
    - Documentation regarding the `relations` field can be found in the `doc/musicbrainz/relations.md` file

6. **Retrieving Genre Information**
    - Run the following script to scrape genres along with their reconciled WikiData IDs:

        ```bash
        python code/musicbrainz/get_genre.py --output ./data/musicbrainz/rdf/
        ```

    - The script is rate-limited to 1 request per second following MusicBrainz' [rate limit guides](https://musicbrainz.org/doc/MusicBrainz_API/Rate_Limiting#How_throttling_works)
    - The script also provides a user-agent header, following the same guidelines
    - The RDF is stored in `linkedmusic-datalake/data/musicbrainz/rdf/`

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
