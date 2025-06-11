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

    entity1 = build_wd_hyperlink(qid1, qid_labels[qid1].get("labels", ""))
    entity2 = build_wd_hyperlink(qid2, qid_labels[qid2].get("labels", ""))
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
        print(f"No Wikidata entity found for term: {term}")
        return

    # Fetch forward predicates (claims) from wbget_statements
    forward_relationships = await client.wbget_statements(qid)

    forward_ids_set = set()
    for pid, objects in forward_relationships.items():
        forward_ids_set.add(pid)
        if objects:
            forward_ids_set.add(objects[0])

    forward_ids_list = list(forward_ids_set)
    forward_props_dict = await client.wbgetentities(forward_ids_list, props="labels")

    # SPARQL query for backward predicates where this entity is object
    backward_query = f"""
    SELECT ?property ?propLabel ?example ?exampleLabel WHERE {{
    {{
        SELECT ?property (SAMPLE(?subject) AS ?example) WHERE {{
        ?subject ?property wd:{term } .
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

    entity = build_wd_hyperlink(qid, term)

    if forward_relationships:
        print_heading("Forward predicates (as subject)")
        for pid, objects in forward_relationships.items():
            prop_label = forward_props_dict.get(pid, {}).get("labels", pid)
            example = objects[0] if objects else ""
            example_label = forward_props_dict.get(example, {}).get("labels", example)
            pred = build_wd_hyperlink(pid, prop_label)
            ex = build_wd_hyperlink(example, example_label)
            print(f"{entity}  {pred}  {ex}")

    if backward_props:
        print_heading("Backward predicates (as object)")
        for row in backward_props:
            pid = extract_wd_id(row["property"])
            label = row.get("propLabel") or pid
            example = extract_wd_id(row.get("example", ""))
            example_label = row.get("exampleLabel", "")
            pred = build_wd_hyperlink(pid, label)
            ex = build_wd_hyperlink(example, example) if example else ""
            print(f"{ex}  {pred}  {entity}")

    if not forward_relationships and not backward_props:
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
            if len(terms) == 1:
                await find_all_predicate(client, terms[0])
                continue
            elif len(terms) == 2:
                await find_relation(client, terms[0], terms[1])
            else:
                print("Unable to parse input")


if __name__ == "__main__":
    asyncio.run(main())
