"""
LLM-Powered Example Agent

This agent uses an LLM to intelligently select relevant examples from the query database
based on semantic similarity rather than simple token overlap.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
import pandas as pd
from pathlib import Path
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

DATASET_FILE = Path(__file__).resolve().parents[1] / "query_database_10july2025.csv"


class LLMExampleAgent(BaseAgent):
    """
    LLM-powered example retrieval agent that selects relevant examples
    using semantic understanding rather than token overlap.
    """
    name = "llm_examples"

    def __init__(
        self, 
        llm_client: Optional[LLMClient] = None,
        k_default: int = 3,
        *args, 
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.llm_client = llm_client or create_llm_client()
        self.k_default = k_default
        self._df: pd.DataFrame | None = None
        self._examples_summary: str | None = None
        self._loaded = False

    def _ensure_loaded(self) -> None:
        """Load the example dataset."""
        if self._loaded:
            return
        
        if DATASET_FILE.exists():
            try:
                self._df = pd.read_csv(DATASET_FILE)
                self.logger.info(f"Loaded {len(self._df)} examples from database")
                self._create_examples_summary()
            except Exception as e:
                self.logger.error(f"Failed to load examples: {e}")
                self._df = None
        else:
            self.logger.warning(f"Examples file not found: {DATASET_FILE}")
            self._df = None
        
        self._loaded = True

    def _create_examples_summary(self) -> None:
        """Create a summary of available examples for LLM processing."""
        if self._df is None or len(self._df) == 0:
            self._examples_summary = "No examples available"
            return
        
        # Find question and SPARQL columns
        col_q = next((c for c in ["NL_question", "question", "nl_question"] if c in self._df.columns), None)
        col_sparql = next((c for c in ["Final_SPARQL", "gold_sparql", "sparql"] if c in self._df.columns), None)
        
        if not col_q:
            self._examples_summary = "No question column found in examples"
            return
        
        # Create a sample of questions for the LLM to understand the types of queries available
        sample_questions = []
        for idx, row in self._df.head(10).iterrows():  # Sample first 10
            q_text = str(row[col_q])
            if len(q_text) > 100:
                q_text = q_text[:97] + "..."
            sample_questions.append(f"- {q_text}")
        
        self._examples_summary = f"""EXAMPLE QUERIES AVAILABLE:
Total examples: {len(self._df)}
Sample questions:
{chr(10).join(sample_questions)}"""

    def _build_example_selection_prompt(self, question: str, k: int) -> str:
        """Build the LLM prompt for example selection."""
        self._ensure_loaded()
        
        if self._df is None or len(self._df) == 0:
            return ""
        
        # Find question column
        col_q = next((c for c in ["NL_question", "question", "nl_question"] if c in self._df.columns), None)
        if not col_q:
            return ""
        
        # Get all available questions for the LLM to choose from
        available_examples = []
        for idx, row in self._df.iterrows():
            q_text = str(row[col_q])
            if q_text and q_text.strip():
                available_examples.append({
                    "index": idx,  # Keep original index
                    "question": q_text
                })
        
        # Limit to reasonable number for LLM processing
        if len(available_examples) > 50:
            # Take a diverse sample
            step = len(available_examples) // 50
            available_examples = available_examples[::step][:50]
        
        examples_text = "\n".join([
            f"{i+1}. (Index {ex['index']}) {ex['question']}"
            for i, ex in enumerate(available_examples)
        ])
        
        prompt = f"""You are a query example selection specialist. Given a natural language question, you need to identify the most semantically similar examples from a database of previous questions and their SPARQL queries.

TARGET QUESTION: "{question}"

AVAILABLE EXAMPLES:
{examples_text}

Your task is to:
1. Analyze the semantic content and intent of the target question
2. Find the {k} most similar examples that could help with SPARQL generation
3. Consider similar concepts, entities, query patterns, and intent
4. Prioritize examples that share similar:
   - Musical concepts (composers, works, instruments, etc.)
   - Query patterns (finding, listing, filtering, etc.)
   - Entity types and relationships
   - Temporal or descriptive constraints

Return your response as a JSON object with this exact structure:
{{
    "selected_indices": [index1, index2, index3],
    "similarity_scores": [0.9, 0.7, 0.6],
    "reasoning": "Brief explanation of why these examples are most relevant"
}}

Where:
- selected_indices: List of the database indices for the most similar examples
- similarity_scores: Confidence scores (0.0-1.0) for each selected example
- reasoning: Your explanation for the selections

Focus on semantic similarity rather than exact keyword matching. Look for examples that solve similar types of musical information needs."""

        return prompt

    async def run(self, **kwargs) -> List[Dict[str, Any]]:  # type: ignore[override]
        """
        Retrieve relevant examples using LLM-based semantic selection.
        
        Args:
            **kwargs: Keyword arguments including:
                - question: The natural language question
                - k: Number of examples to retrieve (optional)
            
        Returns:
            List of relevant example dictionaries
        """
        question = kwargs.get("question", "")
        k = kwargs.get("k", self.k_default)
        
        self.logger.debug(f"LLM example selection for: {question}")
        
        self._ensure_loaded()
        
        if self._df is None or len(self._df) == 0:
            self.logger.warning("No examples available")
            return []
        
        # Find column names
        col_q = next((c for c in ["NL_question", "question", "nl_question"] if c in self._df.columns), None)
        col_sparql = next((c for c in ["Final_SPARQL", "gold_sparql", "sparql"] if c in self._df.columns), None)
        
        if not col_q:
            self.logger.error("No question column found in examples dataset")
            return []
        
        # Build the selection prompt
        prompt = self._build_example_selection_prompt(question, k)
        
        if not prompt:
            self.logger.error("Could not build example selection prompt")
            return []
        
        # Get LLM response with structured output
        expected_keys = ["selected_indices", "similarity_scores", "reasoning"]
        fallback = {
            "selected_indices": [],
            "similarity_scores": [],
            "reasoning": "LLM example selection failed"
        }
        
        llm_result = await self.llm_client.generate_structured(
            prompt=prompt,
            expected_keys=expected_keys,
            fallback_value=fallback
        )
        
        # Extract LLM recommendations
        selected_indices = llm_result.get("selected_indices", [])
        similarity_scores = llm_result.get("similarity_scores", [])
        reasoning = llm_result.get("reasoning", "")
        
        # Validate and clean results
        if not isinstance(selected_indices, list):
            selected_indices = []
        if not isinstance(similarity_scores, list):
            similarity_scores = []
        
        # Ensure we have valid indices
        valid_indices = []
        valid_scores = []
        for i, idx in enumerate(selected_indices):
            if isinstance(idx, int) and 0 <= idx < len(self._df):
                valid_indices.append(idx)
                if i < len(similarity_scores) and isinstance(similarity_scores[i], (int, float)):
                    valid_scores.append(float(similarity_scores[i]))
                else:
                    valid_scores.append(0.5)  # Default score
        
        # Build result examples
        examples = []
        for i, idx in enumerate(valid_indices):
            try:
                row = self._df.iloc[idx]
                example = {
                    "question": str(row[col_q]),
                    "index": idx,
                    "similarity_score": valid_scores[i] if i < len(valid_scores) else 0.5
                }
                
                # Add SPARQL if available
                if col_sparql and col_sparql in row and pd.notna(row[col_sparql]):
                    example["sparql"] = str(row[col_sparql])
                
                # Add any other columns that might be useful
                for col in self._df.columns:
                    if col not in [col_q, col_sparql] and pd.notna(row[col]):
                        example[col] = str(row[col])
                
                examples.append(example)
            except Exception as e:
                self.logger.warning(f"Failed to process example at index {idx}: {e}")
        
        self.logger.info(
            f"LLM example selection complete: {len(examples)} examples selected "
            f"with average similarity {sum(valid_scores)/len(valid_scores):.2f}" if valid_scores else "0"
        )
        
        return examples


__all__ = ["LLMExampleAgent"]
