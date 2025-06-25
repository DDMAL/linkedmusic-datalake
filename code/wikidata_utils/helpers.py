"""
A collection of utility functions for working with Wikidata entities
"""

import re


def build_terminal_link(text: str, link: str) -> str:
    """
    Return a terminal hyperlink string for the given URL and label.

    This uses ANSI escape sequences to create clickable links
    in supported terminals.

    Args:
        text: The label to display in the terminal.
        link: The URL to link to.

    Returns:
        A formatted string that renders as a clickable hyperlink in supported terminals.
    """
    esc = "\033"
    start = f"{esc}]8;;{link}{esc}\\"
    end = f"{esc}]8;;{esc}\\"
    # ANSI escape codes allow for hyperlinks in terminals
    return f"{start}{text}{end}"


def build_wd_hyperlink(item_id, item_label) -> str:
    """
    Format a Wikidata entity into a terminal hyperlink using its label and ID.

    Args:
        item_id: The Wikidata entity ID (e.g., "Q42").
        item_label: The human-readable label for the entity.

    Returns:
        A formatted hyperlink string, like "Douglas Adams(Q42)", linked to the entity's URL.
    """
    uri = f"https://www.wikidata.org/entity/{item_id}"
    text = f"{item_label}({item_id})"
    return build_terminal_link(text, uri)


def extract_wd_id(s: str, all_match: bool = False) -> str | list[str] | None:
    """
    Extract Wikidata ID (Q or P followed by digits) from a string.

    Returns:
        str | list[str] | None:
            - If all_match is False (default), returns the last matched ID as a string.
            - If all_match is True, returns a list of all matched IDs
            - If no matches are found, returns None.
    """
    pattern = re.compile(r"Q\d+|P\d+")
    matches = pattern.findall(s)
    if all_match:
        return matches if matches else None
    # By default, return the last match
    else:
        return matches[-1] if matches else None
