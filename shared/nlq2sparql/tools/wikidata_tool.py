"""Wikidata Tool Functions for NLQ2SPARQL LLM Integrations.

Async helpers that delegate to a loop-safe Wikidata client via the
local integrations adapter. Provides two primary functions:
  - find_entity_id(label) -> QID
  - find_property_id(label) -> PID
"""
from __future__ import annotations

import asyncio
import logging
from functools import lru_cache
from typing import Dict, Optional, Sequence

from ..integrations.wikidata_adapter import (
    get_wikidata_client,
    close_wikidata_client,
)

logger = logging.getLogger(__name__)


async def _get_client():
    """Get a loop-safe Wikidata client via the local adapter."""
    return await get_wikidata_client()


async def _search_entities_precise(term: str, entity_type: str, limit: int = 1):
    client = await _get_client()
    try:
        return await client.wbsearchentities(term, entity_type=entity_type, limit=limit)
    except Exception as e:
        logger.error("wbsearchentities failed for '%s': %s", term, e)
        return []


async def _search_entities_fuzzy(term: str, entity_type: str, limit: int = 5):
    if entity_type != "item":
        return []
    client = await _get_client()
    try:
        return await client.search(term, limit=limit, entity_type="items")
    except Exception as e:
        logger.error("Elastic search failed for '%s': %s", term, e)
        return []


@lru_cache(maxsize=512)
def _normalized_input(s: str) -> str:
    return " ".join(s.strip().split())


def _pick_best_candidate(term: str, candidates: Sequence[Dict]) -> Optional[str]:
    if not candidates:
        return None
    term_lower = term.lower().strip()
    norm = []
    for c in candidates:
        cid = c.get("id") or ""
        label = c.get("label") or c.get("snippet") or ""
        if cid and label:
            norm.append((cid, label))
    if not norm:
        return None
    for cid, label in norm:
        if label.lower() == term_lower:
            return cid
    for cid, label in norm:
        if label.lower().startswith(term_lower):
            return cid
    return norm[0][0]


async def find_entity_id(entity_label: str) -> Optional[str]:
    if not entity_label or not entity_label.strip():
        return None
    term = _normalized_input(entity_label)
    # test suite expects limit=1 call on wbsearchentities
    precise = await _search_entities_precise(term, "item", 1)
    qid = _pick_best_candidate(term, precise)
    if qid:
        return qid
    fuzzy = await _search_entities_fuzzy(term, "item", 5)
    return _pick_best_candidate(term, fuzzy)


async def find_property_id(property_label: str) -> Optional[str]:
    if not property_label or not property_label.strip():
        return None
    term = _normalized_input(property_label)
    precise = await _search_entities_precise(term, "property", 1)
    return _pick_best_candidate(term, precise)


async def _close_session():
    await close_wikidata_client()


class WikidataTool:
    """Lightweight OO wrapper kept for backward compatibility with tests.

    Delegates to module-level async functions.
    """

    async def find_entity_id(self, label: str):  # pragma: no cover simple delegation
        return await find_entity_id(label)

    async def find_property_id(self, label: str):  # pragma: no cover
        return await find_property_id(label)


__all__ = ["find_entity_id", "find_property_id", "WikidataTool"]


if __name__ == "__main__":
    async def _demo():
        print("Entity Bach ->", await find_entity_id("Bach"))
        print("Property composer ->", await find_property_id("composer"))
        await _close_session()

    asyncio.run(_demo())
