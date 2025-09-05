"""
Tests for Wikidata tool functions.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, patch
from pathlib import Path

# Import wikidata tool using relative import
try:
    from ..tools.wikidata_tool import find_entity_id, find_property_id, WikidataTool
except ImportError:
    # Fallback for when running tests directly
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from tools.wikidata_tool import find_entity_id, find_property_id, WikidataTool


class TestWikidataToolFunctions:
    """Test the standalone tool functions."""

    @pytest.mark.asyncio
    async def test_find_entity_id_success(self):
        """Test successful entity lookup."""
        with patch('tools.wikidata_tool.get_wikidata_client') as mock_get:
            mock_client = AsyncMock()
            mock_client.wbsearchentities.return_value = [{"id": "Q123", "label": "Test Entity"}]
            mock_get.return_value = mock_client

            result = await find_entity_id("test entity")
            assert result == "Q123"
            mock_client.wbsearchentities.assert_called_once_with("test entity", entity_type="item", limit=1)

    @pytest.mark.asyncio
    async def test_find_entity_id_not_found(self):
        """Test entity not found."""
        with patch('tools.wikidata_tool.get_wikidata_client') as mock_get:
            mock_client = AsyncMock()
            mock_client.wbsearchentities.return_value = []
            mock_get.return_value = mock_client

            result = await find_entity_id("nonexistent entity")
            assert result is None

    @pytest.mark.asyncio
    async def test_find_property_id_success(self):
        """Test successful property lookup."""
        with patch('tools.wikidata_tool.get_wikidata_client') as mock_get:
            mock_client = AsyncMock()
            mock_client.wbsearchentities.return_value = [{"id": "P123", "label": "test property"}]
            mock_get.return_value = mock_client

            result = await find_property_id("test property")
            assert result == "P123"
            mock_client.wbsearchentities.assert_called_once_with("test property", entity_type="property", limit=1)

    @pytest.mark.asyncio
    async def test_empty_input(self):
        """Test empty input handling."""
        assert await find_entity_id("") is None
        assert await find_entity_id(None) is None
        assert await find_property_id("") is None
        assert await find_property_id(None) is None


class TestWikidataToolClass:
    """Test the WikidataTool class."""

    @pytest.mark.asyncio
    async def test_class_methods_delegate(self):
        """Test that class methods delegate to functions."""
        tool = WikidataTool()
        
        with patch('tools.wikidata_tool.find_entity_id', return_value="Q456") as mock_find_entity:
            result = await tool.find_entity_id("test")
            assert result == "Q456"
            mock_find_entity.assert_called_once_with("test")

        with patch('tools.wikidata_tool.find_property_id', return_value="P456") as mock_find_property:
            result = await tool.find_property_id("test")
            assert result == "P456"
            mock_find_property.assert_called_once_with("test")
