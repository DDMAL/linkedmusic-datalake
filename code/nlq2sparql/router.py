"""
Query router that coordinates between different providers
"""

from pathlib import Path
from typing import Optional

try:
    from .config import Config
except ImportError:
    from config import Config


class QueryRouter:
    """Routes queries to appropriate providers and handles response formatting"""
    
    def __init__(self, config: Config):
        self.config = config
        self.provider_clients = {}
    
    def _get_client(self, provider: str):
        """Get or create a client for the specified provider"""
        if provider not in self.provider_clients:
            if provider == "gemini":
                try:
                    from .providers.gemini_client import GeminiClient
                except ImportError:
                    from providers.gemini_client import GeminiClient
                self.provider_clients[provider] = GeminiClient(self.config)
            elif provider == "chatgpt":
                try:
                    from .providers.chatgpt_client import ChatGPTClient
                except ImportError:
                    from providers.chatgpt_client import ChatGPTClient
                self.provider_clients[provider] = ChatGPTClient(self.config)
            elif provider == "claude":
                try:
                    from .providers.claude_client import ClaudeClient
                except ImportError:
                    from providers.claude_client import ClaudeClient
                self.provider_clients[provider] = ClaudeClient(self.config)
            else:
                raise ValueError(f"Unknown provider: {provider}")
        
        return self.provider_clients[provider]
    
    def process_query(
        self,
        nlq: str,
        provider: str,
        database: str,
        ontology_file: Optional[Path] = None,
        verbose: bool = False
    ) -> str:
        """
        Process a natural language query and return SPARQL
        
        Args:
            nlq: Natural language query
            provider: Provider to use
            database: Target database name
            ontology_file: Optional path to ontology file
            verbose: Enable verbose output
            
        Returns:
            Generated SPARQL query as string
        """
        if verbose:
            print(f"Using provider: {provider}")
            print(f"Target database: {database}")
            print(f"Query: {nlq}")
        
        # Load ontology context if provided
        ontology_context = ""
        if ontology_file and ontology_file.exists():
            with open(ontology_file, 'r') as f:
                ontology_context = f.read()
            if verbose:
                print(f"Loaded ontology from: {ontology_file}")
        
        # Get the appropriate client
        client = self._get_client(provider)
        
        # Generate SPARQL query
        sparql_query = client.generate_sparql(
            nlq=nlq,
            database=database,
            ontology_context=ontology_context,
            verbose=verbose
        )
        
        return sparql_query
