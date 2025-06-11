"""Utilities for interacting with Wikidata SPARQL endpoint and search API calls."""

import asyncio

# readline helps user navigate using left and right arrows
import readline  # type: ignore[import-untyped];
import aiohttp
from wikidata_utils import WikidataAPIClient, format_wd_entity, extract_wd_id


def print_heading(title: str | None) -> None:
    """
    Print title heading with separator
    Print only separator if no title is provided.
    """
    if title:
        print("\n" + "=" * 40 + "\n")
        print(title)
        print("-" * 40 + "\n")
    else:
        print("\n" + "=" * 40 + "\n")


async def lookup_term(term: str, client: WikidataAPIClient) -> str | None:
    if match := extract_wd_id(term.upper()):
        return match[-1]
    elif result := await client.wbsearchentities(term, limit=1):
        return result[0]["id"]
    elif result := await client.search(term, limit=1):
        return result[0]["id"]
    else:
        print(f"No results found for term: {term}")
        return None


async def find_predicate(client: WikidataAPIClient, term1: str, term2: str) -> None:
    """
    Find and print all forward and backward properties connecting two Wikidata entities.
    """
    # Lookup both terms concurrently using the lookup_term helper
    qid1, qid2 = await asyncio.gather(
        lookup_term(term1, client),
        lookup_term(term2, client),
    )

    # Exit if either term is not found
    if not qid1 or not qid2:
        return

    # One API call for forward relationships and one for backward relationships
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

    # Run both SPARQL queries concurrently
    sparql_tasks = [client.sparql(query) for query in queries]
    # Returns a list of two dictionaries
    item_label_task = client.wbgetentities(qid1, qid2)
    forward_props, backward_props, qid_labels = await asyncio.gather(
        *sparql_tasks, item_label_task
    )

    entity1 = format_wd_entity(qid1, qid_labels[0].get("labels", ""))
    entity2 = format_wd_entity(qid2, qid_labels[1].get("labels", ""))
    if forward_props:
        print_heading("Forward properties")
        for row in forward_props:
            # property is a full URI, but we want to print just the QID
            pid = extract_wd_id(row["property"])
            label = row["propLabel"]
            entity = format_wd_entity(pid, label)
            print(f"{entity1}  {entity}  {entity2}")
    if backward_props:
        print_heading("Backward properties")
        for row in backward_props:
            # property is a full URI, but we want to print just the QID
            entity = format_wd_entity(extract_wd_id(row["property"]), row["propLabel"])
            print(f"{entity2}  {entity}  {entity1}")
    if not forward_props and not backward_props:
        # Empty string argument prints a separator
        print_heading(None)
        print(f"No properties found between {entity1} and {entity2}")
    # print a terminating separator
    print_heading(None)


"""
async def find_all_predicate(session, term):
    item = await wikidata_search_api(session, term)
    if not item:
        print(f"No result found for term: {term}")
        return
    triples = [f"wd:{item} ?property ?related .", f"?any ?related wd:{item} ."]
    queries = [
        f\"""
    SELECT ?property ?related WHERE {{
    {triple} .
    FILTER(STRSTARTS(STR(?property), STR(wdt:)))
    }}
    \"""
        for triple in triples
    ]
    sparql_tasks = [sparql_call(session, query) for query in queries]
    forward_pids, backward_pids = await asyncio.gather(*sparql_tasks)
    label_tasks = [
        wikidata_get_label(session, [d["property"] for d in forward_pids]),
        wikidata_get_label(session, [d["property"] for d in backward_pids]),
    ]
    forward_props, backward_props = await asyncio.gather(*label_tasks)
    
    print_table(item1, item2, forward_props, backward_props)
"""


async def main():
    async with aiohttp.ClientSession() as session:
        client = WikidataAPIClient(session)
        while True:
            user_input = input(
                "\033[91m"
                + "Enter two terms separated by a comma (or type 'exit'): "
                + "\033[0m"
            ).strip()
            if user_input.lower() in {"exit", "quit"}:
                print("Exiting...")
                break

            terms = [term.strip() for term in user_input.split(",")]
            if len(terms) != 2:
                print("Please enter exactly two terms separated by a comma.\n")
                continue

            await find_predicate(client, terms[0], terms[1])


if __name__ == "__main__":
    asyncio.run(main())
