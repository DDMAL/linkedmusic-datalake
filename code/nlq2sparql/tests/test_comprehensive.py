#!/usr/bin/env python3
"""
Simple integration tests for nlq2sparql
Tests basic system functionality
"""

import sys
import unittest
from pathlib import Path

# Handle imports - add parent directory to path for direct execution
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from config import Config
    from router import QueryRouter
    from providers.base import BaseLLMClient
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running from the nlq2sparql directory")
    sys.exit(1)


class MockLLMClient(BaseLLMClient):
    """Mock client for testing"""
    
    def _call_llm_api(self, prompt, verbose=False):
        return "SELECT * WHERE { ?s ?p ?o }"


class TestIntegration(unittest.TestCase):
    """Test system integration"""
    
    def test_system_setup(self):
        """Test basic system can be set up"""
        config = Config()
        self.assertIsNotNone(config)
        
        databases = config.get_available_databases()
        self.assertGreater(len(databases), 0)
    
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
        
        self.assertIn("SELECT", sparql)
        self.assertIn("WHERE", sparql)
    
    def test_provider_config_requirements(self):
        """Test providers fail properly without config"""
        config = Config()
        router = QueryRouter(config)
        
        # Should fail without API keys
        with self.assertRaises(ValueError) as cm:
            router._get_client("gemini")
        self.assertIn("API key", str(cm.exception))
    
    def test_cli_import(self):
        """Test CLI can be imported"""
        try:
            import cli
            self.assertIsNotNone(cli)
        except ImportError:
            self.fail("CLI should be importable")


if __name__ == "__main__":
    # Simple test runner for direct execution
    unittest.main(verbosity=2)
