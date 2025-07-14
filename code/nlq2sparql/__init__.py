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
