# Data Preprocessing 

### Prerequisites:
- All IDs and Wikidata links are already reconciled during the conversion process, eliminating the need for OpenRefine.

### Steps:
1. **Navigate to the target folder:**
   - Go to the `linkedmusic-datalake/code/musicbrainz` directory.

2. **Fetch the latest data:**
   - Run the following command to download the latest tar.xz files from the MusicBrainz public data dumps:
     ```bash
     python3 fetch.py
     ```
   - The files will be saved in the local `linkedmusic-datalake/data/musicbrainz/raw/archived/` folder.

3. **Extract the required files:**
   - Unzip and extract the necessary JSON Lines (jsonl) files by running:
     ```bash
     python3 untar.py
     ```
   - The extracted files will be located in the `linkedmusic-datalake/data/raw/extracted_jsonl/mbdump/` folder.

4. **Convert data to CSV:**
   - Execute the conversion script:
     ```bash
     python3 convert_to_rdf.py
     ```
   - This will generate a RDF file in turtle format, named according to its entity type, in the `linkedmusic-datalake/musicbrainz/data/output/` folder.

5. **Output:**
   - The generated RDF files are ready for further processing.
> Extracted properties: name, type, aliases, genre, relation to all other musicbrainz entity types, and all relations to outside links, including WikiData.

---

# Data Postprocessing

### Overview:
- The data can be downloaded from the provided link, typically selecting the latest version.
- The downloaded `.tar.xz` files contain a `mbdump` folder with files named by entity type (e.g., `area`, `artist`, `event`, `instrument`, `label`, `place`). Each file is in "JSON Lines" format, with each line representing a single JSON format record.
- All entity types are reconciled to WikiData in OpenRefine automatically. If an entity is not reconciled, then it might not be present on WikiData.
- None of MusicBrainz types are reconciled to WikiData. Consider Reconciling it using OpenRefine.

---

# Data Upload
- Upload all RDF to Virtuoso.

# Deprecated: Experimental Data Sets

### Experiment Guidelines:
- For experimental purposes, it is recommended to use a small portion of each data dump.
- Use the following bash command to extract the first 3000 entries of a specific entity (e.g., `area`):
  ```bash
  head -n 3000 "area" > "test_area"
  ```
- Apply the same process to other data dumps if needed.