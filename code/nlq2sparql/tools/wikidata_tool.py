"""Wikidata Tool Functions for NLQ2SPARQL LLM Integrations

Clean version (no trailing placeholder corruption).
"""
from __future__ import annotations
import asyncio, logging
from functools import lru_cache
from pathlib import Path
from typing import Optional, Sequence
import aiohttp
try:
    from wikidata_utils import WikidataAPIClient
except ImportError:
    import sys
    root = Path(__file__).resolve().parents[2]
    if str(root) not in sys.path:
        sys.path.append(str(root))
    from wikidata_utils import WikidataAPIClient  # type: ignore
logger = logging.getLogger(__name__)
_session: Optional[aiohttp.ClientSession] = None
_client: Optional[WikidataAPIClient] = None
async def _get_client() -> WikidataAPIClient:
    global _session,_client
    if _session is None or _session.closed:
        _session = aiohttp.ClientSession()
        _client = WikidataAPIClient(_session)  # type: ignore[arg-type]
    return _client  # type: ignore[return-value]
async def _search_entities_precise(term: str, entity_type: str, limit: int = 1):
    client = await _get_client()
    try:
        return await client.wbsearchentities(term, entity_type=entity_type, limit=limit)
    except Exception as e:
        logger.error("wbsearchentities failed for '%s': %s", term, e); return []
async def _search_entities_fuzzy(term: str, entity_type: str, limit: int = 5):
    if entity_type != 'item': return []
    client = await _get_client()
    try:
        return await client.search(term, limit=limit, entity_type='items')
    except Exception as e:
        logger.error("Elastic search failed for '%s': %s", term, e); return []
@lru_cache(maxsize=512)
def _normalized_input(s: str) -> str: return ' '.join(s.strip().split())
from typing import Dict

def _pick_best_candidate(term: str, candidates: Sequence[Dict]) -> Optional[str]:
    if not candidates: return None
    term_lower = term.lower().strip()
    norm = []
    for c in candidates:
        cid = c.get('id') or ''
        label = c.get('label') or c.get('snippet') or ''
        if cid and label: norm.append((cid,label))
    if not norm: return None
    for cid,label in norm:
        if label.lower()==term_lower: return cid
    for cid,label in norm:
        if label.lower().startswith(term_lower): return cid
    return norm[0][0]
async def find_entity_id(entity_label: str) -> Optional[str]:
    if not entity_label or not entity_label.strip(): return None
    term = _normalized_input(entity_label)
    # test suite expects limit=1 call on wbsearchentities
    precise = await _search_entities_precise(term,'item',1)
    qid = _pick_best_candidate(term, precise)
    if qid: return qid
    fuzzy = await _search_entities_fuzzy(term,'item',5)
    return _pick_best_candidate(term, fuzzy)
async def find_property_id(property_label: str) -> Optional[str]:
    if not property_label or not property_label.strip(): return None
    term = _normalized_input(property_label)
    precise = await _search_entities_precise(term,'property',1)
    return _pick_best_candidate(term, precise)
async def _close_session():
    global _session
    if _session and not _session.closed: await _session.close()
class WikidataTool:
    """Lightweight OO wrapper kept for backward compatibility with tests.

    Delegates to module-level async functions.
    """
    async def find_entity_id(self, label: str):  # pragma: no cover simple delegation
        return await find_entity_id(label)

    async def find_property_id(self, label: str):  # pragma: no cover
        return await find_property_id(label)

__all__ = ['find_entity_id','find_property_id','WikidataTool']
if __name__ == '__main__':
    async def _demo():
        print('Entity Bach ->', await find_entity_id('Bach'))
        print('Property composer ->', await find_property_id('composer'))
        await _close_session()
    asyncio.run(_demo())
