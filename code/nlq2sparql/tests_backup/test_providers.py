#!/usr/bin/env python3
"""
Provider tests for nlq2sparql
"""

import sys
from pathlib import Path

# Handle imports - add parent directory to path for direct execution
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from config import Config
    from providers.base import BaseLLMClient
    from router import QueryRouter
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running from the nlq2sparql directory")
    sys.exit(1)


class MockLLMClient(BaseLLMClient):
    """Mock client for testing"""
    
    def _call_llm_api(self, prompt, verbose=False):
        return "SELECT * WHERE { ?s ?p ?o }"


class TestProviders:
    """Test provider functionality"""
    
    def test_base_class_prompt_building(self):
        """Test prompt building in base class via generate_sparql"""
        config = Config()
        client = MockLLMClient(config)
        
        # Test that generate_sparql works (it builds prompt internally)
        sparql = client.generate_sparql("Find all songs", "diamm")
        
        assert isinstance(sparql, str)
        assert len(sparql) > 0
        assert "SELECT * WHERE { ?s ?p ?o }" == sparql
    
    def test_base_class_response_cleaning(self):
        """Test response cleaning"""
        config = Config()
        client = MockLLMClient(config)
        
        test_cases = [
            ("```sparql\nSELECT * WHERE { ?s ?p ?o }\n```", "SELECT * WHERE { ?s ?p ?o }"),
            ("```\nSELECT * WHERE { ?s ?p ?o }\n```", "SELECT * WHERE { ?s ?p ?o }"),
            ("SELECT * WHERE { ?s ?p ?o }", "SELECT * WHERE { ?s ?p ?o }"),
            ("   SELECT * WHERE { ?s ?p ?o }   ", "SELECT * WHERE { ?s ?p ?o }"),
        ]
        
        for dirty, expected in test_cases:
            clean = client._clean_response(dirty)
            assert clean == expected, f"Failed to clean: {dirty} -> {clean} (expected: {expected})"
    
    def test_provider_config_merging(self):
        """Test provider configuration merging"""
        config = Config()
        client = MockLLMClient(config)
        
        for provider in ['gemini', 'chatgpt', 'claude']:
            pconfig = client._get_provider_config(provider)
            
            assert isinstance(pconfig, dict)
            assert 'model' in pconfig
            assert 'temperature' in pconfig
            
            # Verify defaults are present
            if provider == 'gemini':
                assert pconfig['model'] == 'gemini-pro'
            elif provider == 'chatgpt':
                assert pconfig['model'] == 'gpt-3.5-turbo'
                assert 'max_tokens' in pconfig
            elif provider == 'claude':
                assert pconfig['model'] == 'claude-3-sonnet-20240229'
                assert 'max_tokens' in pconfig
    
    def test_generate_sparql_method(self):
        """Test the main generate_sparql method"""
        config = Config()
        client = MockLLMClient(config)
        
        result = client.generate_sparql(
            nlq="Find all songs",
            database="diamm",
            verbose=False
        )
        
        assert isinstance(result, str)
        assert result == "SELECT * WHERE { ?s ?p ?o }"
    
    def test_provider_imports_without_dependencies(self):
        """Test that provider classes can be imported without their dependencies"""
        # These should not raise ImportError at module level
        from providers.gemini_client import GeminiClient
        from providers.chatgpt_client import ChatGPTClient
        from providers.claude_client import ClaudeClient
        
        # Should be able to get the classes
        assert GeminiClient is not None
        assert ChatGPTClient is not None
        assert ClaudeClient is not None


class TestRouter:
    """Test router functionality"""
    
    def test_router_initialization(self):
        """Test router initialization"""
        config = Config()
        router = QueryRouter(config)
        
        assert router.config is config
        assert hasattr(router, 'provider_clients')
        assert router.provider_clients == {}
    
    def test_router_lazy_loading(self):
        """Test that router uses lazy loading"""
        config = Config()
        router = QueryRouter(config)
        
        # Initially no clients loaded
        assert len(router.provider_clients) == 0
        
        # Should fail to create clients due to missing API keys
        providers = ['gemini', 'chatgpt', 'claude']
        
        for provider in providers:
            try:
                client = router._get_client(provider)
                assert False, f"Should have failed for {provider} due to missing API key"
            except ValueError as e:
                assert "API key" in str(e), f"Wrong error for {provider}: {e}"
    
    def test_router_invalid_provider(self):
        """Test router with invalid provider"""
        config = Config()
        router = QueryRouter(config)
        
        try:
            router._get_client("invalid_provider")
            assert False, "Should have failed for invalid provider"
        except ValueError as e:
            assert "Unknown provider" in str(e)


if __name__ == "__main__":
    # Run tests manually
    test_providers = TestProviders()
    test_router = TestRouter()
    
    all_tests = [
        # Provider tests
        test_providers.test_base_class_prompt_building,
        test_providers.test_base_class_response_cleaning,
        test_providers.test_provider_config_merging,
        test_providers.test_generate_sparql_method,
        test_providers.test_provider_imports_without_dependencies,
        # Router tests
        test_router.test_router_initialization,
        test_router.test_router_lazy_loading,
        test_router.test_router_invalid_provider,
    ]
    
    print("Running provider and router tests...")
    
    for i, test in enumerate(all_tests, 1):
        try:
            test()
            print(f"✓ Test {i}: {test.__name__}")
        except Exception as e:
            print(f"✗ Test {i}: {test.__name__} - {e}")
    
    print("Provider and router tests completed!")
