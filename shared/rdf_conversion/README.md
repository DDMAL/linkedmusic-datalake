# RDF Conversion Documentation

This folder contains user guides and technical documentation for converting tabular datasets (e.g., CSV files) to RDF linked data (TTL) as part of the LinkedMusic project. It includes instructions for using the general RDF conversion script, configuring property mappings, and working with Wikidata APIs.

## Contents

### General RDF Conversion Script Documentation

- **[using_rdfconv_script.md](./using_rdfconv_script.md):** User guide for the general RDF conversion script, including prerequisites, configuration, and running the conversion.
- **[rdf_config_syntax.md](./rdf_config_syntax.md):** Detailed guide to the syntax and structure of the RDF config file required by the conversion script.
- **[identifier_preservation.md](./identifier_preservation.md):** Accepted identifier forms, literal/local-key precedence, CSV parsing limits, regression coverage and regeneration checks.

### Property Mapping Guide

- **[rdf_property_mapping_guide.md](./rdf_property_mapping_guide.md):** Use `prop_cli.py` to find candidate properties, verify their definitions and preserve source distinctions when a Wikidata mapping would lose information.

### Wikidata API Documentation

- **[wikidata_apis.md](./wikidata_apis.md):** Overview of Wikidata APIs and how to use the `WikidataAPIClient`

## Notes

- Converter mechanics and input contracts live here alongside the code. Cross-dataset modeling policy lives in the [wiki](https://github.com/DDMAL/linkedmusic-datalake/wiki/RDF-Conversion-Guidelines).
- Run `poetry run python scripts/check_offline.py` from the repository root. See the [current validation and deployment status](../../README.md#preservation-and-evaluation-status).
