"""
Command-line argument handling for NLQ to SPARQL generator

This module handles all argument parsing, validation, and processing for the CLI.
"""

import argparse
import sys
from pathlib import Path

try:
    from .config import Config
except ImportError:
    from config import Config


class ArgumentHandler:
    """Handles command-line argument parsing and validation"""
    
    def __init__(self, config: Config):
        self.config = config
        self.available_databases = config.get_available_databases()
    
    def create_parser(self) -> argparse.ArgumentParser:
        """Create and configure the argument parser"""
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
            choices=self.available_databases,
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

        # Optional: execute generated SPARQL via HTTP and save results
        parser.add_argument(
            "--exec-sparql",
            action="store_true",
            help="Execute generated SPARQL against a SPARQL HTTP endpoint and save results",
        )
        parser.add_argument(
            "--sparql-endpoint",
            type=str,
            default=None,
            help="SPARQL endpoint URL (default: staging Virtuoso if omitted)",
        )
        parser.add_argument(
            "--sparql-format",
            choices=["json", "xml", "csv", "tsv"],
            default="json",
            help="Result format when executing SPARQL (default: json)",
        )
        parser.add_argument(
            "--sparql-timeout",
            type=int,
            default=15,
            help="HTTP timeout in seconds for SPARQL execution (default: 15)",
        )
        parser.add_argument(
            "--sparql-limit",
            type=int,
            default=1000,
            help="Max LIMIT enforced for SELECT when executing SPARQL (default: 1000)",
        )
        parser.add_argument(
            "--sparql-results-dir",
            type=Path,
            default=None,
            help="Directory to save SPARQL results (default: shared/nlq2sparql/results)",
        )
        
        return parser
    
    def validate_args(self, args: argparse.Namespace) -> None:
        """Validate parsed arguments"""
        # Handle list databases command
        if args.list_databases:
            self._list_databases()
            sys.exit(0)
        
        # Validate required arguments for query processing
        if not args.database:
            print("Error: --database is required when processing queries")
            print("Use --list-databases to see available options")
            sys.exit(1)
    
    def _list_databases(self) -> None:
        """List available databases and their test queries"""
        print("Available databases:")
        for db in self.available_databases:
            query = self.config.get_default_query(db)
            print(f"  - {db}: {query[:50]}{'...' if len(query) > 50 else ''}")
    
    def determine_query(self, args: argparse.Namespace) -> str:
        """Determine which query to use based on arguments"""
        if args.test or not args.query:
            # Use default test queries from config
            query = self.config.get_default_query(args.database)
            if args.verbose:
                print(f"Using test query: {query}")
            return query
        else:
            return args.query
