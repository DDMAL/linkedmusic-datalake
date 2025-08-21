"""
Query router that coordinates between different providers
"""

import importlib
from pathlib import Path
from typing import Optional, Dict, Type
import logging

try:
    from .config import Config, ConfigError
    from .providers.base import BaseLLMClient
except ImportError:
    from config import Config, ConfigError
    from providers.base import BaseLLMClient


class RouterError(Exception):
    """Custom exception for router-related errors"""
    pass


class QueryRouter:
    """Routes queries to appropriate providers and handles response formatting"""
    
    def __init__(self, config: Config):
        self.config = config
        self.provider_clients: Dict[str, BaseLLMClient] = {}
        self.logger = logging.getLogger(__name__)
        
        # Validate configuration at startup
        if not config.validate_configuration():
            raise RouterError("Invalid configuration provided to router")
    
    def get_supported_providers(self) -> list[str]:
        """Get list of supported provider names from config"""
        return self.config.get_supported_providers()
    
    def _import_provider_class(self, module_path: str) -> Type[BaseLLMClient]:
        """Dynamically import a provider class using importlib"""
        try:
            # Split module path and class name
            module_name, class_name = module_path.rsplit('.', 1)
            
            # Try relative import first, but handle package context properly
            try:
                if __package__:
                    module = importlib.import_module(f".{module_name}", package=__package__)
                else:
                    # If no package context, try absolute import directly
                    raise ImportError("No package context for relative import")
            except (ImportError, ValueError, TypeError):
                # Fall back to absolute import
                module = importlib.import_module(module_name)
            
            # Get the class from the module
            provider_class = getattr(module, class_name)
            
            # Verify it's a BaseLLMClient subclass
            if not issubclass(provider_class, BaseLLMClient):
                raise RouterError(f"Provider class {class_name} is not a subclass of BaseLLMClient")
            
            return provider_class
            
        except ImportError as e:
            raise RouterError(f"Failed to import provider module {module_path}: {e}")
        except AttributeError as e:
            raise RouterError(f"Provider class not found in module {module_path}: {e}")
        except Exception as e:
            raise RouterError(f"Unexpected error importing provider {module_path}: {e}")
    
    def _get_client(self, provider: str) -> BaseLLMClient:
        """Get or create a client for the specified provider"""
        if provider not in self.provider_clients:
            provider_registry = self.config.get_provider_registry()
            if provider not in provider_registry:
                supported = ", ".join(self.get_supported_providers())
                raise ValueError(f"Unknown provider: {provider}. Supported providers: {supported}")
            
            try:
                # Use dynamic import instead of hardcoded if/elif blocks
                module_path = provider_registry[provider]
                provider_class = self._import_provider_class(module_path)
                
                # Create the client instance
                self.provider_clients[provider] = provider_class(self.config)
                self.logger.info(f"Created {provider} client using {module_path}")
                
            except Exception as e:
                self.logger.error(f"Failed to create {provider} client: {e}")
                raise RouterError(f"Failed to create {provider} client: {e}")
        
        return self.provider_clients[provider]
    
    def _load_ontology_context(self, nlq: str, ontology_file: Optional[Path], verbose: bool = False) -> str:
        """Load ontology context from file or build it via multi-agent orchestrator."""
        # If a file is provided, prefer it (explicit override)
        if ontology_file:
            try:
                if not ontology_file.exists():
                    self.logger.warning(f"Ontology file not found: {ontology_file}")
                    return ""
                content = ontology_file.read_text(encoding='utf-8')
                if verbose:
                    print(f"Loaded ontology from: {ontology_file}")
                if not content.strip():
                    self.logger.warning(f"Ontology file is empty: {ontology_file}")
                return content
            except Exception as e:
                self.logger.error(f"Failed to load ontology file {ontology_file}: {e}")
                if verbose:
                    print(f"Warning: Could not load ontology file: {e}")
                return ""
        # Build via orchestrator
        try:
            from .agents.orchestrator import MultiAgentOrchestrator
        except Exception:
            from agents.orchestrator import MultiAgentOrchestrator  # type: ignore
        orch = MultiAgentOrchestrator()
        context = orch.build_ontology_context(nlq)
        if verbose:
            print("Built ontology context via multi-agent pipeline")
        return context
    
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
            
        Raises:
            ValueError: If provider is not supported or parameters are invalid
            RouterError: If query processing fails
        """
        # Input validation
        if not nlq or not nlq.strip():
            raise ValueError("Natural language query cannot be empty")
        
        if not provider:
            raise ValueError("Provider must be specified")
            
        if not database:
            raise ValueError("Database must be specified")
        
        # Check if database is supported
        available_databases = self.config.get_available_databases()
        if database not in available_databases:
            raise ValueError(f"Unknown database: {database}. Available databases: {', '.join(available_databases)}")
        
        if verbose:
            print(f"Using provider: {provider}")
            print(f"Target database: {database}")
            print(f"Query: {nlq}")

        # Load ontology context with file override or multi-agent pipeline
        ontology_context = self._load_ontology_context(nlq, ontology_file, verbose)
        
        try:
            # Get the appropriate client
            client = self._get_client(provider)
            
            # Generate SPARQL query
            sparql_query = client.generate_sparql(
                nlq=nlq,
                database=database,
                ontology_context=ontology_context,
                verbose=verbose
            )
            
            if not sparql_query or not sparql_query.strip():
                raise RouterError("Provider returned empty SPARQL query")
            
            return sparql_query
            
        except (ValueError, RouterError):
            # Re-raise these as they have meaningful error messages
            raise
        except Exception as e:
            self.logger.error(f"Query processing failed: {e}")
            if verbose:
                print(f"Error processing query: {e}")
            raise RouterError(f"Query processing failed: {e}")
