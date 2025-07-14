"""
Modern pytest tests for LLM provider clients
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from providers.base import BaseLLMClient, ConfigurationError, APIError
    from providers.gemini_client import GeminiClient
    from providers.chatgpt_client import ChatGPTClient  
    from providers.claude_client import ClaudeClient
    from config import Config
except ImportError as e:
    pytest.skip(f"Import error: {e}", allow_module_level=True)


@pytest.mark.unit
class TestBaseLLMClient:
    """Test the abstract base LLM client"""
    
    def test_provider_name_extraction(self):
        """Test that provider names are correctly extracted from class names"""
        
        class TestGeminiClient(BaseLLMClient):
            def get_required_config_fields(self): return ["model"]
            def get_package_name(self): return "test"
            def get_install_command(self): return "pip install test"
            def _call_llm_api(self, prompt, verbose=False): return "test"
        
        with patch.object(TestGeminiClient, '_validate_configuration'):
            with patch.object(TestGeminiClient, '_setup_provider'):
                client = TestGeminiClient.__new__(TestGeminiClient)
                client.config = Mock()
                assert client._get_provider_name() == "testgemini"
    
    def test_clean_response_markdown_removal(self, mock_llm_client):
        """Test response cleaning removes markdown formatting"""
        test_cases = [
            ("```sparql\nSELECT * WHERE { ?s ?p ?o }\n```", "SELECT * WHERE { ?s ?p ?o }"),
            ("```\nSELECT * WHERE { ?s ?p ?o }\n```", "SELECT * WHERE { ?s ?p ?o }"),
            ("SELECT * WHERE { ?s ?p ?o }", "SELECT * WHERE { ?s ?p ?o }"),
            ("", ""),
            ("```sparql\n\n```", ""),
        ]
        
        for input_text, expected in test_cases:
            result = mock_llm_client._clean_response(input_text)
            assert result == expected
    
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
    
    def test_configuration_validation_missing_provider_config(self, mock_config):
        """Test configuration validation fails with missing provider config"""
        mock_config.get_provider_config.return_value = None
        
        class TestClient(BaseLLMClient):
            def get_required_config_fields(self): return ["model"]
            def get_package_name(self): return "test" 
            def get_install_command(self): return "pip install test"
            def _call_llm_api(self, prompt, verbose=False): return "test"
        
        with pytest.raises(ConfigurationError, match="provider configuration not found"):
            TestClient(mock_config)


@pytest.mark.unit
@pytest.mark.parametrize("client_class,expected_fields,package_name", [
    (GeminiClient, ["model", "temperature"], "google.generativeai"),
    (ChatGPTClient, ["model", "max_tokens", "temperature"], "openai"),
    (ClaudeClient, ["model", "max_tokens", "temperature"], "anthropic"),
])
class TestProviderClients:
    """Test individual provider clients"""
    
    def test_required_config_fields(self, client_class, expected_fields, package_name):
        """Test that providers declare correct required fields"""
        # Call as static method to avoid instantiation
        fields = client_class.get_required_config_fields(None)
        assert fields == expected_fields
    
    def test_package_name(self, client_class, expected_fields, package_name):
        """Test that providers declare correct package names"""
        name = client_class.get_package_name(None)
        assert name == package_name
    
    def test_install_command(self, client_class, expected_fields, package_name):
        """Test that providers have install commands"""
        command = client_class.get_install_command(None)
        assert "poetry add" in command or "pip install" in command
        assert package_name.split(".")[0] in command


@pytest.mark.integration 
@pytest.mark.requires_api_key
class TestProviderIntegration:
    """Integration tests for provider clients (require API keys)"""
    
    @pytest.mark.skip(reason="Requires valid API keys")
    def test_gemini_real_api_call(self):
        """Test actual Gemini API call (skipped by default)"""
        config = Config()
        client = GeminiClient(config)
        
        # This would make a real API call
        response = client.generate_sparql(
            "Find all artists", 
            "musicbrainz",
            verbose=True
        )
        assert isinstance(response, str)
        assert len(response) > 0


@pytest.mark.unit
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
    
    def test_api_error_propagation(self, mock_llm_client):
        """Test that API errors are properly propagated"""
        mock_llm_client._call_llm_api = Mock(side_effect=Exception("API failed"))
        
        with pytest.raises(Exception):  # Should be wrapped in ProviderError
            mock_llm_client.generate_sparql("test query", "test_db")


@pytest.mark.slow  
class TestPerformance:
    """Performance-related tests"""
    
    @pytest.mark.skip(reason="Slow test, run manually")
    def test_multiple_requests_performance(self, mock_llm_client):
        """Test performance with multiple requests"""
        import time
        
        queries = ["Find artists", "Get albums", "List songs"] * 10
        
        start_time = time.time()
        for query in queries:
            mock_llm_client.generate_sparql(query, "test_db")
        end_time = time.time()
        
        # Should complete 30 mock requests in under 1 second
        assert (end_time - start_time) < 1.0
