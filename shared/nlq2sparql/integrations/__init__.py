"""Integration package for nlq2sparql.

Note: Avoid importing heavy/provider modules at package import time to keep
lightweight consumers (like tools) free from side effects and import errors
during tests. Import integrations explicitly where needed.
"""

__all__: tuple[str, ...] = ()
