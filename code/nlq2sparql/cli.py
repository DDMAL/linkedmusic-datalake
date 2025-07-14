#!/usr/bin/env python3
"""
CLI interface for NLQ to SPARQL generator
"""

import sys
from pathlib import Path

try:
    from .config import Config
    from .cli_parser import CLIParser
    from .query_processor import QueryProcessor
except ImportError:
    from config import Config
    from cli_parser import CLIParser
    from query_processor import QueryProcessor


def main():
    """Main CLI entry point"""
    try:
        # Load configuration
        config = Config()
        
        # Parse command line arguments
        cli_parser = CLIParser(config)
        parser = cli_parser.create_parser()
        args = parser.parse_args()
        
        # Validate arguments (may exit if --list-databases or validation fails)
        cli_parser.validate_args(args)
        
        # Update configuration with custom config file if provided
        if args.config:
            config = Config(config_file=args.config)
        
        # Determine which query to use
        query = cli_parser.determine_query(args)
        
        # Process the query
        processor = QueryProcessor(config)
        processor.process_query_request(
            query=query,
            provider=args.provider,
            database=args.database,
            ontology_file=args.ontology_file,
            debug_mode=args.debug_prompt,
            verbose=args.verbose
        )
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
