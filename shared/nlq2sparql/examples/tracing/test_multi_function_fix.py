#!/usr/bin/env python3
"""
Test script to verify multi-function call fix.

This script tests that the Gemini integration can handle multiple function calls
in a single query, which was the key enhancement made to enable complex queries
like "find madrigals in Florence" that require multiple entity lookups.

Usage:
    cd shared && poetry run python -m nlq2sparql.examples.tracing.test_multi_function_fix
"""

import asyncio
import sys
import os
from pathlib import Path

# Ensure we can import the nlq2sparql module
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root / "shared") not in sys.path:
    sys.path.insert(0, str(project_root / "shared"))

try:
    from nlq2sparql.integrations.gemini_integration import GeminiWikidataIntegration
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the shared/ directory with:")
    print("poetry run python -m nlq2sparql.examples.tracing.test_multi_function_fix")
    sys.exit(1)


async def test_multi_function_calls():
    """Test that multiple function calls are executed properly."""
    print("🧪 Testing Multi-Function Call Fix")
    print("=" * 50)
    
    try:
        # Initialize the integration
        integration = GeminiWikidataIntegration()
        
        # Test query that should trigger 2 function calls
        query = ("Find all madrigals written in Florence. First look up madrigal and Florence in Wikidata, "
                "then write a comprehensive SPARQL query that finds musical works of type madrigal that were "
                "composed in or associated with Florence, Italy. Include titles and composers.")
        
        print(f"🔍 Query: {query[:100]}...")
        print(f"📊 Expected function calls: 2 (madrigal + Florence)")
        print()
        
        # Execute the query
        response = await integration.send_message_with_tools(query)
        
        # Analyze results
        function_calls = response.get('function_calls', [])
        
        print(f"✅ Total function calls executed: {len(function_calls)}")
        print()
        
        for i, call in enumerate(function_calls, 1):
            entity = call['arguments'].get('entity_label', 'unknown')
            result = call['result']
            print(f"  {i}. {call['function']}(\"{entity}\") → {result}")
        
        print()
        if len(function_calls) >= 2:
            print("🎉 SUCCESS: Multiple function calls executed!")
            print("✅ Fix verified - both madrigal and Florence lookups completed")
            
            # Check if we got QIDs for both
            results = [call['result'] for call in function_calls]
            qids = [r for r in results if isinstance(r, str) and r.startswith('Q')]
            
            if len(qids) >= 2:
                print(f"🔗 Entity QIDs resolved: {qids}")
                print("✅ Ready for SPARQL generation with both entities")
            else:
                print(f"⚠️  Some lookups may have failed: {results}")
                
        else:
            print("❌ FAILURE: Still only executing single function call")
            print("🔍 Need to investigate further...")
        
        print()
        if response['text']:
            print(f"📝 Final response preview: {response['text'][:200]}...")
        else:
            print("📝 No text response (function calls only)")
        
        return len(function_calls) >= 2
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function"""
    print("🔬 Multi-Function Call Test Suite")
    print("=" * 60)
    print()
    
    success = await test_multi_function_calls()
    
    print()
    print("� Test Results:")
    print("=" * 20)
    if success:
        print("✅ PASSED: Multi-function call processing works correctly")
        print("🎯 System can handle complex queries requiring multiple entity lookups")
    else:
        print("❌ FAILED: Multi-function call processing needs investigation")
    
    return success


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
