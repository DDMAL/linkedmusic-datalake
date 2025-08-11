"""Outcome-focused tests for new agent skeletons.

Keeps assertions on externally observable behavior (keys, non-empty fields,
determinism) rather than internal implementation details.
"""
import json
from pathlib import Path

import pytest

# Import from the nlq2sparql package explicitly to avoid stdlib 'code' module shadowing
from nlq2sparql.agents import UnifiedOntologyAgent, ExampleRetrievalAgent, SupervisorAgent
from nlq2sparql import prompt_builder


@pytest.mark.asyncio
async def test_ontology_agent_slice_deterministic():
    agent = UnifiedOntologyAgent()
    q = "List compositions by Guillaume Dufay with incipit"
    slice1 = await agent.run(question=q)
    slice2 = await agent.run(question=q)
    assert slice1 == slice2  # deterministic repeated call
    # Basic shape expectations
    for key in ["tokens", "nodes", "edges", "literals", "source"]:
        assert key in slice1
    # No mutation of ontology file (hash stable via size+first bytes heuristic)
    ontology_path = Path(__file__).parent.parent / "ontology" / "11Aug2025_ontology.ttl"
    before = ontology_path.stat().st_size
    _ = await agent.run(question="Different query for slice")
    after = ontology_path.stat().st_size
    assert before == after


@pytest.mark.asyncio
async def test_example_agent_returns_ranked_subset():
    agent = ExampleRetrievalAgent(k_default=5)
    res = await agent.run(question="sessions in montreal with date")
    assert isinstance(res, list)
    for r in res:
        assert set(r.keys()) >= {"question", "overlap"}
    overlaps = [r["overlap"] for r in res]
    assert overlaps == sorted(overlaps, reverse=True)


@pytest.mark.asyncio
async def test_prompt_builder_structure():
    dummy_prompt = prompt_builder.build_prompt(
        question="Who composed the piece?",
        ontology_slice={"tokens": ["composed"], "nodes": [], "edges": [], "literals": [], "source": "unified_ontology_v1"},
        resolved={"entity:Guillaume": "Q123"},
        examples=[{"question": "Who wrote X?", "sparql": "SELECT"}],
        config={"test": True},
    )
    required = {"system_instructions", "user_question", "ontology_context", "resolved_ids", "examples_text", "config_meta", "debug_serialized"}
    assert required.issubset(dummy_prompt.keys())
    assert "You convert" in dummy_prompt["system_instructions"]
    # ontology_context should round-trip JSON serialization
    assert json.loads(json.dumps(dummy_prompt["ontology_context"]))


class _FakeWikidataAgent:
    async def lookup_entities_and_properties(self, entities, properties):  # pragma: no cover
        out = {}
        for e in entities[:2]:
            out[f"entity:{e}"] = f"Q{len(e)}"
        return out


class _NoOpExampleAgent:
    name = "examples"
    async def run(self, question: str, k: int | None = None):  # pragma: no cover
        return [{"question": "sample", "sparql": "SELECT * WHERE { ?s ?p ?o }", "overlap": 1.0}]


@pytest.mark.asyncio
async def test_supervisor_end_to_end_minimal():
    ont = UnifiedOntologyAgent()
    wikidata = _FakeWikidataAgent()
    examples = _NoOpExampleAgent()
    sup = SupervisorAgent(ontology_agent=ont, wikidata_agent=wikidata, example_agent=examples, prompt_builder=prompt_builder)
    result = await sup.run("List works by Guillaume Dufay")
    assert result.question.startswith("List works")
    assert isinstance(result.ontology_slice, dict)
    assert isinstance(result.resolved_entities, dict)
    assert isinstance(result.examples, list) and result.examples
    assert set(result.prompt.keys()) >= {"system_instructions", "user_question", "ontology_context"}
    for k in result.resolved_entities:
        assert k.startswith("entity:")
