"""
Essential provider architecture tests

Tests the provider base class and client initialization.
Focuses on the core provider functionality that all providers share.
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from providers.base import BaseLLMClient, ProviderError
from config import Config


class TestProviderBase:
    """Test base provider functionality"""
    
    def test_base_client_is_abstract(self):
        """BaseLLMClient cannot be instantiated directly"""
        config = Config()
        
        with pytest.raises(TypeError):
            BaseLLMClient(config)
    
    def test_base_client_has_required_methods(self):
        """BaseLLMClient defines required interface"""
        # Check that abstract methods exist
        assert hasattr(BaseLLMClient, 'generate_sparql')
        assert hasattr(BaseLLMClient, '_call_llm_api')
        assert hasattr(BaseLLMClient, 'get_required_config_fields')
        assert hasattr(BaseLLMClient, 'get_package_name')
        assert hasattr(BaseLLMClient, 'get_install_command')
    
    def test_provider_error_exception(self):
        """ProviderError can be raised and caught"""
        with pytest.raises(ProviderError):
            raise ProviderError("Test error")
        
        # Test with message
        try:
            raise ProviderError("Test message")
        except ProviderError as e:
            assert str(e) == "Test message"


class MockLLMClient(BaseLLMClient):
    """Mock implementation for testing"""
    
    def get_required_config_fields(self) -> list:
        return ["test_api_key"]
    
    def get_package_name(self) -> str:
        return "test_package"
    
    def get_install_command(self) -> str:
        return "pip install test_package"
    
    def _call_llm_api(self, prompt: str, verbose: bool = False) -> str:
        return "SELECT * WHERE { ?s ?p ?o }"


class TestProviderImplementation:
    """Test provider implementation patterns"""
    
    @patch('providers.base.BaseLLMClient._validate_configuration')
    def test_mock_client_initialization(self, mock_validate):
        """Mock client initializes correctly"""
        config = Config()
        
        # Mock the package import check
        with patch('builtins.__import__'):
            client = MockLLMClient(config)
            
            assert client.config is config
            assert hasattr(client, 'logger')
            assert hasattr(client, 'provider_name')
    
    @patch('providers.base.BaseLLMClient._validate_configuration')
    def test_mock_client_sparql_generation(self, mock_validate):
        """Mock client generates SPARQL"""
        config = Config()
        
        with patch('builtins.__import__'):
            client = MockLLMClient(config)
            
            result = client.generate_sparql(
                nlq="Find all artists",
                database="test_db"
            )
            assert isinstance(result, str)
            assert len(result.strip()) > 0
            assert "SELECT" in result
    
    @patch('providers.base.BaseLLMClient._validate_configuration')
    def test_error_handling_in_base_class(self, mock_validate):
        """Base class handles errors appropriately"""
        config = Config()
        
        with patch('builtins.__import__'):
            client = MockLLMClient(config)
            
            # Test with invalid input - should raise ValueError
            with pytest.raises(ValueError):
                client.generate_sparql("", "test_db")
            
            # Test with valid input should work
            result = client.generate_sparql("test query", "test_db")
            assert isinstance(result, str)
    
    @patch('providers.base.BaseLLMClient._validate_configuration')
    def test_api_call_error_handling(self, mock_validate):
        """Provider handles API call errors"""
        config = Config()
        
        with patch('builtins.__import__'):
            client = MockLLMClient(config)
            
            # Override the _call_llm_api method to raise an exception
            def mock_api_call(prompt, verbose=False):
                raise Exception("API Error")
            
            client._call_llm_api = mock_api_call
            
            with pytest.raises(ProviderError):
                client.generate_sparql("test query", "test_db")


class TestProviderIntegration:
    """Test integration between providers and config"""
    
    @patch('providers.base.BaseLLMClient._validate_configuration')
    def test_client_uses_config_data(self, mock_validate):
        """Client properly accesses configuration"""
        config = Config()
        
        with patch('builtins.__import__'):
            client = MockLLMClient(config)
            
            # Should be able to access config methods
            databases = client.config.get_available_databases()
            assert isinstance(databases, list)
    
    def test_client_configuration_validation(self):
        """Client validates configuration on initialization"""
        config = Config()
        
        # Should fail without API key
        with pytest.raises((ProviderError, Exception)):
            with patch('builtins.__import__'):
                MockLLMClient(config)
    
    @patch('providers.base.BaseLLMClient._validate_configuration')
    def test_provider_name_extraction(self, mock_validate):
        """Client correctly extracts provider name from class"""
        config = Config()
        
        with patch('builtins.__import__'):
            client = MockLLMClient(config)
            
            # Should extract "mockllm" from "MockLLMClient"
            assert isinstance(client.provider_name, str)
            assert len(client.provider_name) > 0