"""
Example: How a Manager Agent could use the Wikidata Tool

This demonstrates how other agents (like a manager agent using Gemini function calling)
could import and use the Wikidata tool functions.
"""

import asyncio
import logging
from pathlib import Path

# Import tools using relative imports
try:
    from ..tools.wikidata_tool import find_entity_id, find_property_id, WikidataTool
except ImportError:
    # Fallback for when running directly
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from tools.wikidata_tool import find_entity_id, find_property_id, WikidataTool


async def manager_agent_example():
    """
    Example of how a manager agent might use the Wikidata tools.
    
    This could be integrated with Gemini function calling where the manager
    agent decides when to call these functions based on user queries.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    print("=== Manager Agent Example: Processing a user query ===")
    
    # Simulate a user query about a composer
    user_query = "Tell me about works by Guillaume Dufay"
    print(f"User Query: '{user_query}'")
    
    # The manager agent analyzes the query and identifies entities/properties needed
    entities_to_lookup = ["Guillaume Dufay"]
    properties_to_lookup = ["composer", "work"]
    
    print(f"\nManager Agent identified:")
    print(f"  Entities: {entities_to_lookup}")
    print(f"  Properties: {properties_to_lookup}")
    
    # Look up entities
    print(f"\n--- Looking up entities ---")
    entity_results = {}
    for entity in entities_to_lookup:
        qid = await find_entity_id(entity)
        entity_results[entity] = qid
        print(f"  {entity} -> {qid}")
    
    # Look up properties
    print(f"\n--- Looking up properties ---")
    property_results = {}
    for prop in properties_to_lookup:
        pid = await find_property_id(prop)
        property_results[prop] = pid
        print(f"  {prop} -> {pid}")
    
    # Manager agent could now use these QIDs/PIDs to build a SPARQL query
    print(f"\n--- Results for SPARQL query construction ---")
    print(f"Entity QIDs: {entity_results}")
    print(f"Property PIDs: {property_results}")
    
    # Example of how this could be used in SPARQL
    guillaume_qid = entity_results.get("Guillaume Dufay")
    composer_pid = property_results.get("composer")
    
    if guillaume_qid and composer_pid:
        sparql_fragment = f"""
        ?work wdt:{composer_pid} wd:{guillaume_qid} .
        """
        print(f"\nExample SPARQL fragment:")
        print(f"  {sparql_fragment.strip()}")
    
    return entity_results, property_results


async def batch_lookup_example():
    """
    Example of using the WikidataTool class for batch operations.
    """
    print(f"\n=== Batch Lookup Example ===")
    
    tool = WikidataTool()
    
    # Simulate looking up multiple entities at once
    entities = ["Mozart", "Beethoven", "Bach"]
    results = []
    
    for entity in entities:
        qid = await tool.find_entity_id(entity)
        results.append((entity, qid))
    
    print(f"Batch lookup results:")
    for entity, qid in results:
        print(f"  {entity} -> {qid}")
    
    return results


if __name__ == "__main__":
    asyncio.run(manager_agent_example())
    asyncio.run(batch_lookup_example())
