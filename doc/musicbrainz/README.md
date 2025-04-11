# MusicBrainz Data Conversion Documentation

This guide outlines the steps required to preprocess, convert, and postprocess MusicBrainz data. Follow the steps below to ensure a smooth data conversion and upload process.

## Data Preprocessing

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
   - Download the adjusted data from the specified link, typically selecting the most recent version.
   - The downloaded `.tar.xz` files include a `mbdump` folder with entity-specific files. Each file is formatted with JSON Lines, where each line is a separate JSON record.

3. **Extracting JSON Lines Files**
   - Execute the following command to extract JSON Lines files:
      ```bash
      python3 code/musicbrainz/untar.py --input data/musicbrainz/raw/archived --output data/musicbrainz/raw/extracted_jsonl
      ```
   - The extracted files are located at:
      `linkedmusic-datalake/data/raw/extracted_jsonl/mbdump/`

4. **Converting Data to RDF (Turtle Format)**
   - For each JSON Lines file, convert the data using:
      ```bash
      python3 code/musicbrainz/convert_to_rdf.py --intput data/musicbrainz/raw/extracted_jsonl/mbdump/ --output data/musicbrainz/rdf/
      ```
   - Note:
      - Run the script individually for each file to monitor progress and manage memory usage.
      - TODO: implement batch processing to handle the entire folder at once.
   - The generated RDF files are saved in the `linkedmusic-datalake/data/musicbrainz/rdf/` directory.

5. **Retrieving Genre Information**
   - Run the following script to scrape genres along with their reconciled WikiData IDs:
     ```bash
     python3 code/musicbrainz/get_genre.py --output ./data/musicbrainz/rdf/
     ```
   - The updated RDF is stored in `linkedmusic-datalake/data/musicbrainz/rdf/`.

6. **Key Properties Extracted**
   - The conversion process extracts:
      - Name, type, aliases, genre.
      - Relation (among different MusicBrainz entity types).
      - Relation (url link relations, including those with WikiData).
         - MusicBrainz automatically reconcile the main entities against WikiData. If an entity is not reconciled in MusicBrainz, it's most likely that it's not present on WikiData.
         - Note that the MusicBrainz `type` properties are not reconciled to WikiData, so a manual reconciliation with OpenRefine may be necessary.

## Data Upload

- Upload all converted RDF files to Virtuoso for further use.

## Deprecated: Experimental Data Sets

### Experimental Guidelines
- For testing purposes, consider using a small subset of each data dump.
- To extract the first 3000 entries from a specific entity (e.g., `area`), use:
  ```bash
  head -n 3000 area > test_area
  ```
- Repeat the process for other data dump files as needed.
