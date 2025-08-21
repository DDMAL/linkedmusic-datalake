"""Supervisor Agent (skeleton) orchestrating sub‑agents."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import logging

from .base import BaseAgent, AgentConfig
try:
    from ..catalog.loader import load_capabilities, supports_concepts  # type: ignore
except Exception:  # support direct import in tests
    from catalog.loader import load_capabilities, supports_concepts  # type: ignore


@dataclass
class SupervisorResult:
    question: str
    routing: Dict[str, Any]
    ontology_slice: Dict[str, Any]
    resolved_entities: Dict[str, Optional[str]]
    examples: List[Dict[str, Any]]
    prompt: Dict[str, Any]


class SupervisorAgent(BaseAgent):
    name = "supervisor"

    def __init__(
        self,
        ontology_agent: BaseAgent,
        wikidata_agent: Any,
        example_agent: BaseAgent,
        prompt_builder,
        router_agent: BaseAgent | None = None,
        config: Optional[AgentConfig] = None,
        logger: Optional[logging.Logger] = None,
    ):
        super().__init__(config=config, logger=logger)
        self.ontology_agent = ontology_agent
        self.wikidata_agent = wikidata_agent
        self.example_agent = example_agent
        self.prompt_builder = prompt_builder
        self.router_agent = router_agent

    async def run(self, question: str) -> SupervisorResult:  # type: ignore[override]
        self.logger.debug("Supervisor start: %s", question)
        # Routing (optional first step)
        routing: Dict[str, Any] = {"ranked_datasets": [], "dataset_scores": {}, "concept_hints": []}
        if self.router_agent is not None:
            try:
                routing = await self.router_agent.run(question=question)
            except Exception as e:  # pragma: no cover
                self.logger.error("Routing failed: %s", e)
        # Simple plan derivation: load capabilities and filter ranked datasets by concept support
        ranked = routing.get("ranked_datasets", [])
        concept_hints = routing.get("concept_hints", []) or []
        caps = load_capabilities(ranked if ranked else None)
        selected: List[str] = []
        for ds in ranked:
            cap = caps.get(ds)
            if cap and supports_concepts(cap, concept_hints):
                selected.append(ds)
        # Soft cap to 2 datasets for now
        if len(selected) > 2:
            selected = selected[:2]
        plan = {
            "datasets_selected": selected,
            "concepts": concept_hints,
            "rationale": "capability-filtered routing",
        }
        ontology_mode = self.config.get("ontology_mode", "ttl") if self.config else "ttl"
        ontology_slice = await self.ontology_agent.run(question=question, mode=ontology_mode, datasets=selected or None)
        tokens = [t.strip(",.?;:") for t in question.split() if len(t) > 3]
        resolved = await self.wikidata_agent.lookup_entities_and_properties(tokens, tokens)
        examples = await self.example_agent.run(question=question)
        prompt = self.prompt_builder.build_prompt(
            question=question,
            ontology_slice=ontology_slice,
            resolved=resolved,
            examples=examples,
            config={**(self.config.settings if self.config else {}), "routing": routing, "plan": plan},
        )
        return SupervisorResult(question, routing, ontology_slice, resolved, examples, prompt)


__all__ = ["SupervisorAgent", "SupervisorResult"]
