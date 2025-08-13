# The Global Jukebox Manual

This file details the entire process for the The Global Jukebox database, from fetching the data all the way to converting it into RDF. Note that because The Global Jukebox does not update, these steps will not need to be redone once the process has been finalized.

In general, the [Current Pipeline for Adding a New Dataset](https://github.com/DDMAL/linkedmusic-datalake/wiki/Current-Pipeline-for-Adding-a-New-Dataset) instructions found on the wiki can be followed as written.

## Obtaining a data dump

The Global Jukebox data dump can be found in the 8 repositories in [The Global Jukebox Github](https://github.com/theglobaljukebox). 

## Reconciling the data

Note that for each dataset in The Global Jukebox, the `codings.csv` file is skipped, as it does not contain easily reconcilable data (see [Discussion #322](https://github.com/DDMAL/linkedmusic-datalake/discussions/322)).

Also note that since every section of The Global Jukebox contains a `societies.csv` file, it may be prudent to merge them into one, as they appear to overlap significantly.

Refer to [reconcile_procedures.md](https://github.com/DDMAL/linkedmusic-datalake/blob/main/doc/theglobaljukebox/reconcile_procedures.md) for a step by step guide on The Global Jukebox reconciliation and [general_reconciliation_notes.md](https://github.com/DDMAL/linkedmusic-datalake/blob/main/doc/theglobaljukebox/general_reconciliation_notes.md) for notes on specific entities and properties.

Refer to [Step 3](https://github.com/DDMAL/linkedmusic-datalake/wiki/Current-Pipeline-for-Adding-a-New-Dataset#3-reconcile-the-data-to-wikidata) of the general pipeline instructions for general reconciliation information.

## Converting to RDF

The current TOML file with property matches can be found in [/code/rdf_config/theglobaljukebox.toml](https://github.com/DDMAL/linkedmusic-datalake/blob/main/code/rdf_config/theglobaljukebox.toml).

Refer to [Step 4](https://github.com/DDMAL/linkedmusic-datalake/wiki/Current-Pipeline-for-Adding-a-New-Dataset#4-convert-the-reconciled-data-to-rdf) of the general pipeline instructions for RDF conversion information.

## Uploading to Virtuoso

Refer to [Step 5](https://github.com/DDMAL/linkedmusic-datalake/wiki/Current-Pipeline-for-Adding-a-New-Dataset#5-import-the-rdf-files-to-virtuoso) of the general pipeline instructions for how to upload the RDF files to Virtuoso.

## Final steps

Refer to [Steps 6-10](https://github.com/DDMAL/linkedmusic-datalake/wiki/Current-Pipeline-for-Adding-a-New-Dataset) of the general pipeline instructions for how to create a graph ontology visual, performing and documenting test SPARQL queries, and updating the NLQ2SPARQL context.
