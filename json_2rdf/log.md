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
5. **Old functions preserved**: We can apply the exact same functions in the old CSV2RDF, like marking language, detecting datatype, etc.

#### Disadvantage:
1. **Query Complexity**: RDF is implemented using blank nodes, which can make querying the data more challenging.