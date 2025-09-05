"""
Provider-Agnostic LLM Client for Agents

This module provides a unified interface for LLM providers that can be used
by all agents. It handles retries, validation, and error handling consistently.
"""

import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

try:
    from ..providers.base import BaseLLMClient
except ImportError:
    from providers.base import BaseLLMClient


@dataclass
class LLMResponse:
    """Standardized response from LLM providers."""
    content: str
    metadata: Dict[str, Any]
    success: bool
    error: Optional[str] = None


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 10.0
    exponential_base: float = 2.0


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate a response from the LLM."""
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the name of this provider."""
        pass


class GeminiProvider(LLMProvider):
    """Google Gemini LLM provider."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-1.5-flash"):
        import os
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = model
        self.logger = logging.getLogger(f"{__name__}.GeminiProvider")
        
        # Initialize Gemini client
        try:
            from google import genai
            if not self.api_key:
                raise ValueError("Gemini API key required. Set GEMINI_API_KEY environment variable.")
            self._client = genai.Client(api_key=self.api_key)
        except ImportError:
            raise ImportError("google-genai package required for Gemini provider")
    
    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate response using Gemini."""
        try:
            from google.genai import types
            
            # Convert sync call to async
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: self._client.models.generate_content(
                    model=self.model,
                    contents=prompt
                )
            )
            
            # Extract text from response
            text = ""
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content and hasattr(candidate.content, 'parts') and candidate.content.parts:
                    text = candidate.content.parts[0].text or ""
            
            if not text:
                text = getattr(response, 'text', str(response))
            
            return LLMResponse(
                content=text or "",
                metadata={
                    "model": self.model,
                    "provider": "gemini",
                    "usage": getattr(response, 'usage_metadata', {})
                },
                success=True
            )
        except Exception as e:
            self.logger.error(f"Gemini generation failed: {e}")
            return LLMResponse(
                content="",
                metadata={"model": self.model, "provider": "gemini"},
                success=False,
                error=str(e)
            )
    
    def get_provider_name(self) -> str:
        return "gemini"


class LLMClient:
    """
    Unified LLM client with retry logic, validation, and error handling.
    
    This client provides a consistent interface for all agents to interact
    with LLM providers, handling retries and errors gracefully.
    """
    
    def __init__(
        self, 
        provider: LLMProvider,
        retry_config: Optional[RetryConfig] = None,
        logger: Optional[logging.Logger] = None
    ):
        self.provider = provider
        self.retry_config = retry_config or RetryConfig()
        self.logger = logger or logging.getLogger(f"{__name__}.LLMClient")
    
    async def generate_with_retry(
        self, 
        prompt: str, 
        validate_json: bool = False,
        expected_keys: Optional[List[str]] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate LLM response with retry logic and optional validation.
        
        Args:
            prompt: The prompt to send to the LLM
            validate_json: Whether to validate response as JSON
            expected_keys: List of required keys if validating JSON
            **kwargs: Additional arguments passed to provider
            
        Returns:
            LLMResponse with content and metadata
        """
        last_error = None
        
        for attempt in range(self.retry_config.max_retries + 1):
            try:
                start_time = time.time()
                response = await self.provider.generate(prompt, **kwargs)
                duration = time.time() - start_time
                
                # Log the LLM interaction for debugging
                self.logger.info(
                    f"LLM Request/Response (attempt {attempt + 1})",
                    extra={
                        'llm_prompt': prompt,
                        'llm_response': response.content if response.success else f"ERROR: {response.error}",
                        'agent_step': f"LLM call to {self.provider.get_provider_name()}"
                    }
                )
                
                # Add timing metadata
                response.metadata.update({
                    "duration_seconds": duration,
                    "attempt": attempt + 1
                })
                
                if not response.success:
                    raise Exception(response.error or "LLM generation failed")
                
                # Validate JSON if requested
                if validate_json:
                    try:
                        parsed = json.loads(response.content)
                        if expected_keys:
                            missing = [k for k in expected_keys if k not in parsed]
                            if missing:
                                raise ValueError(f"Missing required keys: {missing}")
                        response.metadata["validated_json"] = True
                    except (json.JSONDecodeError, ValueError) as e:
                        raise ValueError(f"JSON validation failed: {e}")
                
                self.logger.info(
                    f"LLM generation successful (attempt {attempt + 1}): "
                    f"{duration:.2f}s, provider={self.provider.get_provider_name()}"
                )
                return response
                
            except Exception as e:
                last_error = e
                self.logger.warning(
                    f"LLM generation attempt {attempt + 1} failed: {e}"
                )
                
                # Don't retry on validation errors (they won't get better)
                if isinstance(e, ValueError) and "validation" in str(e).lower():
                    break
                
                # Calculate delay for next retry
                if attempt < self.retry_config.max_retries:
                    delay = min(
                        self.retry_config.base_delay * (
                            self.retry_config.exponential_base ** attempt
                        ),
                        self.retry_config.max_delay
                    )
                    self.logger.info(f"Retrying in {delay:.1f}s...")
                    await asyncio.sleep(delay)
        
        # All retries failed
        self.logger.error(f"LLM generation failed after all retries: {last_error}")
        return LLMResponse(
            content="",
            metadata={
                "provider": self.provider.get_provider_name(),
                "attempts": self.retry_config.max_retries + 1,
                "final_error": str(last_error)
            },
            success=False,
            error=str(last_error)
        )
    
    async def generate_structured(
        self,
        prompt: str,
        expected_keys: List[str],
        fallback_value: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate structured JSON response with fallback.
        
        Args:
            prompt: The prompt to send to the LLM
            expected_keys: Required keys in the JSON response
            fallback_value: Value to return if generation fails
            **kwargs: Additional arguments passed to provider
            
        Returns:
            Parsed JSON dictionary or fallback value
        """
        response = await self.generate_with_retry(
            prompt=prompt,
            validate_json=True,
            expected_keys=expected_keys,
            **kwargs
        )
        
        if response.success:
            try:
                return json.loads(response.content)
            except json.JSONDecodeError:
                pass
        
        # Return fallback or empty dict with required keys
        if fallback_value is not None:
            return fallback_value
        
        return {key: None for key in expected_keys}


# Factory function for easy provider creation
def create_llm_client(
    provider_name: str = "gemini",
    retry_config: Optional[RetryConfig] = None,
    logger: Optional[logging.Logger] = None,
    **provider_kwargs
) -> LLMClient:
    """
    Factory function to create LLM client with specified provider.
    
    Args:
        provider_name: Name of the provider ("gemini", etc.)
        retry_config: Retry configuration
        logger: Logger instance
        **provider_kwargs: Additional arguments for provider
        
    Returns:
        Configured LLMClient instance
    """
    if provider_name.lower() == "gemini":
        provider = GeminiProvider(**provider_kwargs)
    else:
        raise ValueError(f"Unknown provider: {provider_name}")
    
    return LLMClient(provider=provider, retry_config=retry_config, logger=logger)
