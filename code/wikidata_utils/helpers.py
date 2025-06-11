import re
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
