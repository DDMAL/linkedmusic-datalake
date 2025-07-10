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
except ImportError:
    from router import QueryRouter
    from config import Config


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
        
        # Initialize router
        router = QueryRouter(config)
        
        # Determine query to use
        if args.test or not args.query:
            # Use default test queries from config
            query = config.get_default_query(args.database)
            if args.verbose:
                print(f"Using test query: {query}")
        else:
            query = args.query
        
        # Process query
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
