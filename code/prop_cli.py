"""
A simple command-line interface to assist reconciling against Wikidata properties.

Supports:
- Basic and fuzzy search of Wikidata entities (items and properties).
- Finding forward/backward relationships (predicates) between two entities.
- Listing all predicates (forward and backward) associated with a single entity.
"""

import asyncio
import readline  # type: ignore[import-untyped]
import aiohttp
from wikidata_utils import WikidataAPIClient, build_wd_hyperlink, extract_wd_id


def print_heading(title: str) -> None:
    """
    Print a formatted heading with the given title.
    Includes separators for visual clarity in CLI output.

    Args:
        title (str): The heading title to print.
    """
    print("\n" + "=" * 40 + "\n")
    print(title)
    print("-" * 40 + "\n")


def print_separator() -> None:
    """
    Print a simple horizontal separator line for CLI output.
    """
    print("-" * 40 + "\n")


async def lookup_term(term: str, client: WikidataAPIClient, limit: int = 1) -> str | None:
    """
    Attempt to resolve a human-readable search term to a Wikidata QID.
    Tries:
    - Direct QID match via regex
    - Exact match via wbsearchentities
    - Fuzzy match via search API

    Args:
        term (str): The search term or possible QID.
        client (WikidataAPIClient): An initialized Wikidata API client.
        limit (int): Maximum number of results to return per search.

    Returns:
        str | None: The resolved QID if found, otherwise None.
    """
    if match := extract_wd_id(term.upper()):
        return match
    elif result := await client.wbsearchentities(term, limit=limit):
        return result[0]["id"]
    elif result := await client.search(term, limit=limit):
        return result[0]["id"]
    else:
        print(f"No results found for term: {term}")
        return None


async def find_relation(client: WikidataAPIClient, term1: str, term2: str) -> None:
    """
    Find and print all Wikidata properties connecting two entities:
    - Forward (term1 → term2)
    - Backward (term2 → term1)

    Args:
        client (WikidataAPIClient): Initialized Wikidata API client.
        term1 (str): First entity (subject or object).
        term2 (str): Second entity (subject or object).
    """
    qid1, qid2 = await asyncio.gather(
        lookup_term(term1, client),
        lookup_term(term2, client),
    )
    if not qid1 or not qid2:
        print_separator()
        return

    triples = ["?item1 ?property ?item2.", "?item2 ?property ?item1."]
    queries = [
        f"""
        SELECT ?property ?propLabel WHERE {{
          VALUES (?item1 ?item2) {{ (wd:{qid1} wd:{qid2}) }}
          {triple}
          ?prop wikibase:directClaim ?property
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }}
        """
        for triple in triples
    ]

    sparql_tasks = [client.sparql(query) for query in queries]
    item_label_task = client.wbgetentities(qid1, qid2)
    forward_props, backward_props, qid_labels = await asyncio.gather(
        *sparql_tasks, item_label_task
    )

    entity1 = build_wd_hyperlink(qid1, qid_labels[qid1].get("labels", ""))
    entity2 = build_wd_hyperlink(qid2, qid_labels[qid2].get("labels", ""))
    if forward_props:
        print_heading("Forward properties")
        for row in forward_props:
            pid = extract_wd_id(row["property"])
            label = row["propLabel"]
            entity = build_wd_hyperlink(pid, label)
            print(f"{entity1}  {entity}  {entity2}")
    if backward_props:
        print_heading("Backward properties")
        for row in backward_props:
            entity = build_wd_hyperlink(
                extract_wd_id(row["property"]), row["propLabel"]
            )
            print(f"{entity2}  {entity}  {entity1}")
    if not forward_props and not backward_props:
        print_separator()
        print(f"No properties found between {entity1} and {entity2}")
    print_separator()


async def find_all_predicates(client: WikidataAPIClient, term: str) -> None:
    """
    Show all forward and backward predicates associated with a given entity.

    - Forward predicates are retrieved via wbget_statements.
    - Backward predicates are found via a SPARQL query for incoming triples.

    Args:
        client (WikidataAPIClient): An initialized Wikidata API client.
        term (str): The search term or QID.
    """
    qid = await lookup_term(term, client)
    if not qid:
        print_separator()
        return

    forward_relationships = await client.wbget_statements(qid)
    forward_ids_set = set()
    for pid, objects in forward_relationships.items():
        forward_ids_set.add(pid)
        if objects:
            forward_ids_set.add(objects[0])

    forward_ids_list = list(forward_ids_set)
    labels_dict = await client.wbgetentities(qid, forward_ids_list, props="labels")

    backward_query = f"""
    SELECT ?property ?propLabel ?example ?exampleLabel WHERE {{
    {{
        SELECT ?property (SAMPLE(?subject) AS ?example) WHERE {{
        ?subject ?property wd:{qid} .
        }}
        GROUP BY ?property
    }}
    ?prop wikibase:directClaim ?property .
    SERVICE wikibase:label {{
        bd:serviceParam wikibase:language "en".
    }}
    }}
    """
    backward_props = await client.sparql(backward_query)

    entity = build_wd_hyperlink(qid, labels_dict.get(qid, {}).get("labels", term))

    if forward_relationships:
        print_heading("Forward predicates (as subject)")
        for pid, objects in forward_relationships.items():
            prop_label = labels_dict.get(pid, {}).get("labels", pid)
            example = objects[0] if objects else ""
            example_label = labels_dict.get(example, {}).get("labels", example)
            pred = build_wd_hyperlink(pid, prop_label)
            ex = build_wd_hyperlink(example, example_label)
            print(f"{entity}  \033[32m{pred}\033[0m  {ex}")

    if backward_props:
        print_heading("Backward predicates (as object)")
        for row in backward_props:
            pid = extract_wd_id(row["property"])
            label = row.get("propLabel") or pid
            example = extract_wd_id(row.get("example", ""))
            example_label = row.get("exampleLabel", "")
            pred = build_wd_hyperlink(pid, label)
            ex = build_wd_hyperlink(example, example_label) if example else ""
            print(f"{ex}  \033[32m{pred}\033[0m  {entity}")

    if not forward_relationships and not backward_props:
        print_separator()
        print(f"No predicates found for {entity}")

    print_separator()


async def basic_search(client: WikidataAPIClient, term: str, entity_type: str = "property") -> None:
    """
    Perform a basic and fuzzy search for a term using both wbsearchentities and search APIs.
    Ensures up to 5 unique results by combining exact and fuzzy search.

    Args:
        client (WikidataAPIClient): An initialized API client.
        term (str): The search term to look up.
        entity_type (str): Optional. One of "property", "item", etc. Defaults to "property".
    """
    results = await client.wbsearchentities(term, limit=5, entity_type=entity_type)
    seen_ids = {result["id"] for result in results}

    if results:
        print_heading(f'Search results for: "{term}"')
        for pos, result in enumerate(results, 1):
            entity = build_wd_hyperlink(result["id"], result.get("label", ""))
            print(f"Result {pos}: {entity}")

    
    fuzzy_results = await client.search(term, limit=5, entity_type=entity_type)
    unique_fuzzy = []
    for res in fuzzy_results:
        id_ = res.get("id")
        if id_ not in seen_ids:
            unique_fuzzy.append(res["id"])
            # In case the code is extended in the future
            seen_ids.add(res["id"])
    
    if unique_fuzzy:
        display_fuzzy = unique_fuzzy[:5 - len(results)]
        labels = await client.wbgetentities(display_fuzzy, props="labels")
        for pos, id_ in enumerate(display_fuzzy, len(results) + 1):
            label = labels.get(id_, {}).get("labels", "")
            entity = build_wd_hyperlink(id_, label)
            print("\033[35m" + f"Result {pos}: {entity}" + "\033[0m")

    if not results and not unique_fuzzy:
        print(f"No results found for term: {term}")
    print_separator()



async def fuzzy_search(client: WikidataAPIClient, term: str) -> None:
    """
    Perform a fuzzy search for a Wikidata term using the general search API.

    Args:
        client (WikidataAPIClient): Initialized API client.
        term (str): The fuzzy term to search for.
    """
    results = await client.search(term, limit=5)
    if not results:
        print(f"No results found for term: {term}")
        return None

    ids = [result["id"] for result in results if "id" in result]
    labels = await client.wbgetentities(ids, props="labels")

    print_heading(f'Fuzzy search results for: "{term}"')
    for position, id_ in enumerate(ids, 1):
        entity = build_wd_hyperlink(id_, labels.get(id_, {}).get("labels", ""))
        print(f"Result {position}: {entity}")
    print_separator()


async def main():
    """
    Entry point for the CLI application.
    Handles user input and calls appropriate search or relationship functions.
    
    Commands:
    - <term1>, <term2>: Show all relations between two entities.
        Example: 
            paris, france
            France(Q142)  capital(P36)  Paris(Q90)
            Paris(Q90)  capital of(P1376)  France(Q142)
    - <term>: Search for a property.
        Example:
            capital
            Result 1: capital(P36)
            Result 2: capital of(P1376)
    - --q <term>: Search for items instead of properties.
        Example:
            --q Paris
            Result 1: Paris(Q90)
            Result 2: Paris Saint-Germain FC(Q483020)
    - --r <term>: Show all predicates that have been used for that entity with an example triple.
        Example:
            --r Paris
            Paris(Q90)  part of(P361)  Île-de-France(Q13917)
            Claude Monet(Q296)  place of birth(P19)  Paris(Q90)

    'exit' or 'quit': End the session.
    """
    async with aiohttp.ClientSession() as session:
        client = WikidataAPIClient(session)
        while True:
            user_input = input(
                "\033[91mEnter a term, two terms (comma-separated), or a flag (--q, --r), or 'exit': \033[0m"
            ).strip()

            if user_input.lower() in {"exit", "quit"}:
                print("Exiting...")
                break

            elif user_input.startswith("--r"):
                term = user_input[3:].strip()
                if not term:
                    print("Please provide a search term after --r")
                    continue
                await find_all_predicates(client, term)
                continue

            elif user_input.startswith("--q"):
                term = user_input[3:].strip()
                if not term:
                    print("Please provide a search term after --q")
                    continue
                await basic_search(client, term, entity_type="item")
                continue

            terms = [term.strip() for term in user_input.split(",")]

            if len(terms) == 1:
                await basic_search(client, terms[0])
                continue
            elif len(terms) == 2:
                await find_relation(client, terms[0], terms[1])
                continue
            else:
                print("Examples: 'paris', 'paris, france', '--r paris', '--q france', or 'exit'")


if __name__ == "__main__":
    asyncio.run(main())
