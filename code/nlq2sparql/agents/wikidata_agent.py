"""
Wikidata Agent

This agent uses the WikidataTool to find QIDs and PIDs for entities and properties 
mentioned in a user's query. It provides an agent-level interface around the tool.
"""

import asyncio
import logging
from typing import Dict, List, Optional
from pathlib import Path
import sys

# Ensure the parent directory is in the path to allow sibling imports
if str(Path(__file__).parent.parent) not in sys.path:
    sys.path.append(str(Path(__file__).parent.parent))

from tools.wikidata_tool import WikidataTool


class WikidataAgent:
    """
    An agent that uses the WikidataTool to find entity and property IDs.
    
    This agent provides a higher-level interface and can be extended with
    additional logic for query analysis, caching, etc.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.tool = WikidataTool()

    async def find_entity_id(self, entity_label: str) -> Optional[str]:
        """
        Finds the QID for a given entity label using the WikidataTool.

        Args:
            entity_label: The name of the entity to search for.

        Returns:
            The QID (e.g., "Q207649") or None if not found.
            
        Raises:
            ValueError: If entity_label is empty or None.
        """
        if not entity_label or not entity_label.strip():
            raise ValueError("Entity label cannot be empty")
            
        return await self.tool.find_entity_id(entity_label.strip())

    async def find_property_id(self, property_label: str) -> Optional[str]:
        """
        Finds the PID for a given property label using the WikidataTool.

        Args:
            property_label: The name of the property to search for.

        Returns:
            The PID (e.g., "P86") or None if not found.
            
        Raises:
            ValueError: If property_label is empty or None.
        """
        if not property_label or not property_label.strip():
            raise ValueError("Property label cannot be empty")
            
        return await self.tool.find_property_id(property_label.strip())

    async def lookup_entities_and_properties(self, entities: List[str], properties: List[str]) -> Dict[str, Optional[str]]:
        """
        Batch lookup of multiple entities and properties with concurrent processing.
        
        Args:
            entities: List of entity labels to look up
            properties: List of property labels to look up
            
        Returns:
            Dictionary mapping labels to their QIDs/PIDs or None
            
        Raises:
            ValueError: If both entities and properties lists are empty.
        """
        if not entities and not properties:
            raise ValueError("At least one entity or property must be provided")
            
        results = {}
        
        # Create concurrent tasks for all lookups
        tasks = []
        
        # Add entity lookup tasks
        for entity in entities:
            if entity and entity.strip():  # Skip empty entities
                task = self._lookup_entity_with_key(entity.strip())
                tasks.append(task)
        
        # Add property lookup tasks
        for prop in properties:
            if prop and prop.strip():  # Skip empty properties
                task = self._lookup_property_with_key(prop.strip())
                tasks.append(task)
        
        # Execute all tasks concurrently
        if tasks:
            completed_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results, handling any exceptions
            for result in completed_results:
                if isinstance(result, Exception):
                    self.logger.error(f"Lookup failed: {result}")
                    continue
                if result:  # result is (key, value) tuple
                    key, value = result
                    results[key] = value
        
        return results
    
    async def _lookup_entity_with_key(self, entity: str) -> tuple[str, Optional[str]]:
        """Helper method to lookup entity and return with prefixed key."""
        try:
            qid = await self.find_entity_id(entity)
            return f"entity:{entity}", qid
        except Exception as e:
            self.logger.error(f"Failed to lookup entity '{entity}': {e}")
            return f"entity:{entity}", None
    
    async def _lookup_property_with_key(self, prop: str) -> tuple[str, Optional[str]]:
        """Helper method to lookup property and return with prefixed key."""
        try:
            pid = await self.find_property_id(prop)
            return f"property:{prop}", pid
        except Exception as e:
            self.logger.error(f"Failed to lookup property '{prop}': {e}")
            return f"property:{prop}", None


async def main():
    """Example usage of the WikidataAgent."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    agent = WikidataAgent()

    # --- Test Case 1: Find an Entity ---
    entity_name = "Guillaume Dufay"
    entity_id = await agent.find_entity_id(entity_name)
    print(f"\nSearch for entity '{entity_name}':")
    if entity_id:
        print(f"  -> Found QID: {entity_id}")
    else:
        print("  -> No QID found.")

    # --- Test Case 2: Find a Property ---
    property_name = "composer"
    property_id = await agent.find_property_id(property_name)
    print(f"\nSearch for property '{property_name}':")
    if property_id:
        print(f"  -> Found PID: {property_id}")
    else:
        print("  -> No PID found.")
        
    # --- Test Case 3: Entity not found ---
    entity_name_fail = "A Completely NonExistent Person"
    entity_id_fail = await agent.find_entity_id(entity_name_fail)
    print(f"\nSearch for non-existent entity '{entity_name_fail}':")
    if entity_id_fail:
        print(f"  -> Found QID: {entity_id_fail}")
    else:
        print("  -> No QID found as expected.")


if __name__ == "__main__":
    asyncio.run(main())
