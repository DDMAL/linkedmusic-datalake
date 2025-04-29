# MusicBrainz Data Conversion Documentation

This guide outlines the steps required to preprocess, convert, and postprocess MusicBrainz data. Follow the steps below to ensure a smooth data conversion and upload process.

### Prerequisites/What is already completed:
- Given Musicbrainz is based on Relational Database (RDB) model, most of the entities (as distinct from relations and attributes, in RDB terms) are already reconciled during the conversion process, negating the need for OpenRefine.


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
      `linkedmusic-datalake/data/musicbrainz/raw/extracted_jsonl/mbdump/`

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
   - The files will be saved in the local `linkedmusic-datalake/data/musicbrainz/raw/archived/` folder. [with suffix ".tar.xz"; the data from the latest download, exceeding gitHub's storage limit, is stored in Junjun Cao's DDMAL-033 desktop]


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

# Data Postprocessing

### Overview:
- The data can be downloaded from the provided link; it's generally recommended to select the latest version.
- The downloaded `.tar.xz` files contain a folder named `mbdump`.  Within this folder, data is organized into files named by entity type (e.g., `area`, `artist`, `event`, `instrument`, `label`, `place`). Each file is in "JSON Lines" format, with each line representing a single JSON record.
- MusicBrainz's relational database structure allows its data to be categorized as entities, relations, and attributes. All entity data has already been reconciled as much as possible to WikiData in OpenRefine automatically. If an entity is not reconciled, then it might not be present on WikiData.
- None of MusicBrainz types are reconciled to WikiData. Consider Reconciling it using OpenRefine.

---

# Data Upload
- Upload all RDF to Virtuoso.

# Deprecated: Experimental Data Sets

### Experiment Guidelines:
- For experimental purposes, it is recommended to use a small portion of each data dump.
- Use the following bash command to extract the first 3000 entries of a specific entity (e.g., `area`):
  ```bash
  head -n 3000 area > test_area
  ```
- Repeat the process for other data dump files as needed.

### Others
- AccountForReconciliation_MusicBrainz.txt records the logs or comments for reconciliation of properties or types.
