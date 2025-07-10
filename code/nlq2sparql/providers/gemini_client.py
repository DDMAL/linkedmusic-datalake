"""
Google Gemini client for NLQ to SPARQL conversion
"""

from typing import Optional
from providers.base import BaseLLMClient


class GeminiClient(BaseLLMClient):
    """Client for Google Gemini API"""
    
    def __init__(self, config):
        super().__init__(config)
        
        # Get API key
        api_key = config.get_api_key("gemini")
        if not api_key or api_key == "PLACEHOLDER":
            raise ValueError("Gemini API key not found or is placeholder. Please set gemini_api_key in .env file")
        
        # Store config for later use
        self.api_key = api_key
        provider_config = self._get_provider_config("gemini")
        self.model_name = provider_config.get("model", "gemini-pro")
        self.temperature = provider_config.get("temperature", 0.1)
        
        # Initialize model lazily in _call_llm_api
        self.model = None
    
    def _call_llm_api(self, prompt: str, verbose: bool = False) -> str:
        """Make API call to Gemini"""
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError("google-generativeai package not installed. Install with: poetry add google-generativeai")
        
        # Initialize model if not already done
        if self.model is None:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature
                )
            )
            return response.text
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")
