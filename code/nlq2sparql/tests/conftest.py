"""
Shared test fixtures and utilities for nlq2sparql test suite

This module provides flexible, parameterizable fixtures for testing:

Example Usage:
    # Basic usage with defaults
    def test_basic(mock_config):
        assert mock_config.get_available_databases()
    
    # Parameterized usage
    @pytest.mark.parametrize("mock_config", [
        {"databases": ["custom_db"], "api_key": "custom_key"}
    ], indirect=True)
    def test_custom(mock_config):
        assert "custom_db" in mock_config.get_available_databases()
    
    # Using mock LLM client with custom response
    @pytest.mark.parametrize("mock_llm_client", [
        {"response": "SELECT ?custom WHERE { ?s ?p ?o }", "should_fail": False}
    ], indirect=True)
    def test_llm(mock_llm_client):
        result = mock_llm_client.generate_sparql("test", "db")
        assert "custom" in result
"""

import pytest
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Core imports
from config import Config
from providers.base import BaseLLMClient, ConfigurationError, APIError


@pytest.fixture
def mock_config(request):
    """Mock configuration for isolated testing
    
    Can be parameterized with custom data:
    @pytest.mark.parametrize("mock_config", [{"databases": ["custom_db"]}], indirect=True)
    """
    # Get custom parameters or use defaults
    params = getattr(request, 'param', {})
    
    # Default configuration data
    default_providers = {
        "gemini": {"model": "gemini-pro", "temperature": 0.1},
        "chatgpt": {"model": "gpt-3.5-turbo", "max_tokens": 1000, "temperature": 0.1},
        "claude": {"model": "claude-3-sonnet", "max_tokens": 1000, "temperature": 0.1}
    }
    
    default_databases = ["diamm", "session", "dlt1000", "global-jukebox"]
    default_api_keys = {
        "gemini": "gemini_api_key",
        "chatgpt": "openai_api_key", 
        "claude": "anthropic_api_key"
    }
    
    # Allow parameter overrides
    providers = params.get("providers", default_providers)
    databases = params.get("databases", default_databases)
    api_keys = params.get("api_keys", default_api_keys)
    prefixes = params.get("prefixes", ["PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>"])
    
    config = Mock(spec=Config)
    config.config_data = {
        "providers": providers,
        "api_key_mappings": api_keys,
        "databases": {db: {"default_query": f"Find all items in {db}"} for db in databases}
    }
    config.prefixes_data = {
        "test_db": {"prefixes": prefixes}
    }
    
    # Mock methods with configurable returns
    config.get_api_key = Mock(return_value=params.get("api_key", "test_api_key"))
    config.get_provider_config = Mock(side_effect=lambda p: providers.get(p))
    config.get_prefix_declarations = Mock(return_value=prefixes)
    config.get_available_databases = Mock(return_value=databases)
    config.get_default_query = Mock(side_effect=lambda db: f"Find all items in {db}")
    
    return config


@pytest.fixture(scope="session")
def real_config():
    """Real configuration for integration testing (session-scoped for performance)"""
    return Config()


@pytest.fixture  
def mock_llm_client(request):
    """Mock LLM client that bypasses validation
    
    Can be parameterized with custom behavior:
    @pytest.mark.parametrize("mock_llm_client", [{"response": "CUSTOM SPARQL"}], indirect=True)
    """
    # Get custom parameters or use defaults
    params = getattr(request, 'param', {})
    custom_response = params.get("response", "SELECT * WHERE { ?s ?p ?o }")
    provider_name = params.get("provider_name", "test")
    should_fail = params.get("should_fail", False)
    
    # Get or create mock config
    mock_config_instance = params.get("config")
    if not mock_config_instance:
        # Create a minimal mock config if none provided
        mock_config_instance = Mock(spec=Config)
        mock_config_instance.get_api_key = Mock(return_value="test_key")
        mock_config_instance.get_provider_config = Mock(return_value={"model": "test_model"})
    
    class TestLLMClient(BaseLLMClient):
        def get_required_config_fields(self):
            return params.get("required_fields", ["model", "temperature"])
        
        def get_package_name(self):
            return params.get("package_name", "test_package")
        
        def get_install_command(self):
            return params.get("install_command", "pip install test_package")
        
        def _call_llm_api(self, prompt, verbose=False):
            if should_fail:
                raise APIError("Mock API failure")
            return custom_response
    
    # Create client without triggering validation
    with patch.object(TestLLMClient, '_validate_configuration'):
        with patch.object(TestLLMClient, '_setup_provider'):
            client = TestLLMClient.__new__(TestLLMClient)
            client.config = mock_config_instance
            client.provider_name = provider_name
            client.logger = Mock()
            client.api_key = params.get("api_key", "test_key")
            client.model = params.get("model", "test_model")
            client.temperature = params.get("temperature", 0.1)
            client.client = None
            return client


# Test data generators (more flexible than hardcoded constants)
def get_sample_queries(domain=None):
    """Generate sample queries, optionally filtered by domain"""
    base_queries = [
        "Find all artists",
        "Get songs by The Beatles", 
        "Show albums from 1970",
        "List composers born in Germany",
        "Find manuscripts from the 15th century",
        "Show recordings from Montreal sessions"
    ]
    
    if domain == "music":
        return [q for q in base_queries if any(term in q.lower() 
                for term in ["artist", "song", "album", "composer"])]
    elif domain == "historical":
        return [q for q in base_queries if any(term in q.lower() 
                for term in ["manuscript", "century", "born"])]
    return base_queries


def get_sample_databases(include_test=False):
    """Get available databases for testing"""
    real_dbs = ["diamm", "session", "dlt1000", "global-jukebox"]
    test_dbs = ["test_db", "mock_db"]
    
    return real_dbs + (test_dbs if include_test else [])


def get_provider_test_data():
    """Generate provider test data tuples"""
    return [
        ("gemini", ["model", "temperature"], "google.generativeai"),
        ("chatgpt", ["model", "max_tokens", "temperature"], "openai"), 
        ("claude", ["model", "max_tokens", "temperature"], "anthropic"),
    ]


# Backward compatibility (deprecated - use functions above)
SAMPLE_QUERIES = get_sample_queries()
SAMPLE_DATABASES = get_sample_databases() 
PROVIDER_TEST_DATA = get_provider_test_data()


def assert_valid_sparql(query: str, expected_type=None):
    """Assert that a string looks like valid SPARQL
    
    Args:
        query: The SPARQL query string to validate
        expected_type: Optional expected query type ('SELECT', 'CONSTRUCT', etc.)
    """
    assert isinstance(query, str), "Query must be a string"
    assert len(query.strip()) > 0, "Query cannot be empty"
    
    # Check for valid SPARQL query types
    valid_types = ["SELECT", "CONSTRUCT", "ASK", "DESCRIBE"]
    has_valid_type = any(kw in query.upper() for kw in valid_types)
    assert has_valid_type, f"Query must contain one of: {', '.join(valid_types)}"
    
    # If specific type expected, verify it
    if expected_type:
        assert expected_type.upper() in query.upper(), f"Expected {expected_type} query"


def create_mock_response(content: str, with_markdown: bool = True, response_type="sparql"):
    """Create mock LLM response with optional formatting
    
    Args:
        content: The response content
        with_markdown: Whether to wrap in markdown code block
        response_type: The type of code block (sparql, sql, etc.)
    """
    if with_markdown:
        return f"```{response_type}\n{content}\n```"
    return content


@pytest.fixture(scope="session")
def sample_sparql_queries():
    """Session-scoped fixture providing various SPARQL query examples"""
    return {
        "select": "SELECT ?artist ?name WHERE { ?artist rdfs:label ?name }",
        "construct": "CONSTRUCT { ?s rdf:type ex:Artist } WHERE { ?s ex:hasName ?name }",
        "ask": "ASK WHERE { ?artist rdf:type ex:Artist }",
        "describe": "DESCRIBE ?artist WHERE { ?artist rdf:type ex:Artist }",
        "complex": """
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            SELECT ?artist ?album ?year WHERE {
                ?artist rdf:type ex:Artist .
                ?artist ex:released ?album .
                ?album ex:year ?year .
                FILTER(?year > 1970)
            }
        """
    }
