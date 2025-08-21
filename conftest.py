"""Root test configuration ensuring repository-root packages resolve first.

Pytest imports test packages using their full package path. Placing the
repository root at the front of ``sys.path`` guarantees package imports like
``shared.nlq2sparql`` resolve to our local sources during test collection.
"""
from __future__ import annotations

import sys
from pathlib import Path

_repo_root = Path(__file__).parent.resolve()
if str(_repo_root) not in sys.path[:1]:  # ensure highest priority
    sys.path.insert(0, str(_repo_root))
