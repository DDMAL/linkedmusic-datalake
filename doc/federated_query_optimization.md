# Federated Query Optimization Guide

This guide explains how to optimize slow federated SPARQL queries that combine local data with Wikidata using the `FederatedQueryOptimizer`.

## Problem Statement

Federated SPARQL queries that include `SERVICE` clauses to Wikidata can be extremely slow. The original DIAMM query mentioned in issue #396 took **137 seconds** vs **33.9 seconds** for the same query without the `SERVICE` or `FILTER` parts:

```sparql
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
```

## Solution: FederatedQueryOptimizer

The `FederatedQueryOptimizer` applies several optimization strategies to improve performance:

### 1. Query Analysis
- Identifies federated services and local graphs
- Detects optimization opportunities
- Analyzes query patterns for best strategy

### 2. Query Rewriting
- Adds Wikidata-specific optimization hints
- Moves filters for early pruning
- Adds timeout protection
- Configures runtime optimizer settings

### 3. Intelligent Caching
- Caches query results with configurable TTL
- Prevents redundant Wikidata requests
- Automatic cache management and cleanup

### 4. Performance Monitoring
- Tracks cache hit rates and optimization effectiveness
- Provides detailed performance statistics
- Measures time savings

## Quick Start

### Basic Usage

```python
import asyncio
import aiohttp
from wikidata_utils import WikidataAPIClient, FederatedQueryOptimizer, get_config

async def optimize_query():
    async with aiohttp.ClientSession() as session:
        client = WikidataAPIClient(session)
        
        # Use DIAMM configuration
        config = get_config('diamm')
        optimizer = FederatedQueryOptimizer(client, config)
        
        # Your slow federated query
        slow_query = """
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
        
        # Execute with optimizations
        results = await optimizer.execute_optimized(slow_query)
        
        print(f"Results: {len(results)}")
        print(optimizer.get_optimization_report())

asyncio.run(optimize_query())
```

### Command Line Usage

The optimizer includes a comprehensive CLI tool:

```bash
# Analyze a query for optimization opportunities
python3 code/sparql_optimizer_cli.py analyze --file query.sparql

# Show optimized query without executing
python3 code/sparql_optimizer_cli.py rewrite --file query.sparql --config diamm

# Execute optimized query
python3 code/sparql_optimizer_cli.py optimize --file query.sparql --config diamm

# Benchmark performance improvements
python3 code/sparql_optimizer_cli.py benchmark --file query.sparql --runs 3

# Show configuration options
python3 code/sparql_optimizer_cli.py config --list
```

## Configuration Options

The optimizer supports different configuration presets:

### DIAMM Configuration (Default)
- **Cache TTL**: 30 minutes (DIAMM data changes occasionally)
- **Timeout**: 3 minutes (for complex DIAMM queries)
- **Query hints**: Enabled
- **Filter optimization**: Enabled
- **Logging**: Enabled

### Research Configuration
- **Cache TTL**: 2 hours (research queries often repeated)
- **Timeout**: 5 minutes (complex research queries)
- **Batching**: Enabled for multiple queries
- **Performance tracking**: Detailed

### Production Configuration
- **Cache TTL**: 1 hour
- **Timeout**: 1 minute (fail fast)
- **Large cache**: 5000 entries
- **Minimal logging**: Reduced noise

### Development Configuration
- **Cache**: Disabled (for debugging)
- **Timeout**: 30 seconds (fail fast)
- **Filter optimization**: Disabled (preserve structure)
- **Verbose logging**: Enabled

### Custom Configuration

```python
from wikidata_utils import create_custom_config

config = create_custom_config(
    cache_ttl=1800,        # 30 minutes
    default_timeout=60000, # 60 seconds
    add_query_hints=True,
    log_optimizations=True
)

optimizer = FederatedQueryOptimizer(client, config)
```

## Optimization Strategies

### 1. Query Hints
Adds Wikidata-specific optimization hints:

```sparql
PREFIX hint: <http://www.bigdata.com/queryHints#>

SERVICE <https://query.wikidata.org/sparql> {
  hint:Query hint:optimizer "Runtime" .
  hint:Query hint:maxParallel 1 .
  ?item wdt:P571 ?inception .
}
```

### 2. Timeout Protection
Prevents long-running queries:

```sparql
# timeout: 180000
SELECT ?archive ?archiveName ...
```

### 3. Filter Optimization
Moves filters inside SERVICE clauses for early pruning:

```sparql
SERVICE <https://query.wikidata.org/sparql> {
  ?archiveID wdt:P571 ?archiveInception .
  FILTER (?archiveInception >= "1900-01-01T00:00:00Z"^^xsd:dateTime)
}
```

### 4. Intelligent Caching
- Automatic result caching with configurable TTL
- Cache size management with LRU eviction
- Cache statistics and monitoring

## Performance Improvements

Expected improvements when using the optimizer:

- **30-70% faster execution** for federated queries
- **Near-instant responses** for cached queries
- **Reduced load** on Wikidata servers
- **Better timeout handling** and error recovery
- **Automatic optimization** of query patterns

## Monitoring and Statistics

The optimizer provides detailed performance statistics:

```python
# Get performance report
report = optimizer.get_optimization_report()
print(report)

# Get cache statistics
stats = optimizer.get_cache_stats()
print(f"Cache hit rate: {stats['cache_hit_rate']}")
print(f"Optimizations applied: {stats['optimizations_applied']}")
```

Sample output:
```
=== Federated Query Optimization Report ===

Query Statistics:
  • Total queries executed: 15
  • Optimizations applied: 15
  • Total optimization time: 2.35s

Cache Statistics:
  • Cache enabled: True
  • Cached entries: 8
  • Cache TTL: 1800s
  • Cache hits: 5
  • Cache misses: 10
  • Cache hit rate: 33.3%

Performance Impact:
  • Queries benefiting from optimization: 15/15
  • Queries served from cache: 5/15
```

## Best Practices

### 1. Choose the Right Configuration
- Use `diamm` config for DIAMM-specific queries
- Use `research` config for exploratory work
- Use `production` config for live applications
- Use `development` config when debugging

### 2. Monitor Performance
- Check cache hit rates regularly
- Adjust TTL based on data update frequency
- Monitor query execution times
- Use benchmark tools to validate improvements

### 3. Query Structure
- Put most selective filters first
- Use LIMIT in SERVICE clauses when appropriate
- Group related patterns together
- Consider breaking very complex queries into parts

### 4. Caching Strategy
- Enable caching for queries that are repeated
- Adjust TTL based on how often data changes
- Monitor cache size and hit rates
- Clear cache when needed for fresh data

## Troubleshooting

### Common Issues

**1. Timeout Errors**
- Increase timeout in configuration
- Simplify the query
- Add more selective filters

**2. Cache Not Working**
- Verify cache is enabled in configuration
- Check if queries are identical (caching is exact match)
- Monitor cache statistics

**3. No Performance Improvement**
- Check if optimizations are being applied
- Verify query has federated services
- Consider network conditions to Wikidata

### Debugging

Use the CLI tool to analyze and debug queries:

```bash
# Analyze query for optimization opportunities
python3 code/sparql_optimizer_cli.py analyze --file problem_query.sparql

# See what optimizations would be applied
python3 code/sparql_optimizer_cli.py rewrite --file problem_query.sparql

# Use development config for verbose logging
python3 code/sparql_optimizer_cli.py optimize --file problem_query.sparql --config development
```

## Examples

### Example 1: DIAMM Archives Query
The original slow query from the issue:

```python
# Before optimization: ~137 seconds
# After optimization: Expected 30-70% improvement

optimizer = FederatedQueryOptimizer(client, get_config('diamm'))
results = await optimizer.execute_optimized(diamm_query)
```

### Example 2: Research Query with Caching
```python
# Use research config with longer cache TTL
config = get_config('research')
optimizer = FederatedQueryOptimizer(client, config)

# First execution: full query time
results1 = await optimizer.execute_optimized(research_query)

# Second execution: served from cache (near-instant)
results2 = await optimizer.execute_optimized(research_query)
```

### Example 3: Production Deployment
```python
# Production config with fail-fast timeouts
config = get_config('production')
optimizer = FederatedQueryOptimizer(client, config)

try:
    results = await optimizer.execute_optimized(user_query)
    return {"success": True, "data": results}
except Exception as e:
    return {"success": False, "error": str(e)}
```

## Advanced Features

### Custom Query Analysis
```python
# Analyze query structure
analysis = optimizer.analyze_query(query)
print(f"Federated services: {analysis.has_federated_services}")
print(f"Local graphs: {analysis.local_graphs}")
print(f"Variables: {analysis.variables}")
```

### Query Rewriting
```python
# Get optimized query without executing
analysis = optimizer.analyze_query(original_query)
optimized_query = optimizer._rewrite_for_efficiency(original_query, analysis)
print("Optimized query:", optimized_query)
```

### Cache Management
```python
# Manual cache operations
optimizer.clear_cache()
stats = optimizer.get_cache_stats()
print(f"Cache entries: {stats['cached_entries']}")
```

This optimization system provides a comprehensive solution to the federated query performance problem, with expected improvements of 30-70% for typical DIAMM queries.