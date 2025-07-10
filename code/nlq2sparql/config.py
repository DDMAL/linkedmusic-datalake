"""
Configuration management for NLQ to SPARQL generator
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
import json


class Config:
    """Configuration manager for the NLQ to SPARQL generator"""
    
    def __init__(self, config_file: Optional[Path] = None):
        self.config_data = {}
        self.prefixes_data = {}
        self._load_env_file()
        self._load_prefixes()
        
        # Load default config file
        default_config = Path(__file__).parent / "config.json"
        if default_config.exists():
            self._load_config_file(default_config)
        
        # Override with custom config file if provided
        if config_file and config_file.exists():
            self._load_config_file(config_file)
    
    def _load_env_file(self):
        """Load environment variables from .env file"""
        # Look for .env file in the project root
        env_file = Path(__file__).parent.parent.parent / ".env"
        
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key] = value
    
    def _load_config_file(self, config_file: Path):
        """Load configuration from JSON file"""
        with open(config_file, 'r') as f:
            self.config_data = json.load(f)
    
    def _load_prefixes(self):
        """Load prefixes from prefixes.json file"""
        prefixes_file = Path(__file__).parent / "prefixes.json"
        
        if prefixes_file.exists():
            with open(prefixes_file, 'r') as f:
                self.prefixes_data = json.load(f)
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for specified provider"""
        key_map = {
            "gemini": "gemini_api_key",
            "chatgpt": "openai_api_key", 
            "claude": "anthropic_api_key"
        }
        
        env_key = key_map.get(provider)
        if not env_key:
            return None
            
        # Check config file first, then environment
        return self.config_data.get(env_key) or os.getenv(env_key)
    
    def get_provider_config(self, provider: str) -> Dict[str, Any]:
        """Get provider-specific configuration"""
        return self.config_data.get(provider, {})
    
    def get_prefixes(self, database: str) -> Dict[str, str]:
        """Get prefixes for specified database"""
        # Always include common prefixes as they're commonly used
        prefixes = self.prefixes_data.get("common", {}).copy()
        
        # Add database-specific prefixes
        db_prefixes = self.prefixes_data.get(database.lower(), {})
        prefixes.update(db_prefixes)
        
        return prefixes
    
    def get_prefix_declarations(self, database: str) -> str:
        """Get SPARQL prefix declarations for specified database"""
        prefixes = self.get_prefixes(database)
        declarations = []
        
        for prefix, uri in prefixes.items():
            declarations.append(f"PREFIX {prefix}: <{uri}>")
        
        return "\n".join(declarations)
    
    def get_available_databases(self) -> list:
        """Get list of available databases"""
        return self.config_data.get("databases", {}).get("available", [])
    
    def get_default_query(self, database: str) -> str:
        """Get default test query for specified database"""
        config_queries = self.config_data.get("databases", {}).get("default_queries", {})
        
        return config_queries.get(database, "Find all items")
