## 1: Procedure

### Prerequisites:
- All IDs and Wikidata links are already reconciled during the conversion process, eliminating the need for OpenRefine.

### Steps:
1. **Navigate to the target folder:**
   - Go to the `linkedmusic-datalake/musicbrainz/csv` directory.

2. **Fetch the latest data:**
   - Run the following command to download the latest tar.xz files from the MusicBrainz public data dumps:
     ```bash
     python3 fetch.py
     ```
   - The files will be saved in the local `data/raw/` folder.

3. **Extract the required files:**
   - Unzip and extract the necessary JSON Lines (jsonl) files by running:
     ```bash
     python3 untar.py
     ```
   - The extracted files will be located in the `data/raw/extracted_jsonl/mbdump/` folder.

4. **Convert data to CSV:**
   - Execute the conversion script:
     ```bash
     python3 convert_to_csv.py
     ```
   - This will generate a CSV file, named according to its entity type, in the `data/output/` folder.

5. **Output:**
   - The generated CSV files are ready for further processing.

---

## 2: Data Details

### Overview:
- The data can be downloaded from the provided link, typically selecting the latest version (e.g., `20240626-001001/`).
- The downloaded `.tar.xz` files contain a `mbdump` folder with files named by entity type (e.g., `area`, `artist`, `event`, `instrument`, `label`, `place`). Each file is in "JSON Lines" format, with each line representing a single record.

### Important Notes:
- **ID Attributes:** Each record has an `id` attribute, which serves as the primary key. When converting to CSV, this `id` is renamed to `{entity_type}_id` for clarity.
- **URI Conversion:** All IDs (e.g., `genre_id`, `artist_id`, `area_id`) are converted to URIs in the format: `https://musicbrainz.org/{entity_type}/{id}`.
- **Wikidata Links:** If a record is linked to a Wikidata entry by MusicBrainz bots, the link can be found under `"relations" > "resources" > "url"`. These are also extracted into the CSV.

---

## 3: Mapping

### Custom Predicate URLs:
- The following made-up predicate URLs are used in the data conversion:
  - `"packaging"`: `https://musicbrainz.org/packaging`
  - `"packaging-id"`: `https://musicbrainz.org/packaging`
  - `"media_pregap_id"`: `https://musicbrainz.org/pregap`
  - `"media_discs_id"`: `https://musicbrainz.org/disc`

---

## Deprecated: Experiment Data Sets

### Experiment Guidelines:
- For experimental purposes, it is recommended to use a small portion of each data dump.
- Use the following bash command to extract the first 3000 entries of a specific entity (e.g., `area`):
  ```bash
  head -n 3000 "area" > "test_area"
  ```
- Apply the same process to other data dumps if needed.