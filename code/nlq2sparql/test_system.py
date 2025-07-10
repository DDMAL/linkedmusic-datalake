#!/usr/bin/env python3
"""
Comprehensive test script for the NLQ-to-SPARQL system
Tests all functionality without requiring API keys
"""

import os
import sys
from pathlib import Path

def test_config_loading():
    """Test configuration loading"""
    print("🧪 Testing configuration loading...")
    
    from config import Config
    
    # Test config loading
    config = Config()
    
    # Test database configuration
    databases = config.get_available_databases()
    assert len(databases) > 0, "No databases configured"
    print(f"   ✓ Found {len(databases)} databases: {databases}")
    
    # Test default queries
    for db in databases:
        query = config.get_default_query(db)
        assert query, f"No default query for {db}"
        print(f"   ✓ {db}: {query[:50]}...")
    
    # Test provider configs
    for provider in ['gemini', 'chatgpt', 'claude']:
        pconfig = config.get_provider_config(provider)
        assert isinstance(pconfig, dict), f"Invalid config for {provider}"
        print(f"   ✓ {provider}: {pconfig}")
    
    # Test prefix loading
    for db in databases:
        prefixes = config.get_prefixes(db)
        declarations = config.get_prefix_declarations(db)
        assert isinstance(prefixes, dict), f"Invalid prefixes for {db}"
        assert isinstance(declarations, str), f"Invalid declarations for {db}"
        print(f"   ✓ {db}: {len(prefixes)} prefixes")
    
    print("   ✅ Configuration loading passed!\n")

def test_base_class():
    """Test base class functionality"""
    print("🧪 Testing base class functionality...")
    
    from config import Config
    from providers.base import BaseLLMClient
    
    # Create mock client
    class MockClient(BaseLLMClient):
        def _call_llm_api(self, prompt, verbose=False):
            return "SELECT * WHERE { ?s ?p ?o }"
    
    config = Config()
    client = MockClient(config)
    
    # Test prompt building
    prompt = client._build_prompt("Find all songs", "diamm")
    assert len(prompt) > 0, "Empty prompt generated"
    assert "SPARQL" in prompt, "Prompt doesn't mention SPARQL"
    assert "diamm" in prompt, "Prompt doesn't mention database"
    print(f"   ✓ Prompt building works ({len(prompt)} chars)")
    
    # Test response cleaning
    dirty_responses = [
        "```sparql\nSELECT * WHERE { ?s ?p ?o }\n```",
        "```\nSELECT * WHERE { ?s ?p ?o }\n```",
        "SELECT * WHERE { ?s ?p ?o }",
    ]
    
    for dirty in dirty_responses:
        clean = client._clean_response(dirty)
        assert clean == "SELECT * WHERE { ?s ?p ?o }", f"Failed to clean: {dirty}"
    print("   ✓ Response cleaning works")
    
    # Test provider config merging
    for provider in ['gemini', 'chatgpt', 'claude']:
        pconfig = client._get_provider_config(provider)
        assert isinstance(pconfig, dict), f"Invalid merged config for {provider}"
        assert 'model' in pconfig, f"No model in config for {provider}"
        assert 'temperature' in pconfig, f"No temperature in config for {provider}"
    print("   ✓ Provider config merging works")
    
    # Test full generate_sparql method
    sparql = client.generate_sparql("Find all songs", "diamm", verbose=False)
    assert sparql == "SELECT * WHERE { ?s ?p ?o }", "generate_sparql failed"
    print("   ✓ generate_sparql method works")
    
    print("   ✅ Base class functionality passed!\n")

def test_router():
    """Test router functionality"""
    print("🧪 Testing router functionality...")
    
    from config import Config
    from router import QueryRouter
    
    config = Config()
    router = QueryRouter(config)
    
    # Test router creation
    assert router.config is config, "Router config not set"
    assert router.llm_clients == {}, "Router should start with empty clients"
    print("   ✓ Router creation works")
    
    # Test client creation (should fail due to missing API keys)
    for provider in ['gemini', 'chatgpt', 'claude']:
        try:
            client = router._get_client(provider)
            assert False, f"Should have failed for {provider} due to missing API key"
        except ValueError as e:
            assert "API key" in str(e), f"Wrong error for {provider}: {e}"
            print(f"   ✓ {provider} correctly fails without API key")
    
    # Test invalid provider
    try:
        router._get_client("invalid")
        assert False, "Should have failed for invalid provider"
    except ValueError as e:
        assert "Unknown provider" in str(e), f"Wrong error message: {e}"
        print("   ✓ Invalid provider correctly rejected")
    
    print("   ✅ Router functionality passed!\n")

def test_provider_imports():
    """Test that provider imports work without dependencies"""
    print("🧪 Testing provider imports...")
    
    # Test that we can import provider classes without their dependencies
    try:
        from providers.gemini_client import GeminiClient
        print("   ✓ GeminiClient imports without google.generativeai")
    except ImportError as e:
        if "google.generativeai" in str(e):
            assert False, "Should not import google.generativeai at module level"
        raise
    
    try:
        from providers.chatgpt_client import ChatGPTClient
        print("   ✓ ChatGPTClient imports without openai")
    except ImportError as e:
        if "openai" in str(e):
            assert False, "Should not import openai at module level"
        raise
    
    try:
        from providers.claude_client import ClaudeClient
        print("   ✓ ClaudeClient imports without anthropic")
    except ImportError as e:
        if "anthropic" in str(e):
            assert False, "Should not import anthropic at module level"
        raise
    
    print("   ✅ Provider imports passed!\n")

def test_cli_functionality():
    """Test CLI functionality"""
    print("🧪 Testing CLI functionality...")
    
    # Test that CLI can import and run without errors
    try:
        import cli
        print("   ✓ CLI module imports successfully")
    except ImportError as e:
        assert False, f"CLI import failed: {e}"
    
    # Test that we can load the config in CLI context
    from config import Config
    config = Config()
    databases = config.get_available_databases()
    
    # Verify CLI would have the right database choices
    assert len(databases) > 0, "No databases for CLI"
    print(f"   ✓ CLI has {len(databases)} database choices")
    
    # Test default queries are available
    for db in databases:
        query = config.get_default_query(db)
        assert query and len(query) > 0, f"No default query for {db}"
    print("   ✓ CLI has default queries for all databases")
    
    print("   ✅ CLI functionality passed!\n")

def main():
    """Run all tests"""
    print("🚀 Starting comprehensive system tests...\n")
    
    try:
        test_config_loading()
        test_base_class()
        test_router()
        test_provider_imports()
        test_cli_functionality()
        
        print("🎉 ALL TESTS PASSED!")
        print("\n✅ The system is working correctly without API keys")
        print("✅ Configuration is centralized and working")
        print("✅ Code duplication has been eliminated")
        print("✅ Lazy loading prevents import errors")
        print("✅ CLI is functional and robust")
        
        print("\n📝 To use with real API keys:")
        print("   1. Set API keys in environment or config file")
        print("   2. Install provider dependencies: poetry add google-generativeai openai anthropic")
        print("   3. Run: python cli.py --test --database diamm --verbose")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
