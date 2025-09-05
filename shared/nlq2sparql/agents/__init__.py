"""Agent package exports (skeleton multi-agent architecture).

Import order keeps wikidata agent (which depends only on tools) first to avoid
any rdflib import overhead when only ID resolution is needed.
"""

from .wikidata_agent import WikidataAgent
from .base import BaseAgent, AgentConfig
from .ontology_agent import UnifiedOntologyAgent
from .example_agent import ExampleRetrievalAgent
from .supervisor import SupervisorAgent
from .router_agent import RouterAgent

# LLM-powered agents
from .llm_router_agent import LLMRouterAgent
from .llm_ontology_agent import LLMOntologyAgent
from .llm_example_agent import LLMExampleAgent
from .llm_supervisor import LLMSupervisorAgent

__all__ = [
	"WikidataAgent",
	"BaseAgent",
	"AgentConfig",
	"UnifiedOntologyAgent",
	"ExampleRetrievalAgent",
	"SupervisorAgent",
	"RouterAgent",
	# LLM-powered variants
	"LLMRouterAgent",
	"LLMOntologyAgent", 
	"LLMExampleAgent",
	"LLMSupervisorAgent",
]

