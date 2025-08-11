"""NLQ2SPARQL lightweight package init.

Intentionally minimalist to avoid importing heavy submodules (network clients,
large ontology files) during test collection or when only agents are needed.

Heavy modules (tools.wikidata_tool, full CLI stack) are accessible via lazy
access functions to prevent side effects at import time.
"""

__version__ = "1.0.0"

def find_entity_id(label: str):  # type: ignore[return-type]
    from .tools.wikidata_tool import find_entity_id as _f
    return _f(label)

def find_property_id(label: str):  # type: ignore[return-type]
    from .tools.wikidata_tool import find_property_id as _f
    return _f(label)

__all__ = [
    "find_entity_id",
    "find_property_id",
    "__version__",
]
