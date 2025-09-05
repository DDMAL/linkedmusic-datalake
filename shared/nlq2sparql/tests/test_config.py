"""
Essential configuration tests

Tests the core configuration loading and validation.
Focuses on the main config functionality users rely on.
"""

import pytest
from pathlib import Path

# Import config from parent directory using relative import
try:
    from ..config import Config, ConfigError
except ImportError:
    # Fallback for when running tests directly
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from config import Config, ConfigError


class TestConfigLoading:
    """Test configuration loading and validation"""
    
    def test_default_config_loads(self):
        """Default configuration loads without errors"""
        config = Config()
        assert config is not None
        assert hasattr(config, 'config_data')
    
    def test_get_available_databases(self):
        """Config provides list of available databases"""
        config = Config()
        databases = config.get_available_databases()
        
        assert isinstance(databases, list)
        assert len(databases) > 0
        
        # Verify we have actual database configurations
        for db_name in databases:
            assert isinstance(db_name, str)
            assert len(db_name) > 0
    
    def test_get_default_query(self):
        """Config provides default queries for databases"""
        config = Config()
        databases = config.get_available_databases()
        
        if databases:
            # Test with first available database
            default_query = config.get_default_query(databases[0])
            assert isinstance(default_query, str)
            assert len(default_query) > 0
    
    def test_invalid_database_fallback(self):
        """Config handles unknown databases gracefully"""
        config = Config()
        
        # Should return fallback query for unknown database
        default_query = config.get_default_query("nonexistent_database")
        assert isinstance(default_query, str)
        assert len(default_query) > 0
    
    def test_provider_registry(self):
        """Config provides provider registry"""
        config = Config()
        
        registry = config.get_provider_registry()
        assert isinstance(registry, dict)
        # Should have some providers configured
        assert len(registry) > 0


class TestConfigValidation:
    """Test configuration validation logic"""
    
    def test_config_has_required_sections(self):
        """Config contains all required sections"""
        config = Config()
        
        # Verify basic structure exists
        assert hasattr(config, 'config_data')
        assert isinstance(config.config_data, dict)
        
        # Should have databases section if any databases are configured
        databases = config.get_available_databases()
        if databases:
            assert 'databases' in config.config_data
            assert isinstance(config.config_data['databases'], dict)
    
    def test_prefixes_functionality(self):
        """Config handles prefixes correctly"""
        config = Config()
        databases = config.get_available_databases()
        
        if databases:
            # Test with first available database
            prefixes = config.get_prefixes(databases[0])
            assert isinstance(prefixes, dict)
            
            # Test prefix declarations
            declarations = config.get_prefix_declarations(databases[0])
            assert isinstance(declarations, str)