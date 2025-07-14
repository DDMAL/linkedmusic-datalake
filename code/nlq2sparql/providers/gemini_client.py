"""
Google Gemini client for NLQ to SPARQL conversion
"""

import logging
from typing import Optional, Any

try:
    from .base import BaseLLMClient, APIError, ConfigurationError
    from ..config import Config
except ImportError:
    from providers.base import BaseLLMClient, APIError, ConfigurationError
    from config import Config


class GeminiClient(BaseLLMClient):
    """Client for Google Gemini API"""
    
    def __init__(self, config: Config):
        super().__init__(config)
        
        # Get provider configuration
        provider_config = self._get_provider_config()
        
        # Validate required config fields
        required_fields = ["model", "temperature"]
        missing_fields = [field for field in required_fields if field not in provider_config]
        if missing_fields:
            raise ConfigurationError(
                f"Missing required Gemini configuration fields: {missing_fields}"
            )
        
        # Store configuration
        self.api_key = self.config.get_api_key(self.provider_name)
        self.model_name = provider_config["model"]
        self.temperature = provider_config["temperature"]
        
        # Validate configuration values
        if not isinstance(self.temperature, (int, float)) or not (0 <= self.temperature <= 1):
            raise ConfigurationError("Gemini temperature must be a number between 0 and 1")
        
        # Initialize model lazily in _call_llm_api
        self.model = None
        
        self.logger.info(f"Initialized Gemini client with model: {self.model_name}")
    
    def _call_llm_api(self, prompt: str, verbose: bool = False) -> str:
        """Make API call to Gemini"""
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError(
                "google-generativeai package not installed. "
                "Install with: poetry add google-generativeai"
            )
        
        # Initialize model if not already done
        if self.model is None:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel(self.model_name)
                self.logger.debug("Gemini model initialized successfully")
            except Exception as e:
                raise APIError(f"Failed to initialize Gemini model: {e}")
        
        try:
            if verbose:
                print(f"Calling Gemini API with model: {self.model_name}")
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature
                )
            )
            
            if not response or not response.text:
                raise APIError("Gemini returned empty response")
            
            self.logger.debug("Gemini API call completed successfully")
            return response.text
            
        except Exception as e:
            self.logger.error(f"Gemini API call failed: {e}")
            raise APIError(f"Gemini API error: {str(e)}")
