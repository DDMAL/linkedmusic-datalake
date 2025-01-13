### 11-8-2024

**RISM**:
- No progress. Andrew responded under the issue, indicating that my data is incorrect. I have paused experimentation with this data, so progress remains the same as last week.

**MusicBrainz & Other Potential Databases**:
- Applied a new approach using JSON logic
- Merged with old CSV2RDF logic for parsing JSON file

#### Advantages of Using JSON Logic:
1. **Data Structure Preservation**: RDF closely aligns with JSON’s structure, perfectly conserving complex data layouts without losing fidelity—unlike CSV, which struggles with nested or hierarchical data.
2. **Simplified Reconciliation**: CSV files introduced excessive, nested columns due to the JSON structure, complicating reconciliation efforts. With RDF, we avoid this, making reconciliation more straightforward.
3. **Data Integrity**: Unlike CSV, where data might be truncated or result in numerous blank cells, RDF maintains full data integrity.
4. **Direct RDF Import for Reconciliation**: RDF files can be directly imported into OpenRefine for reconciliation, allowing us to skip the additional CSV conversion step.
5. **Old Functions Preserved**: We can apply the exact same functions in the old CSV2RDF, like marking language, detecting datatype, etc.

#### Disadvantage:
1. **Query Complexity**: RDF is implemented using blank nodes, which can make querying the data more challenging.

### 11-15-2024

**RISM**:
- No progress was made this week, as the challenges from the previous week remain unresolved.

**RDF Reconciliation**:
- Adjustments to the process included:
  - Removing type recognition.
  - Adding a "tags" column for testing purposes.

#### Challenges Encountered:
- **RDF Reconciliation**:
  - **Issue**: OpenRefine allows RDF input but does not support RDF output, making it challenging to preserve the reconciliation data.
  - **Potential Solution**: Exploring alternative methods to merge OpenRefine data with the original RDF could address this issue.
  - **Possible Advantage**: Retaining both the old reconciliation data and the original RDF file may streamline database updates in the long term.

### 11-22-2024

**RISM**:
- No progress was made this week due to unresolved challenges from the previous week.

**RDF Reconciliation**:
- **Issue**:
  - Encountered a problem during the process of merging reconciled CSV data into RDF. Some blank nodes were not correctly linked, resulting in inaccurate RDF output.
  - Efforts are ongoing to debug and resolve the issue.
  - If an object is a list of blank nodes, only the first item refers to the correct parent.

### 01-10-2025

**RDF CSV Merging New Features**:
**Steps**:
1. Retrieve all raw JSON from MusicBrainz.
2. Convert the JSONs into RDFs. This conserves all schema and structures. Also, extract the predicates to manually reconcile them.
   > Note: Junjun said that due to the structure of JSON, there might be many redundant blank nodes in the converted RDF.
3. Upload these RDFs onto OpenRefine and reconcile following the old processes.
4. Run merge.py to merge the output CSV from OpenRefine into the raw RDF. This step will modify the raw RDF, replacing all reconcilable literal objects as URIs.

**Difficulties Encountered**:
- There might be infinitely many predicates, making reconciliation extremely difficult. We can categorize them by using a single URI for a group of similar predicates.
- Merging blank nodes is difficult since the internal code for each blank node when reading the RDF is different every time. Tracing the reconciled CSV is necessary during the iteration of the raw RDF.
- Using a stack data structure to iterate the RDF structure to effectively trace the blank nodes.

### 01-13-2025

**Reconciliation discussion**:
Countries and citizenships appears in some tags and genres for artist or recordings. Do we consider it to be the language, the culture, or the citizenship of the artist?
"Death", "Hate" and similar genres, do we consider the original meaning of them or should they be considered as special literature genres?
Which one to use for "Person"? Q5 or Q215627
"Artist" as musician (Q639669)?
"Work" as work (Q386724) or work (Q268378)?
