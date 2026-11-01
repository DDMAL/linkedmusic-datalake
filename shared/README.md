# Shared Elements

This folder contains shared scripts used across different databases, notably a generalized RDF conversion script and a wikidata API client.

The CSV converter recognizes complete Wikidata identifiers while preserving text,
external URLs and configured local identifiers. See the
[identifier contract](rdf_conversion/identifier_preservation.md) and run its tests
with `poetry run python scripts/check_offline.py` from the repository root.

The [shared evidence and lineage contract](ontology/README.md) describes the
dataset-specific observation models, keeps uncertainty separate from date
approximation and processing status, and supplies machine-readable schema and
SHACL validation shapes. Its optional PROV-O lineage profile requires actual
snapshot/run metadata; current converters do not fabricate that metadata.
