"""
Application controller for processing NLQ to SPARQL queries
"""

import sys
from pathlib import Path
from typing import Optional

try:
    from .config import Config
    from .router import QueryRouter
    from .debug_client import PromptDebugClient
except ImportError:
    from config import Config
    from router import QueryRouter
    from debug_client import PromptDebugClient


class QueryProcessor:
    """Handles the main application logic for processing queries"""
    
    def __init__(self, config: Config):
        self.config = config
    
    def process_query_request(
        self,
        query: str,
        provider: str,
        database: str,
        ontology_file: Optional[Path] = None,
        debug_mode: bool = False,
        verbose: bool = False
    ) -> str:
        """
        Process a query request in either normal or debug mode
        
        Args:
            query: The natural language query
            provider: LLM provider to use
            database: Target database
            ontology_file: Optional ontology file path
            debug_mode: Whether to capture prompt instead of generating SPARQL
            verbose: Enable verbose output
            
        Returns:
            Generated SPARQL query or debug response
        """
        router = QueryRouter(self.config)
        
        if debug_mode:
            return self._process_debug_mode(
                router, query, provider, database, ontology_file, verbose
            )
        else:
            return self._process_normal_mode(
                router, query, provider, database, ontology_file, verbose
            )
    
    def _process_debug_mode(
        self,
        router: QueryRouter,
        query: str,
        provider: str,
        database: str,
        ontology_file: Optional[Path],
        verbose: bool
    ) -> str:
        """Process query in debug mode (capture prompt)"""
        # Replace the provider client with our debug client
        debug_client = PromptDebugClient(self.config)
        router.provider_clients[provider] = debug_client
        
        sparql_query = router.process_query(
            nlq=query,
            provider=provider,
            database=database,
            ontology_file=ontology_file,
            verbose=verbose
        )
        
        # The debug client automatically saves the prompt during the process
        print(f"Prompt captured and saved to debug_prompts/")
        print(f"Query processed: {query}")
        print(f"Debug response: {sparql_query}")
        
        return sparql_query
    
    def _process_normal_mode(
        self,
        router: QueryRouter,
        query: str,
        provider: str,
        database: str,
        ontology_file: Optional[Path],
        verbose: bool
    ) -> str:
        """Process query in normal mode (generate SPARQL)"""
        sparql_query = router.process_query(
            nlq=query,
            provider=provider,
            database=database,
            ontology_file=ontology_file,
            verbose=verbose
        )
        
        print("Generated SPARQL Query:")
        print("=" * 50)
        print(sparql_query)
        
        return sparql_query
