"""
LLM Integrations

This package contains integrations for various Large Language Models (LLMs)
that can use the NLQ2SPARQL tools via function calling.

Each integration module handles the specific function calling format and
communication protocol for its respective LLM while using the same underlying
tools and agents.
"""

from .base_integration import BaseLLMIntegration
from .gemini_integration import GeminiWikidataIntegration

__all__ = [
    "BaseLLMIntegration",
    "GeminiWikidataIntegration",
]
