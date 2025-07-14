"""
Essential query processing tests

Tests the core query routing and processing functionality.
Focuses on the main workflow users interact with.
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from router import QueryRouter, RouterError
from config import Config


class TestQueryProcessing:
    """Test core query processing functionality"""
    
    def test_router_initialization(self):
        """Router initializes with valid config"""
        config = Config()
        router = QueryRouter(config)
        assert router.config is config
        assert isinstance(router.provider_clients, dict)
        assert len(router.provider_clients) == 0  # Lazy loading
    
    def test_supported_providers(self):
        """Router knows about supported providers"""
        config = Config()
        router = QueryRouter(config)
        providers = router.get_supported_providers()
        
        assert isinstance(providers, list)
        assert len(providers) > 0
        
        # Should include our main providers
        expected = {"gemini", "chatgpt", "claude"}
        actual = set(providers)
        assert expected.issubset(actual)
    
    def test_router_rejects_invalid_provider(self):
        """Router rejects unknown providers"""
        config = Config()
        router = QueryRouter(config)
        
        with pytest.raises(ValueError, match="Unknown provider"):
            router._get_client("nonexistent_provider")
    
    def test_router_handles_missing_api_keys(self):
        """Router handles missing API keys gracefully"""
        config = Config()
        router = QueryRouter(config)
        
        # Should fail due to missing API keys, but with proper error
        with pytest.raises(RouterError, match="Failed to create.*client"):
            router._get_client("gemini")
    
    @patch('router.QueryRouter._get_client')
    def test_query_processing_workflow(self, mock_get_client):
        """Main query processing workflow works"""
        # Mock the client
        mock_client = Mock()
        mock_client.generate_sparql.return_value = "SELECT * WHERE { ?s ?p ?o }"
        mock_get_client.return_value = mock_client
        
        config = Config()
        router = QueryRouter(config)
        
        result = router.process_query(
            nlq="Find all artists",
            database="diamm", 
            provider="gemini"
        )
        
        assert isinstance(result, str)
        assert len(result.strip()) > 0
        mock_client.generate_sparql.assert_called_once()
    
    def test_database_validation(self):
        """Router validates database names"""
        config = Config()
        router = QueryRouter(config)
        
        # Valid database should not raise error (might fail on API keys though)
        try:
            router.process_query("test", "gemini", "diamm")
        except RouterError:
            pass  # Expected due to missing API keys
        except ValueError as e:
            if "database" in str(e).lower():
                pytest.fail("Should not reject valid database")
        
        # Invalid database should raise ValueError
        with pytest.raises(ValueError, match="database"):
            router.process_query("test", "gemini", "invalid_database")
