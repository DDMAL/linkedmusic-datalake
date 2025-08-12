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
            # Safely extract text without assuming response.text exists
            text = None
            try:
                # Some responses support .text; protect access
                text = getattr(response, "text", None)
            except Exception:
                text = None

            # Fallback: assemble text from candidates/parts
            if not text:
                assembled = []
                candidates = getattr(response, "candidates", []) or []
                if candidates:
                    cand = candidates[0]
                    content = getattr(cand, "content", None)
                    parts = getattr(content, "parts", []) if content else []
                    for part in parts:
                        part_text = getattr(part, "text", None)
                        if part_text:
                            assembled.append(part_text)
                text = "".join(assembled).strip() if assembled else None

            if not text:
                # Include finish_reason if present for diagnosability
                finish_reason = None
                try:
                    if getattr(response, "candidates", None):
                        finish_reason = getattr(response.candidates[0], "finish_reason", None)
                except Exception:
                    pass
                raise APIError(
                    "Gemini returned empty response" + (f" (finish_reason={finish_reason})" if finish_reason is not None else "")
                )

            self.logger.debug("Gemini API call completed successfully")
            return text
            
        except Exception as e:
            self.logger.error(f"Gemini API call failed: {e}")
            raise APIError(f"Gemini API error: {str(e)}")
