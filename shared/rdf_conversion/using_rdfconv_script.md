# General RDF Conversion Script: User Guide

This guide is intended for users who wish to utilize the scripts located in `/shared/rdfconv` (i.e. the general RDF conversion script and its auxiliary scripts) to convert tabular data (CSV files) into RDF linked data (TTL).

## 1. Prerequisites

Before starting RDF conversion, you should have reconciled the dataset against Wikidata following the [Data Reconciliation Guideline](https://github.com/DDMAL/linkedmusic-datalake/wiki/Data-Reconciliation-Guidelines).

The general RDF conversion script expects as input CSV files.

This script is not optimized to convert very large datasets (i.e., any dataset that would result in a Turtle file larger than roughly 2 GB), and serialization in such cases may take a very long time to complete. Additionally, since it stores all RDF triples in memory before serialization, it is subject to a hard limit determined by available RAM. For very large datasets, consider writing a custom RDF conversion script (e.g. `musicbrainz/src/convert_to_rdf.py`).

### 1.1 Note: Column Fill-Down

When exporting from OpenRefine in record mode, you may notice that some rows contain empty cells. This is expected (see [OpenRefine documentation on Records](https://openrefine.org/docs/manual/exploring#rows-vs-records)). The RDF conversion script automatically performs a _fill-down_ to ensure each row is complete.

For example:

```csv
Name,Email,Phone
Alice,a@example.com,123-456
,a.work@example.com,
Bob,b@example.com,789-000
,,789-001
Charlie,c@example.com,
```

Becomes:

```csv
Name,Email,Phone
Alice,a@example.com,123-456
Alice,a.work@example.com,123-456
Bob,b@example.com,789-000
Bob,b@example.com,789-001
Charlie,c@example.com,
```

- Note: A more detailed explanation of the fill-down logic can be found in the [Guide to RDF Config File Syntax](./rdf_config_syntax.md#211-note-primary_key-and-fill-down); the reader does not need to consult it now, as they will be directed to it later in this guide.

## 2. Completing The Configuration File

The steps below must be completed before running the general RDF conversion scripts. 

### Step 1: Store all reconciled CSV in one directory

- All reconciled CSVs pertaining to a dataset should be stored inside the same directory.
- Only one TTL file will be outputted for CSVs in a directory
  - Example: If `tune-reconciled.csv`and `recordings-reconciled.csv` are both stored in `thesession/data/reconciled/`, their data will all be part of `thesession.ttl`.

### Step 2: Create a TOML Configuration file

- Check if a configuration file already exists for the dataset you want to convert. It is likely to be found in `shared/rdf_config`.

  - If you found a configuration file, you can update it and build on top of its existing ontology. See [Alternative Step 2](#alternative-step-2-update-the-config-file)
  - If no configuration file exists, continue to follow this section

- Make sure that your working directory is `/shared`
  - All scripts in `/shared/rdfconv` must be run as module from `/shared` because they import `shared/wikidata_utils`
- Run the following command to create a configuration file

```bash
python -m rdfconv.tomlgen <path to csv folder> --output <config output path>
```

In the case of The Session, the command looks like:

```bash
python -m rdfconv.tomlgen ../thesession/data/reconciled --output rdf_config/thesession.toml
```

- A new TOML configuration will be created at your select output path.

- Note: Paths written within config files are currently relative to the script directory (`/shared/rdfconv`). They will be updated to be relative to `/shared` in a future pull request, after `origin/theglobaljukebox_rdf` has been merged.

### Alternative Step 2: Update the Config File

- If a config file already exists for your dataset, and you wish to build on top of what has already been done, you can follow this section.

- Open the config file and find the `csv_folder` field under the `[general]` table

  - For example, in `shared/rdf_config/thesession.toml`, the `csv_folder` is `"../../thesession/data/reconciled"`
  - Note: Paths in the config files are currently relative to the script directory (`/shared/rdfconv`). They will be updated to be relative to `/shared/` in a future pull request, after `origin/theglobaljukebox_rdf` has been merged.

- Either move your reconciled CSV files to the folder specified in `csv_folder`, or update `csv_folder` to point to where your CSVs are stored.

- (Optional but recommended) Make a backup copy of the existing config file to use as a reference while manually filling the new config. You can delete the old config once you have successfully converted your dataset to RDF.

- The purpose of running an update is to ensure that the column names in the config file match those in the reconciled CSVs. 

  - During an update, new column names are added to the config file if they are not present already, while outdated column fields and their values are removed from the config file.
  - Changes will be logged to standard output by default.
  - If you don't yet understand why there are CSV column names in the config file, don’t worry — we’ll walk through it in [Step 3](#step-3-understand-what-is-in-the-config-file).

- Run the following command to update the configuration file:

```bash
python -m rdfconv.tomlgen --update <config_path>
```

In the case of The Session, the command looks like:

```bash
python -m rdfconv.tomlgen --update rdf_config/thesession.toml
```
### Step 3: Manually Filling the Config File 

- This is where you decide the ontology of your TTL file. It is by far the most demanding part of this guide.

- Complete this step by reading through [Guide to RDF Config File Syntax](./rdf_config_syntax.md) and by following the instructions at the end, which will help you fill the config file. 


## 3. Verifying the Config File

### Step 1: Add Wikidata Labels to Config File

- Run the following command to add Wikidata property labels as comments in the config file (e.g. `"P31"` -> `# instance of (P31)`)

```bash
python -m rdfconv.labels <path to config>
```

For example:

```bash
python -m rdfconv.labels rdf_config/thesession.toml
```

- Look at all the labels in comments, make sure they match what you expect — if it doesn't, you may have entered the wrong PID.

- Rerun the label command each time you modify any PIDs in the config.

### Step 2: Test Run RDF conversion

- Under the `[general]` table, set `test_mode` to `true` (no uppercase).

- A test run will sample 20 rows from each CSV file instead of trying to convert entire files.

- Run the following command to start RDF conversion

```bash
python -m rdfconv.convert <path to config>
```

For example:

```bash
python -m rdfconv.convert rdf_config/thesession.toml
```
- If you fail the script's input validation, please fix the config according to the error message. 

- If the conversion process is successful, the output TTL file will be `{name}_test.ttl`, at your specified `rdf_output_folder`

- Try reading through the TTL file to see if it matches what you expected. 

- Change `test_mode` back to `false` once you are done testing

- Note: please [update Wikidata labels](#step-1-add-wikidata-labels-to-config-file) if you changed any Wikidata PID after testing 

Congratulations, you are now ready to convert your dataset to RDF.

## 4. Running the conversion script
- Run the following command to start RDF conversion

```bash
python -m rdfconv.convert <path to config>
```

For example:

```bash
python -m rdfconv.convert rdf_config/thesession.toml
```

- The TTL file can take a while to serialize if your dataset is large

- Once the conversion is finished, the output TTL file can be found at the `rdf_output_folder` you specified in the config.

- You can now try uploading the data to Virtuoso by following [this guide on the wiki](https://github.com/DDMAL/linkedmusic-datalake/wiki/Importing-and-Updating-Data-on-Virtuoso)
	- Note: make sure you follow the "Update Data" section if your dataset has already been uploaded to Virtuoso before.
