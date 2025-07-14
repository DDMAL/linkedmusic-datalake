"""
Anthropic Claude client for NLQ to SPARQL conversion
"""

import logging
from typing import Optional, Any

try:
    from .base import BaseLLMClient, APIError, ConfigurationError
    from ..config import Config
except ImportError:
    from providers.base import BaseLLMClient, APIError, ConfigurationError
    from config import Config


class ClaudeClient(BaseLLMClient):
    """Client for Anthropic Claude API"""
    
    def __init__(self, config: Config):
        super().__init__(config)
        
        # Get provider configuration
        provider_config = self._get_provider_config()
        
        # Validate required config fields
        required_fields = ["model", "max_tokens", "temperature"]
        missing_fields = [field for field in required_fields if field not in provider_config]
        if missing_fields:
            raise ConfigurationError(
                f"Missing required Claude configuration fields: {missing_fields}"
            )
        
        # Store configuration
        self.api_key = self.config.get_api_key(self.provider_name)
        self.model = provider_config["model"]
        self.max_tokens = provider_config["max_tokens"]
        self.temperature = provider_config["temperature"]
        
        # Validate configuration values
        if not isinstance(self.max_tokens, int) or self.max_tokens <= 0:
            raise ConfigurationError("Claude max_tokens must be a positive integer")
        
        if not isinstance(self.temperature, (int, float)) or not (0 <= self.temperature <= 1):
            raise ConfigurationError("Claude temperature must be a number between 0 and 1")
        
        # Initialize client lazily in _call_llm_api
        self.client = None
        
        self.logger.info(f"Initialized Claude client with model: {self.model}")
    
    def _call_llm_api(self, prompt: str, verbose: bool = False) -> str:
        """Make API call to Claude"""
        try:
            import anthropic
        except ImportError:
            raise ImportError(
                "anthropic package not installed. "
                "Install with: poetry add anthropic"
            )
        
        # Initialize client if not already done
        if self.client is None:
            try:
                self.client = anthropic.Anthropic(api_key=self.api_key)
                self.logger.debug("Anthropic client initialized successfully")
            except Exception as e:
                raise APIError(f"Failed to initialize Anthropic client: {e}")
        
        try:
            if verbose:
                print(f"Calling Claude API with model: {self.model}")
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            if not response.content or not response.content[0].text:
                raise APIError("Claude returned empty response")
            
            self.logger.debug("Claude API call completed successfully")
            return response.content[0].text
            
        except Exception as e:
            self.logger.error(f"Claude API call failed: {e}")
            raise APIError(f"Claude API error: {str(e)}")
