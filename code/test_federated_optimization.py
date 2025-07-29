#!/usr/bin/env python3
"""
Federated Query Performance Testing Tool

This script tests the performance improvements of federated SPARQL queries
using the FederatedQueryOptimizer. It includes the specific slow query
mentioned in the issue and provides before/after performance comparisons.

Usage:
    python3 test_federated_optimization.py [--original] [--optimized] [--both]
    
Examples:
    # Run only the optimized version
    python3 test_federated_optimization.py --optimized
    
    # Compare both original and optimized
    python3 test_federated_optimization.py --both
"""

import asyncio
import time
import argparse
import logging
import aiohttp
from typing import List, Dict, Any

# Add the parent directory to the path to import wikidata_utils
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wikidata_utils import WikidataAPIClient, FederatedQueryOptimizer


# The slow query from the issue
SLOW_FEDERATED_QUERY = """
SELECT ?archive ?archiveName ?archiveID ?archiveInception
WHERE {
  GRAPH <https://www.diamm.ac.uk/> {
    ?archive wdt:P2888 ?archiveID .
    ?archive rdfs:label ?archiveName .
    FILTER (STRSTARTS(STR(?archive), "https://www.diamm.ac.uk/archives/"))
  }

  SERVICE <https://query.wikidata.org/sparql> {
    ?archiveID wdt:P571 ?archiveInception .
  }

  FILTER (?archiveInception >= "1900-01-01T00:00:00Z"^^xsd:dateTime)
}
"""

# A simpler Wikidata query for testing optimization techniques
TEST_QUERY = """
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wd: <http://www.wikidata.org/entity/>

SELECT ?item ?itemLabel ?inception
WHERE {
  SERVICE <https://query.wikidata.org/sparql> {
    ?item wdt:P31 wd:Q166118 .  # institutions
    ?item wdt:P571 ?inception .
    FILTER (?inception >= "1900-01-01T00:00:00Z"^^xsd:dateTime)
    SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
  }
}
LIMIT 20
"""


async def run_query_with_timing(
    client: WikidataAPIClient, 
    query: str, 
    description: str,
    use_optimizer: bool = False
) -> Dict[str, Any]:
    """
    Run a SPARQL query and measure its performance.
    
    Args:
        client: WikidataAPIClient instance
        query: SPARQL query string
        description: Description for logging
        use_optimizer: Whether to use the FederatedQueryOptimizer
        
    Returns:
        Dictionary with timing and result information
    """
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        if use_optimizer:
            optimizer = FederatedQueryOptimizer(client)
            print("Using FederatedQueryOptimizer...")
            
            # Show the analysis
            analysis = optimizer.analyze_query(query)
            print(f"Query analysis:")
            print(f"  - Federated services: {analysis.has_federated_services}")
            print(f"  - Wikidata services: {len(analysis.wikidata_services)}")
            print(f"  - Local graphs: {len(analysis.local_graphs)}")
            print(f"  - Variables: {len(analysis.variables)}")
            print(f"  - Filters: {len(analysis.filters)}")
            
            results = await optimizer.execute_optimized(query, timeout=120)
        else:
            print("Using standard WikidataAPIClient...")
            results = await client.sparql(query, timeout=120)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"\nExecution completed successfully!")
        print(f"Execution time: {execution_time:.2f} seconds")
        print(f"Number of results: {len(results)}")
        
        # Show a few sample results
        if results:
            print(f"\nSample results (first 3):")
            for i, result in enumerate(results[:3]):
                print(f"  Result {i+1}: {result}")
        
        return {
            'success': True,
            'execution_time': execution_time,
            'result_count': len(results),
            'results': results,
            'error': None
        }
        
    except Exception as e:
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"\nExecution failed!")
        print(f"Error: {str(e)}")
        print(f"Time until failure: {execution_time:.2f} seconds")
        
        return {
            'success': False,
            'execution_time': execution_time,
            'result_count': 0,
            'results': [],
            'error': str(e)
        }


async def test_optimization_performance(args):
    """
    Test the performance of federated query optimization.
    """
    print("Federated SPARQL Query Optimization Test")
    print("="*50)
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    async with aiohttp.ClientSession() as session:
        client = WikidataAPIClient(session)
        
        # Choose which query to test
        if 'diamm' in args and args.diamm:
            test_query = SLOW_FEDERATED_QUERY
            query_name = "DIAMM Archives Query (from issue)"
        else:
            test_query = TEST_QUERY
            query_name = "Test Institutions Query"
        
        print(f"Testing query: {query_name}")
        print(f"Query length: {len(test_query)} characters")
        
        results = {}
        
        # Run original version if requested
        if args.original or args.both:
            results['original'] = await run_query_with_timing(
                client, test_query, "Original Query (no optimization)", use_optimizer=False
            )
        
        # Run optimized version if requested  
        if args.optimized or args.both:
            results['optimized'] = await run_query_with_timing(
                client, test_query, "Optimized Query", use_optimizer=True
            )
        
        # Show performance comparison if both were run
        if args.both and 'original' in results and 'optimized' in results:
            print(f"\n{'='*60}")
            print("PERFORMANCE COMPARISON")
            print(f"{'='*60}")
            
            orig = results['original']
            opt = results['optimized']
            
            print(f"Original execution time:  {orig['execution_time']:.2f} seconds")
            print(f"Optimized execution time: {opt['execution_time']:.2f} seconds")
            
            if orig['success'] and opt['success']:
                speedup = orig['execution_time'] / opt['execution_time']
                improvement = ((orig['execution_time'] - opt['execution_time']) / orig['execution_time']) * 100
                
                print(f"Speedup factor: {speedup:.2f}x")
                print(f"Performance improvement: {improvement:.1f}%")
                
                # Check if results are consistent
                if orig['result_count'] == opt['result_count']:
                    print(f"✓ Result count consistent: {orig['result_count']} rows")
                else:
                    print(f"⚠ Result count differs: {orig['result_count']} vs {opt['result_count']}")
            else:
                if not orig['success']:
                    print(f"Original query failed: {orig['error']}")
                if not opt['success']:
                    print(f"Optimized query failed: {opt['error']}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Test federated SPARQL query optimization performance',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        '--original', 
        action='store_true',
        help='Run the original query without optimization'
    )
    
    parser.add_argument(
        '--optimized', 
        action='store_true', 
        help='Run the optimized query'
    )
    
    parser.add_argument(
        '--both', 
        action='store_true',
        help='Run both original and optimized versions for comparison'
    )
    
    parser.add_argument(
        '--diamm',
        action='store_true',
        help='Test with the original DIAMM query from the issue (may be slow)'
    )
    
    args = parser.parse_args()
    
    # Default to optimized if no specific option chosen
    if not (args.original or args.optimized or args.both):
        args.optimized = True
    
    # Run the tests
    asyncio.run(test_optimization_performance(args))


if __name__ == "__main__":
    main()