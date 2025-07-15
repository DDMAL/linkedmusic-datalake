"""
Wikidata Tool

This tool provides functions for interacting with the Wikidata API to find
QIDs and PIDs for entities and properties. It uses the existing `WikidataAPIClient`.

Search Strategy:
- Entity searches (QIDs): Uses fuzzy search (client.search()) for better matching
  of descriptive queries like "William Byrd composer" or "Bach musician"
- Property searches (PIDs): Uses strict search (client.wbsearchentities()) for
  precise property matching like "composer", "birth date", etc.

This is designed to be used by other agents (like a manager agent) as a tool.
"""

import asyncio
import logging
from typing import Optional

import aiohttp
from pathlib import Path
import sys

# Ensure the parent directory is in the path to allow sibling imports
if str(Path(__file__).parent.parent) not in sys.path:
    sys.path.append(str(Path(__file__).parent.parent))

try:
    from wikidata_utils.client import WikidataAPIClient
except ImportError:
    # This fallback is for when running the script directly
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from wikidata_utils.client import WikidataAPIClient


# Create a global logger for this module
logger = logging.getLogger(__name__)


async def find_entity_id(entity_label: str) -> Optional[str]:
    """
    Tool function to find the QID for a given entity label using fuzzy search.
    
    Uses client.search() which provides better matching for descriptive queries
    like "Guillaume Dufay composer" or "William Byrd English composer".
    
    This function is designed to be called by other agents or systems that need
    to look up Wikidata entity IDs.

    Args:
        entity_label: The name of the entity to search for. Can include descriptive
                     terms like "composer", "musician", etc.

    Returns:
        The QID (e.g., "Q207649") or None if not found.
    """
    if not entity_label:
        return None

    session = aiohttp.ClientSession()
    client = WikidataAPIClient(session)
    
    try:
        logger.info(f"Searching for entity: '{entity_label}'")
        results = await client.search(entity_label, entity_type="item", limit=1)
        if results:
            entity_id = results[0].get("id")
            logger.info(f"Found entity ID '{entity_id}' for '{entity_label}'")
            return entity_id
        else:
            logger.warning(f"No entity ID found for '{entity_label}'")
            return None
    except Exception as e:
        logger.error(f"An error occurred while finding entity ID for '{entity_label}': {e}")
        return None
    finally:
        await session.close()


async def find_property_id(property_label: str) -> Optional[str]:
    """
    Tool function to find the PID for a given property label using strict search.
    
    Uses client.wbsearchentities() for precise property matching. Properties
    require exact or near-exact matches (e.g., "composer", "birth date").
    
    This function is designed to be called by other agents or systems that need
    to look up Wikidata property IDs.

    Args:
        property_label: The name of the property to search for.

    Returns:
        The PID (e.g., "P86") or None if not found.
    """
    if not property_label:
        return None

    session = aiohttp.ClientSession()
    client = WikidataAPIClient(session)
    
    try:
        logger.info(f"Searching for property: '{property_label}'")
        results = await client.wbsearchentities(property_label, entity_type="property", limit=1)
        if results:
            prop_id = results[0].get("id")
            logger.info(f"Found property ID '{prop_id}' for '{property_label}'")
            return prop_id
        else:
            logger.warning(f"No property ID found for '{property_label}'")
            return None
    except Exception as e:
        logger.error(f"An error occurred while finding property ID for '{property_label}': {e}")
        return None
    finally:
        await session.close()


class WikidataTool:
    """
    A class wrapper for the Wikidata tool functions.
    
    This provides an object-oriented interface for agents that prefer
    to work with class instances rather than standalone functions.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def find_entity_id(self, entity_label: str) -> Optional[str]:
        """Wrapper for the find_entity_id function."""
        return await find_entity_id(entity_label)

    async def find_property_id(self, property_label: str) -> Optional[str]:
        """Wrapper for the find_property_id function."""
        return await find_property_id(property_label)


async def main():
    """
    Example usage of the Wikidata tool functions.
    
    This demonstrates how other agents can import and use these tools.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    print("=== Testing Wikidata Tool Functions ===")
    
    # --- Test Case 1: Find an Entity using function ---
    entity_name = "Guillaume Dufay"
    entity_id = await find_entity_id(entity_name)
    print(f"\nSearch for entity '{entity_name}' (function):")
    if entity_id:
        print(f"  -> Found QID: {entity_id}")
    else:
        print("  -> No QID found.")

    # --- Test Case 2: Find a Property using function ---
    property_name = "composer"
    property_id = await find_property_id(property_name)
    print(f"\nSearch for property '{property_name}' (function):")
    if property_id:
        print(f"  -> Found PID: {property_id}")
    else:
        print("  -> No PID found.")
        
    # --- Test Case 3: Entity not found ---
    entity_name_fail = "A Completely NonExistent Person"
    entity_id_fail = await find_entity_id(entity_name_fail)
    print(f"\nSearch for non-existent entity '{entity_name_fail}' (function):")
    if entity_id_fail:
        print(f"  -> Found QID: {entity_id_fail}")
    else:
        print("  -> No QID found as expected.")

    print("\n=== Testing WikidataTool Class ===")
    
    # --- Test Case 4: Using the class interface ---
    tool = WikidataTool()
    entity_id_class = await tool.find_entity_id("Bach")
    print(f"\nSearch for entity 'Bach' (class):")
    if entity_id_class:
        print(f"  -> Found QID: {entity_id_class}")
    else:
        print("  -> No QID found.")


if __name__ == "__main__":
    asyncio.run(main())
