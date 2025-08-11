"""Root test configuration ensuring local 'code' package shadows stdlib 'code'.

Pytest imports test packages using their full package path. Because our source
lives under a top-level directory named 'code', Python could otherwise resolve
`import code` to the standard library interactive interpreter helper module.
Placing the repository root at the front of sys.path guarantees that
`code` refers to our package during test collection (allowing
`code.nlq2sparql` to import successfully when pytest infers that name from the
filesystem layout).
"""
from __future__ import annotations

import sys
from pathlib import Path

_repo_root = Path(__file__).parent.resolve()
if str(_repo_root) not in sys.path[:1]:  # ensure highest priority
    sys.path.insert(0, str(_repo_root))
