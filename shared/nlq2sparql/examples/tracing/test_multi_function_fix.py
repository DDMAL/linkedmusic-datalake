#!/usr/bin/env python3
"""
Test script to verify multi-function call fix.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from integrations.gemini_integration import GeminiWikidataIntegration
from tracing import get_tracer, export_trace_log

async def test_multi_function_calls():
    """Test that multiple function calls are executed properly."""
    print("🧪 Testing Multi-Function Call Fix")
    print("=" * 50)
    
    # Initialize tracing
    tracer = get_tracer("multi_function_test")
    
    try:
        # Initialize the integration
        integration = GeminiWikidataIntegration()
        
        # Test query that should trigger 2 function calls
        query = "Find all madrigals written in Florence. First look up madrigal and Florence in Wikidata, then write a comprehensive SPARQL query that finds musical works of type madrigal that were composed in or associated with Florence, Italy. Include titles and composers."
        
        print(f"🔍 Query: {query[:100]}...")
        print(f"📊 Expected function calls: 2 (madrigal + Florence)")
        print()
        
                # Execute the query with tracing
        with tracer.trace_operation("multi_function_test"):
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
            print(f"📝 Final response: {response['text'][:200]}...")
            
            # Save detailed trace
            trace_file = export_trace_log("../../../logs/multi_function_test_trace.json")
            print(f"💾 Detailed trace saved to: {trace_file}")
            
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
            print(f"📝 Final response: {response['text'][:200]}...")
            
            # Save detailed trace
            trace_data = tracer.export_trace()
            trace_file = Path("../../../logs/multi_function_test_trace.json")
            trace_file.write_text(json.dumps(trace_data, indent=2))
            print(f"💾 Detailed trace saved to: {trace_file}")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

async def main():
    await test_multi_function_calls()

if __name__ == "__main__":
    asyncio.run(main())
