"""
LLM-Powered RouterAgent

This agent uses an LLM to intelligently route questions to appropriate datasets
based on the semantic content of the question, rather than simple pattern matching.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import logging
import json

from .base import BaseAgent
try:
    from ..llm import create_llm_client, LLMClient
except ImportError:
    # Fallback for test context
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from llm import create_llm_client, LLMClient

try:
    from ..catalog.loader import load_router_indexes
except Exception:
    from catalog.loader import load_router_indexes  # type: ignore


@dataclass
class LLMRoutingResult:
    ranked_datasets: List[str]
    dataset_scores: Dict[str, float]
    concept_hints: List[str]
    reasoning: str
    llm_metadata: Dict[str, Any]


class LLMRouterAgent(BaseAgent):
    """
    LLM-powered router that intelligently routes questions to datasets
    based on semantic understanding rather than pattern matching.
    """
    name = "llm_router"

    def __init__(
        self, 
        llm_client: Optional[LLMClient] = None,
        *args, 
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.llm_client = llm_client or create_llm_client()
        self._dataset_info: Dict[str, Any] | None = None
        self._loaded = False

    def _ensure_loaded(self) -> None:
        """Load dataset information for routing decisions."""
        if self._loaded:
            return
        
        try:
            self._dataset_info = load_router_indexes()
            self._loaded = True
            self.logger.debug(f"Loaded dataset info for {len(self._dataset_info)} datasets")
        except Exception as e:
            self.logger.error(f"Failed to load dataset info: {e}")
            self._dataset_info = {}
            self._loaded = True

    def _get_dataset_descriptions(self) -> Dict[str, str]:
        """Get comprehensive descriptions of available datasets."""
        # Comprehensive dataset descriptions based on the actual system capabilities
        descriptions = {
            "diamm": "DIAMM (Digital Image Archive of Medieval Music) - Medieval and Renaissance music manuscripts, incipits, sources, and paleographic data. Specializes in manuscript context, historical compositions, and early music notation.",
            
            "session": "The Session - Traditional Irish music community platform. Contains tunes, tune sets, session recordings, and Irish traditional music metadata. Focuses on folk melodies and community-contributed content.",
            
            "dlt1000": "Dig That Lick (DTL-1000) - Jazz solo transcriptions and improvisation analysis. Contains recordings, solos, licks, and harmonic analysis from jazz performances, particularly focused on improvisation patterns.",
            
            "global-jukebox": "The Global Jukebox - Ethnomusicological database of world music traditions. Contains cultural classification, indigenous music, language associations, and cross-cultural musical analysis.",
            
            "musicbrainz": "MusicBrainz - Comprehensive music metadata database. Rich recording and release metadata, composer and performer relations, label hierarchy, and detailed discographic information.",
            
            "thesession": "The Session - Traditional Irish music tunes and session metadata. Community-driven database of Irish traditional music with tune variants and session details."
        }
        
        # Get the actual available datasets from the config
        try:
            from ..config import Config
            config = Config()
            available_databases = config.get_available_databases()
            
            # Filter descriptions to only include available datasets
            filtered_descriptions = {}
            for db in available_databases:
                if db in descriptions:
                    filtered_descriptions[db] = descriptions[db]
                elif db == "dlt1000":
                    filtered_descriptions[db] = descriptions.get("dlt1000", "Jazz improvisation and solo analysis database")
                elif db == "global-jukebox":
                    filtered_descriptions[db] = descriptions.get("global-jukebox", "World music and ethnomusicological database")
                else:
                    # Fallback for any other datasets
                    filtered_descriptions[db] = f"Music database: {db}"
            
            return filtered_descriptions
            
        except Exception as e:
            self.logger.warning(f"Could not load dataset config: {e}")
            # Fallback to core datasets if config loading fails
            return {
                "diamm": descriptions["diamm"],
                "session": descriptions["session"], 
                "dlt1000": descriptions["dlt1000"],
                "global-jukebox": descriptions["global-jukebox"]
            }

    def _build_routing_prompt(self, question: str) -> str:
        """Build the LLM prompt for routing decisions."""
        self._ensure_loaded()
        
        # Get comprehensive dataset descriptions
        dataset_descriptions = self._get_dataset_descriptions()
        
        # Format dataset information for the LLM
        dataset_info_text = []
        for ds_name, description in dataset_descriptions.items():
            dataset_info_text.append(f"- **{ds_name}**: {description}")
        
        available_datasets = "\n".join(dataset_info_text)
        
        prompt = f"""You are a music data routing specialist. Given a natural language question about music, you need to determine which dataset(s) would be most relevant to answer it.

IMPORTANT: Most queries benefit from MULTIPLE datasets. Don't hesitate to select 2-3 relevant datasets, especially when combining specialized datasets with comprehensive ones like MusicBrainz.

AVAILABLE DATASETS:
{available_datasets}

DATASET ROUTING GUIDELINES:
- **DIAMM**: Best for medieval/renaissance composers, manuscripts, historical sources, incipits, paleography
- **The Session**: Best for Irish traditional music, folk tunes, community sessions, tune variants
- **DTL-1000**: Best for jazz analysis, improvisation, solos, harmonic analysis, recording details
- **Global Jukebox**: Best for world music, ethnomusicology, cultural classification, indigenous traditions
- **MusicBrainz**: Best for modern recordings, releases, labels, comprehensive metadata, discography (OFTEN ESSENTIAL)

MULTI-DATABASE ROUTING STRATEGIES:
- **Historical + Modern**: DIAMM + MusicBrainz (manuscripts + recordings of historical works)
- **Traditional + Commercial**: The Session + MusicBrainz (folk tunes + official releases)
- **Jazz Analysis + Metadata**: DTL-1000 + MusicBrainz (transcriptions + recording details)
- **Cultural + Commercial**: Global Jukebox + MusicBrainz (ethnographic + commercial recordings)
- **Comprehensive Artist Queries**: MusicBrainz + all relevant specialized datasets

QUESTION: "{question}"

Your task is to:
1. Analyze the semantic content of the question
2. Identify key musical concepts, time periods, genres, or entities mentioned
3. Select 1-3 relevant datasets (prefer multiple when beneficial)
4. Assign confidence scores (0.0 to 1.0) for each relevant dataset
5. Extract concept hints that might help with further processing

Return your response as a JSON object with this exact structure:
{{
    "ranked_datasets": ["dataset1", "dataset2", "dataset3"],
    "dataset_scores": {{"dataset1": 0.9, "dataset2": 0.7, "dataset3": 0.5}},
    "concept_hints": ["concept1", "concept2", ...],
    "reasoning": "Brief explanation of your multi-dataset routing decision"
}}

Focus on semantic relevance and consider that combining datasets often provides richer, more complete answers:
- **Time periods**: medieval/renaissance → DIAMM + MusicBrainz, traditional → The Session + MusicBrainz
- **Geography**: Irish → The Session + MusicBrainz, world cultures → Global Jukebox + MusicBrainz
- **Musical forms**: manuscripts → DIAMM + MusicBrainz, jazz → DTL-1000 + MusicBrainz
- **Analysis type**: improvisation → DTL-1000 + MusicBrainz, cultural → Global Jukebox + MusicBrainz

Only include datasets with scores > 0.1 in your response."""

        return prompt

    async def run(self, question: str) -> Dict[str, Any]:  # type: ignore[override]
        """
        Route the question to appropriate datasets using LLM reasoning.
        
        Args:
            question: The natural language question to route
            
        Returns:
            Dictionary with routing results in the expected format
        """
        self.logger.info(f"🎯 LLM Router: Starting routing for query: {question}")
        
        # Build the routing prompt
        prompt = self._build_routing_prompt(question)
        self.logger.debug(f"📝 Built routing prompt ({len(prompt)} chars)")
        
        # Get LLM response with structured output
        expected_keys = ["ranked_datasets", "dataset_scores", "concept_hints", "reasoning"]
        fallback = {
            "ranked_datasets": [],
            "dataset_scores": {},
            "concept_hints": [],
            "reasoning": "LLM routing failed"
        }
        
        self.logger.info("🤖 Sending routing request to LLM")
        llm_result = await self.llm_client.generate_structured(
            prompt=prompt,
            expected_keys=expected_keys,
            fallback_value=fallback
        )
        
        # Validate and clean the results
        ranked_datasets = llm_result.get("ranked_datasets", [])
        dataset_scores = llm_result.get("dataset_scores", {})
        concept_hints = llm_result.get("concept_hints", [])
        reasoning = llm_result.get("reasoning", "")
        
        self.logger.info(
            f"✅ LLM Router: Received response",
            extra={
                'agent_step': 'Routing result received',
                'llm_response': json.dumps(llm_result, indent=2)
            }
        )
        
        # Validate and clean the results
        ranked_datasets = llm_result.get("ranked_datasets", [])
        dataset_scores = llm_result.get("dataset_scores", {})
        concept_hints = llm_result.get("concept_hints", [])
        reasoning = llm_result.get("reasoning", "")
        
        # Ensure types are correct
        if not isinstance(ranked_datasets, list):
            ranked_datasets = []
        if not isinstance(dataset_scores, dict):
            dataset_scores = {}
        if not isinstance(concept_hints, list):
            concept_hints = []
        if not isinstance(reasoning, str):
            reasoning = ""
        
        # Filter out invalid scores
        dataset_scores = {
            k: float(v) for k, v in dataset_scores.items() 
            if isinstance(v, (int, float)) and 0.0 <= float(v) <= 1.0
        }
        
        # Re-rank datasets by scores if needed
        if dataset_scores:
            ranked_datasets = sorted(
                dataset_scores.keys(), 
                key=lambda x: dataset_scores.get(x, 0.0), 
                reverse=True
            )
        
        self.logger.info(
            f"🎯 LLM Router: Routing complete - {len(ranked_datasets)} datasets selected",
            extra={
                'agent_step': 'Final routing result',
                'llm_response': json.dumps({
                    "ranked_datasets": ranked_datasets,
                    "dataset_scores": dataset_scores,
                    "concept_hints": concept_hints,
                    "reasoning": reasoning
                }, indent=2)
            }
        )
        
        return {
            "ranked_datasets": ranked_datasets,
            "dataset_scores": dataset_scores,
            "concept_hints": concept_hints,
            "reasoning": reasoning,
            "llm_metadata": {
                "agent": "llm_router",
                "question_length": len(question),
                "datasets_considered": len(self._dataset_info or {})
            }
        }


__all__ = ["LLMRouterAgent", "LLMRoutingResult"]
