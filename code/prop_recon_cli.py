"""Utilities for interacting with Wikidata SPARQL endpoint and search API calls."""

import asyncio

# readline helps user navigate using left and right arrows
# it works as long as it is imported
import readline  # type: ignore[import-untyped];
import aiohttp
from wikidata_utils import WikidataAPIClient, build_wd_hyperlink, extract_wd_id


def print_heading(title: str) -> None:
    """
    Print title heading with separator
    """
    if title:
        print("\n" + "=" * 40 + "\n")
        print(title)
        print("-" * 40 + "\n")


def print_separator() -> None:
    """
    Print a separator line.
    """
    print("-" * 40 + "\n")


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


async def find_relation(client: WikidataAPIClient, term1: str, term2: str) -> None:
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
        print_separator()
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

    entity1 = build_wd_hyperlink(qid1, qid_labels[0].get("labels", ""))
    entity2 = build_wd_hyperlink(qid2, qid_labels[1].get("labels", ""))
    if forward_props:
        print_heading("Forward properties")
        for row in forward_props:
            # property is a full URI, but we want to print just the QID
            pid = extract_wd_id(row["property"])
            label = row["propLabel"]
            entity = build_wd_hyperlink(pid, label)
            print(f"{entity1}  {entity}  {entity2}")
    if backward_props:
        print_heading("Backward properties")
        for row in backward_props:
            # property is a full URI, but we want to print just the QID
            entity = build_wd_hyperlink(
                extract_wd_id(row["property"]), row["propLabel"]
            )
            print(f"{entity2}  {entity}  {entity1}")
    if not forward_props and not backward_props:
        # Empty string argument prints a separator
        print_separator()
        print(f"No properties found between {entity1} and {entity2}")
    # print a terminating separator
    print_separator()


async def find_all_predicate(client: WikidataAPIClient, term: str) -> None:
    """
    Find and print all forward and backward predicates for a single Wikidata entity (term).
    Only one QID example is shown for each predicate.
    """
    qid = await lookup_term(term, client)
    if not qid:
        print_separator()
        return

    # Prepare SPARQL queries using the QID
    
    query = f"""
        SELECT ?property ?propLabel ?example ?exampleLabel WHERE {{
        {{
            SELECT ?property (SAMPLE(?value) AS ?example) WHERE {{
            ?value ?property wd:{item} .
            ?prop wikibase:directClaim ?property .
            }}
            GROUP BY ?property
        }}

        ?prop wikibase:directClaim ?property .
        FILTER(STRSTARTS(STR(?example), "http://www.wikidata.org/entity/"))
        
        SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        OPTIONAL {{
            ?example rdfs:label ?exampleLabel .
            FILTER(LANG(?exampleLabel) = "en")
        }}
        }}
        ORDER BY ?property
        """

    # Run both SPARQL queries concurrently
    sparql_tasks = [client.sparql(forward_query), client.sparql(backward_query)]
    forward_props, backward_props = await asyncio.gather(*sparql_tasks)

    entity = build_wd_hyperlink(qid, term)
    if forward_props:
        print_heading("Forward predicates (as subject)")
        for row in forward_props:
            pid = extract_wd_id(row["property"])
            label = row["propLabel"]
            example = extract_wd_id(row["example"])
            pred = build_wd_hyperlink(pid, label)
            ex = build_wd_hyperlink(example, example) if example else ""
            print(f"{entity}  {pred}  {ex}")
    if backward_props:
        print_heading("Backward predicates (as object)")
        for row in backward_props:
            pid = extract_wd_id(row["property"])
            label = row["propLabel"]
            example = extract_wd_id(row["example"])
            pred = build_wd_hyperlink(pid, label)
            ex = build_wd_hyperlink(example, example) if example else ""
            print(f"{ex}  {pred}  {entity}")
    if not forward_props and not backward_props:
        print_separator()
        print(f"No predicates found for {entity}")
    print_separator()


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

            await find_relation(client, terms[0], terms[1])


if __name__ == "__main__":
    asyncio.run(main())
