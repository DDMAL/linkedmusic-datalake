"""
LLM-Powered Ontology Agent

This agent uses an LLM to intelligently extract relevant ontology sections
based on semantic understanding of the question, rather than simple keyword matching.
"""
from __future__ import annotations

from typing import Any, Dict, List, Set, Optional
from dataclasses import dataclass
import logging
import json
from pathlib import Path
from rdflib import Graph, RDFS, URIRef, Literal

from .base import BaseAgent
try:
    from ..llm import create_llm_client, LLMClient
except ImportError:
    # Fallback for test context
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from llm import create_llm_client, LLMClient

# Reuse the ontology file detection from the original agent
ONTOLOGY_DIR = Path(__file__).resolve().parents[1] / "ontology"

def _find_latest_ontology_file():
    """Find the latest ontology file by scanning directory and sorting by filename."""
    if not ONTOLOGY_DIR.exists():
        return ONTOLOGY_DIR / "4Sept2025_ontology.ttl"
    
    ontology_files = list(ONTOLOGY_DIR.glob("*ontology.ttl"))
    
    if not ontology_files:
        return ONTOLOGY_DIR / "4Sept2025_ontology.ttl"
    
    latest_file = sorted(ontology_files, key=lambda p: p.name, reverse=True)[0]
    return latest_file

ONTOLOGY_FILE = _find_latest_ontology_file()


@dataclass
class LLMOntologySlice:
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    literals: List[Dict[str, Any]]
    reasoning: str
    llm_metadata: Dict[str, Any]


class LLMOntologyAgent(BaseAgent):
    """
    LLM-powered ontology agent that extracts relevant ontology sections
    using semantic understanding rather than keyword matching.
    """
    name = "llm_ontology"

    def __init__(
        self, 
        llm_client: Optional[LLMClient] = None,
        *args, 
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.llm_client = llm_client or create_llm_client()
        self._graph: Graph | None = None
        self._ontology_summary: str | None = None
        self._loaded = False

    def _ensure_loaded(self) -> None:
        """Load and summarize the ontology for LLM processing."""
        if self._loaded:
            return
        
        try:
            self._graph = Graph()
            if ONTOLOGY_FILE.exists():
                self._graph.parse(ONTOLOGY_FILE, format="turtle")
                self.logger.info(f"Loaded ontology: {len(self._graph)} triples")
                self._create_ontology_summary()
            else:
                self.logger.warning(f"Ontology file not found: {ONTOLOGY_FILE}")
            self._loaded = True
        except Exception as e:
            self.logger.error(f"Failed to load ontology: {e}")
            self._graph = Graph()
            self._loaded = True

    def _create_ontology_summary(self) -> None:
        """Create a human-readable summary of the ontology for LLM consumption."""
        if not self._graph:
            self._ontology_summary = "No ontology available"
            return
        
        # Extract key information about classes and properties
        classes = []
        properties = []
        
        # Get classes (subjects that are classes)
        for s, p, o in self._graph.triples((None, None, None)):
            if isinstance(s, URIRef):
                # Look for class-like patterns
                s_str = str(s)
                if any(keyword in s_str.lower() for keyword in ['class', 'type', 'concept']):
                    classes.append(s_str.split('/')[-1].split('#')[-1])
                
            # Look for properties
            if isinstance(p, URIRef):
                p_str = str(p)
                if p_str not in [str(RDFS.label), str(RDFS.comment)]:  # Skip basic RDF properties
                    properties.append(p_str.split('/')[-1].split('#')[-1])
        
        # Remove duplicates and sort
        classes = sorted(set(classes))[:20]  # Limit to top 20
        properties = sorted(set(properties))[:30]  # Limit to top 30
        
        summary = f"""ONTOLOGY SUMMARY:
Classes ({len(classes)} shown): {', '.join(classes)}
Properties ({len(properties)} shown): {', '.join(properties)}
Total triples: {len(self._graph)}"""
        
        self._ontology_summary = summary

    def _build_ontology_prompt(self, question: str, datasets: Optional[List[str]] = None) -> str:
        """Build the LLM prompt for ontology extraction."""
        self._ensure_loaded()
        
        dataset_context = ""
        if datasets:
            dataset_context = f"\nFOCUS DATASETS: {', '.join(datasets)}"
        
        prompt = f"""You are an ontology extraction specialist for music data. Given a natural language question, you need to identify the most relevant parts of the music ontology that would be needed to answer the question.

{self._ontology_summary}{dataset_context}

QUESTION: "{question}"

Your task is to:
1. Analyze the semantic content of the question
2. Identify key musical concepts, entities, and relationships mentioned or implied
3. Extract the most relevant ontology elements (classes, properties, individuals)
4. Consider both direct matches and related concepts

Return your response as a JSON object with this exact structure:
{{
    "relevant_classes": ["class1", "class2", ...],
    "relevant_properties": ["property1", "property2", ...],
    "key_concepts": ["concept1", "concept2", ...],
    "reasoning": "Brief explanation of why these ontology elements are relevant"
}}

Focus on:
- Musical entities (composers, works, instruments, etc.)
- Temporal concepts (dates, periods, etc.)
- Structural relationships (part-of, created-by, etc.)
- Descriptive properties (title, genre, key, etc.)

Be comprehensive but focused - include elements that are directly relevant or might be needed for joins/relationships."""

        return prompt

    def _extract_ontology_elements(self, relevant_classes: List[str], relevant_properties: List[str]) -> Dict[str, Any]:
        """Extract the actual ontology elements based on LLM recommendations."""
        if not self._graph:
            return {"nodes": [], "edges": [], "literals": []}
        
        nodes = []
        edges = []
        literals = []
        
        # Build case-insensitive lookup for matching
        class_keywords = [c.lower() for c in relevant_classes]
        prop_keywords = [p.lower() for p in relevant_properties]
        
        # Extract relevant triples
        for s, p, o in self._graph.triples((None, None, None)):
            s_str = str(s).split('/')[-1].split('#')[-1].lower()
            p_str = str(p).split('/')[-1].split('#')[-1].lower()
            
            # Check if this triple is relevant
            is_relevant = False
            
            # Check subject against classes
            if any(keyword in s_str for keyword in class_keywords):
                is_relevant = True
            
            # Check predicate against properties
            if any(keyword in p_str for keyword in prop_keywords):
                is_relevant = True
            
            # Check object if it's a URI
            if isinstance(o, URIRef):
                o_str = str(o).split('/')[-1].split('#')[-1].lower()
                if any(keyword in o_str for keyword in class_keywords):
                    is_relevant = True
            
            if is_relevant:
                # Add to appropriate collection
                if isinstance(o, Literal):
                    literals.append({
                        "subject": str(s),
                        "predicate": str(p),
                        "object": str(o),
                        "datatype": str(o.datatype) if o.datatype else None
                    })
                else:
                    edges.append({
                        "subject": str(s),
                        "predicate": str(p),
                        "object": str(o)
                    })
                
                # Add nodes for subjects and objects
                if str(s) not in [n.get("uri") for n in nodes]:
                    nodes.append({
                        "uri": str(s),
                        "type": "resource",
                        "local_name": str(s).split('/')[-1].split('#')[-1]
                    })
                
                if isinstance(o, URIRef) and str(o) not in [n.get("uri") for n in nodes]:
                    nodes.append({
                        "uri": str(o),
                        "type": "resource", 
                        "local_name": str(o).split('/')[-1].split('#')[-1]
                    })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "literals": literals
        }

    async def run(self, **kwargs) -> Dict[str, Any]:  # type: ignore[override]
        """
        Extract relevant ontology slice using LLM reasoning.
        
        Args:
            **kwargs: Keyword arguments including:
                - question: The natural language question
                - mode: Output mode (currently only "ttl" supported)
                - datasets: Optional list of target datasets to focus on
            
        Returns:
            Dictionary with ontology slice in the expected format
        """
        question = kwargs.get("question", "")
        mode = kwargs.get("mode", "ttl")
        datasets = kwargs.get("datasets")
        
        self.logger.debug(f"LLM ontology extraction for: {question}")
        
        # Build the extraction prompt
        prompt = self._build_ontology_prompt(question, datasets)
        
        # Get LLM response with structured output
        expected_keys = ["relevant_classes", "relevant_properties", "key_concepts", "reasoning"]
        fallback = {
            "relevant_classes": [],
            "relevant_properties": [],
            "key_concepts": [],
            "reasoning": "LLM ontology extraction failed"
        }
        
        llm_result = await self.llm_client.generate_structured(
            prompt=prompt,
            expected_keys=expected_keys,
            fallback_value=fallback
        )
        
        # Extract LLM recommendations
        relevant_classes = llm_result.get("relevant_classes", [])
        relevant_properties = llm_result.get("relevant_properties", [])
        key_concepts = llm_result.get("key_concepts", [])
        reasoning = llm_result.get("reasoning", "")
        
        # Validate types
        if not isinstance(relevant_classes, list):
            relevant_classes = []
        if not isinstance(relevant_properties, list):
            relevant_properties = []
        if not isinstance(key_concepts, list):
            key_concepts = []
        
        # Extract actual ontology elements based on LLM recommendations
        ontology_elements = self._extract_ontology_elements(relevant_classes, relevant_properties)
        
        self.logger.info(
            f"LLM ontology extraction complete: {len(ontology_elements['nodes'])} nodes, "
            f"{len(ontology_elements['edges'])} edges, {len(ontology_elements['literals'])} literals"
        )
        
        return {
            "nodes": ontology_elements["nodes"],
            "edges": ontology_elements["edges"],
            "literals": ontology_elements["literals"],
            "reasoning": reasoning,
            "key_concepts": key_concepts,
            "llm_metadata": {
                "agent": "llm_ontology",
                "question_length": len(question),
                "datasets_focused": datasets or [],
                "classes_identified": len(relevant_classes),
                "properties_identified": len(relevant_properties)
            }
        }


__all__ = ["LLMOntologyAgent", "LLMOntologySlice"]
