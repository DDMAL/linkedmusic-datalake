# RDF Conversion Documentation

This folder contains user guides and technical documentation for converting tabular datasets (e.g., CSV files) to RDF linked data (TTL) as part of the LinkedMusic project. It includes instructions for using the general RDF conversion script, configuring property mappings, and working with Wikidata APIs.

## Contents

### General RDF Conversion Script Documentation

- **[using_rdfconv_script.md](./using_rdfconv_script.md):** User guide for the general RDF conversion script, including prerequisites, configuration, and running the conversion.
- **[rdf_config_syntax.md](./rdf_config_syntax.md):** Detailed guide to the syntax and structure of the RDF config file required by the conversion script.

### Property Mapping Guide

- **[rdf_property_mapping_guide.md](./rdf_property_mapping_guide.md):** How to map dataset relations to Wikidata properties, including usage of `prop_cli.py`. Useful for anyone building a Wikidata-style ontology.

### Wikidata API Documentation

- **[wikidata_apis.md](./wikidata_apis.md):** Overview of Wikidata APIs and how to use the `WikidataAPIClient`

## Notes

- Documents in this folder may be moved to the [Wiki](https://github.com/DDMAL/linkedmusic-datalake/wiki/RDF-Conversion-Guidelines). We still must decide how to organize documentation.
