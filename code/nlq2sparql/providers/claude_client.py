"""
Anthropic Claude client for NLQ to SPARQL conversion
"""

import logging
from typing import List

try:
    from .base import BaseLLMClient, APIError, ConfigurationError
    from ..config import Config
except ImportError:
    from providers.base import BaseLLMClient, APIError, ConfigurationError
    from config import Config


class ClaudeClient(BaseLLMClient):
    """Client for Anthropic Claude API"""
    
    def get_required_config_fields(self) -> List[str]:
        """Return required configuration fields for Claude"""
        return ["model", "max_tokens", "temperature"]
    
    def get_package_name(self) -> str:
        """Return the package name for Anthropic"""
        return "anthropic"
    
    def get_install_command(self) -> str:
        """Return install command for Anthropic"""
        return "poetry add anthropic"
    
    def _call_llm_api(self, prompt: str, verbose: bool = False) -> str:
        """Make API call to Claude"""
        self._ensure_package_installed()
        
        # Import here to avoid dependency issues
        import anthropic
        
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
