"""
OpenAI ChatGPT client for NLQ to SPARQL conversion
"""

import logging
from typing import Optional, Any

try:
    from .base import BaseLLMClient, APIError, ConfigurationError
    from ..config import Config
except ImportError:
    from providers.base import BaseLLMClient, APIError, ConfigurationError
    from config import Config


class ChatGPTClient(BaseLLMClient):
    """Client for OpenAI ChatGPT API"""
    
    def __init__(self, config: Config):
        super().__init__(config)
        
        # Get provider configuration
        provider_config = self._get_provider_config()
        
        # Validate required config fields
        required_fields = ["model", "max_tokens", "temperature"]
        missing_fields = [field for field in required_fields if field not in provider_config]
        if missing_fields:
            raise ConfigurationError(
                f"Missing required ChatGPT configuration fields: {missing_fields}"
            )
        
        # Store configuration
        self.api_key = self.config.get_api_key(self.provider_name)
        self.model = provider_config["model"]
        self.max_tokens = provider_config["max_tokens"]
        self.temperature = provider_config["temperature"]
        
        # Validate configuration values
        if not isinstance(self.max_tokens, int) or self.max_tokens <= 0:
            raise ConfigurationError("ChatGPT max_tokens must be a positive integer")
        
        if not isinstance(self.temperature, (int, float)) or not (0 <= self.temperature <= 2):
            raise ConfigurationError("ChatGPT temperature must be a number between 0 and 2")
        
        # Initialize client lazily in _call_llm_api
        self.client = None
        
        self.logger.info(f"Initialized ChatGPT client with model: {self.model}")
    
    def _call_llm_api(self, prompt: str, verbose: bool = False) -> str:
        """Make API call to ChatGPT"""
        try:
            import openai
        except ImportError:
            raise ImportError(
                "openai package not installed. "
                "Install with: poetry add openai"
            )
        
        # Initialize client if not already done
        if self.client is None:
            try:
                self.client = openai.OpenAI(api_key=self.api_key)
                self.logger.debug("OpenAI client initialized successfully")
            except Exception as e:
                raise APIError(f"Failed to initialize OpenAI client: {e}")
        
        try:
            if verbose:
                print(f"Calling ChatGPT API with model: {self.model}")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            if not response.choices or not response.choices[0].message.content:
                raise APIError("ChatGPT returned empty response")
            
            self.logger.debug("ChatGPT API call completed successfully")
            return response.choices[0].message.content
            
        except Exception as e:
            self.logger.error(f"ChatGPT API call failed: {e}")
            raise APIError(f"ChatGPT API error: {str(e)}")
