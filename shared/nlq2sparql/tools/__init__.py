"""Tool subpackage for NLQ2SPARQL (Wikidata resolution, etc.).

Avoid importing heavy or side-effectful modules at package import time.
Consumers should import needed symbols directly from their modules, e.g.:
	from shared.nlq2sparql.tools.wikidata_tool import find_entity_id
"""

__all__: list[str] = []
