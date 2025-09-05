"""Agent package exports (skeleton multi-agent architecture).

This module provides safe imports that handle missing optional dependencies.
Only core base classes are imported unconditionally.
"""

# Core base classes - no dependencies
from .base import BaseAgent, AgentConfig

# Agents with dependencies - import conditionally
try:
    from .ontology_agent import UnifiedOntologyAgent
except ImportError:
    UnifiedOntologyAgent = None

try:
    from .example_agent import ExampleRetrievalAgent
except ImportError:
    ExampleRetrievalAgent = None

try:
    from .supervisor import SupervisorAgent
except ImportError:
    SupervisorAgent = None

try:
    from .router_agent import RouterAgent
except ImportError:
    RouterAgent = None

# LLM-powered agents
try:
    from .llm_router_agent import LLMRouterAgent
except ImportError:
    LLMRouterAgent = None

# Agents with optional dependencies 
try:
    from .wikidata_agent import WikidataAgent
except ImportError:
    # Wikidata agent requires aiohttp and other optional dependencies
    WikidataAgent = None

# More LLM-powered agents with optional dependencies
try:
    from .llm_ontology_agent import LLMOntologyAgent
except ImportError:
    LLMOntologyAgent = None

try:
    from .llm_example_agent import LLMExampleAgent
except ImportError:
    LLMExampleAgent = None

try:
    from .llm_supervisor import LLMSupervisorAgent
except ImportError:
    LLMSupervisorAgent = None

# Export list for clarity
__all__ = [
    'BaseAgent', 
    'AgentConfig',
    'UnifiedOntologyAgent',
    'ExampleRetrievalAgent', 
    'SupervisorAgent',
    'RouterAgent',
    'LLMRouterAgent',
    'WikidataAgent',
    'LLMOntologyAgent',
    'LLMExampleAgent', 
    'LLMSupervisorAgent'
]

