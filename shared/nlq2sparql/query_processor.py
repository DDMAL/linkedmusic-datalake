"""
Application controller for processing NLQ to SPARQL queries
"""

import sys
from pathlib import Path
from typing import Optional

try:
    from .config import Config
    from .router import QueryRouter
    from .debug_client import PromptDebugClient
except ImportError:
    from config import Config
    from router import QueryRouter
    from debug_client import PromptDebugClient


class QueryProcessor:
    """Handles the main application logic for processing queries"""
    
    def __init__(self, config: Config):
        self.config = config
    
    def process_query_request(
        self,
        query: str,
        provider: str,
        database: str,
        ontology_file: Optional[Path] = None,
        debug_mode: bool = False,
        verbose: bool = False,
        use_llm_agents: bool = False
    ) -> str:
        """
        Process a query request in either normal or debug mode
        
        Args:
            query: The natural language query
            provider: LLM provider to use
            database: Target database
            ontology_file: Optional ontology file path
            debug_mode: Whether to capture prompt instead of generating SPARQL
            verbose: Enable verbose output
            use_llm_agents: Whether to use LLM-powered agents instead of rule-based ones
            
        Returns:
            Generated SPARQL query or debug response
        """
        router = QueryRouter(self.config)
        
        if debug_mode:
            return self._process_debug_mode(
                router, query, provider, database, ontology_file, verbose, use_llm_agents
            )
        else:
            return self._process_normal_mode(
                router, query, provider, database, ontology_file, verbose, use_llm_agents
            )
    
    def _process_debug_mode(
        self,
        router: QueryRouter,
        query: str,
        provider: str,
        database: str,
        ontology_file: Optional[Path],
        verbose: bool,
        use_llm_agents: bool
    ) -> str:
        """Process query in debug mode (capture prompt)"""
        # Replace the provider client with our debug client
        debug_client = PromptDebugClient(self.config)
        router.provider_clients[provider] = debug_client
        
        sparql_query = router.process_query(
            nlq=query,
            provider=provider,
            database=database,
            ontology_file=ontology_file,
            verbose=verbose,
            use_llm_agents=use_llm_agents
        )
        
        # The debug client automatically saves the prompt during the process
        print(f"Prompt captured and saved to debug_prompts/")
        print(f"Query processed: {query}")
        print(f"Debug response: {sparql_query}")
        
        return sparql_query
    
    def _process_normal_mode(
        self,
        router: QueryRouter,
        query: str,
        provider: str,
        database: str,
        ontology_file: Optional[Path],
        verbose: bool,
        use_llm_agents: bool
    ) -> str:
        """Process query in normal mode (generate SPARQL)"""
        sparql_query = router.process_query(
            nlq=query,
            provider=provider,
            database=database,
            ontology_file=ontology_file,
            verbose=verbose,
            use_llm_agents=use_llm_agents
        )
        
        print("Generated SPARQL Query:")
        print("=" * 50)
        print(sparql_query)
        
        # Optional: execute SPARQL over HTTP if configured via CLI flags (attrs on config)
        try:
            from .tools.sparql_http import run_http_sparql
        except Exception:
            from tools.sparql_http import run_http_sparql  # type: ignore

        # Extract execution settings injected by ArgumentHandler via Config side channel
        exec_sparql = getattr(self.config, "exec_sparql", False)
        if exec_sparql and sparql_query and sparql_query.strip():
            endpoint = getattr(self.config, "sparql_endpoint", None) or "https://virtuoso.staging.simssa.ca/sparql"
            fmt = getattr(self.config, "sparql_format", "json")
            timeout = int(getattr(self.config, "sparql_timeout", 15))
            limit = int(getattr(self.config, "sparql_limit", 1000))
            out_dir = getattr(self.config, "sparql_results_dir", None)
            if out_dir is None:
                out_dir = (Path(__file__).resolve().parent / "results")
            else:
                out_dir = Path(out_dir)

            try:
                res = run_http_sparql(
                    endpoint_url=endpoint,
                    raw_query=sparql_query,
                    out_dir=out_dir,
                    fmt=fmt,
                    timeout_sec=timeout,
                    max_limit=limit,
                    allow_construct=False,
                )
                print("\nSPARQL execution:")
                print("- Endpoint:", endpoint)
                print("- Saved:", res.output_path)
                print("- Content-Type:", res.content_type)
                print("- Duration:", f"{res.duration_ms} ms")
            except Exception as e:
                print("\nWarning: SPARQL execution failed:", e)

        return sparql_query
