"""RouterAgent

Lightweight lexical router that scores dataset candidates based on ordered
pattern rules defined in `catalog/router_rules.yml`.

Scoring heuristic (initial simple approach):
 - For each rule, if ANY pattern appears as a substring in the question text
   (case‑insensitive), the rule 'fires'.
 - Each dataset listed in the rule receives +`boost` points.
 - Multiple rules can accumulate scores for the same dataset.
 - Concept hints union the `concepts` fields of matched rules.
 - Rules later in the file do NOT override earlier ones; all matches aggregate.

Returns a routing payload with transparency for debugging.
This is intentionally simple; future iterations can add token frequency,
embedding similarity, negative patterns, or score normalization.
"""
from __future__ import annotations

from typing import Any, Dict, List, Set
from dataclasses import dataclass
from pathlib import Path
import logging
import yaml
import re

from .base import BaseAgent

RULES_FILE = Path(__file__).resolve().parents[1] / "catalog" / "router_rules.yml"


@dataclass
class RoutingResult:
    ranked_datasets: List[str]
    dataset_scores: Dict[str, float]
    concept_hints: List[str]
    matched_rules: List[Dict[str, Any]]
    tokens: List[str]


class RouterAgent(BaseAgent):
    name = "router"

    def __init__(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        super().__init__(*args, **kwargs)
        self._rules: List[Dict[str, Any]] | None = None
        self.logger = logging.getLogger(self.__class__.__name__)

    def _ensure_rules(self):
        if self._rules is not None:
            return
        if not RULES_FILE.exists():  # pragma: no cover
            raise FileNotFoundError(f"Router rules file missing: {RULES_FILE}")
        with RULES_FILE.open("r", encoding="utf-8") as f:
            self._rules = yaml.safe_load(f) or []
        if not isinstance(self._rules, list):  # pragma: no cover
            raise ValueError("router_rules.yml must contain a top-level list")

    def _tokenize(self, question: str) -> List[str]:
        return [t for t in re.findall(r"[a-zA-Z0-9]+", question.lower()) if len(t) >= 3]

    async def run(self, question: str) -> Dict[str, Any]:  # type: ignore[override]
        self._ensure_rules()
        assert self._rules is not None
        q_lower = question.lower()
        tokens = self._tokenize(question)
        dataset_scores: Dict[str, float] = {}
        concept_hints: Set[str] = set()
        matched_rules: List[Dict[str, Any]] = []
        for idx, rule in enumerate(self._rules):
            pats = rule.get("patterns", [])
            boost = float(rule.get("boost", 1.0))
            datasets = rule.get("datasets", [])
            concepts = rule.get("concepts", []) or []
            matched_patterns = [p for p in pats if p.lower() in q_lower]
            if not matched_patterns:
                continue
            # Rule fires
            for ds in datasets:
                dataset_scores[ds] = dataset_scores.get(ds, 0.0) + boost
            concept_hints.update(concepts)
            matched_rules.append({
                "rule_index": idx,
                "matched_patterns": matched_patterns,
                "datasets": datasets,
                "boost": boost,
                "concepts": concepts,
            })
        ranked = sorted(dataset_scores.items(), key=lambda x: (-x[1], x[0]))
        ranked_datasets = [d for d, _ in ranked]
        result: Dict[str, Any] = {
            "ranked_datasets": ranked_datasets,
            "dataset_scores": dataset_scores,
            "concept_hints": sorted(concept_hints),
            "matched_rules": matched_rules,
            "tokens": tokens,
            "rule_count": len(self._rules),
        }
        return result


__all__ = ["RouterAgent", "RoutingResult"]
