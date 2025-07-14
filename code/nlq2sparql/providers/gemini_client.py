"""
Google Gemini client for NLQ to SPARQL conversion
"""

import logging
from typing import List

try:
    from .base import BaseLLMClient, APIError, ConfigurationError
    from ..config import Config
except ImportError:
    from providers.base import BaseLLMClient, APIError, ConfigurationError
    from config import Config


class GeminiClient(BaseLLMClient):
    """Client for Google Gemini API"""
    
    def get_required_config_fields(self) -> List[str]:
        """Return required configuration fields for Gemini"""
        return ["model", "temperature"]
    
    def get_package_name(self) -> str:
        """Return the package name for Gemini"""
        return "google.generativeai"
    
    def get_install_command(self) -> str:
        """Return install command for Gemini"""
        return "poetry add google-generativeai"
    
    def _call_llm_api(self, prompt: str, verbose: bool = False) -> str:
        """Make API call to Gemini"""
        self._ensure_package_installed()
        
        # Import here to avoid dependency issues
        import google.generativeai as genai
        
        # Initialize model if not already done
        if self.client is None:
            try:
                genai.configure(api_key=self.api_key)
                self.client = genai.GenerativeModel(self.model)
                self.logger.debug("Gemini model initialized successfully")
            except Exception as e:
                raise APIError(f"Failed to initialize Gemini model: {e}")
        
        try:
            if verbose:
                print(f"Calling Gemini API with model: {self.model}")
            
            response = self.client.generate_content(
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
