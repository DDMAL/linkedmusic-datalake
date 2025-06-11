"""
Asynchronous Python client for querying Wikidata APIs.

Features:
- Execute queries with rate limiting and error handling.
- Perform full-text searches using Wikidata's Elasticsearch API.
- Access wbsearchentities and wbgetentities APIs.
- Supports batching and concurrency for efficient entity data retrieval.

Usage:
- Instantiate with an aiohttp.ClientSession.
- Use async methods to perform searches, queries, and entity fetches.
- Handles raw API calls and processes results into list of dictionaries.

Dependencies:
- aiohttp
- aiolimiter

Example:

    async with aiohttp.ClientSession() as session:
        client = WikidataAPIClient(session)
        results = await client.sparql("SELECT ?item WHERE {?item wdt:P31 wd:Q146}")
        print(results)

"""

from typing import Any, Optional, Union, TypeAlias
import asyncio
import aiohttp
from aiolimiter import AsyncLimiter

# Type aliases allow better type hinting
WikiId: TypeAlias = str
JsonResponse: TypeAlias = dict[str, Any]
WikiEntity: TypeAlias = dict[str, Any]
SparqlResultRow: TypeAlias = dict[str, Any]


class _WikidataAPIClientRaw:
    """
    Base client for interacting with Wikidata APIs.

    Provides asynchronous methods to request different Wikidata API endpoints
    and returns raw JSON responses.
    Handles HTTP errors and rate limiting internally.

    Supported endpoints:
    - Wikidata Query Service (SPARQL)
    - Wikidata Elasticsearch API
    - Wikidata wbsearchentities
    - Wikidata wbgetentities
    """

    def __init__(
        self,
        session: aiohttp.ClientSession,
    ):
        """
        Initialize the WikidataAPIClient with an aiohttp session.

        Args:
            session (aiohttp.ClientSession): An active aiohttp session for making requests.

        Initializes two rate limiters:
            - `limiter_sparql`: For SPARQL queries, allowing 20 requests per second.
            - `limiter_wikidata`: For all other Wikidata API calls, allowing 30 requests per second.
        """
        # Session is user-provided to allow control over reuse and cleanup.
        self.session = session
        self.limiter_sparql = AsyncLimiter(max_rate=20, time_period=1)
        # limiter for all API calls starting with "https://www.wikidata.org/w/api.php"
        self.limiter_wikidata = AsyncLimiter(max_rate=30, time_period=1)

    async def _get(
        self,
        url: str,
        params: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
        timeout: int = 10,
    ) -> Optional[dict[str, Any]]:
        """
        Internal helper method to perform GET requests with consistent error handling.
        Returns the JSON response or None on error.
        """
        try:
            async with self.session.get(
                url,
                params=params or {},
                headers=headers or {},
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ContentTypeError as e:
            print(f"Content type error at {url}: {e}")
            return None
        except aiohttp.ClientConnectionError as e:
            print(f"Connection error at {url}: {e}")
            return None
        except aiohttp.ClientResponseError as e:
            print(f"HTTP error at {url}: Status {e.status}, message: {e.message}")
            return None
        except aiohttp.ClientError as e:
            print(f"Client error at {url}: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error at {url}: {e}")
            return None

    async def sparql_raw(self, query: str, timeout: int = 40) -> JsonResponse:
        """
        Executes a SPARQL query at the Wikidata endpoint.

        Returns raw JSON response, or an empty dictionary on request error.
        """
        url = "https://query.wikidata.org/sparql"
        headers = {"Accept": "application/sparql-results+json"}
        async with self.limiter_sparql:
            data = await self._get(
                url, params={"query": query}, headers=headers, timeout=timeout
            )
            if not data:
                return {}
            else:
                return data

    async def search_raw(
        self, query: str, limit: Optional[int] = 10, timeout: int = 10
    ) -> JsonResponse:
        """
        Queries Wikidata Elasticsearch API.

        Allows for more powerful fuzzy matching than wbsearchentities API.
        Returns raw JSON response, or an empty dictionary on request error.
        """
        url = "https://www.wikidata.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "format": "json",
            "srsearch": str(query),
        }
        if limit:
            params["srlimit"] = str(limit)
        async with self.limiter_wikidata:
            data = await self._get(url, params=params, timeout=timeout)
            if not data:
                return {}
            else:
                return data

    async def wbsearchentities_raw(
        self,
        term: str,
        entity_type: str = "item",
        limit: Optional[int] = 10,
        timeout: int = 10,
    ) -> JsonResponse:
        """
        Queries wbsearchentities API

        Searches for precise matches in names or aliases.
        Returns raw JSON response, or an empty dictionary on request error.
        """
        url = "https://www.wikidata.org/w/api.php"
        params = {
            "action": "wbsearchentities",
            "search": term,
            "language": "en",
            "format": "json",
            "type": entity_type,
        }
        if limit:
            params["limit"] = str(limit)
        async with self.limiter_wikidata:
            data = await self._get(url, params=params, timeout=timeout)
            if not data:
                return {}
            else:
                return data

    async def wbgetentities_raw(
        self,
        *ids_input: Union[str, list[str]],
        props: Union[str, list[str]] = "labels",
        languages: str = "en",
        timeout: int = 10,
    ) -> JsonResponse:
        """
        Queries wbgetentities API.

        Fetches additional information on Wikidata entities using their IDs.
        Returns raw JSON response, or an empty dictionary on request error.
        Up to 50 items can be requested at once.  
        """

        # Flatten ids_input into a single list of strings
        ids: list[str] = []
        for arg in ids_input:
            if isinstance(arg, list):
                ids.extend(arg)
            elif isinstance(arg, str):
                ids.append(arg)
        if len(ids) > 50:
            print("wbgetentities can only handle up to 50 IDs at a time")
            return {}
        # Properties requested simultaneously must be separated by "|"
        # Example: "labels|descriptions|claims"
        props_str = props if isinstance(props, str) else "|".join(props)
        url = "https://www.wikidata.org/w/api.php"
        params = {
            "action": "wbgetentities",
            "ids": "|".join(ids),
            "format": "json",
            "props": props_str,
            "languages": languages,
        }
        async with self.limiter_wikidata:
            data = await self._get(url, params=params, timeout=timeout)
            if data:
                return data
            else:
                return {}


class WikidataAPIClient(_WikidataAPIClientRaw):
    """
    Asynchronous Client for Wikidata APIs

    Provides asynchronous methods to request different Wikidata API endpoints.
    Handles HTTP errors and rate limiting internally.

    Supported endpoints:
    - Wikidata Query Service (SPARQL)
    - Wikidata Elasticsearch API
    - Wikidata wbsearchentities
    - Wikidata wbgetentities

    Inherits from WikidataAPIClientRaw and provides higher-level methods
    that parses raw JSON responses into a list of dictionaries:
        - For SPARQL queries, each dictionary corresponds to a row in the result set.
        - For all other queries, each dictionary contain a single Wikidata entity.

    Methods to fetch raw/unprocessed JSON response remain available.

    Usage example:
    async def main():
        async with aiohttp.ClientSession() as session:
            client = WikidataAPIClient(session)
            await client.wbget_statements("Q91")

    asyncio.run(main())
    """

    async def sparql(
        self,
        query: str,
        timeout: int = 40,
    ) -> list[SparqlResultRow]:
        """
        Execute a SPARQL query and return results as a list of dictionaries.

        Each dictionary represents a SPARQL result row, with variable names as keys.

        Args:
            query: SPARQL query string.
            timeout: Request timeout in seconds (default: 40).

        Returns:
            List of dictionaries, one per SPARQL result row.
        """
        data = await self.sparql_raw(query, timeout=timeout)
        bindings = data.get("results", {}).get("bindings", [])
        results = [{var: row[var]["value"] for var in row} for row in bindings]
        return results

    async def search(
        self, query: str, limit: int = 10, timeout: int = 10
    ) -> list[WikiEntity]:
        """
        Perform a full-text search using Wikidata's Elasticsearch-backed API.

        This method offers better fuzzy matching than `wbsearchentities`,
        but returns only the entity ID and a text snippet.

        Args:
            query: Search term.
            limit: Maximum number of results (default: 10).
            timeout: Request timeout in seconds (default: 10).

        Returns:
            List of dictionaries with keys:
                - "id": Entity ID (e.g., "Q42")
                - "description": Text snippet or matched context
        """
        data = await self.search_raw(query, limit=limit, timeout=timeout)
        matches_list = data.get("query", {}).get("search", [])
        results = []
        # Each match is a dictionary containing a search result
        for match in matches_list:
            match_dict = {
                "id": match.get("title", ""),
                "description": match.get("snippet", ""),
            }
            results.append(match_dict)
        return results

    async def wbsearchentities(
        self,
        term: str,
        entity_type: str = "item",
        limit: Optional[int] = None,
        timeout: int = 10,
    ) -> list[WikiEntity]:
        """
        Searches for entities by name or alias using the wbsearchentities API.

        Searches for precise matches in names or aliases.
        Returns the ID and label of matched entities.

        Args:
            term: Search term.
            entity_type: Type of entity to search ("item"(default) or "property").
            limit: Maximum number of results to return.
            timeout: Request timeout in seconds (default: 10).

        Returns:
            List of dictionaries with keys:
                - "id": Entity ID
                - "label": Label in the language of the search term
        """
        data = await self.wbsearchentities_raw(
            term, entity_type=entity_type, limit=limit, timeout=timeout
        )
        results = []
        # Each entry is a dict containing a search result
        for entry in data.get("search", []):
            results.append(
                {
                    "id": entry.get("id", ""),
                    "label": entry.get("label", ""),
                }
            )
        return results

    async def wbgetentities(
        self,
        *ids_input: Union[str, list[str]],
        props: Union[str, list[str]] = "labels",
        languages: str = "en",
        timeout: int = 10,
    ) -> dict[str, WikiEntity]:
        """
        Fetch Wikidata entities by ID and extract text-based properties as an embedded dictionary.

        Args:
            *ids_input: One or more entity IDs, or lists of IDs.
            props: Single property or list of properties to retrieve (default: "labels").
                Only supports: "labels", "descriptions", "aliases"
            languages: Language code for property values (default: "en").
            timeout: Request timeout in seconds (default: 10).

        Returns:
            dict: Mapping from entity ID to a dictionary of requested properties.
                Example: {"Q42": {"labels": "Douglas Adams", ...}, ...}
        """
        supported_props = {"labels", "descriptions", "aliases"}
        if isinstance(props, str):
            props_list = [props]
        else:
            props_list = props
        invalid_props = [p for p in props_list if p not in supported_props]
        if invalid_props:
            raise ValueError(f"Unsupported props requested: {', '.join(invalid_props)}")

        ids: list[str] = []
        for arg in ids_input:
            if isinstance(arg, list):
                ids.extend(arg)
            elif isinstance(arg, str):
                ids.append(arg)

        # Chunk to max 50 IDs per request
        def chunk(lst: list[str], size: int = 50) -> list[list[str]]:
            return [lst[i : i + size] for i in range(0, len(lst), size)]

        raw_responses = await asyncio.gather(
            *(
                self.wbgetentities_raw(
                    *group, props=props, languages=languages, timeout=timeout
                )
                for group in chunk(ids)
            )
        )

        results: dict[str, WikiEntity] = {}
        for response in raw_responses:
            entities = response.get("entities", {})
            for id_, entity in entities.items():
                # id is stored twice for convenience of the user
                item_dict = {"id": id_}
                for prop in props_list:
                    if prop in ("labels", "descriptions"):
                        item_dict[prop] = entity.get(prop, {}).get(languages, {}).get("value", "")
                    elif prop == "aliases":
                        aliases = entity.get("aliases", {}).get(languages, [])
                        item_dict[prop] = [alias.get("value", "") for alias in aliases]
                results[id_] = item_dict
        return results


    async def wbget_statements(
        self,
        entity_id: str,
        timeout: int = 10,
    ) -> dict[str, list[str]]:
        """
        Fetches claims/statements of a single Wikidata entity by ID.
        
        Uses wbgetentities API.
        Exists as a separate method to simplify the data structure.

        Args:
            entity_id: Single entity ID (e.g., "Q42").
            timeout: Request timeout in seconds (default: 10).

        Returns:
            Dict mapping PIDs (e.g., "P31") to lists of QIDs.
            Only statements whose values are Wikidata entities are included.
            Statements with more complex data types (e.g., dates, quantities, strings) are excluded 
            to avoid overly complex or nested data structures.
        """
        response = await self.wbgetentities_raw(entity_id, props="claims", timeout=timeout)
        entities = response.get("entities", {})
        entity = entities.get(entity_id, {})
        claims = entity.get("claims", {})

        simplified_claims: dict[str, list[str]] = {}
        for p, values in claims.items():
            for statement in values:
                object_list = []
                try:
                    datavalue = statement["mainsnak"]["datavalue"]["value"]
                    if isinstance(datavalue, dict) and "id" in datavalue:
                        
                        object_list.append(datavalue["id"])
                    else:
                        continue
                except KeyError:
                    continue
            if object_list:
                simplified_claims[p] = object_list
        return simplified_claims
