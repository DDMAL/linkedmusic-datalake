"""
Base Integration Class

This module defines the abstract base class for all LLM integrations.
It provides a common interface that all specific LLM integrations should implement.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any


class BaseLLMIntegration(ABC):
    """
    Abstract base class for LLM integrations.
    
    This class defines the common interface that all LLM integrations should
    implement, ensuring consistency across different LLM providers.
    """
    
    def __init__(self, name: str):
        """
        Initialize the base integration.
        
        Args:
            name: A descriptive name for this integration (e.g., "Gemini", "GPT-4")
        """
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    @abstractmethod
    def get_function_declarations(self) -> List[Dict[str, Any]]:
        """
        Get the function declarations in the format expected by the LLM.
        
        Each LLM has its own format for function declarations, so this method
        should return the declarations in the appropriate format.
        
        Returns:
            List of function declaration dictionaries.
        """
        pass
    
    @abstractmethod
    async def execute_function_call(self, function_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Execute a function call requested by the LLM.
        
        Args:
            function_name: The name of the function to execute.
            arguments: The arguments to pass to the function.
            
        Returns:
            The result of the function execution.
        """
        pass
    
    @abstractmethod
    async def send_message_with_tools(self, message: str) -> str:
        """
        Send a message to the LLM with tool capabilities enabled.
        
        Args:
            message: The user message to send to the LLM.
            
        Returns:
            The LLM's response after potentially using tools.
        """
        pass
    
    def log_function_call(self, function_name: str, arguments: Dict[str, Any], result: Any):
        """
        Log a function call for debugging purposes.
        
        Args:
            function_name: The name of the function that was called.
            arguments: The arguments that were passed.
            result: The result that was returned.
        """
        self.logger.info(f"Function call: {function_name}({arguments}) -> {result}")
    
    def log_error(self, error: Exception, context: str = ""):
        """
        Log an error with context.
        
        Args:
            error: The exception that occurred.
            context: Additional context about where the error occurred.
        """
        self.logger.error(f"Error in {self.name} integration{f' ({context})' if context else ''}: {error}")
