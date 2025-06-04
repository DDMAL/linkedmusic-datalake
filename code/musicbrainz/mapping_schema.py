"""
Class to hold the mapping schema for MusicBrainz to Wikidata.
The first type is meant to be the type that you're pointing from (source),
and the second type is the type that you're pointing to (target).
This class handles wildcards, passing None as the first type will match any type,
but will give priority to specific mappings.
Any mappings passed as a string will be converted to a URIRef
with the Wikidata namespace (WDT).

To retrieve values, use the syntax:
`MB_SCHEMA[(pointing_from, pointing_to)]`
where `pointing_from` is the type you're pointing from
and `pointing_to` is the type you're pointing to.

Additionally, you can use the `to_dict_for_type` method to convert the schema
to a dictionary for a specific entity type.
This will simplify calls to the schema to avoid having to pass the pointing_from type.
"""

from rdflib import Namespace, URIRef

WDT = Namespace("http://www.wikidata.org/prop/direct/")


class MappingSchema:
    """
    Class to hold the mapping schema for MusicBrainz to Wikidata.
    The first type is meant to be the type that you're pointing from (source),
    and the second type is the type that you're pointing to (target).
    This class handles wildcards, passing None as the first type will match any type,
    but will give priority to specific mappings.
    Any mappings passed as a string will be converted to a URIRef
    with the Wikidata namespace (WDT).

    To retrieve values, use the syntax:
    `MB_SCHEMA[(pointing_from, pointing_to)]`
    where `pointing_from` is the type you're pointing from
    and `pointing_to` is the type you're pointing to.

    Additionally, you can use the `to_dict_for_type` method to convert the schema
    to a dictionary for a specific entity type.
    This will simplify calls to the schema to avoid having to pass the pointing_from type.
    """

    def __init__(self, schema):
        """
        Initialize the MappingSchema with a given schema.
        The schema should be a dictionary where keys are tuples of (pointing_from, pointing_to)
        and values are the corresponding Wikidata property IDs.
        pointing_from can be a single type or an iterable of types.
        pointing_to should always be a single type.
        If the value is a string, it will be converted to a URIRef with the Wikidata namespace (WDT).
        """
        self.schema = {}
        for types, mapping in schema.items():
            if not isinstance(mapping, URIRef):
                mapping = URIRef(f"{WDT}{mapping}")
            pointing_from, pointing_to = types
            if pointing_to not in self.schema:
                self.schema[pointing_to] = {}
            if pointing_from and not isinstance(pointing_from, str):  # Handle iterables
                for pf in pointing_from:
                    self.schema[pointing_to][pf] = mapping
            else:
                self.schema[pointing_to][pointing_from] = mapping

    def __getitem__(self, types):
        """Get the mapping for a given pair of types."""
        pointing_from, pointing_to = types
        if pointing_to in self.schema:
            if pointing_from in self.schema[pointing_to]:
                return self.schema[pointing_to][pointing_from]
            elif None in self.schema[pointing_to]:
                return self.schema[pointing_to][None]
        raise KeyError(f"No mapping found for types: {types}")

    def __contains__(self, t):
        """Check if a type is in the schema."""
        return t in self.schema

    def __bool__(self):
        """Check if the schema is not empty."""
        return bool(self.schema)

    def add(self, schema):
        """
        Add an additional mapping to the schema,
        with the same properties and behaviour as init.
        """
        for types, mapping in schema.items():
            if not isinstance(mapping, URIRef):
                mapping = URIRef(f"{WDT}{mapping}")
            pointing_from, pointing_to = types
            if pointing_to not in self.schema:
                self.schema[pointing_to] = {}
            if pointing_from and not isinstance(pointing_from, str):  # Handle iterables
                for pf in pointing_from:
                    self.schema[pointing_to][pf] = mapping
            else:
                self.schema[pointing_to][pointing_from] = mapping

    def to_dict_for_type(self, entity_type):
        """
        Convert the schema to a dictionary for a specific entity type.
        This will simplify calls to the schema to avoid having to pass the pointing_from type.
        This will return a dictionary where keys are the pointing_to types
        and values are the corresponding URIRef.
        """
        to_return = {}
        for pointing_to, mappings in self.schema.items():
            for pointing_from, mapping in mappings.items():
                if pointing_from == entity_type or (
                    pointing_from is None and pointing_to not in to_return
                ):
                    to_return[pointing_to] = mapping
        return to_return

    def add_from_formatted_dict(self, formatted_dict):
        """
        Add mappings from a formatted dictionary to the schema.
        The formatted dictionary should have the same layout as the internal schema
        (the outer dictionary's keys are the pointing_to types,
        and the inner dictionaries' keys are the pointing_from types),
        with the exception that values are full URLs as a string instead of URIRefs.
        Additionally, if keys corresponding to `pointing_from` are the string value
        "null", they will be converted to None.

        This is a convenience method to add mappings from a dictionary
        that was the internal schema dictionary dumped to a JSON file.
        """
        self.add(
            {
                (key if key != "null" else None, k): URIRef(val)
                for k, v in formatted_dict.items()
                for key, val in v.items()
            }
        )
