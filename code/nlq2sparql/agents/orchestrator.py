"""Multi-agent orchestrator that builds ontology context text for providers.

Runs RouterAgent → UnifiedOntologyAgent (dataset-aware) → WikidataAgent → ExampleRetrievalAgent
and composes a compact textual context to feed into provider prompt builders.
"""
from __future__ import annotations

from typing import Dict, Any, List
import asyncio

from .router_agent import RouterAgent
from .ontology_agent import UnifiedOntologyAgent
from .wikidata_agent import WikidataAgent
from .example_agent import ExampleRetrievalAgent


class MultiAgentOrchestrator:
    def __init__(self) -> None:
        self.router = RouterAgent()
        self.ontology = UnifiedOntologyAgent()
        self.wikidata = WikidataAgent()
        self.examples = ExampleRetrievalAgent()

    async def _run_async(self, question: str) -> Dict[str, Any]:
        routing = await self.router.run(question=question)
        selected = routing.get("ranked_datasets", [])
        ont = await self.ontology.run(question=question, mode="ttl", datasets=selected or None)
        # Token list from question; reuse tokens from ontology or simple split
        tokens = ont.get("tokens") or [t for t in question.split() if len(t) > 3]
        resolved = await self.wikidata.lookup_entities_and_properties(tokens, tokens)
        ex = await self.examples.run(question=question, k=2)
        return {"routing": routing, "ontology": ont, "resolved": resolved, "examples": ex}

    def build_ontology_context(self, question: str) -> str:
        """Run the pipeline and return a compact plain-text context block."""
        # Execute async subagents in a fresh event loop
        try:
            res = asyncio.run(self._run_async(question))
        except RuntimeError:
            # In case already inside an event loop (rare for CLI), use new loop
            loop = asyncio.new_event_loop()
            try:
                asyncio.set_event_loop(loop)
                res = loop.run_until_complete(self._run_async(question))
            finally:
                loop.close()
        routing = res["routing"]
        ont = res["ontology"]
        resolved = res["resolved"]
        examples: List[Dict[str, Any]] = res["examples"]

        # Compose text sections
        parts: List[str] = []
        # Routing summary
        parts.append("# Routing Plan\n")
        parts.append(f"Datasets: {', '.join(routing.get('ranked_datasets', [])) or '(none)'}")
        ch = routing.get("concept_hints", [])
        if ch:
            parts.append(f"Concepts: {', '.join(ch)}")

        # Resolved IDs
        if resolved:
            parts.append("\n# Resolved IDs (labels → QID/PID)\n")
            for k, v in sorted(resolved.items()):
                parts.append(f"{k} = {v}")

        # Ontology TTL snippets
        snippets = ont.get("ttl_snippets", [])
        if snippets:
            parts.append("\n# Ontology TTL Snippets (verbatim)\n")
            # Limit to a safe number of lines
            for sn in snippets[:20]:
                parts.append(sn)

        # Examples (optional, lightweight)
        if examples:
            parts.append("\n# Related Examples (NLQ → SPARQL)\n")
            for ex in examples[:2]:
                q = ex.get("question") or ""
                sp = ex.get("sparql") or "(none)"
                parts.append(f"Q: {q}\nSPARQL: {sp}")

        return "\n".join(parts).strip()


__all__ = ["MultiAgentOrchestrator"]
