# Shared Elements

This folder contains shared scripts used across different databases, notably a generalized RDF conversion script and a wikidata API client.

The CSV converter recognizes complete Wikidata identifiers while preserving text,
external URLs and configured local identifiers. See the
[identifier contract](rdf_conversion/identifier_preservation.md) and run its tests
with `poetry run python scripts/check_offline.py` from the repository root.
