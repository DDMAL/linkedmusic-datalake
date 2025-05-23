# MusicBrainz Data Conversion Documentation

This guide outlines the steps required to preprocess, convert, and postprocess MusicBrainz data. Follow the steps below to ensure a smooth data conversion and upload process.

## Prerequisites/What is already completed

- Given Musicbrainz is based on Relational Database (RDB) model, most of the entities (as distinct from relations and attributes, in RDB terms) are already reconciled during the conversion process, negating the need for OpenRefine.

## Data Processing

### Process Overview

1. **Navigate to the Target Folder**
    - Change directory to `linkedmusic-datalake/`.

2. **Fetching the Latest Data**
    - Run the command below to download the latest `.tar.xz` dumps from the MusicBrainz public data sources:

        ```bash
        python3 code/musicbrainz/fetch.py
        ```

    - The downloaded files are stored in:
        `linkedmusic-datalake/data/musicbrainz/raw/archived/`
    - The script downloads the data from musicbrainz, always choosing the latest dump.
    - The downloaded `.tar.xz` files include a `mbdump` folder with entity-specific files. Each file is formatted with JSON Lines, where each line is a separate JSON record. The other files in the `.tar.xz` files aren't useful for data processing, they contain tings like the tmestamp of the dump and the data license.

3. **Extracting JSON Lines Files**
    - Execute the following command to extract JSON Lines files from the archives:

        ```bash
        python3 code/musicbrainz/untar.py --input_folder data/musicbrainz/raw/archived --dest_folder data/musicbrainz/raw/extracted_jsonl
        ```

    - The extracted files are located at:
        `linkedmusic-datalake/data/musicbrainz/raw/extracted_jsonl/mbdump/`

4. **Converting Data to RDF (Turtle Format)**
    - For each JSON Lines file, convert the data using:

        ```bash
        python3 code/musicbrainz/convert_to_rdf.py --input_folder data/musicbrainz/raw/extracted_jsonl/mbdump/ --output_folder data/musicbrainz/rdf/
        ```

    - Note:
        - The script is optimized to be memory-efficient, but there's only so much you can do when one of the input files is >250GB.
        - The script uses disk storage to store the graph as it builds it to save on memory space. By default, this folder is `./store` from the script's working directory. The script will automatically delete the folder when it finishes, but if it crashes, it is recommended to delete the folder before running the script again.
        - By default, the script will ignore any data types that already have a corresponding file in the output directory. This is useful in the event that the program crashes and you only need to rerun the RDF conversion on the data that wasn't processed instead of the entire input directory.
        - Settings for queue sizes, as well as the number of parallel processes are in global variables at the beginning of the script
    - The generated RDF files are saved in the `linkedmusic-datalake/data/musicbrainz/rdf/` directory.

5. **Retrieving Genre Information**
    - Run the following script to scrape genres along with their reconciled WikiData IDs:

        ```bash
        python3 code/musicbrainz/get_genre.py --output ./data/musicbrainz/rdf/
        ```

    - The RDF is stored in `linkedmusic-datalake/data/musicbrainz/rdf/`

6. **Key Properties Extracted**
    - The conversion process extracts:
        - Name, type, aliases, genre.
        - Relation (among different MusicBrainz entity types).
        - Relation (url link relations, including those with WikiData).
            - MusicBrainz automatically reconciles the main entities against WikiData. If an entity is not reconciled in MusicBrainz, it's most likely that it's not present on WikiData. Thus, manual reconciliation with OpenRefine is largely redundant.
            - Note that the MusicBrainz `type` properties are not reconciled to WikiData, so a manual reconciliation with OpenRefine may be necessary.

## Data Upload

- Upload all converted RDF files to Virtuoso for further use.

## Script Testing

If you're experimenting on the scripts, it's recommended to take a small subset of the data, to save time. As an example, to get the first 100000 lines from the `area` file, run the following command:

```bash
head -n 100000 area.jsonl > small_area.jsonl
```
