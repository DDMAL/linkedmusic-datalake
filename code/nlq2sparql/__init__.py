"""NLQ2SPARQL package initialization.

Exposes high-level tools for resolving Wikidata IDs when translating natural
language to SPARQL over the linked music datasets.
"""

from .tools.wikidata_tool import find_entity_id, find_property_id  # re-export

__all__ = ["find_entity_id", "find_property_id"]
"""
NLQ to SPARQL Generator Package

A tool for converting natural language queries to SPARQL queries using various LLM providers (ChatGPT, Claude, Gemini).
"""

from .config import Config
from .router import QueryRouter
from .arguments import ArgumentHandler
from .query_processor import QueryProcessor
from .debug_client import PromptDebugClient

__version__ = "1.0.0"
__all__ = [
    "Config",              # Configuration management
    "QueryRouter",         # LLM provider routing
    "ArgumentHandler",     # Command-line argument handling
    "QueryProcessor",     # Main query processing logic
    "PromptDebugClient"   # Debug prompt inspection
]
