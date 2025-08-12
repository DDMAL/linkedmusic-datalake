"""Catalog capability loader utilities.

Loads capabilities.*.json manifests and provides helpers to validate concept support
and map dataset codes to ontology prefixes.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Any, Optional
import json

CATALOG_DIR = Path(__file__).resolve().parent

_DATASET_PREFIX: Dict[str, str] = {
    "musicbrainz": "mb:",
    "thesession": "ts:",
    "diamm": "diamm:",
    "dtl": "dtl:",
    "gj": "gj:",
}


def dataset_prefix(dataset: str) -> Optional[str]:
    return _DATASET_PREFIX.get(dataset)


def load_capabilities(datasets: List[str] | None = None) -> Dict[str, Dict[str, Any]]:
    """Load capability manifests for specified datasets (or all present if None).

    Returns a dict: {dataset_code: manifest_dict}
    """
    out: Dict[str, Dict[str, Any]] = {}
    if datasets:
        candidates = [CATALOG_DIR / f"capabilities.{d}.json" for d in datasets]
    else:
        candidates = list(CATALOG_DIR.glob("capabilities.*.json"))
    for p in candidates:
        if not p.exists():
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        # derive dataset code from filename
        name = p.stem.split(".", 1)[1] if "." in p.stem else p.stem
        out[name] = data
    return out


def supports_concepts(cap: Dict[str, Any], concept_hints: List[str]) -> bool:
    """Return True if capabilities declare entities that cover the hinted concepts.

    Very lenient: if any hinted concept exists in entities keys, treat as supported.
    """
    if not concept_hints:
        return True
    ents = set((cap.get("entities") or {}).keys())
    return any(c in ents for c in concept_hints)


__all__ = ["load_capabilities", "supports_concepts", "dataset_prefix"]
