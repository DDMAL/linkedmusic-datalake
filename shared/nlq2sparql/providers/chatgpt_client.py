"""
OpenAI ChatGPT client for NLQ to SPARQL conversion
"""

import logging
from typing import List

try:
    from .base import BaseLLMClient, APIError, ConfigurationError
    from ..config import Config
except ImportError:
    from providers.base import BaseLLMClient, APIError, ConfigurationError
    from config import Config


class ChatGPTClient(BaseLLMClient):
    """Client for OpenAI ChatGPT API"""
    
    def get_required_config_fields(self) -> List[str]:
        """Return required configuration fields for ChatGPT"""
        return ["model", "max_tokens", "temperature"]
    
    def get_package_name(self) -> str:
        """Return the package name for OpenAI"""
        return "openai"
    
    def get_install_command(self) -> str:
        """Return install command for OpenAI"""
        return "poetry add openai"
    
    def _call_llm_api(self, prompt: str, verbose: bool = False) -> str:
        """Make API call to ChatGPT"""
        self._ensure_package_installed()
        
        # Import here to avoid dependency issues
        import openai
        
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
