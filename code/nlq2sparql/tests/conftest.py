"""
Simple test fixtures for nlq2sparql
"""

import pytest
from unittest.mock import Mock, patch
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config
from providers.base import BaseLLMClient, APIError


@pytest.fixture
def mock_config():
    """Basic mock configuration"""
    config = Mock(spec=Config)
    config.get_available_databases.return_value = ["diamm", "session", "dlt1000"]
    config.get_api_key.return_value = "test_key"
    config.get_provider_config.return_value = {"model": "test_model", "temperature": 0.1}
    config.get_prefix_declarations.return_value = ["PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>"]
    config.get_default_query.return_value = "Find all items"
    # Add minimal config_data for validation
    config.config_data = {"api_key_mappings": {"test": "test_key"}}
    return config


@pytest.fixture(scope="session")
def real_config():
    """Real configuration for integration tests"""
    return Config()


@pytest.fixture  
def mock_llm_client(request):
    """Mock LLM client for testing"""
    params = getattr(request, 'param', {})
    response = params.get("response", "SELECT * WHERE { ?s ?p ?o }")
    should_fail = params.get("should_fail", False)
    
    class TestClient(BaseLLMClient):
        def get_required_config_fields(self): return ["model"]
        def get_package_name(self): return "test_package"
        def get_install_command(self): return "pip install test_package"
        def _call_llm_api(self, prompt, verbose=False):
            if should_fail:
                raise APIError("Mock failure")
            return response
    
    with patch.object(TestClient, '_validate_configuration'), \
         patch.object(TestClient, '_setup_provider'):
        client = TestClient.__new__(TestClient)
        client.config = Mock()
        client.provider_name = "test"
        client.logger = Mock()
        return client


def assert_valid_sparql(query: str):
    """Check if query looks like valid SPARQL"""
    assert isinstance(query, str) and len(query.strip()) > 0
    assert any(kw in query.upper() for kw in ["SELECT", "CONSTRUCT", "ASK", "DESCRIBE"])
