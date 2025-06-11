from typing import Generator, Any, Optional, Union, TypeAlias
import re
import asyncio
import aiohttp
from aiolimiter import AsyncLimiter


def print_hyperlink(text: str, link: str) -> str:
    """
    Return a terminal hyperlink string for the given URL and label.
    """
    ESC = "\033"
    start = f"{ESC}]8;;{link}{ESC}\\"
    end = f"{ESC}]8;;{ESC}\\"
    return f"{start}{text}{end}"

# This function is a utility function to format 
def format_wd_entity(item_id, item_label) -> str:
    """
    Format a Wikidata entity into a string with a hyperlink"""
    uri = f"https://www.wikidata.org/entity/{item_id}"
    text = f"{item_label}({item_id})"
    return print_hyperlink(text, uri)

def extract_wd_id(s: str, all_match: bool = False) -> str | list[str] | None:
    """
    Extract Wikidata ID (Q or P followed by digits) from a string.
    
    Returns the last ID as a string if found, else None.
    If all_match is set to True, returns a list of all matches.
    """
    pattern = re.compile(r"Q\d+|P\d+")
    matches = pattern.findall(s)
    if all_match:
        return matches if matches else None
    else:
        return matches[-1] if matches else None


WikiId: TypeAlias = str
JsonResponse: TypeAlias = dict[str, Any]
WikiEntity: TypeAlias = dict[str, Any]
SparqlResultRow: TypeAlias = dict[str, Any]


class WikidataAPIClientRaw:
    """
    Base client for interacting with Wikidata APIs, providing raw API responses.
    """

    def __init__(
        self,
        session: aiohttp.ClientSession,
    ):
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
        Executes a SPARQL query and returns the results as a list of dictionaries.
        Each dictionary corresponds to a row in the result set, with the variable names as keys.
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
        self, query: str, limit: int = 10, timeout: int = 10
    ) -> JsonResponse:
        """
        Wikidata full-text search API backed by Elastic Search.
        More powerful fuzzy matching than wbsearchentities API.
        Will not return the labels, just the ID.
        """
        url = "https://www.wikidata.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "format": "json",
            "srsearch": str(query),
            "srlimit": str(limit),
        }
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
        limit: Optional[int] = None,
        timeout: int = 10,
    ) -> JsonResponse:
        """
        Call the rudimentary wbsearchentities API.

        It searches for precise matches in names or aliases
        and returns a list of {id, label} dicts.
        """
        url = "https://www.wikidata.org/w/api.php"
        params = {
            "action": "wbsearchentities",
            "search": term,
            "language": "en",
            "format": "json",
            "type": entity_type,
        }
        if limit is not None:
            params["limit"] = str(limit)
        async with self.limiter_wikidata:
            data = await self._get(url, params=params, timeout=timeout)
            if not data:
                return {}
            else:
                return data
        # Each entry is a dict containing a search result

    async def wbgetentities_raw(
        self,
        *ids_input: Union[str, list[str]],
        props: Union[str, list[str]] = "labels",
        languages: str = "en",
        timeout: int = 10,
    ) -> JsonResponse:
        """Fetch raw wbgetentities responses for given IDs.
        Returns a dictionary, containing the raw JSON response from the API"""

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
        # Format props
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


class WikidataAPIClient(WikidataAPIClientRaw):
    """
    Client for interacting with Wikidata APIs, providing processed (non-raw) results.
    Inherits from WikidataAPIClientRaw.
    """
    async def sparql(
        self,
        query: str,
        timeout: int = 40,
    ) -> list[SparqlResultRow]:
        """
        Executes a SPARQL query and returns the results as a list of dictionaries.
        Each dictionary corresponds to a row in the result set, with the variable names as keys.
        """
        data = await self.sparql_raw(query, timeout=timeout)
        bindings = data.get("results", {}).get("bindings", [])
        results = [{var: row[var]["value"] for var in row} for row in bindings]
        return results

    async def search(
        self, query: str, limit: int = 10, timeout: int = 10
    ) -> list[WikiEntity]:
        """
        Wikidata full-text search API backed by Elastic Search.
        More powerful fuzzy matching than wbsearchentities API.
        Will not return the labels, just the ID.
        """
        data = await self.search_raw(query, limit=limit, timeout=timeout)
        matches_list = data.get("query", {}).get("search", [])
        results = []
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
        Call the rudimentary wbsearchentities API.

        It searches for precise matches in names or aliasess
        and returns a list of {id, label} dicts.
        """
        data = await self.wbsearchentities_raw(
            term, entity_type=entity_type, limit=limit, timeout=timeout
        )
        # Each entry is a dict containing a search result
        results = []
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
    ) -> Union[list[WikiEntity]]:
        """Fetch and process wbgetentities data into a flat list of entity dicts.
        Props are currently mandatory"""

        ids: list[str] = []
        for arg in ids_input:
            if isinstance(arg, list):
                ids.extend(arg)
            elif isinstance(arg, str):
                ids.append(arg)

        def chunk(lst: list[str], size: int = 50) -> Generator[list[str], None, None]:
            for i in range(0, len(lst), size):
                yield lst[i : i + size]

        raw_responses = await asyncio.gather(
            *(
                self.wbgetentities_raw(
                    *group, props=props, languages=languages, timeout=timeout
                )
                for group in chunk(ids)
            )
        )

        # Ensure that we have a list of properties to iterate over
        if isinstance(props, str):
            props_list = [props]
        else:
            props_list = props

        results: Union[dict[str, dict[str, Any]], list[dict[str, str]]]

        results = []
        for response in raw_responses:
            entities = response.get("entities", {})
            # entity contains information on a single item
            for id_, entity in entities.items():
                item_dict = {}
                for prop in props_list:
                    # Retrieve all properties specified as argument
                    item_dict[prop] = (
                        entity.get(prop, {}).get(languages, {}).get("value", "")
                    )
                    # Add id inside the nested dictionary
                    item_dict["id"] = id_
                    # results would be a list instead of a dictionary
                    results.append(item_dict)

        return results
