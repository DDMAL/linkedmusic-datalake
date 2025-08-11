"""NLQ2SPARQL package initialization.

High-level tooling for natural language → SPARQL with ontology grounding and
Wikidata assistance. Consolidated exports for public API.
"""

from .tools.wikidata_tool import find_entity_id, find_property_id  # re-export

from .config import Config
from .router import QueryRouter
from .arguments import ArgumentHandler
from .query_processor import QueryProcessor
from .debug_client import PromptDebugClient

__version__ = "1.0.0"
__all__ = [
    "find_entity_id",
    "find_property_id",
    "Config",
    "QueryRouter",
    "ArgumentHandler",
    "QueryProcessor",
    "PromptDebugClient",
]
