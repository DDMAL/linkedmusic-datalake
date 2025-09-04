"""Unified Ontology Subagent (skeleton, read‑only)."""
from __future__ import annotations

from typing import Any, Dict, List, Set, Optional
from dataclasses import dataclass
import logging
from pathlib import Path
import re
from rdflib import Graph, RDFS, URIRef, Literal
from functools import lru_cache

from .base import BaseAgent

# Automatically find the latest ontology file based on filename sorting
ONTOLOGY_DIR = Path(__file__).resolve().parents[1] / "ontology"

def _find_latest_ontology_file():
    """Find the latest ontology file by scanning directory and sorting by filename."""
    if not ONTOLOGY_DIR.exists():
        return ONTOLOGY_DIR / "4Sept2025_ontology.ttl"  # fallback for missing directory
    
    # Find all *ontology.ttl files
    ontology_files = list(ONTOLOGY_DIR.glob("*ontology.ttl"))
    
    if not ontology_files:
        return ONTOLOGY_DIR / "11Aug2025_ontology.ttl"  # fallback if no files found
    
    # Sort by filename (date strings sort chronologically: "11Aug2025" < "4Sept2025" etc.)
    # Use reverse=True to get the latest (newest) file first
    latest_file = sorted(ontology_files, key=lambda p: p.name, reverse=True)[0]
    return latest_file

ONTOLOGY_FILE = _find_latest_ontology_file()


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

    async def run(self, question: str, max_neighbors: int = 30, mode: str = "ttl", datasets: Optional[List[str]] = None) -> Dict[str, Any]:  # type: ignore[override]
        self._ensure_loaded()
        assert self._graph is not None
        tokens = self._tokenize(question)
        # Try cached result for identical tokens + datasets + mode
        cache_key = (tuple(tokens), tuple(sorted(datasets or [])), mode)
        cached = self._get_cached_slice(cache_key)
        if cached is not None:
            return cached
        matched_subjects: Set[str] = set()
        for token in tokens:
            for label, subs in self._label_index.items():
                if token in label:
                    matched_subjects.update(subs)
        # Optional dataset filtering by prefix
        allowed_prefixes: Optional[Set[str]] = None
        if datasets:
            # Map dataset codes to known prefixes used by _shorten
            ds_map = {
                "musicbrainz": "mb:",
                "thesession": "ts:",
                "diamm": "diamm:",
                "dtl": "dtl:",
                "gj": "gj:",
            }
            allowed_prefixes = {ds_map[d] for d in datasets if d in ds_map and ds_map[d]}
        g = self._graph
        if mode == "ttl":
            # Return raw TTL snippet(s) verbatim for each matched subject
            snippets: List[str] = []
            # Deterministic subject ordering
            subjects_sorted = sorted(matched_subjects)
            # Limit subjects to avoid runaway size
            for subj in subjects_sorted[: max_neighbors]:
                subj_ref = URIRef(subj)
                lines: List[str] = []
                # Collect triples for this subject
                triples = list(g.triples((subj_ref, None, None)))
                # Deterministic predicate/object ordering
                triples.sort(key=lambda t: (str(t[1]), str(t[2])))
                for _, pred, obj in triples:
                    if isinstance(obj, Literal):
                        o_txt = f'"{obj}"@en' if obj.language == 'en' else f'"{obj}"'
                    else:
                        o_txt = self._shorten(str(obj))
                    lines.append(f"{self._shorten(str(pred))}\t{o_txt} .")
                if lines:
                    header = self._shorten(str(subj_ref))
                    # If dataset filtering is enabled, skip subjects not matching allowed prefixes
                    if allowed_prefixes and not any(header.startswith(p) for p in allowed_prefixes):
                        continue
                    # Sort lines for deterministic snippet content
                    snippet = header + "\n\t" + "\n\t".join(sorted(lines))
                    snippets.append(snippet)
            # Maintain backward-compatible empty structural fields so older tests / consumers don't break.
            result = {"tokens": tokens, "ttl_snippets": snippets, "nodes": [], "edges": [], "literals": [], "source": "unified_ontology_v1", "mode": "ttl"}
            self._set_cached_slice(cache_key, result)
            return result
        else:
            # Structured mode (original behavior) retained for future experimentation
            edges: List[Dict[str, Any]] = []
            literals: List[Dict[str, Any]] = []
            added_nodes: Set[str] = set(matched_subjects)
            for subj in list(matched_subjects):
                if len(edges) >= max_neighbors:
                    break
                subj_ref = URIRef(subj)
                triples = list(g.triples((subj_ref, None, None)))
                triples.sort(key=lambda t: (str(t[1]), str(t[2])))
                for _, pred, obj in triples:
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
            # Deterministic ordering of edges
            edges_sorted = sorted(edges, key=lambda e: (e["subject"], e["predicate"], e["object"]))
            result = {"tokens": tokens, "nodes": nodes, "edges": edges_sorted, "literals": literals, "source": "unified_ontology_v1", "mode": "structured"}
            self._set_cached_slice(cache_key, result)
            return result

    def _shorten(self, iri: str) -> str:
        """Best‑effort compaction of full IRI to prefix:local if it matches known namespaces.
        Falls back to original IRI if no match.
        """
        # Simple static prefix mapping mirroring top of TTL file
        prefixes = {
            "https://linkedmusic.ca/graphs/musicbrainz/": "mb:",
            "https://linkedmusic.ca/graphs/thesession/": "ts:",
            "https://linkedmusic.ca/graphs/diamm/": "diamm:",
            "https://linkedmusic.ca/graphs/dig-that-lick/": "dtl:",
            "https://linkedmusic.ca/graphs/theglobaljukebox/": "gj:",
            "http://www.wikidata.org/prop/direct/": "wdt:",
            "http://www.w3.org/2000/01/rdf-schema#": "rdfs:",
            "http://www.w3.org/2004/02/skos/core#": "skos:",
        }
        for base, p in prefixes.items():
            if iri.startswith(base):
                return p + iri[len(base):]
        return iri

    # Simple in-process cache for slices
    @lru_cache(maxsize=256)
    def _get_cached_slice(self, key):  # type: ignore[no-untyped-def]
        return None

    def _set_cached_slice(self, key, value):  # type: ignore[no-untyped-def]
        # lru_cache-based getter cannot be set directly; emulate via memoization in instance
        # For simplicity, store on instance dict keyed by key
        cache = getattr(self, "_slice_cache", None)
        if cache is None:
            cache = {}
            setattr(self, "_slice_cache", cache)
        cache[key] = value
        # Monkey-patch getter to check this map first
        def getter(k):
            return getattr(self, "_slice_cache", {}).get(k)
        object.__setattr__(self, "_get_cached_slice", getter)


__all__ = ["UnifiedOntologyAgent", "OntologySlice"]
