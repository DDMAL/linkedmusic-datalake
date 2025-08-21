"""Prompt Builder Skeleton.

Produces a structured dict which provider adapters can turn into concrete
LLM calls. Keeping structured form simplifies testing & hashing.
"""
from __future__ import annotations

from typing import Any, Dict, List
import json


def _serialize_examples(examples: List[Dict[str, Any]]) -> str:
    if not examples:
        return "(no examples available)"
    parts = []
    for ex in examples:
        parts.append(f"Q: {ex.get('question')}\nSPARQL: {ex.get('sparql') or '(none)'}")
    return "\n\n".join(parts)


def build_prompt(question: str, ontology_slice: Dict[str, Any], resolved: Dict[str, Any], examples: List[Dict[str, Any]], config: Dict[str, Any] | None = None) -> Dict[str, Any]:
    system_msg = (
        "You convert natural language about musical / historical datasets into concise SPARQL. "
        "Use only provided ontology slice, resolved IDs, and examples."
    )
    payload = {
        "system_instructions": system_msg,
        "user_question": question,
        "ontology_context": ontology_slice,
        "resolved_ids": resolved,
        "examples_text": _serialize_examples(examples),
        "config_meta": config or {},
    }
    payload["debug_serialized"] = json.dumps(ontology_slice, sort_keys=True)[:500]
    return payload


__all__ = ["build_prompt"]
