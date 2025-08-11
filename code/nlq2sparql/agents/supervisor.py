"""Supervisor Agent (skeleton) orchestrating sub‑agents."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import logging

from .base import BaseAgent, AgentConfig


@dataclass
class SupervisorResult:
    question: str
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
        config: Optional[AgentConfig] = None,
        logger: Optional[logging.Logger] = None,
    ):
        super().__init__(config=config, logger=logger)
        self.ontology_agent = ontology_agent
        self.wikidata_agent = wikidata_agent
        self.example_agent = example_agent
        self.prompt_builder = prompt_builder

    async def run(self, question: str) -> SupervisorResult:  # type: ignore[override]
        self.logger.debug("Supervisor start: %s", question)
        ontology_mode = self.config.get("ontology_mode", "ttl") if self.config else "ttl"
        ontology_slice = await self.ontology_agent.run(question=question, mode=ontology_mode)
        tokens = [t.strip(",.?;:") for t in question.split() if len(t) > 3]
        resolved = await self.wikidata_agent.lookup_entities_and_properties(tokens, tokens)
        examples = await self.example_agent.run(question=question)
        prompt = self.prompt_builder.build_prompt(
            question=question,
            ontology_slice=ontology_slice,
            resolved=resolved,
            examples=examples,
            config=self.config.settings,
        )
        return SupervisorResult(question, ontology_slice, resolved, examples, prompt)


__all__ = ["SupervisorAgent", "SupervisorResult"]
