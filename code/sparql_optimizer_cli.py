#!/usr/bin/env python3
"""
Federated Query Optimizer CLI Tool

This command-line tool provides an easy interface to optimize and test
federated SPARQL queries using the FederatedQueryOptimizer.

Usage:
    python3 sparql_optimizer_cli.py [command] [options]

Commands:
    analyze       Analyze a query for optimization opportunities
    optimize      Optimize and execute a query  
    rewrite       Show optimized query without executing
    config        Show configuration options
    benchmark     Benchmark original vs optimized query performance

Examples:
    # Analyze a query file
    python3 sparql_optimizer_cli.py analyze --file query.sparql
    
    # Optimize and execute a query
    python3 sparql_optimizer_cli.py optimize --query "SELECT ?s ?p ?o WHERE { ?s ?p ?o }" --config research
    
    # Show optimized query without executing
    python3 sparql_optimizer_cli.py rewrite --file query.sparql --config diamm
    
    # Benchmark performance
    python3 sparql_optimizer_cli.py benchmark --file slow_query.sparql --runs 3
"""

import argparse
import asyncio
import aiohttp
import sys
import os
import time
import json
from pathlib import Path
from typing import Optional, Dict, Any

# Add the parent directory to the path to import wikidata_utils
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wikidata_utils import (
    WikidataAPIClient, 
    FederatedQueryOptimizer, 
    OptimizationConfig,
    get_config, 
    create_custom_config
)


class QueryOptimizerCLI:
    """Command-line interface for the FederatedQueryOptimizer."""
    
    def __init__(self):
        self.client = None
        self.optimizer = None
        self.session = None
    
    async def setup(self, config_name: str = 'default', custom_config: Optional[Dict[str, Any]] = None):
        """Set up the optimizer with the specified configuration."""
        self.session = aiohttp.ClientSession()
        self.client = WikidataAPIClient(self.session)
        
        if custom_config:
            config = create_custom_config(**custom_config)
        else:
            config = get_config(config_name)
        
        self.optimizer = FederatedQueryOptimizer(self.client, config)
    
    async def cleanup(self):
        """Clean up resources."""
        if self.session:
            await self.session.close()
    
    def load_query(self, query_text: Optional[str] = None, query_file: Optional[str] = None) -> str:
        """Load a query from text or file."""
        if query_text:
            return query_text
        elif query_file:
            with open(query_file, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            raise ValueError("Either query_text or query_file must be provided")
    
    async def analyze_command(self, args):
        """Analyze a query for optimization opportunities."""
        print("=== SPARQL Query Analysis ===\\n")
        
        query = self.load_query(args.query, args.file)
        
        print(f"Query source: {'inline' if args.query else args.file}")
        print(f"Query length: {len(query)} characters")
        
        analysis = self.optimizer.analyze_query(query)
        
        print(f"\\nAnalysis Results:")
        print(f"  • Has federated services: {analysis.has_federated_services}")
        print(f"  • Wikidata services found: {len(analysis.wikidata_services)}")
        print(f"  • Local graphs: {len(analysis.local_graphs)}")
        if analysis.local_graphs:
            for graph in analysis.local_graphs:
                print(f"    - {graph}")
        print(f"  • Variables: {len(analysis.variables)}")
        if analysis.variables:
            print(f"    {', '.join(sorted(analysis.variables))}")
        print(f"  • Filters: {len(analysis.filters)}")
        
        if analysis.wikidata_services:
            print(f"\\nWikidata Services:")
            for i, service in enumerate(analysis.wikidata_services, 1):
                print(f"  Service {i}:")
                print(f"    • Endpoint: {service.endpoint}")
                print(f"    • Patterns: {len(service.patterns)}")
                for pattern in service.patterns[:3]:  # Show first 3 patterns
                    print(f"      - {pattern.strip()}")
                if len(service.patterns) > 3:
                    print(f"      ... and {len(service.patterns) - 3} more")
        
        print(f"\\nOptimization Opportunities:")
        
        if not analysis.has_federated_services:
            print("  • No federated services found - no optimization needed")
        else:
            print("  • Query can benefit from federated optimization")
            
            if analysis.local_graphs and analysis.wikidata_services:
                print("  • Local-first execution strategy applicable")
            
            if len(analysis.wikidata_services) == 1:
                print("  • Single SERVICE optimization applicable")
            
            if any('dateTime' in f for f in analysis.filters):
                print("  • Date filter optimization applicable")
            
            print("  • Query hint optimization applicable")
            print("  • Timeout protection applicable")
    
    async def optimize_command(self, args):
        """Optimize and execute a query."""
        print("=== SPARQL Query Optimization & Execution ===\\n")
        
        query = self.load_query(args.query, args.file)
        
        print(f"Query source: {'inline' if args.query else args.file}")
        print(f"Configuration: {args.config}")
        print(f"Timeout: {args.timeout}s")
        
        start_time = time.time()
        
        try:
            results = await self.optimizer.execute_optimized(query, timeout=args.timeout)
            execution_time = time.time() - start_time
            
            print(f"\\n✓ Query executed successfully!")
            print(f"  • Execution time: {execution_time:.2f}s")
            print(f"  • Results returned: {len(results)}")
            
            if results and args.show_results:
                print(f"\\n  Sample results (first {min(5, len(results))}):")
                for i, result in enumerate(results[:5], 1):
                    print(f"    Result {i}:")
                    for key, value in result.items():
                        print(f"      {key}: {value}")
                    if i < min(5, len(results)):
                        print()
            
            # Show optimization stats
            stats = self.optimizer.get_cache_stats()
            print(f"\\nOptimization Statistics:")
            print(f"  • Total queries: {stats['total_queries']}")
            print(f"  • Optimizations applied: {stats['optimizations_applied']}")
            print(f"  • Cache hits: {stats['cache_hits']}")
            
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"\\n✗ Query execution failed!")
            print(f"  • Error: {str(e)}")
            print(f"  • Time until failure: {execution_time:.2f}s")
            return 1
        
        return 0
    
    async def rewrite_command(self, args):
        """Show the optimized query without executing it."""
        print("=== SPARQL Query Rewriting ===\\n")
        
        query = self.load_query(args.query, args.file)
        
        print(f"Query source: {'inline' if args.query else args.file}")
        print(f"Configuration: {args.config}")
        
        analysis = self.optimizer.analyze_query(query)
        optimized_query = self.optimizer._rewrite_for_efficiency(query, analysis)
        
        print(f"\\nOriginal query ({len(query)} chars):")
        print("```sparql")
        print(query)
        print("```")
        
        print(f"\\nOptimized query ({len(optimized_query)} chars):")
        print("```sparql")
        print(optimized_query)
        print("```")
        
        print(f"\\nOptimizations applied:")
        changes = len(optimized_query) - len(query)
        print(f"  • Size change: {changes:+d} characters")
        
        if "hint:Query" in optimized_query and "hint:Query" not in query:
            print("  • Added Wikidata query hints")
        if "timeout:" in optimized_query and "timeout:" not in query:
            print("  • Added timeout directive")
        if "hint:optimizer" in optimized_query:
            print("  • Added runtime optimizer hints")
        if "maxParallel" in optimized_query:
            print("  • Added parallel execution limits")
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(optimized_query)
            print(f"\\nOptimized query saved to: {args.output}")
    
    async def config_command(self, args):
        """Show configuration options and details."""
        print("=== Configuration Options ===\\n")
        
        if args.list:
            from wikidata_utils.config import CONFIGS, get_config_summary
            
            print("Available configurations:")
            for name in CONFIGS.keys():
                config = get_config(name)
                print(f"\\n{name.upper()}:")
                print(f"  • Cache TTL: {config.cache_ttl}s ({config.cache_ttl/3600:.1f}h)")
                print(f"  • Default timeout: {config.default_timeout}ms ({config.default_timeout/1000:.0f}s)")
                print(f"  • Query hints: {config.add_query_hints}")
                print(f"  • Filter optimization: {config.move_filters_to_service}")
                print(f"  • Logging: {config.log_optimizations}")
        
        elif args.show:
            from wikidata_utils.config import get_config_summary
            
            config = get_config(args.show)
            print(get_config_summary(config))
        
        else:
            print("Use --list to see all configurations or --show CONFIG_NAME for details")
    
    async def benchmark_command(self, args):
        """Benchmark original vs optimized query performance."""
        print("=== Performance Benchmark ===\\n")
        
        query = self.load_query(args.query, args.file)
        
        print(f"Query source: {'inline' if args.query else args.file}")
        print(f"Number of runs: {args.runs}")
        print(f"Configuration: {args.config}")
        
        # Results storage
        original_times = []
        optimized_times = []
        
        # Run benchmarks
        for run in range(args.runs):
            print(f"\\nRun {run + 1}/{args.runs}:")
            
            # Original query (without optimization)
            print("  Running original query...", end=" ")
            start_time = time.time()
            try:
                original_results = await self.client.sparql(query, timeout=args.timeout)
                original_time = time.time() - start_time
                original_times.append(original_time)
                print(f"{original_time:.2f}s ({len(original_results)} results)")
            except Exception as e:
                print(f"FAILED ({str(e)})")
                original_times.append(float('inf'))
            
            # Optimized query
            print("  Running optimized query...", end=" ")
            start_time = time.time()
            try:
                optimized_results = await self.optimizer.execute_optimized(query, timeout=args.timeout)
                optimized_time = time.time() - start_time
                optimized_times.append(optimized_time)
                print(f"{optimized_time:.2f}s ({len(optimized_results)} results)")
            except Exception as e:
                print(f"FAILED ({str(e)})")
                optimized_times.append(float('inf'))
        
        # Calculate statistics
        print(f"\\n=== Benchmark Results ===")
        
        if original_times and all(t != float('inf') for t in original_times):
            avg_original = sum(original_times) / len(original_times)
            print(f"Original query average: {avg_original:.2f}s")
        else:
            avg_original = None
            print("Original query: Failed or timed out")
        
        if optimized_times and all(t != float('inf') for t in optimized_times):
            avg_optimized = sum(optimized_times) / len(optimized_times)
            print(f"Optimized query average: {avg_optimized:.2f}s")
        else:
            avg_optimized = None
            print("Optimized query: Failed or timed out")
        
        if avg_original and avg_optimized:
            speedup = avg_original / avg_optimized
            improvement = ((avg_original - avg_optimized) / avg_original) * 100
            
            print(f"\\nPerformance improvement:")
            print(f"  • Speedup: {speedup:.2f}x")
            print(f"  • Time reduction: {improvement:.1f}%")
            print(f"  • Time saved: {avg_original - avg_optimized:.2f}s per query")
        
        # Show optimization report
        print(f"\\n{self.optimizer.get_optimization_report()}")


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Federated SPARQL Query Optimizer CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Common arguments
    common_parser = argparse.ArgumentParser(add_help=False)
    query_group = common_parser.add_mutually_exclusive_group(required=True)
    query_group.add_argument('--query', '-q', help='SPARQL query string')
    query_group.add_argument('--file', '-f', help='File containing SPARQL query')
    
    common_parser.add_argument(
        '--config', '-c', 
        default='default',
        choices=['default', 'diamm', 'research', 'production', 'development'],
        help='Configuration preset to use'
    )
    
    # Analyze command
    analyze_parser = subparsers.add_parser(
        'analyze', 
        parents=[common_parser],
        help='Analyze a query for optimization opportunities'
    )
    
    # Optimize command  
    optimize_parser = subparsers.add_parser(
        'optimize',
        parents=[common_parser], 
        help='Optimize and execute a query'
    )
    optimize_parser.add_argument('--timeout', '-t', type=int, default=60, help='Query timeout in seconds')
    optimize_parser.add_argument('--show-results', action='store_true', help='Show sample query results')
    
    # Rewrite command
    rewrite_parser = subparsers.add_parser(
        'rewrite',
        parents=[common_parser],
        help='Show optimized query without executing'
    )
    rewrite_parser.add_argument('--output', '-o', help='Save optimized query to file')
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Show configuration options')
    config_group = config_parser.add_mutually_exclusive_group()
    config_group.add_argument('--list', action='store_true', help='List all available configurations')
    config_group.add_argument('--show', help='Show details for a specific configuration')
    
    # Benchmark command
    benchmark_parser = subparsers.add_parser(
        'benchmark',
        parents=[common_parser],
        help='Benchmark original vs optimized performance'
    )
    benchmark_parser.add_argument('--runs', '-r', type=int, default=3, help='Number of benchmark runs')
    benchmark_parser.add_argument('--timeout', '-t', type=int, default=60, help='Query timeout in seconds')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    cli = QueryOptimizerCLI()
    
    try:
        # Set up the CLI with the specified configuration
        if args.command != 'config':
            await cli.setup(getattr(args, 'config', 'default'))
        
        # Execute the requested command
        if args.command == 'analyze':
            result = await cli.analyze_command(args)
        elif args.command == 'optimize':
            result = await cli.optimize_command(args)
        elif args.command == 'rewrite':
            result = await cli.rewrite_command(args)
        elif args.command == 'config':
            result = await cli.config_command(args)
        elif args.command == 'benchmark':
            result = await cli.benchmark_command(args)
        else:
            print(f"Unknown command: {args.command}")
            return 1
        
        return result or 0
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1
    
    finally:
        await cli.cleanup()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)