#!/usr/bin/env python3
"""
Simple demo script for the NLQ to SPARQL generator
Run this from the code directory with: poetry run python nlq2sparql/demo.py
"""

from config import Config
from router import QueryRouter


def main():
    """Run a simple demo"""
    print("NLQ to SPARQL Generator - Demo")
    print("=" * 40)
    
    try:
        # Initialize configuration
        config = Config()
        
        # Check if Gemini API key is available
        gemini_key = config.get_api_key("gemini")
        if not gemini_key or gemini_key == "PLACEHOLDER":
            print("⚠️  No valid Gemini API key found.")
            print("Please set gemini_api_key in the .env file to test the system.")
            return
        
        print("✅ Configuration loaded successfully")
        
        # Initialize router
        router = QueryRouter(config)
        print("✅ Router initialized successfully")
        
        # Test query
        test_query = "Find all manuscripts from Paris"
        print(f"\n🔍 Testing query: '{test_query}'")
        print("📡 Sending to Gemini...")
        
        sparql_query = router.process_query(
            nlq=test_query,
            provider="gemini",
            database="diamm",
            verbose=True
        )
        
        print("\n🎯 Generated SPARQL:")
        print("-" * 50)
        print(sparql_query)
        print("-" * 50)
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
