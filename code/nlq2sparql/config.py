"""
Configuration management for NLQ to SPARQL generator
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
import json


class ConfigError(Exception):
    """Custom exception for configuration-related errors"""
    pass


class Config:
    """Configuration manager for the NLQ to SPARQL generator"""
    
    def __init__(self, config_file: Optional[Path] = None):
        self.config_data = {}
        self.prefixes_data = {}
        self.logger = logging.getLogger(__name__)
        
        try:
            self._load_env_file()
            self._load_prefixes()
            
            # Load default config file
            default_config = Path(__file__).parent / "config.json"
            if default_config.exists():
                self._load_config_file(default_config)
            
            # Override with custom config file if provided
            if config_file and config_file.exists():
                self._load_config_file(config_file)
                
        except Exception as e:
            raise ConfigError(f"Failed to initialize configuration: {e}")
    
    def _load_env_file(self) -> None:
        """Load environment variables from .env file"""
        # Look for .env file in the project root
        env_file = Path(__file__).parent.parent.parent / ".env"
        
        if not env_file.exists():
            self.logger.info("No .env file found, using system environment variables only")
            return
            
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        try:
                            key, value = line.split('=', 1)
                            os.environ[key.strip()] = value.strip()
                        except ValueError:
                            self.logger.warning(f"Malformed line in .env file at line {line_num}: {line}")
        except Exception as e:
            raise ConfigError(f"Failed to load .env file: {e}")
    
    def _load_config_file(self, config_file: Path) -> None:
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                self.config_data = json.load(f)
            self.logger.info(f"Loaded configuration from {config_file}")
        except json.JSONDecodeError as e:
            raise ConfigError(f"Invalid JSON in config file {config_file}: {e}")
        except Exception as e:
            raise ConfigError(f"Failed to load config file {config_file}: {e}")
    
    def _load_prefixes(self) -> None:
        """Load prefixes from prefixes.json file"""
        prefixes_file = Path(__file__).parent / "prefixes.json"
        
        if not prefixes_file.exists():
            self.logger.info("No prefixes.json file found")
            return
            
        try:
            with open(prefixes_file, 'r', encoding='utf-8') as f:
                self.prefixes_data = json.load(f)
            self.logger.info(f"Loaded prefixes from {prefixes_file}")
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in prefixes file {prefixes_file}: {e}")
        except Exception as e:
            self.logger.error(f"Failed to load prefixes file {prefixes_file}: {e}")
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for specified provider"""
        # Get key mapping from config, with fallback to hardcoded mapping
        key_mappings = self.config_data.get("api_key_mappings", {
            "gemini": "gemini_api_key",
            "chatgpt": "openai_api_key", 
            "claude": "anthropic_api_key"
        })
        
        env_key = key_mappings.get(provider)
        if not env_key:
            self.logger.warning(f"No API key mapping found for provider: {provider}")
            return None
            
        # Check config file first, then environment
        api_key = self.config_data.get(env_key) or os.getenv(env_key)
        
        if not api_key:
            self.logger.warning(f"No API key found for provider {provider} (looking for {env_key})")
            
        return api_key
    
    def get_provider_config(self, provider: str) -> Dict[str, Any]:
        """Get provider-specific configuration"""
        config = self.config_data.get("providers", {}).get(provider, {})
        if not config:
            self.logger.warning(f"No configuration found for provider: {provider}")
        return config
    
    def get_prefixes(self, database: str) -> Dict[str, str]:
        """Get prefixes for specified database"""
        if not database:
            self.logger.warning("No database specified for prefix lookup")
            return {}
            
        # Check config.json first, then prefixes.json
        config_prefixes = self.config_data.get("prefixes", {}).get(database.lower(), {})
        if config_prefixes:
            return config_prefixes
        
        # Fallback to prefixes.json
        # Always include common prefixes as they're commonly used
        prefixes = self.prefixes_data.get("common", {}).copy()
        
        # Add database-specific prefixes
        db_prefixes = self.prefixes_data.get(database.lower(), {})
        prefixes.update(db_prefixes)
        
        if not prefixes:
            self.logger.warning(f"No prefixes found for database: {database}")
        
        return prefixes
    
    def get_prefix_declarations(self, database: str) -> str:
        """Get SPARQL prefix declarations for specified database"""
        prefixes = self.get_prefixes(database)
        declarations = []
        
        for prefix, uri in prefixes.items():
            if not uri:
                self.logger.warning(f"Empty URI for prefix {prefix} in database {database}")
                continue
            declarations.append(f"PREFIX {prefix}: <{uri}>")
        
        return "\n".join(declarations)
    
    def get_available_databases(self) -> List[str]:
        """Get list of available databases"""
        databases = list(self.config_data.get("databases", {}).keys())
        if not databases:
            self.logger.warning("No databases configured")
        return databases
    
    def get_default_query(self, database: str) -> str:
        """Get default test query for specified database"""
        if not database:
            return "Find all items"
            
        databases = self.config_data.get("databases", {})
        db_config = databases.get(database, {})
        
        default_query = db_config.get("default_query", "Find all items")
        if default_query == "Find all items":
            self.logger.warning(f"Using fallback default query for database: {database}")
            
        return default_query
    
    def get_provider_registry(self) -> Dict[str, str]:
        """Get provider registry mapping provider names to module paths"""
        registry = self.config_data.get("provider_registry", {})
        if not registry:
            self.logger.error("No provider registry found in configuration")
        return registry
    
    def get_supported_providers(self) -> List[str]:
        """Get list of supported provider names"""
        providers = list(self.get_provider_registry().keys())
        if not providers:
            self.logger.error("No supported providers found")
        return providers
    
    def validate_configuration(self) -> bool:
        """Validate that required configuration is present"""
        errors = []
        
        # Check for required sections
        required_sections = ["databases", "providers", "provider_registry"]
        for section in required_sections:
            if section not in self.config_data:
                errors.append(f"Missing required section: {section}")
        
        # Check that provider registry matches providers
        registry_providers = set(self.get_provider_registry().keys())
        config_providers = set(self.config_data.get("providers", {}).keys())
        
        if registry_providers != config_providers:
            missing_in_config = registry_providers - config_providers
            missing_in_registry = config_providers - registry_providers
            
            if missing_in_config:
                errors.append(f"Providers in registry but not in config: {missing_in_config}")
            if missing_in_registry:
                errors.append(f"Providers in config but not in registry: {missing_in_registry}")
        
        if errors:
            for error in errors:
                self.logger.error(f"Configuration validation error: {error}")
            return False
            
        self.logger.info("Configuration validation passed")
        return True
