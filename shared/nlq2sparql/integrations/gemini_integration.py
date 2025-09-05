"""
Gemini Integration for Wikidata Tools

This module provides integration between Google's Gemini API and the Wikidata tools,
enabling Gemini to use function calling to look up QIDs and PIDs from Wikidata.

The integration follows Gemini's function calling specification and provides
a clean interface for natural language queries that need Wikidata lookups.
"""

import asyncio
import logging
import os
import time
import warnings
from typing import Dict, List, Optional, Any
from pathlib import Path
import sys

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, that's okay
    pass

# Import parent modules using relative imports  
try:
    from ..config import Config
    from ..providers.base import BaseLLMClient, APIError, ConfigurationError
    from ..tracing import get_tracer
except ImportError:
    # Fallback for when running directly
    sys.path.append(str(Path(__file__).parent.parent))
    from config import Config
    from providers.base import BaseLLMClient, APIError, ConfigurationError
    from tracing import get_tracer

try:
    from google import genai
    from google.genai import types
except ImportError as e:
    genai = None
    types = None
    import warnings
    warnings.warn(f"Google GenAI not available: {e}. Install with: poetry add google-genai")

# Use a conditional import to handle both module and direct script execution
try:
    from .base_integration import BaseLLMIntegration
    from ..tools.wikidata_tool import find_entity_id, find_property_id
except (ImportError, ValueError):
    # This fallback allows the script to be run directly for development/testing
    from base_integration import BaseLLMIntegration
    from tools.wikidata_tool import find_entity_id, find_property_id


class GeminiWikidataIntegration(BaseLLMIntegration):
    """
    Gemini integration for Wikidata tools.
    
    This class handles the communication between Gemini's function calling API
    and the Wikidata lookup tools, enabling natural language queries that can
    resolve entities and properties to their QIDs and PIDs.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Gemini Wikidata integration.
        
        Args:
            api_key: Gemini API key. If not provided, will look for GEMINI_API_KEY env var.
        """
        super().__init__("Gemini")
        
        # Initialize tracing
        self.tracer = get_tracer("gemini_integration")
        self.tracer.info("initialization", "Initializing Gemini Wikidata Integration")
        
        if genai is None:
            raise ImportError("Google GenAI SDK not available. Install with: poetry add google-genai")
        
        # Set up API key
        api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Gemini API key required. Set GEMINI_API_KEY environment variable or pass api_key parameter.")
        
        # Configure the client
        self.client = genai.Client(api_key=api_key)
        self.tracer.info("initialization", "Gemini client configured successfully")
        
        # Available functions mapped to their implementations
        self.available_functions = {
            "find_entity_id": find_entity_id,
            "find_property_id": find_property_id,
        }
        
        self.tracer.info("initialization", "Available functions registered", {
            "functions": list(self.available_functions.keys())
        })
    
    def get_function_declarations(self) -> List[Dict[str, Any]]:
        """
        Get function declarations in Gemini's expected format.
        
        Returns:
            List of function declarations for Gemini function calling.
        """
        return [
            {
                "name": "find_entity_id",
                "description": (
                    "Find the Wikidata QID (entity identifier) for a given entity like a composer, "
                    "musician, instrument, or musical work. Uses fuzzy search that can handle "
                    "descriptive queries like 'Bach composer' or 'William Byrd English composer'. "
                    "Returns the QID (e.g., 'Q1339' for Bach) or None if not found."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "entity_label": {
                            "type": "string",
                            "description": (
                                "The name or description of the entity to search for. "
                                "Can include descriptive terms like 'composer', 'musician', "
                                "'English composer', etc. Examples: 'Guillaume Dufay', "
                                "'Bach composer', 'William Byrd English composer'."
                            ),
                        }
                    },
                    "required": ["entity_label"],
                },
            },
            {
                "name": "find_property_id",
                "description": (
                    "Find the Wikidata PID (property identifier) for a given property or "
                    "relationship type. Uses strict search for precise property matching. "
                    "Returns the PID (e.g., 'P86' for 'composer') or None if not found."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "property_label": {
                            "type": "string",
                            "description": (
                                "The name of the property to search for. Should be precise "
                                "property names like 'composer', 'birth date', 'genre', "
                                "'instrument', 'performer', etc."
                            ),
                        }
                    },
                    "required": ["property_label"],
                },
            },
        ]
    
    async def execute_function_call(self, function_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Execute a function call requested by Gemini.
        
        Args:
            function_name: The name of the function to execute.
            arguments: The arguments to pass to the function.
            
        Returns:
            The result of the function execution.
        """
        with self.tracer.trace_operation("function_call", {
            "function": function_name,
            "arguments": arguments
        }) as operation_id:
            
            if function_name not in self.available_functions:
                error_msg = f"Unknown function: {function_name}"
                self.tracer.error("function_call", error_msg, {
                    "function": function_name,
                    "available_functions": list(self.available_functions.keys())
                })
                self.log_error(ValueError(error_msg), "execute_function_call")
                return {"error": error_msg}

            start_time = time.time()
            try:
                # Get the function implementation
                func = self.available_functions[function_name]
                
                self.tracer.debug("function_call", f"Executing {function_name}", {
                    "function": function_name,
                    "arguments": arguments
                })
                
                # Execute the function (all our functions are async)
                result = await func(**arguments)
                
                duration_ms = (time.time() - start_time) * 1000
                
                # Trace the function call
                self.tracer.trace_function_call(function_name, arguments, result, duration_ms)
                
                # Log the function call (existing method)
                self.log_function_call(function_name, arguments, result)
                
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                self.tracer.error("function_call", f"Function {function_name} failed: {str(e)}", {
                    "function": function_name,
                    "arguments": arguments,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "duration_ms": duration_ms
                })
                self.log_error(e, f"execute_function_call({function_name})")
                return {"error": str(e)}
    
    async def send_message_with_tools(self, message: str, model: str = "gemini-2.5-flash") -> Dict[str, Any]:  # type: ignore[override]
        """
        Send a message to Gemini with Wikidata tools enabled.
        
        Args:
            message: The user message to send to Gemini.
            model: The Gemini model to use.
            
        Returns:
            Dict containing:
            - text: The final response text
            - reasoning: Gemini's internal reasoning (if available)
            - function_calls: List of function calls made
            - thought_signatures: Encrypted reasoning signatures
        """
        result = {
            "text": "",
            "reasoning": None,
            "function_calls": [],
            "thought_signatures": []
        }
        
        try:
            # Check if types module is available
            if types is None:
                result["text"] = "Google GenAI SDK not available. Install with: poetry add google-genai"
                return result
                
            self.tracer.info("send_message_with_tools", "Preparing LLM API call", {
                "model": model,
                "message_length": len(message),
                "message_preview": message[:200] + "..." if len(message) > 200 else message,
                "tools_available": len(self.get_function_declarations())
            })
                
            # Create tools configuration
            tools = types.Tool(function_declarations=self.get_function_declarations())  # type: ignore
            config = types.GenerateContentConfig(tools=[tools])  # type: ignore
            
            start_time = time.time()
            
            # Send initial request
            self.tracer.info("send_message_with_tools", "Making LLM API call", {
                "provider": "gemini",
                "model": model,
                "input_message": message,
                "tools_enabled": True
            })
            
            response = self.client.models.generate_content(
                model=model,
                contents=message,
                config=config,
            )
            
            api_duration = (time.time() - start_time) * 1000
            
            # Log the complete LLM API interaction
            self.tracer.trace_llm_call(
                provider="gemini",
                model=model,
                messages=[{"role": "user", "content": message}],
                response=response,
                duration_ms=api_duration
            )
            
            # Extract thought signatures and collect all function calls from the response
            function_calls_to_execute = []
            candidate = None
            
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content and hasattr(candidate.content, 'parts'):
                    for part in candidate.content.parts:  # type: ignore
                        # Capture thought signatures for reasoning
                        if hasattr(part, 'thought_signature') and part.thought_signature:
                            result["thought_signatures"].append(part.thought_signature)
                        
                        # Collect function calls (don't execute yet)
                        if hasattr(part, 'function_call') and part.function_call:
                            function_calls_to_execute.append(part.function_call)
            
            # If we have function calls, execute ALL of them
            if function_calls_to_execute and candidate:
                self.tracer.info("send_message_with_tools", f"Found {len(function_calls_to_execute)} function calls to execute")
                
                # Execute all function calls
                function_response_parts = []
                for func_call in function_calls_to_execute:
                    # Log the function call attempt
                    call_info = {
                        "function": func_call.name,
                        "arguments": dict(func_call.args) if func_call.args else {},  # type: ignore
                        "result": None,
                        "error": None
                    }
                    
                    # Execute the function call
                    func_result = await self.execute_function_call(
                        func_call.name or "",  # type: ignore
                        dict(func_call.args) if func_call.args else {}  # type: ignore
                    )
                    call_info["result"] = func_result
                    result["function_calls"].append(call_info)
                    
                    # Create function response part
                    function_response_part = types.Part.from_function_response(  # type: ignore
                        name=func_call.name or "",  # type: ignore
                        response={"result": func_result},
                    )
                    function_response_parts.append(function_response_part)
                
                # Continue the conversation with ALL function results
                contents = [
                    types.Content(role="user", parts=[types.Part(text=message)]),  # type: ignore
                    candidate.content,  # Gemini's function calls
                    types.Content(role="user", parts=function_response_parts)  # type: ignore
                ]
                
                final_response = self.client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=config,
                )
                
                # Extract final reasoning and response
                if hasattr(final_response, 'candidates') and final_response.candidates:
                    final_candidate = final_response.candidates[0]
                    if hasattr(final_candidate, 'content') and final_candidate.content and hasattr(final_candidate.content, 'parts'):
                        for final_part in final_candidate.content.parts:  # type: ignore
                            if hasattr(final_part, 'thought_signature') and final_part.thought_signature:
                                result["thought_signatures"].append(final_part.thought_signature)
                
                result["text"] = final_response.text
                return result
            
            # No function calls needed, return direct response
            # Extract text parts directly to avoid warnings about thought signatures
            direct_text = ""
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content and hasattr(candidate.content, 'parts'):
                    for part in candidate.content.parts:  # type: ignore
                        if hasattr(part, 'thought_signature') and part.thought_signature:
                            result["thought_signatures"].append(part.thought_signature)
                        if hasattr(part, 'text') and part.text:
                            direct_text += part.text
            
            result["text"] = direct_text or response.text
            return result
            
        except Exception as e:
            self.log_error(e, "send_message_with_tools")
            result["text"] = f"Error communicating with Gemini: {e}"
            return result
    
    async def demo(self, queries: Optional[List[str]] = None):
        """
        Run a demonstration of the Gemini Wikidata integration.
        
        Args:
            queries: Optional list of queries to test. If not provided, uses default examples.
        """
        if queries is None:
            queries = [
                "Find the Wikidata QID for Guillaume Dufay",
                "What is the QID for Bach?",
                "Find the property ID for 'composer'",
                "Get me the QID for William Byrd the English composer",
            ]
        
        print(f"=== {self.name} Wikidata Integration Demo ===")
        
        for i, query in enumerate(queries, 1):
            print(f"\n--- Query {i}: \"{query}\" ---")
            try:
                response_data = await self.send_message_with_tools(query)
                
                print(f"Response: {response_data['text']}")
                
                # Show function calls if any were made
                if response_data['function_calls']:
                    print(f"Function Calls Made:")
                    for call in response_data['function_calls']:
                        print(f"  → {call['function']}({call['arguments']}) → {call['result']}")
                
                # Show reasoning indicators
                if response_data['thought_signatures']:
                    print(f"Reasoning: {len(response_data['thought_signatures'])} thought signature(s) captured")
                    print("  (This shows Gemini reasoned through the request)")
                
            except Exception as e:
                print(f"Error: {e}")


async def main():
    """
    Example usage of the Gemini Wikidata integration.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        # Initialize the integration
        integration = GeminiWikidataIntegration()
        
        # Run the demo
        await integration.demo()
        
    except Exception as e:
        print(f"Failed to initialize Gemini integration: {e}")
        print("Make sure you have:")
        print("1. Installed google-genai: poetry add google-genai")
        print("2. Set GEMINI_API_KEY environment variable")


if __name__ == "__main__":
    asyncio.run(main())
