"""
Prompt templates for SPARQL query generation
"""


def build_sparql_generation_prompt(nlq: str, database: str, prefix_declarations: str, ontology_context: str = "") -> str:
    """
    Build the prompt for the LLM to generate SPARQL queries
    
    Args:
        nlq: Natural language query
        database: Target database name
        prefix_declarations: Available SPARQL prefixes
        ontology_context: Optional ontology context information
        
    Returns:
        Formatted prompt string
    """
    prompt = f"""You are a SPARQL query generator working with musical Linked Data.

Task: Convert the following natural language query to a SPARQL query that retrieve all 
relevant results from the {database} database. Do not guess Wikidata QIDs or PIDs, use the provided
ontology context if available. Return only the SPARQL query, no explanations. Ensure the query is syntatically correct.

Natural Language Query: {nlq}

Available Prefixes:
{prefix_declarations}

{"Ontology Context:" if ontology_context else ""}
{ontology_context}

SPARQL Query:"""
    
    return prompt
