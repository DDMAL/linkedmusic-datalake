"""
Wikidata Utilities Package

This package provides utilities for interacting with Wikidata APIs:
- WikidataAPIClient: Asynchronous client for various Wikidata APIs
- FederatedQueryOptimizer: Optimizer for federated SPARQL queries
- Helper functions for common operations

Usage:
    from wikidata_utils import WikidataAPIClient, FederatedQueryOptimizer, build_wd_hyperlink

Dependencies:
- aiohttp
- aiolimiter
"""

from .client import WikidataAPIClient
from .query_optimizer import FederatedQueryOptimizer
from .helpers import build_wd_hyperlink, extract_wd_id
from .config import OptimizationConfig, get_config, create_custom_config

__all__ = [
    "WikidataAPIClient",
    "FederatedQueryOptimizer",
    "OptimizationConfig",
    "get_config",
    "create_custom_config",
    "build_wd_hyperlink", 
    "extract_wd_id"
]
