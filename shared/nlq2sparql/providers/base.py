"""
Base class for LLM provider clients
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List

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
        
        # Validate configuration and setup provider
        self._validate_configuration()
        self._setup_provider()
    
    @abstractmethod
    def get_required_config_fields(self) -> List[str]:
        """Return list of required configuration fields for this provider"""
        pass
    
    @abstractmethod
    def get_package_name(self) -> str:
        """Return the package name to import for this provider"""
        pass
    
    @abstractmethod
    def get_install_command(self) -> str:
        """Return the command to install the required package"""
        pass
    
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
        
        # Validate required fields
        required_fields = self.get_required_config_fields()
        missing_fields = [field for field in required_fields if field not in provider_config]
        if missing_fields:
            raise ConfigurationError(
                f"Missing required {self.provider_name.title()} configuration fields: {missing_fields}"
            )
        
        self.logger.info(f"Configuration validated for {self.provider_name} provider")
    
    def _setup_provider(self) -> None:
        """Setup provider-specific configuration and validate parameters"""
        # Get provider configuration
        provider_config = self._get_provider_config()
        
        # Store API key
        self.api_key = self.config.get_api_key(self.provider_name)
        
        # Store common configuration parameters
        self.model = provider_config.get("model")
        self.temperature = provider_config.get("temperature")
        self.max_tokens = provider_config.get("max_tokens")
        
        # Validate common parameters
        if self.temperature is not None:
            if not isinstance(self.temperature, (int, float)) or not (0 <= self.temperature <= 2):
                raise ConfigurationError(
                    f"{self.provider_name.title()} temperature must be a number between 0 and 2"
                )
        
        if self.max_tokens is not None:
            if not isinstance(self.max_tokens, int) or self.max_tokens <= 0:
                raise ConfigurationError(
                    f"{self.provider_name.title()} max_tokens must be a positive integer"
                )
        
        # Initialize client as None - will be lazy loaded in _call_llm_api
        self.client = None
        
        self.logger.info(f"Initialized {self.provider_name.title()} client with model: {self.model}")
    
    def _ensure_package_installed(self) -> None:
        """Ensure the required package is installed, with helpful error message"""
        try:
            __import__(self.get_package_name())
        except ImportError:
            raise ImportError(
                f"{self.get_package_name()} package not installed. "
                f"Install with: {self.get_install_command()}"
            )
    
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
