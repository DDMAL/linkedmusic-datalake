#!/usr/bin/env python3
"""
Configuration tests for nlq2sparql
"""

import pytest
import sys
from pathlib import Path

# Handle imports - add parent directory to path for direct execution
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from config import Config
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running from the nlq2sparql directory")
    sys.exit(1)


class TestConfig:
    """Test configuration loading and validation"""
    
    def test_config_initialization(self):
        """Test that Config can be initialized"""
        config = Config()
        assert config is not None
        assert hasattr(config, 'config_data')
        assert hasattr(config, 'prefixes_data')
    
    def test_available_databases(self):
        """Test that available databases are loaded"""
        config = Config()
        databases = config.get_available_databases()
        
        assert isinstance(databases, list)
        assert len(databases) > 0
        assert all(isinstance(db, str) for db in databases)
    
    def test_default_queries(self):
        """Test that default queries exist for all databases"""
        config = Config()
        databases = config.get_available_databases()
        
        for db in databases:
            query = config.get_default_query(db)
            assert query is not None
            assert len(query) > 0
            assert isinstance(query, str)
    
    def test_provider_configs(self):
        """Test provider configurations"""
        config = Config()
        providers = ['gemini', 'chatgpt', 'claude']
        
        for provider in providers:
            pconfig = config.get_provider_config(provider)
            assert isinstance(pconfig, dict)
            # Should have at least model and temperature
            assert 'model' in pconfig
            assert 'temperature' in pconfig
    
    def test_prefixes(self):
        """Test prefix loading for databases"""
        config = Config()
        databases = config.get_available_databases()
        
        for db in databases:
            prefixes = config.get_prefixes(db)
            declarations = config.get_prefix_declarations(db)
            
            assert isinstance(prefixes, dict)
            assert isinstance(declarations, str)
            
            # Should have some common prefixes
            assert len(prefixes) > 0
    
    def test_api_key_handling(self):
        """Test API key retrieval"""
        config = Config()
        providers = ['gemini', 'chatgpt', 'claude']
        
        for provider in providers:
            # Should not raise an error, even if key is None
            api_key = config.get_api_key(provider)
            assert api_key is None or isinstance(api_key, str)


if __name__ == "__main__":
    # Run tests manually if pytest not available
    test_config = TestConfig()
    
    tests = [
        test_config.test_config_initialization,
        test_config.test_available_databases,
        test_config.test_default_queries,
        test_config.test_provider_configs,
        test_config.test_prefixes,
        test_config.test_api_key_handling,
    ]
    
    print("Running configuration tests...")
    
    for i, test in enumerate(tests, 1):
        try:
            test()
            print(f"✓ Test {i}: {test.__name__}")
        except Exception as e:
            print(f"✗ Test {i}: {test.__name__} - {e}")
    
    print("Configuration tests completed!")
