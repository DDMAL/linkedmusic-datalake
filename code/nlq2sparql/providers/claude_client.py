"""
Anthropic Claude client for NLQ to SPARQL conversion
"""

from typing import Optional
try:
    from .base import BaseLLMClient
except ImportError:
    from providers.base import BaseLLMClient


class ClaudeClient(BaseLLMClient):
    """Client for Anthropic Claude API"""
    
    def __init__(self, config):
        super().__init__(config)
        
        # Get API key
        api_key = config.get_api_key("claude")
        if not api_key:
            raise ValueError("Anthropic API key not found. Please set anthropic_api_key in config or environment")
        
        # Store config for later use
        self.api_key = api_key
        provider_config = self._get_provider_config("claude")
        
        # Get provider settings from config (all defaults should be in config.json)
        if not provider_config:
            raise ValueError("Claude provider configuration not found in config.json")
            
        self.model = provider_config["model"]
        self.max_tokens = provider_config["max_tokens"]
        self.temperature = provider_config["temperature"]
        
        # Initialize client lazily in _call_llm_api
        self.client = None
    
    def _call_llm_api(self, prompt: str, verbose: bool = False) -> str:
        """Make API call to Claude"""
        try:
            import anthropic
        except ImportError:
            raise ImportError("anthropic package not installed. Install with: poetry add anthropic")
        
        # Initialize client if not already done
        if self.client is None:
            self.client = anthropic.Anthropic(api_key=self.api_key)
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.content[0].text
