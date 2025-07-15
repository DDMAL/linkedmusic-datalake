"""
Tests for WikidataAgent.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, patch
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from agents.wikidata_agent import WikidataAgent


class TestWikidataAgent:
    """Test the WikidataAgent class."""

    @pytest.mark.asyncio
    async def test_agent_uses_tool(self):
        """Test that agent delegates to the tool."""
        agent = WikidataAgent()
        
        with patch.object(agent.tool, 'find_entity_id', return_value="Q789") as mock_tool_entity:
            result = await agent.find_entity_id("test entity")
            assert result == "Q789"
            mock_tool_entity.assert_called_once_with("test entity")

        with patch.object(agent.tool, 'find_property_id', return_value="P789") as mock_tool_property:
            result = await agent.find_property_id("test property")
            assert result == "P789"
            mock_tool_property.assert_called_once_with("test property")

    @pytest.mark.asyncio
    async def test_batch_lookup(self):
        """Test batch lookup functionality."""
        agent = WikidataAgent()
        
        with patch.object(agent, 'find_entity_id', side_effect=["Q1", "Q2"]) as mock_entity:
            with patch.object(agent, 'find_property_id', side_effect=["P1", "P2"]) as mock_property:
                
                results = await agent.lookup_entities_and_properties(
                    entities=["entity1", "entity2"],
                    properties=["prop1", "prop2"]
                )
                
                expected = {
                    "entity:entity1": "Q1",
                    "entity:entity2": "Q2", 
                    "property:prop1": "P1",
                    "property:prop2": "P2"
                }
                
                assert results == expected
