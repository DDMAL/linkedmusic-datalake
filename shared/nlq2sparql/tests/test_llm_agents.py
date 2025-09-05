#!/usr/bin/env python3
"""
Test script for LLM-powered agents.

This script tests the new LLM-powered agents to ensure they work correctly
and produce outputs in the expected format.
"""

import asyncio
import sys
import logging
from pathlib import Path

# Add the parent directory to the path for imports
sys.path.append(str(Path(__file__).parent.parent))

from shared.nlq2sparql.agents import (
    LLMRouterAgent,
    LLMOntologyAgent,
    LLMExampleAgent,
    LLMSupervisorAgent,
    WikidataAgent
)
from shared.nlq2sparql.llm import create_llm_client


async def test_llm_router():
    """Test the LLM Router Agent."""
    print("\n=== Testing LLM Router Agent ===")
    
    try:
        agent = LLMRouterAgent()
        result = await agent.run("Who composed masses in the Renaissance period?")
        
        print(f"Ranked datasets: {result.get('ranked_datasets', [])}")
        print(f"Dataset scores: {result.get('dataset_scores', {})}")
        print(f"Concept hints: {result.get('concept_hints', [])}")
        print(f"Reasoning: {result.get('reasoning', 'N/A')}")
        
        return True
    except Exception as e:
        print(f"LLM Router Agent failed: {e}")
        return False


async def test_llm_ontology():
    """Test the LLM Ontology Agent."""
    print("\n=== Testing LLM Ontology Agent ===")
    
    try:
        agent = LLMOntologyAgent()
        result = await agent.run(
            question="Find compositions by Palestrina",
            datasets=["diamm"]
        )
        
        print(f"Nodes: {len(result.get('nodes', []))}")
        print(f"Edges: {len(result.get('edges', []))}")
        print(f"Literals: {len(result.get('literals', []))}")
        print(f"Reasoning: {result.get('reasoning', 'N/A')}")
        
        return True
    except Exception as e:
        print(f"LLM Ontology Agent failed: {e}")
        return False


async def test_llm_examples():
    """Test the LLM Example Agent."""
    print("\n=== Testing LLM Example Agent ===")
    
    try:
        agent = LLMExampleAgent(k_default=2)
        result = await agent.run(question="Show me works by Bach")
        
        print(f"Examples found: {len(result)}")
        for i, example in enumerate(result[:2]):  # Show first 2
            print(f"Example {i+1}: {example.get('question', 'N/A')}")
            print(f"  Similarity: {example.get('similarity_score', 'N/A')}")
        
        return True
    except Exception as e:
        print(f"LLM Example Agent failed: {e}")
        return False


async def test_llm_supervisor():
    """Test the LLM Supervisor Agent."""
    print("\n=== Testing LLM Supervisor Agent ===")
    
    try:
        # Create mock prompt builder
        class MockPromptBuilder:
            def build_prompt(self, **kwargs):
                return {
                    "prompt_text": "Mock prompt for testing",
                    "metadata": kwargs
                }
        
        # Set up agents
        router_agent = LLMRouterAgent()
        ontology_agent = LLMOntologyAgent()
        example_agent = LLMExampleAgent()
        wikidata_agent = WikidataAgent()
        prompt_builder = MockPromptBuilder()
        
        supervisor = LLMSupervisorAgent(
            router_agent=router_agent,
            ontology_agent=ontology_agent,
            example_agent=example_agent,
            wikidata_agent=wikidata_agent,
            prompt_builder=prompt_builder
        )
        
        result = await supervisor.run("Find masses composed by William Byrd")
        
        print(f"Question: {result.question}")
        print(f"Datasets: {result.routing.get('ranked_datasets', [])}")
        print(f"Entities resolved: {len(result.resolved_entities)}")
        print(f"Examples: {len(result.examples)}")
        print(f"Orchestration reasoning: {result.orchestration_reasoning}")
        
        return True
    except Exception as e:
        print(f"LLM Supervisor Agent failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("Testing LLM-powered agents...")
    print("=" * 50)
    
    # Test individual agents
    tests = [
        ("Router", test_llm_router),
        ("Ontology", test_llm_ontology),
        ("Examples", test_llm_examples),
        ("Supervisor", test_llm_supervisor),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            success = await test_func()
            results[test_name] = success
        except Exception as e:
            print(f"Test {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY:")
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:12}: {status}")
    
    overall_success = all(results.values())
    print(f"\nOverall: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
    
    return 0 if overall_success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
