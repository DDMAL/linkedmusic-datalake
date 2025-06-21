"""
Asynchronous Python client for querying Wikidata APIs.

Supported APIs:
- Wikidata Query Service (SPARQL)
- Wikidata Elasticsearch API  (Full-text search)
- Wikidata wbsearchentities (Entity search by label or alias)
- Wikidata wbgetentities (Entity retrieval by ID)

Features:
- Built-in rate limiting to comply with Wikidata usage policies
- Structured JSON parsing 
- Common HTTP error handling
- Support for asynchronous requests using asyncio and aiohttp

Dependencies:
- aiohttp
- aiolimiter

Usage:
- Instantiate WikidataAPIClient with an existing aiohttp.ClientSession
- Use the client's async methods to perform entity searches, SPARQL queries, and QID/PID-based fetches.

Example:
    async with aiohttp.ClientSession() as session:
        client = WikidataAPIClient(session)
        results = await client.search("capital of", limit=10, entity_type="property", timeout=10)
        print(results)

"""

from typing import Any, Optional, Union, TypeAlias
import logging
import asyncio
import aiohttp
from aiolimiter import AsyncLimiter

# Type aliases allow more informative type hinting
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
        Asking the user to provide session to allow their control over session reuse.

        Args:
            session (aiohttp.ClientSession): An active aiohttp session for making requests.

        Initializes two rate limiters:
            - `limiter_sparql`: For SPARQL queries, allowing 20 requests per second.
            - `limiter_wikidata`: For all other Wikidata API calls, allowing 30 requests per second.
        """
        
        self.session = session
        self.limiter_sparql = AsyncLimiter(max_rate=20, time_period=1)
        # limiter for all API calls starting with "https://www.wikidata.org/w/api.php"
        self.limiter_wikidata = AsyncLimiter(max_rate=30, time_period=1)
        self.logger = logging.getLogger(__name__)

    async def _get(
        self,
        url: str,
        params: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
        timeout: int = 10,
    ) -> Optional[dict[str, Any]]:
        """
        Internal helper method to perform HTTP GET requests with consistent error handling.
        Returns either the JSON response or None on error.
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
            self.logger.error("Content type error at %s: %s", url, e)
            return None
        except aiohttp.ClientConnectionError as e:
            self.logger.error("Connection error at %s: %s", url, e)
            return None
        except aiohttp.ClientResponseError as e:
            self.logger.error("HTTP error at %s: Status %s, message: %s", url, e.status, e.message)
            return None
        except aiohttp.ClientError as e:
            self.logger.error("Client error at %s: %s", url, e)
            return None
        except Exception as e:
            self.logger.error("Unexpected error at %s: %s", url, e)
            return None

    async def sparql_raw(self, query: str, timeout: int = 60) -> JsonResponse:
        """
        Executes a SPARQL query at Wikidata Query Service.

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
        self, query: str, limit: Optional[int] = 10, entity_type: str = "item", timeout: int = 10
    ) -> JsonResponse:
        """
        Queries Wikidata Elasticsearch API.

        Allows for more powerful fuzzy matching than wbsearchentities API.
        Returns raw JSON response, or an empty dictionary on request error.
        
        By default, the query searches for Wikidata entities ("items") and returns up to 10 results
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
        if entity_type == "item":
            params["srnamespace"] = "0"
        elif entity_type == "property":
            params["srnamespace"] = "120"

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

        By default, the query searches for Wikidata entities ("items") and returns up to 10 results
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

        Be default, only the English labels of the entities are returned.
        """

        # Flatten ids_input into a single list of strings
        ids: list[str] = []
        for arg in ids_input:
            if isinstance(arg, list):
                ids.extend(arg)
            elif isinstance(arg, str):
                ids.append(arg)
        if len(ids) > 50:
            self.logger.error("wbgetentities can only handle up to 50 IDs at a time")
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

    Methods:
    - Raw methods (search_raw) fetch raw JSON response from the APIs. 
    - Higher-level methods (search) return parsed API responses. 
    - All methods are coroutines and must be awaited.
    
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
        self, query: str, limit: int = 10, entity_type: str = "", timeout: int = 10
    ) -> list[WikiEntity]:
        """
        Perform a full-text search using Wikidata's ElasticSearch API.

        This method offers better fuzzy matching than `wbsearchentities`,
        but returns only the entity ID and a text snippet.

        Args:
            query: Search term.
            limit: Maximum number of results (default: 10).
            timeout: Request timeout in seconds (default: 10).

        Returns:
            List of dictionaries with keys:
                - "id": ID (e.g. "Q42")
                - "snippet": Text snippet matching the search term
        """
        data = await self.search_raw(query, limit=limit,entity_type=entity_type,timeout=timeout)
        matches_list = data.get("query", {}).get("search", [])
        results = []
        # Each match is a dictionary containing a search result
        for match in matches_list:
            match_dict = {
                "id": match.get("title", "").split(":")[-1],  # ID can be in the format "Property:P134"
                "snippet": match.get("snippet", ""),
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
                   Example: [{"id": "Q42", "label": "Douglas Adams"}, {"id":..., "label": ...}]
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
        Fetch Wikidata entities by ID and returns requested "props" an embedded dictionary.

        Args:
            *ids_input: One or more entity IDs, or lists of IDs.
            props: Prop or list of props to retrieve (default: "labels").
                Only supports: "labels", "descriptions", "aliases"
            languages: Language code of props to retrieve(default: "en").
            timeout: Request timeout in seconds (default: 10).

        Returns:
            dict: Mapping from entity ID to a dictionary of requested props
            - The keys of the returned dictionary are entity IDs (e.g. "Q42"),
            - the values are dictionaries containing "props" (e.g. "labels", "descriptions", "aliases").
                Example: {"Q42": {"labels": "Douglas Adams", ...}, ...}
        
        Note:
            - wbgetentities uses "labels" whereas wbsearchentities uses "label"
        """
        supported_props = {"labels", "descriptions", "aliases"}
        if isinstance(props, str):
            # Ensure that there will be no iteration over a string
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
                item_dict = {}
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
        Fetches claims/statements about a single Wikidata entity using wbgetentities.

        - Exists as a separate method because the JSON response structure is different.
        - Allows fetching only one entity at a time to simplify the return type. 
        - Only returns statements in which the object is a Wikidata entity 

        Args:
            entity_id: Single entity ID (e.g. "Q42").
            timeout: Request timeout in seconds (default: 10).

        Returns:
            dict: mapping from PID to lists of QIDs.
                - Each PID is the predicate of the statement.
                - Each QID is an object of a statement with that PID.
                Example: {"P25": ["Q66671"], "P279": ["Q146", "Q42"]}
            

        """
        response = await self.wbgetentities_raw(entity_id, props="claims", timeout=timeout)
        entities = response.get("entities", {})
        entity = entities.get(entity_id, {})
        claims = entity.get("claims", {})

        results: dict[str, list[str]] = {}
        for prop, values in claims.items():
            object_list = []
            for statement in values:
                try:
                    datavalue = statement["mainsnak"]["datavalue"]["value"]
                    if isinstance(datavalue, dict) and "id" in datavalue:
                        object_list.append(datavalue["id"])
                    else:
                        continue
                except KeyError:
                    continue
            if object_list:
                results[prop] = object_list
        return results
