#!/usr/bin/env python3
"""
CLI interface for NLQ to SPARQL generator
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

try:
    from .router import QueryRouter
    from .config import Config
    from .providers.base import BaseLLMClient
except ImportError:
    from router import QueryRouter
    from config import Config
    from providers.base import BaseLLMClient


class PromptDebugClient(BaseLLMClient):
    """Debug client that captures prompts instead of calling APIs"""
    
    def __init__(self, config):
        super().__init__(config)
        self.captured_prompt = None
    
    def _call_llm_api(self, prompt: str, verbose: bool = False) -> str:
        """Capture the prompt instead of calling an API"""
        self.captured_prompt = prompt
        return "DEBUG_MODE_NO_API_CALL"
    
    def capture_prompt(self, nlq: str, database: str, ontology_file=None):
        """Capture the prompt that would be sent to the LLM and save it to a file"""
        from pathlib import Path
        import os
        from datetime import datetime
        try:
            from .prompts import build_sparql_generation_prompt
        except ImportError:
            from prompts import build_sparql_generation_prompt
        
        # Generate the prompt using the same logic as production
        prefix_declarations = self.config.get_prefix_declarations(database)
        ontology_context = ""
        if ontology_file:
            # Read ontology file if provided
            try:
                with open(ontology_file, 'r') as f:
                    ontology_context = f.read()
            except Exception as e:
                print(f"Warning: Could not read ontology file {ontology_file}: {e}")
        
        prompt = build_sparql_generation_prompt(nlq, database, prefix_declarations, ontology_context)
        
        # Create output directory
        output_dir = Path("debug_prompts")
        output_dir.mkdir(exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_query = "".join(c for c in nlq if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_query = safe_query.replace(' ', '_')[:50]  # Limit length
        filename = f"prompt_{database}_{safe_query}_{timestamp}.txt"
        
        # Save prompt to file
        output_file = output_dir / filename
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"Database: {database}\n")
            f.write(f"Query: {nlq}\n")
            f.write(f"Ontology file: {ontology_file}\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write("=" * 80 + "\n")
            f.write("PROMPT:\n")
            f.write("=" * 80 + "\n")
            f.write(prompt)
        
        return str(output_file)


def main():
    # Load configuration early to get database choices
    config = Config()
    available_databases = config.get_available_databases()
    
    parser = argparse.ArgumentParser(
        description="Convert natural language queries to SPARQL using LLMs"
    )
    
    parser.add_argument(
        "query",
        nargs="?",
        help="Natural language query to convert to SPARQL (optional - uses test query if not provided)"
    )
    
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run with a default test query to verify setup"
    )
    
    parser.add_argument(
        "--provider",
        choices=["gemini", "chatgpt", "claude"],
        default="gemini",
        help="Provider to use (default: gemini)"
    )
    
    parser.add_argument(
        "--database",
        choices=available_databases,
        help="Database to query against"
    )
    
    parser.add_argument(
        "--ontology-file",
        type=Path,
        help="Path to ontology file for context"
    )
    
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to configuration file"
    )
    
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--list-databases",
        action="store_true",
        help="List available databases and exit"
    )
    
    parser.add_argument(
        "--debug-prompt",
        action="store_true",
        help="Save the prompt to file instead of sending to LLM (for debugging)"
    )
    
    args = parser.parse_args()
    
    # Handle list databases command
    if args.list_databases:
        print("Available databases:")
        for db in available_databases:
            query = config.get_default_query(db)
            print(f"  - {db}: {query[:50]}{'...' if len(query) > 50 else ''}")
        return
    
    # Validate required arguments for query processing
    if not args.database:
        print("Error: --database is required when processing queries")
        print("Use --list-databases to see available options")
        sys.exit(1)
    
    try:
        # Update configuration with custom config file if provided
        if args.config:
            config = Config(config_file=args.config)
        
        # Determine query to use
        if args.test or not args.query:
            # Use default test queries from config
            query = config.get_default_query(args.database)
            if args.verbose:
                print(f"Using test query: {query}")
        else:
            query = args.query
        
        # Handle debug prompt mode
        if args.debug_prompt:
            debug_client = PromptDebugClient(config)
            prompt_file = debug_client.capture_prompt(
                nlq=query,
                database=args.database,
                ontology_file=args.ontology_file
            )
            print(f"Prompt captured and saved to: {prompt_file}")
            print(f"Query processed: {query}")
        else:
            # Initialize router and process query normally
            router = QueryRouter(config)
            sparql_query = router.process_query(
                nlq=query,
                provider=args.provider,
                database=args.database,
                ontology_file=args.ontology_file,
                verbose=args.verbose
            )
            
            print("Generated SPARQL Query:")
            print("=" * 50)
            print(sparql_query)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
