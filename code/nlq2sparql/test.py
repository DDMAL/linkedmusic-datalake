#!/usr/bin/env python3
"""
Simple test script for the NLQ to SPARQL generator
"""

import sys
from pathlib import Path

# Add the parent directories to Python path so we can import the module
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.nlq2sparql.config import Config
from code.nlq2sparql.router import QueryRouter


def test_config():
    """Test configuration loading"""
    print("Testing configuration...")
    
    config = Config()
    
    # Test API key loading
    gemini_key = config.get_api_key("gemini")
    print(f"Gemini API key loaded: {'Yes' if gemini_key and gemini_key != 'PLACEHOLDER' else 'No'}")
    
    # Test provider config
    gemini_config = config.get_provider_config("gemini")
    print(f"Gemini config: {gemini_config}")
    
    # Test prefix loading
    prefixes = config.get_prefixes("musicbrainz")
    print(f"MusicBrainz prefixes: {list(prefixes.keys())}")
    
    return config


def test_router(config):
    """Test router initialization"""
    print("\nTesting router...")
    
    try:
        router = QueryRouter(config)
        print("Router initialized successfully")
        
        # Test with a simple query if Gemini key is available
        gemini_key = config.get_api_key("gemini")
        if gemini_key and gemini_key != "PLACEHOLDER":
            print("\nTesting query generation...")
            query = "Find all compositions by Bach"
            
            try:
                sparql = router.process_query(
                    nlq=query,
                    provider="gemini",
                    database="musicbrainz",
                    verbose=True
                )
                print(f"\nGenerated SPARQL:\n{sparql}")
                
            except Exception as e:
                print(f"Query generation failed: {e}")
        else:
            print("Skipping query test - no valid Gemini API key")
            
    except Exception as e:
        print(f"Router initialization failed: {e}")


def main():
    """Run tests"""
    print("NLQ to SPARQL Generator - Test Script")
    print("=" * 50)
    
    try:
        config = test_config()
        test_router(config)
        
    except Exception as e:
        print(f"Test failed: {e}")
        sys.exit(1)
    
    print("\nTest completed!")


if __name__ == "__main__":
    main()
