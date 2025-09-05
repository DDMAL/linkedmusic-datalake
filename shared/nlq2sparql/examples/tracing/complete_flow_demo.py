#!/usr/bin/env python3
"""
Complete Execution Flow Tracer

This demonstrates the complete execution flow with:
- Every LLM API call with full input/output
- Function calls and results
- Agent routing decisions
- Timing and performance data
- Error handling

Everything gets captured in both console output and a detailed JSON file.

Usage:
    poetry run python -m nlq2sparql.examples.tracing.complete_flow_demo
    
Or from the project root:
    cd shared && poetry run python -m nlq2sparql.examples.tracing.complete_flow_demo
"""

import sys
import asyncio
import os
import json
from pathlib import Path

# Ensure we can import the nlq2sparql module
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

async def complete_flow_demo():
    """Demonstrate complete execution flow tracing"""
    
    from nlq2sparql.tracing import setup_tracing, get_trace_summary, export_trace_log, clear_trace_buffer
    from nlq2sparql.integrations.gemini_integration import GeminiWikidataIntegration
    
    print("🔍 COMPLETE EXECUTION FLOW TRACER")
    print("=" * 60)
    print("This will show you EVERYTHING that happens:")
    print("• Every LLM API call with full input/output")
    print("• Function calls and their results")
    print("• Agent routing and decisions")
    print("• Timing and performance data")
    print("• Complete execution trace")
    print()
    
    # Setup comprehensive tracing
    tracing_manager = setup_tracing(level="DEBUG", enable_file_logging=True)
    clear_trace_buffer()
    
    try:
        print("🧪 RUNNING: Complex SPARQL Query Generation")
        print("-" * 50)
        
        integration = GeminiWikidataIntegration()
        
        # This will trigger multiple steps:
        # 1. LLM API call to understand the request
        # 2. Function call to find Palestrina 
        # 3. Another LLM API call to generate SPARQL
        response = await integration.send_message_with_tools(
            "Write a comprehensive SPARQL query to find all compositions by Palestrina. "
            "First find Palestrina in Wikidata, then create a detailed query that gets "
            "all his musical works with their titles and any available metadata."
        )
        
        print("✅ QUERY COMPLETED")
        print()
        
        # Show the final result
        print("📝 FINAL SPARQL QUERY:")
        print("-" * 30)
        print(response.get('text', 'No response text'))
        print()
        
        # Export the complete trace to logs directory
        logs_dir = project_root / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        trace_file = export_trace_log(str(logs_dir / "complete_execution_trace.json"))
        print(f"💾 Complete execution trace saved to: {trace_file}")
        
        # Show summary
        print()
        print("🔍 EXECUTION FLOW SUMMARY:")
        print("=" * 50)
        print(get_trace_summary())
        
        # Parse and display the detailed trace
        print()
        print("📋 DETAILED EXECUTION BREAKDOWN:")
        print("=" * 50)
        
        with open(trace_file, 'r') as f:
            trace_data = json.load(f)
            
        print(f"Total events captured: {trace_data['total_events']}")
        print()
        
        # Group events by operation type
        by_operation = {}
        for event in trace_data['events']:
            op = event['operation']
            if op not in by_operation:
                by_operation[op] = []
            by_operation[op].append(event)
        
        for operation, events in by_operation.items():
            print(f"🔸 {operation.upper()} ({len(events)} events):")
            for event in events:
                timestamp = event['timestamp'].split('T')[1][:12]
                print(f"  {timestamp} | {event['level']} | {event['message']}")
                
                # Show key data
                if event.get('data'):
                    data = event['data']
                    if 'input_text' in data:
                        input_text = data['input_text'][:100] + "..." if len(data['input_text']) > 100 else data['input_text']
                        print(f"    📥 Input: {input_text}")
                    if 'output_text' in data:
                        output_text = data['output_text'][:100] + "..." if len(data['output_text']) > 100 else data['output_text']
                        print(f"    📤 Output: {output_text}")
                    if 'function' in data:
                        print(f"    🔧 Function: {data['function']}")
                    if 'arguments' in data:
                        print(f"    📋 Args: {data['arguments']}")
                    if 'result' in data:
                        result = str(data['result'])[:50] + "..." if len(str(data['result'])) > 50 else str(data['result'])
                        print(f"    ✅ Result: {result}")
                    if 'duration_ms' in data:
                        print(f"    ⏱️ Duration: {data['duration_ms']:.1f}ms")
            print()
                        
        print("🎉 COMPLETE EXECUTION FLOW CAPTURED!")
        print(f"📁 Full details in: {trace_file}")
        
    except Exception as e:
        print(f"❌ Error during execution: {e}")
        import traceback
        traceback.print_exc()
        
        # Still export trace on error
        logs_dir = project_root / "logs"
        logs_dir.mkdir(exist_ok=True)
        trace_file = export_trace_log(str(logs_dir / "error_execution_trace.json"))
        print(f"💾 Error trace saved to: {trace_file}")

if __name__ == "__main__":
    # Check for API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ Error: GEMINI_API_KEY environment variable not set")
        print("Please set your Gemini API key:")
        print("export GEMINI_API_KEY=your_api_key_here")
        sys.exit(1)
    
    asyncio.run(complete_flow_demo())
