#!/usr/bin/env python3
"""
Debug the LLM Router Agent to see what prompts it's actually generating.
"""

import asyncio
import sys
from pathlib import Path

# Import from the nlq2sparql package using relative imports
try:
    from ..agents.llm_router_agent import LLMRouterAgent, LLMRoutingResult
    from ..config import Config
    from ..llm.client import LLMClient
except ImportError:
    # Fallback for repository-level debugging - add repository root to path
    sys.path.append(str(Path(__file__).parent.parent.parent.parent))
    from shared.nlq2sparql.agents.llm_router_agent import LLMRouterAgent, LLMRoutingResult
    from shared.nlq2sparql.config import Config
    from shared.nlq2sparql.llm.client import LLMClient

# Mock the LLM client with debugging
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
        print(f"\n🔍 DEBUG: Prompt received by mock LLM:")
        print(f"{'='*60}")
        print(prompt)
        print(f"{'='*60}")
        
        # Analyze the actual question content in the prompt
        prompt_lower = prompt.lower()
        
        print(f"🔎 Key detections:")
        print(f"  - palestrina: {'palestrina' in prompt_lower}")
        print(f"  - irish + traditional: {'irish' in prompt_lower and 'traditional' in prompt_lower}")
        print(f"  - bach: {'bach' in prompt_lower}")
        print(f"  - beatles: {'beatles' in prompt_lower}")
        print(f"  - indigenous + australia: {'indigenous' in prompt_lower and 'australia' in prompt_lower}")
        
        if "palestrina" in prompt_lower:
            mock_response = """{
                "ranked_datasets": ["diamm"],
                "dataset_scores": {"diamm": 0.95},
                "concept_hints": ["composer", "renaissance", "manuscript", "palestrina"],
                "reasoning": "Question about Renaissance composer Palestrina - DIAMM specializes in medieval/renaissance manuscripts and historical sources"
            }"""
        elif "irish" in prompt_lower and "traditional" in prompt_lower:
            mock_response = """{
                "ranked_datasets": ["session"],
                "dataset_scores": {"session": 0.9},
                "concept_hints": ["traditional", "irish", "folk", "tune"],
                "reasoning": "Question about traditional Irish music - The Session specializes in Irish traditional tunes and folk music"
            }"""
        elif "bach" in prompt_lower:
            mock_response = """{
                "ranked_datasets": ["diamm", "dlt1000"],
                "dataset_scores": {"diamm": 0.7, "dlt1000": 0.4},
                "concept_hints": ["composer", "baroque", "work", "analysis"],
                "reasoning": "Bach is primarily historical (DIAMM) but could also involve analytical approaches (DTL-1000 for harmonic analysis)"
            }"""
        elif "beatles" in prompt_lower:
            mock_response = """{
                "ranked_datasets": ["musicbrainz"],
                "dataset_scores": {"musicbrainz": 0.9},
                "concept_hints": ["recording", "release", "metadata"],
                "reasoning": "Question about recordings/releases - MusicBrainz has comprehensive recording and release metadata"
            }"""
        elif "indigenous" in prompt_lower and "australia" in prompt_lower:
            mock_response = """{
                "ranked_datasets": ["global-jukebox"],
                "dataset_scores": {"global-jukebox": 0.9},
                "concept_hints": ["culture", "world", "ethnomusicology"],
                "reasoning": "Question about world music/cultural context - Global Jukebox specializes in ethnomusicological data"
            }"""
        else:
            mock_response = """{
                "ranked_datasets": ["diamm", "session"],
                "dataset_scores": {"diamm": 0.6, "session": 0.5},
                "concept_hints": ["music", "general"],
                "reasoning": "General music question - routing to primary historical and traditional music databases"
            }"""
        
        print(f"🤖 Mock LLM Response: {mock_response.strip()}")
        return MockLLMResponse(mock_response)

class MockLLMClient:
    def __init__(self):
        self.provider = MockGeminiProvider()
    
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
llm.create_llm_client = mock_create_llm_client

async def debug_router():
    """Debug the router to see what prompts it generates."""
    from shared.nlq2sparql.agents import LLMRouterAgent
    
    router = LLMRouterAgent()
    
    test_questions = [
        "Find compositions by Palestrina",
        "Show me Irish traditional tunes in D major",
        "Find Bach's works and their harmonic analysis",
        "Show me recordings by The Beatles",
        "Find indigenous music from Australia"
    ]
    
    print("Debugging LLM Router Agent Prompts")
    print("=" * 70)
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n{'='*70}")
        print(f"TEST {i}: {question}")
        print(f"{'='*70}")
        
        try:
            result = await router.run(question)
            print(f"\n✅ Final routing result:")
            print(f"   Datasets: {result.get('ranked_datasets', [])}")
            print(f"   Reasoning: {result.get('reasoning', '')}")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_router())
