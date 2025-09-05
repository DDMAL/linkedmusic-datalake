"""
LLM-Powered Supervisor Agent

This agent uses an LLM to orchestrate and coordinate the other agents,
making intelligent decisions about which agents to call and how to combine their results.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import logging
import json

from .base import BaseAgent, AgentConfig
try:
    from ..llm import create_llm_client, LLMClient
except ImportError:
    # Fallback for test context
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from llm import create_llm_client, LLMClient

try:
    from ..catalog.loader import load_capabilities, supports_concepts
except Exception:
    from catalog.loader import load_capabilities, supports_concepts  # type: ignore


@dataclass
class LLMSupervisorResult:
    question: str
    routing: Dict[str, Any]
    ontology_slice: Dict[str, Any]
    resolved_entities: Dict[str, Optional[str]]
    examples: List[Dict[str, Any]]
    prompt: Dict[str, Any]
    orchestration_reasoning: str
    llm_metadata: Dict[str, Any]


class LLMSupervisorAgent(BaseAgent):
    """
    LLM-powered supervisor that orchestrates sub-agents using intelligent reasoning
    about which agents to call and how to combine their results.
    """
    name = "llm_supervisor"

    def __init__(
        self,
        ontology_agent: BaseAgent,
        wikidata_agent: Any,
        example_agent: BaseAgent,
        prompt_builder,
        router_agent: BaseAgent | None = None,
        llm_client: Optional[LLMClient] = None,
        config: Optional[AgentConfig] = None,
        logger: Optional[logging.Logger] = None,
    ):
        super().__init__(config=config, logger=logger)
        self.ontology_agent = ontology_agent
        self.wikidata_agent = wikidata_agent
        self.example_agent = example_agent
        self.prompt_builder = prompt_builder
        self.router_agent = router_agent
        self.llm_client = llm_client or create_llm_client()

    def _build_orchestration_prompt(self, question: str) -> str:
        """Build the LLM prompt for orchestration decisions."""
        agent_descriptions = {
            "router": "Routes questions to relevant datasets based on content analysis",
            "ontology": "Extracts relevant ontology elements for the question domain",
            "wikidata": "Resolves entities and properties to Wikidata QIDs/PIDs", 
            "examples": "Finds similar previous questions and their SPARQL queries"
        }
        
        available_agents = []
        if self.router_agent:
            available_agents.append("router")
        available_agents.extend(["ontology", "wikidata", "examples"])
        
        agents_text = "\n".join([
            f"- **{agent}**: {agent_descriptions.get(agent, 'No description')}"
            for agent in available_agents
        ])
        
        prompt = f"""You are an intelligent orchestration agent for a natural language to SPARQL system. Given a question, you need to decide how to coordinate different specialist agents to gather the information needed for SPARQL generation.

QUESTION: "{question}"

AVAILABLE AGENTS:
{agents_text}

Your task is to:
1. Analyze the question to understand what information will be needed
2. Decide which agents should be called and in what order
3. Determine any special parameters or focus areas for each agent
4. Consider dependencies between agents (e.g., routing results can guide ontology focus)
5. Plan how to handle potential failures gracefully

Return your response as a JSON object with this exact structure:
{{
    "execution_plan": [
        {{
            "agent": "agent_name",
            "parameters": {{"param1": "value1", "param2": "value2"}},
            "reasoning": "Why this agent is needed",
            "critical": true
        }}
    ],
    "dataset_hints": ["dataset1", "dataset2"],
    "entity_extraction_focus": ["entity_type1", "entity_type2"],
    "orchestration_strategy": "sequential|parallel|adaptive",
    "fallback_plan": "What to do if critical agents fail",
    "reasoning": "Overall reasoning for this orchestration plan"
}}

Consider:
- **Sequential**: Call agents one by one, using results to inform subsequent calls
- **Parallel**: Call independent agents simultaneously for efficiency
- **Adaptive**: Start with core agents, then adapt based on their results

Focus on:
- Musical domain expertise (composers, works, instruments, etc.)
- Temporal constraints (dates, periods, etc.)
- Geographic or cultural context
- Query complexity and specificity"""

        return prompt

    async def _execute_orchestration_plan(
        self, 
        question: str, 
        execution_plan: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute the orchestration plan and gather results from agents."""
        results = {
            "routing": {"ranked_datasets": [], "dataset_scores": {}, "concept_hints": []},
            "ontology_slice": {"nodes": [], "edges": [], "literals": []},
            "resolved_entities": {},
            "examples": []
        }
        
        # Execute plan steps
        for step in execution_plan:
            agent_name = step.get("agent", "")
            parameters = step.get("parameters", {})
            is_critical = step.get("critical", False)
            
            try:
                if agent_name == "router" and self.router_agent:
                    self.logger.debug("Executing router agent")
                    routing_result = await self.router_agent.run(question=question, **parameters)
                    results["routing"] = routing_result
                    
                elif agent_name == "ontology":
                    self.logger.debug("Executing ontology agent")
                    # Use routing results to focus ontology extraction
                    datasets = results["routing"].get("ranked_datasets", [])[:2]  # Top 2 datasets
                    ontology_params = {"question": question, "datasets": datasets, **parameters}
                    ontology_result = await self.ontology_agent.run(**ontology_params)
                    results["ontology_slice"] = ontology_result
                    
                elif agent_name == "wikidata":
                    self.logger.debug("Executing Wikidata agent")
                    # Extract tokens for entity resolution
                    tokens = [t.strip(",.?;:") for t in question.split() if len(t) > 3]
                    entity_result = await self.wikidata_agent.lookup_entities_and_properties(tokens, tokens)
                    results["resolved_entities"] = entity_result
                    
                elif agent_name == "examples":
                    self.logger.debug("Executing example agent")
                    example_params = {"question": question, **parameters}
                    example_result = await self.example_agent.run(**example_params)
                    results["examples"] = example_result
                    
                else:
                    self.logger.warning(f"Unknown agent in plan: {agent_name}")
                    
            except Exception as e:
                self.logger.error(f"Agent {agent_name} failed: {e}")
                if is_critical:
                    self.logger.error(f"Critical agent {agent_name} failed, continuing with partial results")
        
        return results

    async def run(self, question: str) -> LLMSupervisorResult:  # type: ignore[override]
        """
        Orchestrate the multi-agent system using LLM-powered coordination.
        
        Args:
            question: The natural language question to process
            
        Returns:
            LLMSupervisorResult with all agent outputs and orchestration metadata
        """
        self.logger.debug("LLM supervisor orchestrating: %s", question)
        
        # Get orchestration plan from LLM
        orchestration_prompt = self._build_orchestration_prompt(question)
        
        expected_keys = [
            "execution_plan", "dataset_hints", "entity_extraction_focus",
            "orchestration_strategy", "fallback_plan", "reasoning"
        ]
        fallback_plan = {
            "execution_plan": [
                {"agent": "router", "parameters": {}, "reasoning": "Default routing", "critical": False},
                {"agent": "ontology", "parameters": {}, "reasoning": "Default ontology", "critical": True},
                {"agent": "wikidata", "parameters": {}, "reasoning": "Default entity resolution", "critical": True},
                {"agent": "examples", "parameters": {}, "reasoning": "Default examples", "critical": False}
            ],
            "dataset_hints": [],
            "entity_extraction_focus": [],
            "orchestration_strategy": "sequential",
            "fallback_plan": "Continue with available results",
            "reasoning": "LLM orchestration failed, using default plan"
        }
        
        orchestration_result = await self.llm_client.generate_structured(
            prompt=orchestration_prompt,
            expected_keys=expected_keys,
            fallback_value=fallback_plan
        )
        
        # Extract orchestration plan
        execution_plan = orchestration_result.get("execution_plan", fallback_plan["execution_plan"])
        orchestration_reasoning = orchestration_result.get("reasoning", "")
        
        # Validate execution plan
        if not isinstance(execution_plan, list):
            execution_plan = fallback_plan["execution_plan"]
        
        # Execute the orchestration plan
        agent_results = await self._execute_orchestration_plan(question, execution_plan)
        
        # Apply capability filtering (legacy logic for compatibility)
        routing = agent_results["routing"]
        ranked = routing.get("ranked_datasets", [])
        concept_hints = routing.get("concept_hints", []) or []
        
        caps = load_capabilities(ranked if ranked else None)
        selected: List[str] = []
        for ds in ranked:
            cap = caps.get(ds)
            if cap and supports_concepts(cap, concept_hints):
                selected.append(ds)
        
        # Soft cap to 2 datasets
        if len(selected) > 2:
            selected = selected[:2]
        
        plan = {
            "datasets_selected": selected,
            "concepts": concept_hints,
            "rationale": "LLM-guided capability-filtered routing",
            "orchestration_strategy": orchestration_result.get("orchestration_strategy", "sequential")
        }
        
        # Build final prompt
        ontology_mode = self.config.get("ontology_mode", "ttl") if self.config else "ttl"
        prompt = self.prompt_builder.build_prompt(
            question=question,
            ontology_slice=agent_results["ontology_slice"],
            resolved=agent_results["resolved_entities"],
            examples=agent_results["examples"],
            config={
                **(self.config.settings if self.config else {}), 
                "routing": routing, 
                "plan": plan,
                "orchestration": orchestration_result
            },
        )
        
        self.logger.info(
            f"LLM supervisor orchestration complete: "
            f"{len(selected)} datasets, {len(agent_results['examples'])} examples"
        )
        
        return LLMSupervisorResult(
            question=question,
            routing=routing,
            ontology_slice=agent_results["ontology_slice"],
            resolved_entities=agent_results["resolved_entities"],
            examples=agent_results["examples"],
            prompt=prompt,
            orchestration_reasoning=orchestration_reasoning,
            llm_metadata={
                "agent": "llm_supervisor",
                "execution_plan_steps": len(execution_plan),
                "datasets_selected": len(selected),
                "entities_resolved": len(agent_results["resolved_entities"]),
                "examples_found": len(agent_results["examples"]),
                "orchestration_strategy": orchestration_result.get("orchestration_strategy", "sequential")
            }
        )


__all__ = ["LLMSupervisorAgent", "LLMSupervisorResult"]
