"""
NLQ to SPARQL Generator Package

A tool for converting natural language queries to SPARQL queries using various LLM providers (ChatGPT, Claude, Gemini).
"""

from .config import Config
from .router import QueryRouter
from .cli_parser import CLIParser
from .query_processor import QueryProcessor
from .debug_client import PromptDebugClient

__version__ = "1.0.0"
__all__ = [
    "Config",              # Configuration management
    "QueryRouter",         # LLM provider routing
    "CLIParser",          # Command-line argument parsing
    "QueryProcessor",     # Main query processing logic
    "PromptDebugClient"   # Debug prompt inspection
]
