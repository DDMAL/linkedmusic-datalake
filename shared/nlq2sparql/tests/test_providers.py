"""
Lightweight provider tests

Tests the essential provider functionality without unnecessary complexity.
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path

# Import providers and config using relative imports
try:
    from ..providers.base import BaseLLMClient, ConfigurationError, APIError
    from ..providers.gemini_client import GeminiClient
    from ..providers.chatgpt_client import ChatGPTClient  
    from ..providers.claude_client import ClaudeClient
    from ..config import Config
except ImportError:
    # Fallback for when running tests directly
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    try:
        from providers.base import BaseLLMClient, ConfigurationError, APIError
        from providers.gemini_client import GeminiClient
        from providers.chatgpt_client import ChatGPTClient  
        from providers.claude_client import ClaudeClient
        from config import Config
    except ImportError as e:
        pytest.skip(f"Import error: {e}", allow_module_level=True)


class TestProviderBase:
    """Test base provider functionality"""
    
    def test_base_client_is_abstract(self):
        """BaseLLMClient cannot be instantiated directly"""
        config = Config()
        with pytest.raises(TypeError):
            BaseLLMClient(config)
    
    def test_base_client_has_required_methods(self):
        """BaseLLMClient defines required interface"""
        required_methods = ['generate_sparql', '_call_llm_api', 'get_required_config_fields', 
                          'get_package_name', 'get_install_command']
        for method in required_methods:
            assert hasattr(BaseLLMClient, method)
    
    def test_response_cleaning(self, mock_llm_client):
        """Test response cleaning removes markdown formatting"""
        test_cases = [
            ("```sparql\nSELECT * WHERE { ?s ?p ?o }\n```", "SELECT * WHERE { ?s ?p ?o }"),
            ("SELECT * WHERE { ?s ?p ?o }", "SELECT * WHERE { ?s ?p ?o }"),
            ("", ""),
        ]
        for input_text, expected in test_cases:
            result = mock_llm_client._clean_response(input_text)
            assert result == expected


@pytest.mark.parametrize("client_class,expected_fields,package_name", [
    (GeminiClient, ["model", "temperature"], "google.generativeai"),
    (ChatGPTClient, ["model", "max_tokens", "temperature"], "openai"),
    (ClaudeClient, ["model", "max_tokens", "temperature"], "anthropic"),
])
class TestProviderClients:
    """Test individual provider clients"""
    
    def test_required_config_fields(self, client_class, expected_fields, package_name):
        """Test that providers declare correct required fields"""
        fields = client_class.get_required_config_fields(None)
        assert fields == expected_fields
    
    def test_package_name(self, client_class, expected_fields, package_name):
        """Test that providers declare correct package names"""
        name = client_class.get_package_name(None)
        assert name == package_name


class TestErrorHandling:
    """Test error handling scenarios"""
    
    def test_empty_nlq_raises_error(self, mock_llm_client):
        """Test that empty natural language query raises ValueError"""
        with pytest.raises(ValueError, match="Natural language query cannot be empty"):
            mock_llm_client.generate_sparql("", "test_db")
    
    def test_empty_database_raises_error(self, mock_llm_client):
        """Test that empty database name raises ValueError"""
        with pytest.raises(ValueError, match="Database name cannot be empty"):
            mock_llm_client.generate_sparql("test query", "")
    
    def test_configuration_validation_missing_api_key(self, mock_config):
        """Test configuration validation fails with missing API key"""
        mock_config.get_api_key.return_value = None
        
        class TestClient(BaseLLMClient):
            def get_required_config_fields(self): return ["model"]
            def get_package_name(self): return "test"
            def get_install_command(self): return "pip install test"
            def _call_llm_api(self, prompt, verbose=False): return "test"
        
        with pytest.raises(ConfigurationError, match="API key not found"):
            TestClient(mock_config)