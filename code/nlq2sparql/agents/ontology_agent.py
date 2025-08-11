"""Unified Ontology Subagent (skeleton, read‑only)."""
from __future__ import annotations

from typing import Any, Dict, List, Set
from dataclasses import dataclass
import logging
from pathlib import Path
import re
from rdflib import Graph, RDFS, URIRef, Literal

from .base import BaseAgent

ONTOLOGY_FILE = Path(__file__).resolve().parents[1] / "ontology" / "11Aug2025_ontology.ttl"


@dataclass
class OntologySlice:
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    literals: List[Dict[str, Any]]


class UnifiedOntologyAgent(BaseAgent):
    name = "ontology"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._graph: Graph | None = None
        self._label_index: Dict[str, Set[str]] = {}
        self._loaded = False
        self.logger = logging.getLogger(self.__class__.__name__)

    def _ensure_loaded(self):
        if self._loaded:
            return
        if not ONTOLOGY_FILE.exists():  # pragma: no cover
            raise FileNotFoundError(f"Unified ontology file missing: {ONTOLOGY_FILE}")
        g = Graph()
        g.parse(ONTOLOGY_FILE)
        self._graph = g
        for s, _, o in g.triples((None, RDFS.label, None)):
            if isinstance(o, Literal):
                self._label_index.setdefault(str(o).lower(), set()).add(str(s))
        self._loaded = True

    def _tokenize(self, question: str) -> List[str]:
        return [t for t in re.findall(r"[a-zA-Z0-9]+", question.lower()) if len(t) >= 3]

    async def run(self, question: str, max_neighbors: int = 30) -> Dict[str, Any]:  # type: ignore[override]
        self._ensure_loaded()
        assert self._graph is not None
        tokens = self._tokenize(question)
        matched_subjects: Set[str] = set()
        for token in tokens:
            for label, subs in self._label_index.items():
                if token in label:
                    matched_subjects.update(subs)
        edges: List[Dict[str, Any]] = []
        literals: List[Dict[str, Any]] = []
        added_nodes: Set[str] = set(matched_subjects)
        g = self._graph
        for subj in list(matched_subjects):
            if len(edges) >= max_neighbors:
                break
            subj_ref = URIRef(subj)
            for _, pred, obj in g.triples((subj_ref, None, None)):
                if len(edges) >= max_neighbors:
                    break
                if isinstance(obj, Literal):
                    literals.append({"subject": subj, "predicate": str(pred), "value": str(obj)})
                else:
                    oid = str(obj)
                    edges.append({"subject": subj, "predicate": str(pred), "object": oid})
                    added_nodes.add(oid)
        labels_map: Dict[str, str] = {}
        for s in added_nodes:
            for _, _, o in g.triples((URIRef(s), RDFS.label, None)):
                if isinstance(o, Literal):
                    labels_map[s] = str(o)
                    break
        nodes = [{"id": nid, "label": labels_map.get(nid)} for nid in sorted(added_nodes)]
        return {"tokens": tokens, "nodes": nodes, "edges": edges, "literals": literals, "source": "unified_ontology_v1"}


__all__ = ["UnifiedOntologyAgent", "OntologySlice"]
