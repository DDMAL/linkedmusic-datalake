#!/usr/bin/env python3
"""
CLI interface for NLQ to SPARQL generator
"""

import sys
from pathlib import Path

try:
    from .config import Config
    from .arguments import ArgumentHandler
    from .query_processor import QueryProcessor
    from .logging_config import setup_end_to_end_logging
except ImportError:
    from config import Config
    from arguments import ArgumentHandler
    from query_processor import QueryProcessor
    from logging_config import setup_end_to_end_logging


def main():
    """Main CLI entry point"""
    try:
        # Load configuration
        config = Config()
        
        # Parse command line arguments
        cli_parser = ArgumentHandler(config)
        parser = cli_parser.create_parser()
        args = parser.parse_args()
        
        # Validate arguments (may exit if --list-databases or validation fails)
        cli_parser.validate_args(args)
        
        # Set up logging if requested
        if args.debug_logging or args.verbose:
            log_file = str(args.log_file) if args.log_file else None
            setup_end_to_end_logging(verbose=args.debug_logging or args.verbose, log_file=log_file)
        
        # Update configuration with custom config file if provided
        if args.config:
            config = Config(config_file=args.config)
        
        # Determine which query to use
        query = cli_parser.determine_query(args)
        
        # Process the query
        processor = QueryProcessor(config)
        # Surface execution flags from args into config (side-channel attributes)
        # This avoids expanding the Config schema right now.
        if hasattr(args, "exec_sparql") and args.exec_sparql:
            setattr(config, "exec_sparql", True)
            if getattr(args, "sparql_endpoint", None):
                setattr(config, "sparql_endpoint", args.sparql_endpoint)
            if getattr(args, "sparql_format", None):
                setattr(config, "sparql_format", args.sparql_format)
            if getattr(args, "sparql_timeout", None) is not None:
                setattr(config, "sparql_timeout", args.sparql_timeout)
            if getattr(args, "sparql_limit", None) is not None:
                setattr(config, "sparql_limit", args.sparql_limit)
            if getattr(args, "sparql_results_dir", None):
                setattr(config, "sparql_results_dir", str(args.sparql_results_dir))
        processor.process_query_request(
            query=query,
            provider=args.provider,
            database=args.database,
            ontology_file=args.ontology_file,
            debug_mode=args.debug_prompt,
            verbose=args.verbose,
            use_llm_agents=args.llm_agents
        )
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
