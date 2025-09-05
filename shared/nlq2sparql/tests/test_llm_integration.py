#!/usr/bin/env python3
"""
Test the LLM agents integration without requiring actual API keys.

This creates a mock LLM client to test the agent orchestration workflow.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the parent directory to the path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Mock the LLM client to avoid needing real API keys
class MockLLMResponse:
    def __init__(self, content: str):
        self.content = content
        self.metadata = {"provider": "mock", "model": "mock"}
        self.success = True
        self.error = None

class MockGeminiProvider:
    def get_provider_name(self):
        return "mock_gemini"
    
    async def generate(self, prompt: str, **kwargs):
        # Generate appropriate mock responses based on prompt content
        if "routing" in prompt.lower() or "dataset" in prompt.lower():
            mock_response = """{
                "ranked_datasets": ["diamm"],
                "dataset_scores": {"diamm": 0.9},
                "concept_hints": ["composer", "renaissance", "manuscript"],
                "reasoning": "Mock routing based on musical content detection"
            }"""
        elif "ontology" in prompt.lower() or "extract" in prompt.lower():
            mock_response = """{
                "relevant_classes": ["Composer", "MusicalWork", "Manuscript"],
                "relevant_properties": ["hasComposer", "hasTitle", "composedIn"],
                "key_concepts": ["composition", "manuscript", "renaissance"],
                "reasoning": "Mock ontology extraction for musical query"
            }"""
        elif "example" in prompt.lower() or "similar" in prompt.lower():
            mock_response = """{
                "selected_indices": [1, 5, 12],
                "similarity_scores": [0.9, 0.7, 0.6],
                "reasoning": "Mock example selection based on semantic similarity"
            }"""
        elif "orchestration" in prompt.lower() or "execution" in prompt.lower():
            mock_response = """{
                "execution_plan": [
                    {"agent": "router", "parameters": {}, "reasoning": "Route to appropriate datasets", "critical": false},
                    {"agent": "ontology", "parameters": {}, "reasoning": "Extract relevant ontology", "critical": true},
                    {"agent": "wikidata", "parameters": {}, "reasoning": "Resolve entities", "critical": true},
                    {"agent": "examples", "parameters": {}, "reasoning": "Find similar queries", "critical": false}
                ],
                "dataset_hints": ["diamm"],
                "entity_extraction_focus": ["composer", "work"],
                "orchestration_strategy": "sequential",
                "fallback_plan": "Continue with available results",
                "reasoning": "Mock orchestration plan for musical information query"
            }"""
        else:
            mock_response = '{"mock": true, "reasoning": "Default mock response"}'
        
        return MockLLMResponse(mock_response)

class MockLLMClient:
    def __init__(self):
        self.provider = MockGeminiProvider()
    
    async def generate_with_retry(self, *args, **kwargs):
        return await self.provider.generate(*args, **kwargs)
    
    async def generate_structured(self, prompt, expected_keys, fallback_value=None):
        response = await self.provider.generate(prompt)
        try:
            import json
            return json.loads(response.content)
        except:
            return fallback_value or {key: None for key in expected_keys}

# Monkey patch the LLM client creation
def mock_create_llm_client(*args, **kwargs):
    return MockLLMClient()

# Apply the monkey patch
from shared.nlq2sparql import llm
original_create_llm_client = llm.create_llm_client
llm.create_llm_client = mock_create_llm_client

async def test_llm_agents_integration():
    """Test the LLM agents integration with mock responses."""
    print("Testing LLM agents integration with mock responses...")
    print("=" * 60)
    
    try:
        # Import after monkey patching
        from shared.nlq2sparql.agents import (
            LLMRouterAgent,
            LLMOntologyAgent,
            LLMExampleAgent,
            LLMSupervisorAgent,
            WikidataAgent
        )
        from shared.nlq2sparql.prompt_builder import build_prompt
        
        print("✅ Successfully imported LLM agents")
        
        # Test individual agents
        print("\n--- Testing Router Agent ---")
        router = LLMRouterAgent()
        routing_result = await router.run("Find compositions by Palestrina")
        print(f"Router result: {routing_result.get('ranked_datasets', [])}")
        print(f"Concepts: {routing_result.get('concept_hints', [])}")
        
        print("\n--- Testing Ontology Agent ---")
        ontology = LLMOntologyAgent()
        ontology_result = await ontology.run(
            question="Find compositions by Palestrina",
            datasets=["diamm"]
        )
        print(f"Ontology nodes: {len(ontology_result.get('nodes', []))}")
        print(f"Ontology edges: {len(ontology_result.get('edges', []))}")
        
        print("\n--- Testing Example Agent ---")
        examples = LLMExampleAgent(k_default=2)
        example_result = await examples.run(question="Find works by Bach")
        print(f"Examples found: {len(example_result)}")
        
        print("\n--- Testing Supervisor Agent ---")
        
        # Create a simple prompt builder wrapper
        class PromptBuilderWrapper:
            def build_prompt(self, **kwargs):
                return build_prompt(**kwargs)
        
        supervisor = LLMSupervisorAgent(
            router_agent=router,
            ontology_agent=ontology,
            example_agent=examples,
            wikidata_agent=WikidataAgent(),
            prompt_builder=PromptBuilderWrapper()
        )
        
        supervisor_result = await supervisor.run("Find masses composed by William Byrd")
        print(f"✅ Supervisor completed successfully")
        print(f"Datasets selected: {supervisor_result.routing.get('ranked_datasets', [])}")
        print(f"Entities resolved: {len(supervisor_result.resolved_entities)}")
        print(f"Examples found: {len(supervisor_result.examples)}")
        if hasattr(supervisor_result, 'orchestration_reasoning'):
            print(f"Reasoning: {supervisor_result.orchestration_reasoning}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run the test."""
    success = await test_llm_agents_integration()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 LLM agents integration test PASSED!")
        print("\nThe LLM agents are working correctly with mock responses.")
        print("To use with real LLM calls, set GEMINI_API_KEY environment variable.")
        print("\nUsage:")
        print("  poetry run python -m shared.nlq2sparql.cli \\")
        print("    --llm-agents \\")
        print("    --database diamm \\")
        print("    --provider gemini \\")
        print("    \"Find compositions by Palestrina\"")
        return 0
    else:
        print("❌ LLM agents integration test FAILED!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
