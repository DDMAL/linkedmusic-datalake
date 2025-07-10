"""
Base class for LLM provider clients
"""

from abc import ABC, abstractmethod
from typing import Optional


class BaseLLMClient(ABC):
    """Abstract base class for LLM provider clients"""
    
    def __init__(self, config):
        self.config = config
    
    @abstractmethod
    def _call_llm_api(self, prompt: str, verbose: bool = False) -> str:
        """
        Make the actual API call to the LLM provider
        
        This is the only method that differs between providers.
        Each provider implements their specific API call here.
        
        Args:
            prompt: The formatted prompt to send to the LLM
            verbose: Enable verbose output
            
        Returns:
            Raw response text from the LLM
        """
        pass
    
    def generate_sparql(
        self,
        nlq: str,
        database: str,
        ontology_context: str = "",
        verbose: bool = False
    ) -> str:
        """
        Generate SPARQL query from natural language query
        
        This method is implemented in the base class to provide consistent
        behavior across all providers. Only the API call differs.
        """
        prompt = self._build_prompt(nlq, database, ontology_context)
        
        if verbose:
            print(f"Sending request to {self.__class__.__name__}...")
            print(f"Prompt length: {len(prompt)} characters")
        
        try:
            # Call provider-specific API
            raw_response = self._call_llm_api(prompt, verbose)
            
            # Clean up the response - remove markdown formatting
            sparql_query = self._clean_response(raw_response)
            
            if verbose:
                print(f"Received response from {self.__class__.__name__}")
            
            return sparql_query
            
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} API error: {str(e)}")
    
    def _clean_response(self, response: str) -> str:
        """Clean up LLM response by removing markdown formatting"""
        sparql_query = response.strip()
        
        # Remove markdown code blocks
        if sparql_query.startswith("```sparql"):
            sparql_query = sparql_query[9:]
        if sparql_query.startswith("```"):
            sparql_query = sparql_query[3:]
        if sparql_query.endswith("```"):
            sparql_query = sparql_query[:-3]
        
        return sparql_query.strip()
    
    def _get_provider_config(self, provider_name: str) -> dict:
        """Get configuration for this provider with defaults"""
        defaults = {
            "gemini": {
                "model": "gemini-pro",
                "temperature": 0.1
            },
            "chatgpt": {
                "model": "gpt-3.5-turbo",
                "max_tokens": 1000,
                "temperature": 0.1
            },
            "claude": {
                "model": "claude-3-sonnet-20240229",
                "max_tokens": 1000,
                "temperature": 0.1
            }
        }
        
        # Get config from file, fall back to defaults
        config_data = self.config.get_provider_config(provider_name)
        provider_defaults = defaults.get(provider_name, {})
        
        # Merge defaults with config file values
        final_config = provider_defaults.copy()
        final_config.update(config_data)
        
        return final_config
    
    def _build_prompt(self, nlq: str, database: str, ontology_context: str = "") -> str:
        """Build the prompt for the LLM"""
        
        # Get prefix declarations for the database
        prefix_declarations = self.config.get_prefix_declarations(database)
        
        prompt = f"""You are a SPARQL query generator working with musical Linked Data.

Task: Convert the following natural language query to a SPARQL query that retrieve all 
relevant results from the {database} database. Do not guess Wikidata QIDs or PIDs, use the provided
ontology context if available. Return only the SPARQL query, no explanations. Ensure the query is syntatically correct.

Natural Language Query: {nlq}

Available Prefixes:
{prefix_declarations}

{"Ontology Context:" if ontology_context else ""}
{ontology_context}

SPARQL Query:"""
        
        return prompt
