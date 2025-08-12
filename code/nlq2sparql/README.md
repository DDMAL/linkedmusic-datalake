# NLQ2SPARQL Module

Natural Language → SPARQL generation for LinkedMusic graphs (DIAMM, The Session) using LLM function calling, ontology grounding, and Wikidata resolution tools.

This README reflects the CURRENT implemented scope (ontology summarization + Wikidata ID resolution + Gemini integration scaffold). For roadmap and detailed status see `STATUS.md`.

## Implemented (Current)
- UnifiedOntologyAgent (`agents/ontology_agent.py`) – read‑only unified TTL slice heuristic.
- ExampleRetrievalAgent (`agents/example_agent.py`) – token overlap baseline retrieval.
- Wikidata tool functions (`tools/wikidata_tool.py`) – async entity & property ID resolution.
- SupervisorAgent skeleton (`agents/supervisor.py`).
- Prompt builder (`prompt_builder.py`).
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

## Quick Smoke Tests
Install (if not already):
```bash
poetry install
```

Wikidata resolution:
```bash
poetry run python - <<'PY'
from code.nlq2sparql.tools.wikidata_tool import find_entity_id, find_property_id
import asyncio
async def main():
    print('Dufay ->', await find_entity_id('Guillaume Dufay'))
    print('composer ->', await find_property_id('composer'))
asyncio.run(main())
PY
```

Supervisor dry run (no LLM call yet):
```bash
poetry run python - <<'PY'
import asyncio
from code.nlq2sparql.agents import UnifiedOntologyAgent, ExampleRetrievalAgent, SupervisorAgent, WikidataAgent
from code.nlq2sparql import prompt_builder

async def main():
    sup = SupervisorAgent(
        ontology_agent=UnifiedOntologyAgent(),
        wikidata_agent=WikidataAgent(),
        example_agent=ExampleRetrievalAgent(),
        prompt_builder=prompt_builder,
    )
    result = await sup.run("List compositions by Guillaume Dufay with incipit information")
    print('Prompt keys:', list(result.prompt.keys()))
    print('Resolved sample:', list(result.resolved_entities.items())[:5])
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

### Execute generated SPARQL (optional)

You can have the main CLI execute the generated SPARQL against a SPARQL HTTP endpoint (read‑only):

- Save JSON to `code/nlq2sparql/results/` (gitignored):

```bash
poetry run python -m code.nlq2sparql.cli \
    --provider gemini \
    --database session \
    --exec-sparql \
    --sparql-endpoint https://virtuoso.staging.simssa.ca/sparql \
    --sparql-format json \
    "Return all entries in The Session that took place in Montreal"
```

Guardrails: SELECT/ASK only, LIMIT capped (default 1000), HTTP timeout (default 15s), dangerous tokens rejected (INSERT/DELETE/LOAD/...)

For ad‑hoc queries without the LLM path, use the small SPARQL runner:

```bash
poetry run python -m code.nlq2sparql.tools.sparql_cli \
    --endpoint https://virtuoso.staging.simssa.ca/sparql \
    --query "SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 1" \
    --format json
```
asyncio.run(run())
```

## Ontology Slices
The `UnifiedOntologyAgent` automatically loads `ontology/11Aug2025_ontology.ttl` (read‑only). The heuristic will improve; current output structure is stable for prompt building.

### Toggle: Structured vs Delegate (Full Ontology)
- Default strategy is structured slicing (router + UnifiedOntologyAgent with TTL snippets).
- To compare against a simple "give the whole ontology to the LLM" approach, set one of:
    - Config file `code/nlq2sparql/config.json`: `"ontology_strategy": "llm_delegate"`
    - Or environment: `NLQ2SPARQL_ONTOLOGY_STRATEGY=llm_delegate`

In delegate mode, the orchestrator uses `OntologyDelegateAgent` to provide the full ontology (verbatim). The prompt text includes a small header rather than dumping the entire TTL; provider wrappers should pass the TTL as a separate large-context input and instruct the model to extract the relevant parts.

## Contributing
- Keep changes off `main`; use `nlq2sparql-api` (current working branch) or feature branches.
- Update `STATUS.md` with decisions & milestones.
- Keep ontology prompt footprint minimal (strip unrelated classes/properties).

## License
Part of the LinkedMusic Data Lake repository. See root LICENSE (if present) or repository terms.

Last Updated: 2025-08-11 (skeleton multi‑agent components added)
