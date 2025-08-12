"""Wikidata adapter for nlq2sparql.

Purpose: wrap WikidataAPIClient construction and session lifecycle so nlq2sparql
code doesn't import shared libs directly and avoids cross-event-loop reuse.
"""
from __future__ import annotations
import asyncio
import atexit
from typing import Optional
import aiohttp

try:
    # Import from shared lib without modifying it
    from wikidata_utils import WikidataAPIClient  # type: ignore
except Exception as _e:  # pragma: no cover - import error surfaced in tests
    WikidataAPIClient = None  # type: ignore


# Module-level cache, but tied to event loop
_session: Optional[aiohttp.ClientSession] = None
_client: Optional[WikidataAPIClient] = None  # type: ignore[valid-type]
_loop: Optional[asyncio.AbstractEventLoop] = None


async def get_wikidata_client() -> WikidataAPIClient:
    """Return a WikidataAPIClient with loop-aware caching.

    Recreates client/session whenever the running event loop changes to avoid
    pytest loop reuse issues. Does not modify shared wikidata_utils.
    """
    global _session, _client, _loop
    loop = asyncio.get_running_loop()
    if _client is None or _session is None or _session.closed or _loop is not loop:
        if _session and not _session.closed:
            try:
                await _session.close()
            except Exception:
                pass
        _session = aiohttp.ClientSession()
        if WikidataAPIClient is None:  # pragma: no cover
            raise RuntimeError("wikidata_utils.WikidataAPIClient not available")
        _client = WikidataAPIClient(_session)  # type: ignore[arg-type]
        _loop = loop
    return _client  # type: ignore[return-value]


async def close_wikidata_client():
    """Close the cached session and reset references (for tests/shutdown)."""
    global _session, _client, _loop
    if _session and not _session.closed:
        await _session.close()
    _session = None
    _client = None
    _loop = None


__all__ = ["get_wikidata_client", "close_wikidata_client"]


# Best-effort cleanup on process exit to avoid unclosed session warnings.
def _close_session_at_exit() -> None:
    try:
        # If a loop is available and running, schedule async close; otherwise run a tiny loop.
        if _session and not _session.closed:
            try:
                loop = _loop or asyncio.get_event_loop()
            except RuntimeError:
                loop = None  # no loop

            if loop and loop.is_running():
                loop.create_task(close_wikidata_client())
            else:
                try:
                    asyncio.run(close_wikidata_client())
                except RuntimeError:
                    # Event loop policy/platform oddities; ignore at exit
                    pass
    except Exception:
        # Swallow any exit-time errors
        pass


atexit.register(_close_session_at_exit)
