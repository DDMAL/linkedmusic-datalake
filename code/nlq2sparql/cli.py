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
        self.last_query_info = {}
    
    def _call_llm_api(self, prompt: str, verbose: bool = False) -> str:
        """Capture the prompt instead of calling an API"""
        self.captured_prompt = prompt
        
        # Save prompt to file immediately when captured
        self._save_prompt_to_file()
        
        return "DEBUG_MODE_NO_API_CALL"
    
    def _extract_keywords(self, text: str, max_words: int = 4) -> str:
        """Extract key terms from natural language query for filename"""
        # Common English stop words to remove
        stop_words = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from', 'has', 
            'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the', 'to', 'was', 
            'will', 'with', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 
            'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 
            'so', 'than', 'too', 'very', 'can', 'will', 'just', 'should', 'now',
            'show', 'me', 'get', 'find', 'return', 'give', 'list', 'display'
        }
        
        # First, handle special compound terms (like musical keys)
        text_lower = text.lower()
        
        # Look for musical keys and preserve them as single terms
        import re
        # Match patterns like "D major", "C# minor", "Bb major", etc.
        key_pattern = r'\b([a-g][#b]?)\s+(major|minor)\b'
        keys = re.findall(key_pattern, text_lower)
        key_terms = [f"{note}{mode}" for note, mode in keys]
        
        # Remove the matched key patterns from text to avoid double-processing
        text_cleaned = re.sub(key_pattern, '', text_lower)
        
        # Clean and split the remaining text
        words = text_cleaned.replace('-', ' ').split()
        
        # Filter out stop words and keep meaningful terms
        keywords = []
        
        # Add preserved key terms first
        for key_term in key_terms:
            keywords.append(key_term)
            if len(keywords) >= max_words:
                break
        
        # Add other meaningful words
        if len(keywords) < max_words:
            for word in words:
                # Remove punctuation and keep only alphanumeric
                clean_word = ''.join(c for c in word if c.isalnum())
                if clean_word and clean_word not in stop_words and len(clean_word) > 1:  # Changed from >2 to >1 to keep single meaningful chars
                    keywords.append(clean_word)
                    if len(keywords) >= max_words:
                        break
        
        # Join with underscores, limit total length
        result = '_'.join(keywords)
        return result[:30] if result else 'query'  # Fallback and length limit
    
    def generate_sparql(self, nlq: str, database: str, ontology_context: str = "", verbose: bool = False) -> str:
        """Override to store query info before calling parent method"""
        # Store info for filename generation
        self.last_query_info = {
            'nlq': nlq,
            'database': database,
            'ontology_context': ontology_context
        }
        
        # Call parent method which will trigger _call_llm_api where we capture the prompt
        return super().generate_sparql(nlq, database, ontology_context, verbose)
    
    def _save_prompt_to_file(self):
        """Save the captured prompt to a file"""
        from pathlib import Path
        from datetime import datetime
        
        if not self.captured_prompt or not self.last_query_info:
            return ""
        
        # Create output directory
        output_dir = Path("debug_prompts")
        output_dir.mkdir(exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        keywords = self._extract_keywords(self.last_query_info['nlq'])
        filename = f"prompt_{self.last_query_info['database']}_{keywords}_{timestamp}.txt"
        
        # Save prompt to file
        output_file = output_dir / filename
        with open(output_file, 'w', encoding='utf-8') as f:
            # Format timestamp with timezone shown separately
            dt_with_tz = datetime.now().astimezone()
            timezone_name = dt_with_tz.strftime("%Z")  # e.g., "EDT", "PDT", "UTC"
            timestamp_formatted = dt_with_tz.strftime("%Y-%m-%d %H:%M:%S")
            
            f.write(f"Database: {self.last_query_info['database']}\n")
            f.write(f"Query: {self.last_query_info['nlq']}\n")
            f.write(f"Ontology context: {'Yes' if self.last_query_info['ontology_context'] else 'None'}\n")
            f.write(f"Timestamp ({timezone_name}): {timestamp_formatted}\n")
            f.write("=" * 80 + "\n")
            f.write("PROMPT SENT TO LLM:\n")
            f.write("=" * 80 + "\n")
            f.write(self.captured_prompt)
        
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
            # Use the debug client through the router to follow the same code path
            router = QueryRouter(config)
            # Temporarily replace the provider client with our debug client
            debug_client = PromptDebugClient(config)
            router.provider_clients[args.provider] = debug_client
            
            sparql_query = router.process_query(
                nlq=query,
                provider=args.provider,
                database=args.database,
                ontology_file=args.ontology_file,
                verbose=args.verbose
            )
            
            # The debug client automatically saves the prompt during the process
            print(f"Prompt captured and saved to debug_prompts/")
            print(f"Query processed: {query}")
            print(f"Debug response: {sparql_query}")
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
