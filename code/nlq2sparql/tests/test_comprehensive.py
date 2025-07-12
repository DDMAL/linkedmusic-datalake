#!/usr/bin/env python3
"""
Simple integration tests for nlq2sparql
Tests basic system functionality
"""

import sys
from pathlib import Path

# Handle imports
try:
    from ..config import Config
    from ..router import QueryRouter
    from ..providers.base import BaseLLMClient
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import Config
    from router import QueryRouter
    from providers.base import BaseLLMClient


class MockLLMClient(BaseLLMClient):
    """Mock client for testing"""
    
    def _call_llm_api(self, prompt, verbose=False):
        return "SELECT * WHERE { ?s ?p ?o }"


class TestIntegration:
    """Test system integration"""
    
    def test_system_setup(self):
        """Test basic system can be set up"""
        config = Config()
        assert config is not None
        
        databases = config.get_available_databases()
        assert len(databases) > 0
    
    def test_router_with_mock_client(self):
        """Test router works with mock API"""
        config = Config()
        
        # Mock API key to avoid errors
        def mock_get_api_key(provider):
            return "mock_key"
        config.get_api_key = mock_get_api_key
        
        # Test with mock client
        client = MockLLMClient(config)
        sparql = client.generate_sparql("Find all songs", "diamm")
        
        assert "SELECT" in sparql
        assert "WHERE" in sparql
    
    def test_provider_config_requirements(self):
        """Test providers fail properly without config"""
        config = Config()
        router = QueryRouter(config)
        
        # Should fail without API keys
        try:
            router._get_client("gemini")
            assert False, "Should have failed without API key"
        except ValueError as e:
            assert "API key" in str(e)
    
    def test_cli_import(self):
        """Test CLI can be imported"""
        try:
            import cli
            assert cli is not None
        except ImportError:
            assert False, "CLI should be importable"


if __name__ == "__main__":
    # Simple test runner for direct execution
    import unittest
    
    # Convert to unittest format for direct execution
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestIntegration)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if result.wasSuccessful():
        print("✅ All integration tests passed!")
    else:
        print("❌ Some tests failed")
        sys.exit(1)


if __name__ == "__main__":
    # Simple test runner for direct execution
    import unittest
    
    # Convert to unittest format for direct execution
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestIntegration)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if result.wasSuccessful():
        print("✅ All integration tests passed!")
    else:
        print("❌ Some tests failed")
        sys.exit(1)
