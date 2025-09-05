#!/usr/bin/env python3
"""
Comprehensive end-to-end test with full logging to show all inputs and outputs.
Uses the CLI with enhanced logging to show the full pipeline.
"""

import subprocess
import sys
import tempfile
from pathlib import Path
import os

def run_end_to_end_test():
    """Run comprehensive end-to-end tests using the CLI with full logging."""
    
    print("🚀 Starting Comprehensive End-to-End Test")
    print("=" * 80)
    print("This will run multiple queries through the full pipeline with comprehensive logging")
    print("Using mock LLM responses to avoid API key requirements")
    print("=" * 80)
    
    # Test cases with different query types
    test_queries = [
        {
            "query": "Find compositions by Palestrina",
            "database": "diamm",
            "description": "Renaissance composer query - should route to DIAMM + MusicBrainz"
        },
        {
            "query": "Show me Irish traditional tunes in D major",
            "database": "session", 
            "description": "Irish traditional music - should route to The Session + MusicBrainz"
        },
        {
            "query": "Find jazz solos with harmonic analysis",
            "database": "dlt1000",
            "description": "Jazz analysis - should route to DTL-1000 + MusicBrainz"
        },
        {
            "query": "Show me recordings by The Beatles",
            "database": "musicbrainz",
            "description": "Popular music recordings - should route to MusicBrainz"
        }
    ]
    
    # Create a temporary log file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as log_file:
        log_file_path = log_file.name
    
    print(f"📝 Logs will be saved to: {log_file_path}")
    print()
    
    base_dir = Path(__file__).parent.parent.parent.parent
    
    for i, test_case in enumerate(test_queries, 1):
        print(f"🔍 TEST {i}: {test_case['description']}")
        print(f"Query: '{test_case['query']}'")
        print(f"Database: {test_case['database']}")
        print("-" * 60)
        
        try:
            # Run the CLI with comprehensive logging
            cmd = [
                "poetry", "run", "python", "shared/nlq2sparql/cli.py",
                "--debug-logging",
                "--log-file", log_file_path,
                "--llm-agents",
                "--database", test_case["database"],
                "--provider", "gemini",  # Will use mock in debug mode
                test_case["query"]
            ]
            
            print(f"🔄 Running: {' '.join(cmd)}")
            
            # Run the command
            result = subprocess.run(
                cmd,
                cwd=base_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            print(f"📤 Return code: {result.returncode}")
            
            if result.stdout:
                print("📥 STDOUT:")
                print(result.stdout)
            
            if result.stderr:
                print("⚠️ STDERR:")
                print(result.stderr)
            
            print("=" * 60)
            
        except subprocess.TimeoutExpired:
            print("⏰ Command timed out")
            print("=" * 60)
        except Exception as e:
            print(f"❌ Command failed: {e}")
            print("=" * 60)
    
    print("🎉 All tests completed!")
    print(f"📋 Full detailed logs available in: {log_file_path}")
    
    # Show a sample of the log file
    if os.path.exists(log_file_path):
        print("\n📖 Sample log contents:")
        print("-" * 40)
        try:
            with open(log_file_path, 'r') as f:
                lines = f.readlines()
                # Show first and last few lines
                for line in lines[:10]:
                    print(line.rstrip())
                if len(lines) > 20:
                    print("... (truncated) ...")
                    for line in lines[-10:]:
                        print(line.rstrip())
        except Exception as e:
            print(f"Could not read log file: {e}")
    
    return log_file_path


def main():
    """Main entry point."""
    log_file = run_end_to_end_test()
    print(f"\n✅ Test completed! Check the full logs at: {log_file}")


if __name__ == "__main__":
    main()
