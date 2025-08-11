# NLQ2SPARQL Module

Natural Language → SPARQL generation for LinkedMusic graphs (DIAMM, The Session) using LLM function calling, ontology grounding, and Wikidata resolution tools.

This README reflects the CURRENT implemented scope (ontology summarization + Wikidata ID resolution + Gemini integration scaffold). For roadmap and detailed status see `STATUS.md`.

## Implemented (Current)
- OntologyAgent (`agents/ontology_agent.py`) – simplified schema extraction.
- Wikidata tool functions (`tools/wikidata_tool.py`) – async entity & property ID resolution.
- Gemini integration scaffold (`integrations/gemini_integration.py`) – function calling support.
- Evaluation dataset (`query_database_10july2025.csv`).

## Planned Multi‑Agent Flow
```
User NL Query
    ↓
Supervisor / Router Agent
    ├─ Entity/Property Agent -> resolve QIDs/PIDs (tool calls)
    ├─ Ontology Agent -> extract filtered schema slice (relevant classes/properties)
    ├─ Example Retrieval Agent -> fetch k similar NLQ↔SPARQL pairs
    ├─ (Future) Verification Agent -> validate / repair draft SPARQL
    ↓
Prompt Builder -> unified structured prompt + tool call results
    ↓
LLM Provider(s) (Gemini / OpenAI / Anthropic)
    ↓
Draft SPARQL → Verification → Final SPARQL
```

## Not Yet Implemented (See STATUS.md for detail)
- Supervisor orchestrator & message schema.
- Prompt builder module.
- Example retrieval agent & similarity index.
- Property phrase → PID mapping population.
- Test suite & CI.
- Multi‑provider integrations (OpenAI, Anthropic).
- Query verification / self‑repair loop.

## Quick Smoke Test
```
poetry install
poetry run python - <<'PY'
from nlq2sparql.tools.wikidata_tool import find_entity_id, find_property_id
import asyncio
async def main():
    print('Dufay ->', await find_entity_id('Guillaume Dufay'))
    print('composer ->', await find_property_id('composer'))
asyncio.run(main())
PY
```

## Usage (Gemini Integration Example)
```
# Pseudocode sketch
from nlq2sparql.integrations.gemini_integration import GeminiWikidataIntegration
import asyncio
async def run():
    integ = GeminiWikidataIntegration()  # needs GEMINI_API_KEY in env
    resp = await integ.send_message_with_tools('Find the property ID for composer and QID for Guillaume Dufay')
    print(resp)
asyncio.run(run())
```

## Ontology Summaries
Use the `OntologyAgent` directly:
```
poetry run python - <<'PY'
from nlq2sparql.agents.ontology_agent import OntologyAgent
from pathlib import Path
agent = OntologyAgent(Path('code/nlq2sparql/ontology/diamm_ontology.ttl'))
schema = agent.get_schema_summary()
print('Classes:', schema['classes'][:5])
print('Relationships sample:', schema['relationships'][:5])
PY
```

## Contributing
- Keep changes off `main`; use `nlq2sparql-api` (current working branch) or feature branches.
- Update `STATUS.md` with decisions & milestones.
- Keep ontology prompt footprint minimal (strip unrelated classes/properties).

## License
Part of the LinkedMusic Data Lake repository. See root LICENSE (if present) or repository terms.

Last Updated: 2025-08-11 (multi‑agent vision added)
