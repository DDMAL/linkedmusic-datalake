# Understanding Different Wikidata APIs

This short guide is meant to be an introduction to different Wikidata APIs that can be useful to the LinkedMusic project.

The APIs covered in this guide are:

- Wikidata wbgetentities (Entity retrieval by ID)
- Wikidata wbsearchentities (Entity search by label or alias)
- Wikidata Search (Full-text search)
- Wikidata Query Service (SPARQL endpoint)

# 1. The difference between Wikidata, Wikibase, MediaWiki

- [MediaWiki](https://en.wikipedia.org/wiki/MediaWiki) is the engine/backend/platform that powers Wikipedia and other "Wiki-" projects. It should not be confused with [Wikimedia](https://en.wikipedia.org/wiki/Wikimedia_Foundation), which is the movement/organization in charge of Wikipedia, Wiktionary, Wikidata and other similar projects. The correct wording would be "Wikipedia is a Wikimedia project powered by MediaWiki".

- [Wikibase](https://en.wikipedia.org/wiki/Wikibase) is a set of MediaWiki extensions. Wikibase provides MediaWiki with the ability to store and manage [semi-structured data](https://en.wikipedia.org/wiki/Semi-structured_data). For example, it defines the concept of Entities and Properties.

- [Wikidata](https://en.wikipedia.org/wiki/Wikidata) is a Wikimedia project powered by MediaWiki + Wikibase. It is often referred to as an "instance of" Wikibase.

## 1.1 Where to find API documentation?

- Some Wikidata APIs are available to all **MediaWiki instances**; these are documented in the [General MediaWiki API page](https://www.mediawiki.org/wiki/API:Main_page). These APIs have in common the fact that they can be reached at `/w/api.php` after the domain name. In the context of Wikidata, you can find more detailed documentation of these APIs at https://www.wikidata.org/w/api.php.

- Some Wikidata APIs are available only to **Wikibase instances**; these are documented at the [MediaWiki page on Wikibase APIs](https://www.mediawiki.org/wiki/Wikibase/API). These APIs would also be reached at `/w/api.php` after the domain name. In the context of Wikidata, you can likewise find more detailed documentation of these APIs at https://www.wikidata.org/w/api.php.

- Some Wikidata APIs are available just to Wikidata (e.g. https://query.wikidata.org/); these are documented at the [Wikidata Data Access page](https://www.wikidata.org/wiki/Wikidata:Data_access#).

# 2. Introducing Four Wikidata APIs

## 2.1 wbgetentities

- It allows retrieving information about a Wikidata entity using its QID/PID, which is very similar to retrieving an entity's Wikidata page (e.g. https://www.wikidata.org/wiki/Q9294).
- It also allows retrieving multiple Wikidata entities at a time (their IDs must be separated by "|"). It is recommended to make one call for multiple entities instead of making multiple calls.

- Example query: https://www.wikidata.org/w/api.php?action=wbgetentities&ids=Q1|Q42&props=descriptions|labels|claims&languages=en|de|fr

- Help page: https://www.wikidata.org/w/api.php?action=help&modules=wbgetentities

- Basic Parameters:

  - `action`: the API action you are using (`wbgetentities` in this case)
  - `ids` (required): QID/PID of entities you want to retrieve (e.g. `Q2`; `Q23|Q340|Q22222`)
  - `props`: information you want to retrieve (e.g. `labels`, `labels|descriptions`)
  - `languages`: output languages (two-letter code) (e.g. `en`)

- Note: The keywords of this API are almost all plural (e.g. ids, labels, languages).
- Note: Amongst the retrieveable `props`, "claims" (statements) are significantly more difficult to parse than "labels", "descriptions", and "aliases".

## 2.2 wbsearchentities

- wbsearchentities looks for an entity whose label or alias exactly matches the search term.
- wbsearchentities, unlike the [Wikidata Search Page](https://www.wikidata.org/wiki/Special:Search), doesn't allow any fuzzy matching. Although, to be fair, Wikidata's ElasticSearch fuzzy-matching is not very fuzzy either.

- Example query: https://www.wikidata.org/w/api.php?action=wbsearchentities&search=abc&language=en&limit=1

- Help page: https://www.wikidata.org/w/api.php?action=help&modules=wbsearchentities

- Basic parameters:

  - `action` (required): the API action you are using (`wbsearchentities` in this case)
  - `search` (required): string to look up (e.g. "napoléon")
  - `language` (required): language (two-letter code) of the label or aliases to match against (e.g. "fr")
  - `type` (default = "item"): type of entity to search for (e.g. "item", "property")
  - `limit`: number of results to return (e.g. "5")

- Note: Unlike wbgetentities, the keywords in wbsearchentities are singular (e.g. language, label).
- Note: wbsearchentities retrieves the label of any entity it finds, unlike Wikidata Search, which we will discuss in the next section.

## 2.3 Wikidata Search

- This performs full-text search (with fuzzy matching) on Wikidata entities. This is sould be identical to using the [Wikidata Search Page](https://www.wikidata.org/wiki/Special:Search).

- Example query: https://www.wikidata.org/w/api.php?action=query&list=search&srsearch=Earl+Warren&&format=json

- Help page: https://www.wikidata.org/w/api.php?action=help&modules=query%2Bsearch

- Basic Parameters:

  - `action`: the API action you are using (`query` in this case)
  - `list`: the API sub-action you are using on top of the API action (`search` in this case)
  - `srsearch` (required): the string to query (e.g. "napoleon")
  - `srslimit`: number of results to return (e.g. "5")
  - `srsnamespace` (default = 0): the type of entity to search for (e.g. "0" for items, "120" for properties)

- Note: The API does not include labels in its response. Even with `srprop=redirecttitle`, only the QID is returned as the title — not the actual label.

### 2.3.1 CirrusSearch Keywords

The official name of the extension that implements ElasticSearch across all Wikimedia projects is [CirrusSearch](https://www.mediawiki.org/wiki/Help:Extension:CirrusSearch). Wikidata's CirrusSearch extension has an extension on top of it called [WikibaseCirrusSearch](https://www.mediawiki.org/wiki/Help:Extension:WikibaseCirrusSearch).

WikibaseCirrusSearch comes with keywords that can help filter the query. For example, `haswbstatement:P31=Q5` would filter the results such that only instances of human are returned.

When calling https://www.wikidata.org/w/api.php?action=query&list=search, it is possible to include CirrusSearch keywords in the search string.

- Example query: `https://www.wikidata.org/w/api.php?action=query&list=search&srsearch=Earle+Warren+haswbstatement:P106=Q15981151&format=json`

## 2.4 Wikidata Query Service

- This performs a SPARQL query at Wikidata's SPARQL endpoint. 

- Example query: https://query.wikidata.org/sparql?query=SELECT%20%3Fitem%20%3FitemLabel%20WHERE%20%7B%20%3Fitem%20wdt%3AP31%20wd%3AQ5%20.%20SERVICE%20wikibase%3Alabel%20%7B%20bd%3AserviceParam%20wikibase%3Alanguage%20%22en%22.%20%7D%20%7D%20LIMIT%205&format=json

- Help page: https://www.wikidata.org/wiki/Wikidata:SPARQL_query_service#Interfacing

- Basic Parameters:
  - `query`: the SPARQL query to run
  - `format` (default = "xml"): the format of the response (e.g. "json", "ttl")

# 3. Using WikidataAPIClient

WikidataAPIClient is a Python class which provides async methods to call the four Wikidata APIs described above.

## 3.1 Importing WikidataAPIClient

- WikidataAPIClient can be directly imported from the `wikidata_utils` package, located in `/code/`.
- `from wikidata_utils import WikidataAPIClient` or any similar relative import is only guaranteed to work if the working directory is `/` or `/code`. Thus, all scripts utilizing WikidataAPIClient are expected to be run from `/` or `/code`. (Our previous standard expected the script to be run from its own directory: we should change it. See [Issue 279](https://github.com/DDMAL/linkedmusic-datalake/issues/279))

## 3.2 Using WikidataAPIClient

- Functionalities overview:

  - The class simplifies making asynchronous requests to various Wikidata API endpoints.
  - It parses raw JSON responses into simpler data types (e.g. list of dictionaries).
  - It handles basic HTTP errors.
  - It has built-in rate limiting to comply with Wikidata usage policies (although Wikidata doesn't have a hard rate limit, users are advised to make fewer than 30 requests per second).

- Usage example:

  ```python
  from wikidata_utils import WikidataAPIClient
  import asyncio
  import aiohttp

  async def main():
      async with aiohttp.ClientSession() as session:
          client = WikidataAPIClient(session)
          results = await client.search("capital of", limit=10, entity_type="property", timeout=10)
          print(results)
        
        # Output example:
        # [
        #   {'id': 'P1376', 'snippet': 'country, state, department, canton or other administrative division of which the municipality is the governmental seat'},
        #   {'id': 'P36', 'snippet': ...},
        #   {'id': ..., 'snippet': ...},
        #   ...
        # ]
               
  asyncio.run(main())
  ```

## 3.3 Implementation Ideas

### 3.3.1 "Productivity Tools"
- `WikidataAPIClient` is currently implemented in `code/prop_cli.py`, a command-line interface to assist mapping properties against Wikidata (read more about it [here](./rdf_property_mapping_guide.md)).
- The client is also implemented in `add_labels.py` (will appear in a separate pull request), which adds Wikidata labels as comments next to PIDs in `rdf_config` files.
- Similar "productivity tools" could be developed to make other parts of our workflow more efficient.

### 3.3.2 Custom Reconciliation Logic

Another potential application of this API is in the development of custom reconciliation logic. 
- Having our own reconciliation service (which we can connect to OpenRefine) would give us much more opportunity to fine-tune match scoring, which (hopefully) would increase reconciliation accuracy. 
- It is also likely faster than OpenRefine's built-in reconciliation service.

- Example of custom reconciliation logic for performers on Dig That Lick:

  1. Search performer name using Wikidata Search API.
  2. For each match, retrieve claims (e.g. statements) using `wbgetentities`. Assign higher scores to entities with `occupation = jazz musician`.
  3. Give bonus scores to people with a high number of music-related external identifiers (e.g. Grove Music Online ID).
  4. Calculate final score based on Levenshtein distance (i.e. how closely two words match each other).

- Currently, it’s difficult to apply even a simple reconciliation logic like this in OpenRefine — OpenRefine simply struggles to execute custom logic properly and resists being refined.
