#!/usr/bin/env python3
"""
Simple Palestrina SPARQL Query Demo

A focused example showing SPARQL query generation for Palestrina compositions
with detailed execution tracing.

Usage:
    poetry run python -m nlq2sparql.examples.tracing.palestrina_demo
    
Or from the project root:
    cd shared && poetry run python -m nlq2sparql.examples.tracing.palestrina_demo
"""

import sys
import asyncio
import os
from pathlib import Path

# Ensure we can import the nlq2sparql module
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

async def palestrina_demo():
    """Simple focused demo for Palestrina SPARQL query generation"""
    
    from nlq2sparql.tracing import setup_tracing, get_trace_summary, clear_trace_buffer
    from nlq2sparql.integrations.gemini_integration import GeminiWikidataIntegration
    
    # Setup detailed tracing
    setup_tracing(level='DEBUG')
    clear_trace_buffer()
    
    print('🎵 PALESTRINA SPARQL QUERY WITH DETAILED TRACING')
    print('='*60)
    
    try:
        integration = GeminiWikidataIntegration()
        
        response = await integration.send_message_with_tools(
            'Write a SPARQL query that will return all compositions by Palestrina. '
            'First find Palestrina in Wikidata, then write a query to get his compositions.'
        )
        
        print('\\n📝 RESPONSE:')
        print('-' * 40)
        print(response.get('text', 'No text response'))
        
        print('\\n🔍 EXECUTION TRACE:')
        print('-' * 40)
        print(get_trace_summary())
        
        print('\\n📊 FUNCTION CALLS MADE:')
        print('-' * 40)
        for i, call in enumerate(response.get('function_calls', []), 1):
            entity_label = call['arguments'].get('entity_label', 'unknown')
            result = call['result']
            print(f'{i}. {call["function"]}("{entity_label}") → {result}')
        
        print('\\n✅ COMPLETE EXECUTION FLOW TRACED!')
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Check for API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ Error: GEMINI_API_KEY environment variable not set")
        print("Please set your Gemini API key:")
        print("export GEMINI_API_KEY=your_api_key_here")
        sys.exit(1)
    
    asyncio.run(palestrina_demo())
