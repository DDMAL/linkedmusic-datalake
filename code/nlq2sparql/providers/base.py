"""
Base class for LLM provider clients
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

try:
    from ..prompts import build_sparql_generation_prompt
    from ..config import Config
except ImportError:
    from prompts import build_sparql_generation_prompt
    from config import Config


class ProviderError(Exception):
    """Base exception for provider-related errors"""
    pass


class APIError(ProviderError):
    """Exception for API-related errors"""
    pass


class ConfigurationError(ProviderError):
    """Exception for configuration-related errors"""
    pass


class BaseLLMClient(ABC):
    """Abstract base class for LLM provider clients"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Get provider name from class name (e.g., "GeminiClient" -> "gemini")
        self.provider_name = self._get_provider_name()
        
        # Validate configuration
        self._validate_configuration()
    
    def _get_provider_name(self) -> str:
        """Extract provider name from class name"""
        class_name = self.__class__.__name__
        if class_name.endswith("Client"):
            return class_name[:-6].lower()  # Remove "Client" suffix
        return class_name.lower()
    
    def _validate_configuration(self) -> None:
        """Validate that required configuration is present"""
        # Check API key
        api_key = self.config.get_api_key(self.provider_name)
        if not api_key or api_key.strip() == "" or api_key == "PLACEHOLDER":
            key_mappings = self.config.config_data.get("api_key_mappings", {})
            env_key = key_mappings.get(self.provider_name, f"{self.provider_name}_api_key")
            raise ConfigurationError(
                f"{self.provider_name.title()} API key not found or invalid. "
                f"Please set {env_key} in .env file or config.json"
            )
        
        # Check provider configuration
        provider_config = self.config.get_provider_config(self.provider_name)
        if not provider_config:
            raise ConfigurationError(
                f"{self.provider_name.title()} provider configuration not found in config.json"
            )
        
        self.logger.info(f"Configuration validated for {self.provider_name} provider")
    
    @abstractmethod
    def _call_llm_api(self, prompt: str, verbose: bool = False) -> str:
        """
        Make the actual API call to the LLM provider
        
        This is the only method that differs between providers.
        Each provider implements their specific API call here.
        
        Args:
            prompt: The formatted prompt to send to the LLM
            verbose: Enable verbose output
            
        Returns:
            Raw response text from the LLM
            
        Raises:
            APIError: If the API call fails
        """
        pass
    
    def generate_sparql(
        self,
        nlq: str,
        database: str,
        ontology_context: str = "",
        verbose: bool = False
    ) -> str:
        """
        Generate SPARQL query from natural language query
        
        This method is implemented in the base class to provide consistent
        behavior across all providers. Only the API call differs.
        
        Args:
            nlq: Natural language query
            database: Target database name
            ontology_context: Optional ontology context
            verbose: Enable verbose output
            
        Returns:
            Generated SPARQL query
            
        Raises:
            ProviderError: If query generation fails
        """
        # Input validation
        if not nlq or not nlq.strip():
            raise ValueError("Natural language query cannot be empty")
        
        if not database or not database.strip():
            raise ValueError("Database name cannot be empty")
        
        try:
            # Get prefix declarations for the database and build prompt
            prefix_declarations = self.config.get_prefix_declarations(database)
            prompt = build_sparql_generation_prompt(nlq, database, prefix_declarations, ontology_context)
            
            if verbose:
                print(f"Sending request to {self.__class__.__name__}...")
                print(f"Prompt length: {len(prompt)} characters")
            
            self.logger.debug(f"Generating SPARQL for query: {nlq[:100]}...")
            
            # Call provider-specific API
            raw_response = self._call_llm_api(prompt, verbose)
            
            if not raw_response or not raw_response.strip():
                raise APIError(f"{self.provider_name} returned empty response")
            
            # Clean up the response - remove markdown formatting
            sparql_query = self._clean_response(raw_response)
            
            if verbose:
                print(f"Received response from {self.__class__.__name__}")
            
            self.logger.debug("SPARQL generation completed successfully")
            return sparql_query
            
        except (ValueError, ProviderError):
            # Re-raise these as they have meaningful messages
            raise
        except Exception as e:
            self.logger.error(f"SPARQL generation failed: {e}")
            raise ProviderError(f"{self.provider_name.title()} error: {str(e)}")
    
    def _clean_response(self, response: str) -> str:
        """Clean up LLM response by removing markdown formatting"""
        if not response:
            return ""
            
        sparql_query = response.strip()
        
        # Remove markdown code blocks
        if sparql_query.startswith("```sparql"):
            sparql_query = sparql_query[9:]
        elif sparql_query.startswith("```"):
            sparql_query = sparql_query[3:]
            
        if sparql_query.endswith("```"):
            sparql_query = sparql_query[:-3]
        
        cleaned = sparql_query.strip()
        
        if not cleaned:
            self.logger.warning("Response became empty after cleaning")
            
        return cleaned
    
    def _get_provider_config(self) -> Dict[str, Any]:
        """Get configuration for this provider from config.json"""
        config_data = self.config.get_provider_config(self.provider_name)
        
        if not config_data:
            self.logger.warning(f"No configuration found for provider '{self.provider_name}' in config.json")
        
        return config_data
