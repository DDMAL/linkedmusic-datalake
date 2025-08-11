"""Example Retrieval Agent (token overlap baseline)."""
from __future__ import annotations

from typing import Any, Dict, List
import pandas as pd
from pathlib import Path
import re
from .base import BaseAgent

DATASET_FILE = Path(__file__).resolve().parents[1] / "query_database_10july2025.csv"


class ExampleRetrievalAgent(BaseAgent):
    name = "examples"

    def __init__(self, *args, k_default: int = 3, **kwargs):
        super().__init__(*args, **kwargs)
        self.k_default = k_default
        self._df = None

    def _ensure_loaded(self):
        if self._df is not None:
            return
        if DATASET_FILE.exists():
            try:
                self._df = pd.read_csv(DATASET_FILE)
            except Exception:  # pragma: no cover
                self._df = None

    def _tokenize(self, text: str) -> set[str]:
        return {t for t in re.findall(r"[a-zA-Z0-9]+", text.lower()) if len(t) >= 3}

    async def run(self, question: str, k: int | None = None) -> List[Dict[str, Any]]:  # type: ignore[override]
        self._ensure_loaded()
        if self._df is None:
            return []
        k = k or self.k_default
        q_tokens = self._tokenize(question)
        if not q_tokens:
            return []
        rows: List[Dict[str, Any]] = []
        col_q = next((c for c in ["NL_question", "question", "nl_question"] if c in self._df.columns), None)
        col_sparql = next((c for c in ["Final_SPARQL", "gold_sparql", "sparql"] if c in self._df.columns), None)
        if not col_q:
            return []
        for _, r in self._df.iterrows():
            txt = str(r[col_q])
            ex_tokens = self._tokenize(txt)
            if not ex_tokens:
                continue
            overlap = len(q_tokens & ex_tokens) / max(1, len(q_tokens))
            if overlap == 0:
                continue
            rows.append({"question": txt, "sparql": str(r[col_sparql]) if col_sparql else None, "overlap": overlap})
        rows.sort(key=lambda x: x["overlap"], reverse=True)
        return rows[:k]


__all__ = ["ExampleRetrievalAgent"]
