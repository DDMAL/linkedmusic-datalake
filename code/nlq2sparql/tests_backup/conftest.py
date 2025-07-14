"""
Test configuration and fixtures for nlq2sparql tests
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import our modules
from config import Config
from providers.base import BaseLLMClient, ConfigurationError, APIError


@pytest.fixture
def mock_config():
    """Provide a mock configuration for testing"""
    config = Mock(spec=Config)
    config.config_data = {
        "providers": {
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
        },
        "api_key_mappings": {
            "gemini": "gemini_api_key",
            "chatgpt": "openai_api_key",
            "claude": "anthropic_api_key"
        }
    }
    config.prefixes_data = {
        "test_db": {
            "prefixes": [
                "PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>",
                "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>"
            ]
        }
    }
    config.get_api_key = Mock(return_value="test_api_key")
    config.get_provider_config = Mock(side_effect=lambda provider: config.config_data["providers"].get(provider))
    config.get_prefix_declarations = Mock(return_value=config.prefixes_data["test_db"]["prefixes"])
    return config


@pytest.fixture
def real_config():
    """Provide a real configuration instance for integration tests"""
    return Config()


@pytest.fixture
def mock_llm_client(mock_config):
    """Provide a mock LLM client for testing"""
    
    class MockLLMClient(BaseLLMClient):
        def get_required_config_fields(self):
            return ["model", "temperature"]
        
        def get_package_name(self):
            return "mock_package"
        
        def get_install_command(self):
            return "pip install mock_package"
        
        def _call_llm_api(self, prompt, verbose=False):
            return "SELECT * WHERE { ?s ?p ?o }"
    
    with patch.object(MockLLMClient, '_validate_configuration'):
        with patch.object(MockLLMClient, '_setup_provider'):
            client = MockLLMClient.__new__(MockLLMClient)
            client.config = mock_config
            client.provider_name = "mock"
            client.logger = Mock()
            client.api_key = "test_key"
            client.model = "test_model"
            client.temperature = 0.1
            client.client = None
            return client


@pytest.fixture
def sample_nlq():
    """Provide sample natural language queries for testing"""
    return [
        "Find all artists",
        "Get all songs by The Beatles", 
        "Show me albums released in 1970",
        "List composers from Germany"
    ]


@pytest.fixture
def sample_databases():
    """Provide sample database names for testing"""
    return ["musicbrainz", "cantus", "diamm", "thesession"]


class TestHelpers:
    """Helper methods for tests"""
    
    @staticmethod
    def assert_valid_sparql(query: str):
        """Assert that a string looks like a valid SPARQL query"""
        assert isinstance(query, str)
        assert len(query.strip()) > 0
        # Basic SPARQL structure check
        assert any(keyword in query.upper() for keyword in ["SELECT", "CONSTRUCT", "ASK", "DESCRIBE"])
    
    @staticmethod
    def create_mock_response(content: str, has_markdown: bool = True):
        """Create a mock LLM response"""
        if has_markdown:
            return f"```sparql\n{content}\n```"
        return content
