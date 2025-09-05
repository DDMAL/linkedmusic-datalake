#!/usr/bin/env python3
"""
Enhanced NLQ2SPARQL Tracing Demo

This script demonstrates the comprehensive tracing capabilities of the NLQ2SPARQL system,
showing detailed execution flow, function calls, timing, and error handling.

Usage:
    poetry run python -m nlq2sparql.examples.tracing.enhanced_demo
    
Or from the project root:
    cd shared && poetry run python -m nlq2sparql.examples.tracing.enhanced_demo
"""

import sys
import asyncio
import os
from pathlib import Path

# Ensure we can import the nlq2sparql module
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

async def main():
    """Run comprehensive NLQ2SPARQL tests with full tracing"""
    
    from nlq2sparql.tracing import setup_tracing, get_trace_summary, export_trace_log, clear_trace_buffer
    from nlq2sparql.integrations.gemini_integration import GeminiWikidataIntegration
    
    # Setup tracing with DEBUG level to see everything
    print("🔧 Setting up enhanced tracing...")
    tracing_manager = setup_tracing(level="DEBUG", enable_file_logging=True)
    
    # Clear any previous trace data
    clear_trace_buffer()
    
    print("✅ Tracing configured and ready\n")
    
    try:
        # Test 1: Simple entity lookup
        print("=" * 80)
        print("🧪 TEST 1: Simple Entity Lookup")
        print("=" * 80)
        
        integration = GeminiWikidataIntegration()
        
        response = await integration.send_message_with_tools(
            "Find the Wikidata QID for Johann Sebastian Bach"
        )
        
        print(f"📝 Response: {response.get('text', 'No text response')}")
        
        print("\n" + "=" * 80)
        print("🔍 TRACE SUMMARY FOR TEST 1")
        print("=" * 80)
        print(get_trace_summary())
        
        # Clear buffer for next test
        clear_trace_buffer()
        
        # Test 2: Complex SPARQL generation
        print("\n\n" + "=" * 80)
        print("🧪 TEST 2: Complex SPARQL Query Generation")
        print("=" * 80)
        
        response = await integration.send_message_with_tools(
            "Write a SPARQL query to find all compositions by Guillaume Dufay. "
            "First look up Guillaume Dufay in Wikidata, then create a query "
            "that gets all his musical works with their titles."
        )
        
        print(f"📝 Response: {response.get('text', 'No text response')}")
        
        print("\n" + "=" * 80)
        print("🔍 TRACE SUMMARY FOR TEST 2")
        print("=" * 80)
        print(get_trace_summary())
        
        # Export full trace log to logs directory
        print("\n" + "=" * 80)
        print("💾 EXPORTING FULL TRACE LOG")
        print("=" * 80)
        
        # Ensure logs directory exists
        logs_dir = project_root / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        log_file = export_trace_log(str(logs_dir / "nlq2sparql_enhanced_demo.json"))
        print(f"📁 Full trace log exported to: {log_file}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        
        # Still show trace summary even on error
        print("\n" + "=" * 80)
        print("🔍 TRACE SUMMARY (ERROR CASE)")
        print("=" * 80)
        print(get_trace_summary())


if __name__ == "__main__":
    # Check for API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ Error: GEMINI_API_KEY environment variable not set")
        print("Please set your Gemini API key:")
        print("export GEMINI_API_KEY=your_api_key_here")
        sys.exit(1)
    
    print("🚀 Starting Enhanced NLQ2SPARQL Tracing Demo")
    print("=" * 80)
    
    asyncio.run(main())
