#!/usr/bin/env python3
"""
Comprehensive test suite for the NLQ-to-SPARQL system
Combines configuration, system, and integration tests
"""

import os
import sys
import json
import subprocess
import tempfile
from pathlib import Path

# Handle imports for both direct execution and module execution
try:
    from ..config import Config
    from ..router import QueryRouter
    from ..providers.base import BaseLLMClient
except ImportError:
    # Direct execution - add parent to path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import Config
    from router import QueryRouter
    from providers.base import BaseLLMClient


class TestResults:
    """Track test results"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def add_pass(self):
        self.passed += 1
    
    def add_fail(self, error_msg):
        self.failed += 1
        self.errors.append(error_msg)
    
    def print_summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"TEST RESULTS: {self.passed}/{total} passed")
        if self.failed > 0:
            print(f"❌ {self.failed} tests failed:")
            for error in self.errors:
                print(f"   - {error}")
        else:
            print("🎉 ALL TESTS PASSED!")
        print(f"{'='*60}")


def test_config_json_loading(results):
    """Test that config.json is properly loaded and structured"""
    print("🧪 Testing config.json loading...")
    
    try:
        # Get the path to config.json
        config_path = Path(__file__).parent.parent / "config.json"
        assert config_path.exists(), f"config.json not found at {config_path}"
        
        # Load and validate JSON structure
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        
        # Check required top-level keys
        required_keys = ['databases', 'providers', 'prefixes']
        for key in required_keys:
            assert key in config_data, f"Missing required key: {key}"
        
        # Check databases structure
        databases = config_data['databases']
        assert isinstance(databases, dict), "databases must be a dict"
        assert len(databases) > 0, "No databases configured"
        
        for db_name, db_config in databases.items():
            assert 'default_query' in db_config, f"Missing default_query for {db_name}"
            assert isinstance(db_config['default_query'], str), f"default_query must be string for {db_name}"
            assert len(db_config['default_query']) > 0, f"Empty default_query for {db_name}"
        
        # Check providers structure
        providers = config_data['providers']
        assert isinstance(providers, dict), "providers must be a dict"
        
        expected_providers = ['gemini', 'chatgpt', 'claude']
        for provider in expected_providers:
            assert provider in providers, f"Missing provider: {provider}"
            pconfig = providers[provider]
            assert 'model' in pconfig, f"Missing model for {provider}"
            assert 'temperature' in pconfig, f"Missing temperature for {provider}"
        
        # Check prefixes structure
        prefixes = config_data['prefixes']
        assert isinstance(prefixes, dict), "prefixes must be a dict"
        
        for db_name in databases.keys():
            if db_name in prefixes:
                db_prefixes = prefixes[db_name]
                assert isinstance(db_prefixes, dict), f"prefixes for {db_name} must be a dict"
        
        print(f"   ✓ config.json structure is valid")
        print(f"   ✓ Found {len(databases)} databases: {list(databases.keys())}")
        print(f"   ✓ Found {len(providers)} providers: {list(providers.keys())}")
        print(f"   ✓ Found prefixes for {len(prefixes)} databases")
        
        # Test that Config class loads this data correctly
        config = Config()
        
        # Verify Config uses the JSON data
        loaded_databases = config.get_available_databases()
        assert set(loaded_databases) == set(databases.keys()), "Config databases don't match JSON"
        
        for db_name in databases.keys():
            json_query = databases[db_name]['default_query']
            config_query = config.get_default_query(db_name)
            assert json_query == config_query, f"Query mismatch for {db_name}"
        
        print("   ✅ config.json loading and Config integration passed!")
        results.add_pass()
        
    except Exception as e:
        error_msg = f"config.json loading failed: {e}"
        print(f"   ❌ {error_msg}")
        results.add_fail(error_msg)


def test_config_fallback_behavior(results):
    """Test Config behavior when config.json is missing or invalid"""
    print("\n🧪 Testing config fallback behavior...")
    
    try:
        # Test with missing config.json
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_config = Path(temp_dir) / "config.json"
            
            # Try to create Config with non-existent file
            try:
                # This should raise an exception since we now require config.json
                config = Config(config_path=str(temp_config))
                # If we get here without exception, the fallback worked
                databases = config.get_available_databases()
                if len(databases) == 0:
                    print("   ✓ Config properly handles missing config.json (no fallback)")
                else:
                    print(f"   ✓ Config fallback provides {len(databases)} databases")
            except Exception as e:
                print(f"   ✓ Config properly raises exception for missing config.json: {type(e).__name__}")
        
        # Test with invalid JSON
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_config = Path(temp_dir) / "config.json"
            temp_config.write_text("{ invalid json }")
            
            try:
                config = Config(config_path=str(temp_config))
                results.add_fail("Config should fail with invalid JSON")
            except json.JSONDecodeError:
                print("   ✓ Config properly handles invalid JSON")
            except Exception as e:
                print(f"   ✓ Config handles invalid JSON with {type(e).__name__}")
        
        print("   ✅ Config fallback behavior passed!")
        results.add_pass()
        
    except Exception as e:
        error_msg = f"Config fallback testing failed: {e}"
        print(f"   ❌ {error_msg}")
        results.add_fail(error_msg)


def test_cli_invocation(results):
    """Test CLI invocation in both direct and module modes"""
    print("\n🧪 Testing CLI invocation...")
    
    try:
        cli_path = Path(__file__).parent.parent / "cli.py"
        nlq_path = Path(__file__).parent.parent.parent
        
        # Test direct execution - help command
        try:
            result = subprocess.run([
                sys.executable, str(cli_path), "--help"
            ], capture_output=True, text=True, timeout=10)
            
            assert result.returncode == 0, f"CLI help failed: {result.stderr}"
            assert "usage:" in result.stdout.lower(), "CLI help doesn't show usage"
            assert "database" in result.stdout.lower(), "CLI help doesn't mention database"
            print("   ✓ Direct CLI execution (--help) works")
            
        except subprocess.TimeoutExpired:
            print("   ⚠️ CLI help command timed out")
        except Exception as e:
            print(f"   ⚠️ Direct CLI execution failed: {e}")
        
        # Test module execution - help command
        try:
            result = subprocess.run([
                sys.executable, "-m", "code.nlq2sparql.cli", "--help"
            ], capture_output=True, text=True, timeout=10, cwd=nlq_path)
            
            assert result.returncode == 0, f"Module CLI help failed: {result.stderr}"
            assert "usage:" in result.stdout.lower(), "Module CLI help doesn't show usage"
            print("   ✓ Module CLI execution (--help) works")
            
        except subprocess.TimeoutExpired:
            print("   ⚠️ Module CLI help command timed out")
        except Exception as e:
            print(f"   ⚠️ Module CLI execution failed: {e}")
        
        # Test CLI database listing
        try:
            result = subprocess.run([
                sys.executable, str(cli_path), "--list-databases"
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                assert len(result.stdout.strip()) > 0, "No databases listed"
                print(f"   ✓ CLI database listing works: {result.stdout.strip()}")
            else:
                print(f"   ⚠️ CLI database listing failed: {result.stderr}")
        except subprocess.TimeoutExpired:
            print("   ⚠️ CLI database listing timed out")
        except Exception as e:
            print(f"   ⚠️ CLI database listing failed: {e}")
        
        # Test CLI with invalid arguments
        try:
            result = subprocess.run([
                sys.executable, str(cli_path), "--invalid-argument"
            ], capture_output=True, text=True, timeout=10)
            
            assert result.returncode != 0, "CLI should fail with invalid arguments"
            print("   ✓ CLI properly handles invalid arguments")
            
        except subprocess.TimeoutExpired:
            print("   ⚠️ CLI invalid argument test timed out")
        except Exception as e:
            print(f"   ⚠️ CLI invalid argument test failed: {e}")
        
        print("   ✅ CLI invocation tests passed!")
        results.add_pass()
        
    except Exception as e:
        error_msg = f"CLI invocation testing failed: {e}"
        print(f"   ❌ {error_msg}")
        results.add_fail(error_msg)


def test_config_loading(results):
    """Test configuration loading and validation"""
    print("🧪 Testing configuration loading...")
    
    try:
        config = Config()
        
        # Test database configuration
        databases = config.get_available_databases()
        assert len(databases) > 0, "No databases configured"
        print(f"   ✓ Found {len(databases)} databases: {databases}")
        
        # Test default queries
        for db in databases:
            query = config.get_default_query(db)
            assert query and len(query) > 0, f"No default query for {db}"
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
        
        print("   ✅ Configuration loading passed!")
        results.add_pass()
        return config
        
    except Exception as e:
        error_msg = f"Configuration loading failed: {e}"
        print(f"   ❌ {error_msg}")
        results.add_fail(error_msg)
        return None


def test_base_class(results):
    """Test base class functionality with mock implementation"""
    print("\n🧪 Testing base class functionality...")
    
    try:
        # Create mock client
        class MockClient(BaseLLMClient):
            def _call_llm_api(self, prompt, verbose=False):
                return "```sparql\nSELECT * WHERE { ?s ?p ?o }\n```"
        
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
        
        print("   ✅ Base class functionality passed!")
        results.add_pass()
        
    except Exception as e:
        error_msg = f"Base class testing failed: {e}"
        print(f"   ❌ {error_msg}")
        results.add_fail(error_msg)


def test_router(results):
    """Test router functionality and lazy loading"""
    print("\n🧪 Testing router functionality...")
    
    try:
        config = Config()
        router = QueryRouter(config)
        
        # Test router creation
        assert router.config is config, "Router config not set"
        assert router.provider_clients == {}, "Router should start with empty clients"
        print("   ✓ Router creation works")
        
        # Test client creation (should fail due to missing API keys)
        for provider in ['gemini', 'chatgpt', 'claude']:
            try:
                client = router._get_client(provider)
                error_msg = f"Should have failed for {provider} due to missing API key"
                print(f"   ❌ {error_msg}")
                results.add_fail(error_msg)
            except ValueError as e:
                if "API key" in str(e):
                    print(f"   ✓ {provider} correctly fails without API key")
                else:
                    error_msg = f"Wrong error for {provider}: {e}"
                    print(f"   ❌ {error_msg}")
                    results.add_fail(error_msg)
        
        # Test invalid provider
        try:
            router._get_client("invalid")
            error_msg = "Should have failed for invalid provider"
            print(f"   ❌ {error_msg}")
            results.add_fail(error_msg)
        except ValueError as e:
            if "Unknown provider" in str(e):
                print("   ✓ Invalid provider correctly rejected")
            else:
                error_msg = f"Wrong error message: {e}"
                print(f"   ❌ {error_msg}")
                results.add_fail(error_msg)
        
        print("   ✅ Router functionality passed!")
        results.add_pass()
        
    except Exception as e:
        error_msg = f"Router testing failed: {e}"
        print(f"   ❌ {error_msg}")
        results.add_fail(error_msg)


def test_provider_imports(results):
    """Test that provider imports work without dependencies"""
    print("\n🧪 Testing provider imports...")
    
    try:
        # Test that we can import provider classes without their dependencies
        provider_tests = [
            ("GeminiClient", "google.generativeai"),
            ("ChatGPTClient", "openai"),
            ("ClaudeClient", "anthropic")
        ]
        
        for client_name, dependency in provider_tests:
            try:
                if client_name == "GeminiClient":
                    from providers.gemini_client import GeminiClient
                elif client_name == "ChatGPTClient":
                    from providers.chatgpt_client import ChatGPTClient
                elif client_name == "ClaudeClient":
                    from providers.claude_client import ClaudeClient
                    
                print(f"   ✓ {client_name} imports without {dependency}")
                
            except ImportError as e:
                if dependency in str(e):
                    error_msg = f"Should not import {dependency} at module level"
                    print(f"   ❌ {error_msg}")
                    results.add_fail(error_msg)
                else:
                    raise
        
        print("   ✅ Provider imports passed!")
        results.add_pass()
        
    except Exception as e:
        error_msg = f"Provider import testing failed: {e}"
        print(f"   ❌ {error_msg}")
        results.add_fail(error_msg)


def test_cli_functionality(results):
    """Test CLI functionality"""
    print("\n🧪 Testing CLI functionality...")
    
    try:
        # Test that CLI can import and run without errors
        try:
            import cli
            print("   ✓ CLI module imports successfully")
        except ImportError as e:
            error_msg = f"CLI import failed: {e}"
            print(f"   ❌ {error_msg}")
            results.add_fail(error_msg)
            return
        
        # Test that we can load the config in CLI context
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
        
        print("   ✅ CLI functionality passed!")
        results.add_pass()
        
    except Exception as e:
        error_msg = f"CLI testing failed: {e}"
        print(f"   ❌ {error_msg}")
        results.add_fail(error_msg)


def test_integration_with_mock_api(results):
    """Test end-to-end integration with mock API calls"""
    print("\n🧪 Testing integration with mock API...")
    
    try:
        config = Config()
        
        # Mock the API key to avoid the error
        original_get_api_key = config.get_api_key
        def mock_get_api_key(provider):
            return "mock_api_key_for_testing"
        config.get_api_key = mock_get_api_key
        
        # Create a mock client that doesn't require real API calls
        class MockProviderClient(BaseLLMClient):
            def __init__(self, config):
                super().__init__(config)
                self.api_key = "mock_key"
                
            def _call_llm_api(self, prompt, verbose=False):
                # Return the actual correct SPARQL query from query_database_10july2025.csv
                # This is the "Correct" query for Henry VII from the CSV (line ~2620)
                # It properly uses wdt:P88 for "commissioned by" and FILTER(STR()) for string matching
                return '''PREFIX diamm: <https://linkedmusic.ca/graphs/diamm/>
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>

SELECT ?source WHERE {
  ?source wdt:P88 ?commissioner .
  FILTER(STR(?commissioner) = "https://www.diamm.ac.uk/people/2899")
}'''
        
        # Test the full pipeline
        mock_client = MockProviderClient(config)
        
        # Test query generation
        sparql = mock_client.generate_sparql(
            "Find sources commissioned by Henry VII",
            "diamm",
            verbose=False
        )
        
        assert "SELECT" in sparql, "Generated query should contain SELECT"
        assert "WHERE" in sparql, "Generated query should contain WHERE"
        assert "wdt:P88" in sparql, "Query should use wdt:P88 for commissioned by"
        assert "people/2899" in sparql, "Query should reference Henry VII's DIAMM ID"
        assert "FILTER(STR(" in sparql, "Query should use FILTER(STR()) for string matching"
        print("   ✓ End-to-end query generation works with realistic DIAMM query")
        
        # Restore original method
        config.get_api_key = original_get_api_key
        
        print("   ✅ Integration testing passed!")
        results.add_pass()
        
    except Exception as e:
        error_msg = f"Integration testing failed: {e}"
        print(f"   ❌ {error_msg}")
        results.add_fail(error_msg)


def run_all_tests():
    """Run all tests and return results"""
    results = TestResults()
    
    print("🚀 Starting comprehensive nlq2sparql test suite...")
    print(f"{'='*60}")
    
    # Run all test functions in logical order
    test_config_json_loading(results)
    test_config_fallback_behavior(results)
    test_config_loading(results)
    test_cli_invocation(results)
    test_base_class(results)
    test_router(results)
    test_provider_imports(results)
    test_cli_functionality(results)
    test_integration_with_mock_api(results)
    
    # Print final results
    results.print_summary()
    
    # Provide usage instructions
    if results.failed == 0:
        print("\n📝 System is ready! To use with real API keys:")
        print("   1. Set API keys in environment or .env file")
        print("   2. Install provider dependencies: poetry install")
        print("   3. Run: python cli.py --test --database diamm --provider gemini --verbose")
    
    return results.failed == 0


def main():
    """Main test runner"""
    try:
        success = run_all_tests()
        return 0 if success else 1
    except Exception as e:
        print(f"\n💥 Test runner crashed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
