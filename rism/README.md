# RISM Data Processing Guide

This document explains the process for handling RISM (Répertoire International des Sources Musicales) data provided by Andrew Hankinson.

## Prerequisites

### OpenRefine Setup

1. Install [OpenRefine](https://openrefine.org/), version 3.9 or later.
2. Install [RDF-transform](https://github.com/AtesComp/rdf-transform) to convert OpenRefine project data to RDF-based formats using the RDF-extension.

> Note: the RDF-transform extension does not work on browsers Firefox or Safari.

### Mapping Configuration

- Review the mapping file at `rism/src/ontology/mapping.json`.

> This mapping file contains mappings for some properties used in the RISM dataset

- Detailed mapping decisions are documented in `rism/src/ontology/mappingWithLog.json5`.

## Processing Workflow

### 1. Splitting the Graph

1. Open a terminal in the `linkedmusic-datalake` directory.
2. Navigate to `rism/src`.
3. Run the splitting script using:
    - `python3 force_split.py` to use the default 500MB chunk size, or
    - `python3 force_split.py [size]` to specify a custom chunk size (e.g., `python3 force_split.py 500` for 500MB).
    > Note: ensure the path to input_file and output_dir are configured properly within the `__main__` function of `force_split.py`. The processed files with corrected predicates will by default be saved to `rism/data/split_output`. It is highly recommended to store the data files outside of this github repo.

### 2. Processing with OpenRefine

> Note: Red circles or rectangles in the screenshots indicate the elements you need to click. Other annotations are for reference only.

For each file in the `split_output` directory (e.g., `part_1.ttl`, where all blank nodes from the original RDF n-triples file have been converted to specific URIs):

1. **Create a New OpenRefine Project**:
    - Open the target file located within your `split_output` directory e.g., `rism/data/split_output/part_1.ttl`.

2. **Apply the RDF Skeleton for RISM**:
    > Follow the instructions in sequential order:
    ![RDF Skeleton](./doc/assets/01.png)
    ![RDF Skeleton](./doc/assets/02.jpg)

    > Note: The ontology file has been moved to `rism/src/ontology`.

    ![RDF Skeleton](./doc/assets/03.jpg)
    ![RDF Skeleton](./doc/assets/04.png)

3. **Reconcile the Type Column**:
    ![RDF Skeleton](./doc/assets/05.jpg)
    ![RDF Skeleton](./doc/assets/06.png)
    
    Use the `instance_of.json` file located in `rism/openrefine/history/`.

    > Note: The OpenRefine step files used to be in `rism/data/reconciled`.

    ![RDF Skeleton](./doc/assets/07.jpg)

    > Note: OpenRefine may prompt you to select the file multiple times due to a bug. Simply reselect the same file each time.

    ![RDF Skeleton](./doc/assets/08.jpg)

4. **Reconcile All Cells of the "Label" Predicates for Human/Person Subjects**:
    ![RDF Skeleton](./doc/assets/09.jpg)
    ![RDF Skeleton](./doc/assets/10.jpg)

5. **Apply Judgments to Unreconciled Cells**:
    > **IMPORTANT**: Make informed decisions for unreconciled cells. This repository does not include predefined judgments, as this process is for testing purposes.
    ![RDF Skeleton](./doc/assets/11.jpg)
    ![RDF Skeleton](./doc/assets/12.jpg)

6. **Reconcile Other Relevant Columns** using the other json files located in `rism/openrefine`. Detailed reconciliation procedures for the relevant columns are located in `rism/doc/reconciliation_procedures`.

7. **Export to CSV**:
    Go to `Export > Comma-separated value`.

8. **Repeat Steps 1-7** for all remaining files located in the designated split output folder, by default located at `rism/data/split_output/`.

9. **Store All Reconciled Files** (in `.nt` format) within a folder titled `split_input` (e.g. on your desktop).

> In some cases, the output file might be empty due RDF-transform error.
> Reapply the RDF transform (repeat step 2) if you encounter an output error.

### 3. Converting the reconciled CSV to Turtle

Ensure that the reconciled CSV files are in the `rism/data/reconciled/` folder.

Then, from the `linkedmusic-datalake` directory, run the following command to convert the CSV files to Turtle:

```bash
python convert_to_rdf.py --input_folder rism/data/reconciled/ --mappings_folder rism/src/mappings/ --output_folder rism/data/rdf/
```

Each CSV file will be converted into a Turtle file in the `rism/data/rdf/` folder.

For more details on the RDF conversion process, read [`rdf_conversion.md`](./doc/rdf_conversion.md)
