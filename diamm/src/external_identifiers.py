"""DIAMM identifier-list projection; see doc/external_identifier_selection.md."""

import json


def identifier_values(identifiers, fields):
    """Return distinct supplied strings for reviewed full labels, without coercion."""
    if identifiers is not None and not isinstance(identifiers, list):
        raise ValueError("expected an identifier list or null")
    values = {field: set() for field in fields}
    for entry in identifiers or []:
        if not isinstance(entry, dict):
            continue
        label, value = entry.get("label"), entry.get("identifier")
        if not isinstance(label, str) or not isinstance(value, str) or not value:
            continue
        field = {"rism online": "rism_id", "viaf": "viaf_id"}.get(label.casefold())
        if field in values:
            values[field].add(value)
    return values


def identifier_columns(data, fields):
    """Keep the source list and supply hints only for one distinct nonblank value."""
    identifiers = data.get("identifiers", [])
    values = identifier_values(identifiers, fields)
    columns = {}
    for field, candidates in values.items():
        # Whitespace remains in the evidence/RDF, but is not a useful hint.
        nonblank = {value for value in candidates if value.strip()}
        columns[field] = next(iter(nonblank)) if len(nonblank) == 1 else ""
    columns["source_identifiers"] = json.dumps(
        identifiers, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return columns
