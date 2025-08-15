# Dig That Lick Documentation

This directory contains all documentation related to ingesting Dig That Lick datasets.

## Files Overview

### Main Files

1. **`digthatlick_data_schema.md`**: Introduce the user to Dig That Lick and explain the data schema of DTL1000.
2. **`workflow.md`**: Describes the workflow for processing the DTL1000 dataset, from fetching raw data to splitting, cleaning, reconciling, and converting it to RDF.
3. **`reconciliation_procedures.md`**: A subsection of the workflow. Detailed steps for reconciling the DTL1000 dataset using OpenRefine, including transformations and export guidelines.

### Subdirectories

- **`reconciliation_history/`**: Contains JSON files generated in OpenRefine for applying reconciliation histories to specific CSV files. Files include:
  - `dtl_performers_history.json`
  - `dtl_solos_history.json`
  - `dtl_tracks_history.json`
