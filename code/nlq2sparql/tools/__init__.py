"""Tool subpackage for NLQ2SPARQL (Wikidata resolution, etc.)."""

from .wikidata_tool import find_entity_id, find_property_id

__all__ = ["find_entity_id", "find_property_id"]
