"""
OpenAI ChatGPT client for NLQ to SPARQL conversion
"""

from typing import Optional
from providers.base import BaseLLMClient


class ChatGPTClient(BaseLLMClient):
    """Client for OpenAI ChatGPT API"""
    
    def __init__(self, config):
        super().__init__(config)
        
        # Get API key
        api_key = config.get_api_key("chatgpt")
        if not api_key:
            raise ValueError("OpenAI API key not found. Please set openai_api_key in config or environment")
        
        # Store config for later use
        self.api_key = api_key
        provider_config = self._get_provider_config("chatgpt")
        self.model = provider_config.get("model", "gpt-3.5-turbo")
        self.max_tokens = provider_config.get("max_tokens", 1000)
        self.temperature = provider_config.get("temperature", 0.1)
        
        # Initialize client lazily in _call_llm_api
        self.client = None
    
    def _call_llm_api(self, prompt: str, verbose: bool = False) -> str:
        """Make API call to ChatGPT"""
        try:
            import openai
        except ImportError:
            raise ImportError("openai package not installed. Install with: poetry add openai")
        
        # Initialize client if not already done
        if self.client is None:
            self.client = openai.OpenAI(api_key=self.api_key)
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=self.max_tokens,
            temperature=self.temperature
        )
        
        return response.choices[0].message.content
