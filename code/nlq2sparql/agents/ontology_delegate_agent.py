"""Ontology Delegate Agent

Simple agent that returns the entire user-provided ontology (verbatim text or
preloaded content) and relies on the LLM to extract relevant parts.

This is intentionally minimal and bypasses structured slicing.
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional
from pathlib import Path


class OntologyDelegateAgent:
    def __init__(self, ontology_path: Optional[Path] = None) -> None:
        # Default to unified ontology reference noted in STATUS (adjust if relocated)
        default_path = Path(__file__).resolve().parents[1] / "ontology" / "11Aug2025_ontology.ttl"
        self.ontology_path = ontology_path or default_path

    def run(self, question: str) -> Dict[str, Any]:
        text = ""
        if self.ontology_path.exists():
            try:
                text = self.ontology_path.read_text(encoding="utf-8")
            except Exception:
                text = ""
        return {
            "mode": "delegate",
            "ttl_full": text,
            "note": "Full ontology provided; model should extract relevant parts.",
            "question": question,
        }

__all__ = ["OntologyDelegateAgent"]
