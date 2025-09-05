#!/usr/bin/env python3
"""
Comprehensive end-to-end test with full logging to show all inputs and outputs.
Uses mock LLM client to avoid API key requirements.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Import modules using relative imports
try:
    from .logging_config import setup_end_to_end_logging
    from .config import Config
    from .router import QueryRouter
    from .llm.client import LLMClient
except ImportError:
    # Fallback for when running as a script
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from logging_config import setup_end_to_end_logging
    from config import Config
    from router import QueryRouter
    from llm.client import LLMClient


# Mock LLM Provider for testing
class MockLLMResponse:
    def __init__(self, content: str):
        self.content = content
        self.metadata = {"provider": "mock", "model": "debug"}
        self.success = True
        self.error = None


class MockLLMProvider:
    def get_provider_name(self):
        return "mock_llm"
    
    async def generate(self, prompt: str, **kwargs):
        """Generate mock responses based on the prompt content."""
        prompt_lower = prompt.lower()
        
        # Router agent responses
        if "routing specialist" in prompt_lower:
            if "palestrina" in prompt_lower:
                response = """{
                    "ranked_datasets": ["diamm", "musicbrainz"],
                    "dataset_scores": {"diamm": 0.95, "musicbrainz": 0.7},
                    "concept_hints": ["composer", "renaissance", "manuscript", "palestrina"],
                    "reasoning": "Renaissance composer query: DIAMM for manuscripts + MusicBrainz for recordings"
                }"""
            elif "irish" in prompt_lower and "traditional" in prompt_lower:
                response = """{
                    "ranked_datasets": ["session", "musicbrainz"],
                    "dataset_scores": {"session": 0.9, "musicbrainz": 0.6},
                    "concept_hints": ["traditional", "irish", "folk", "tune"],
                    "reasoning": "Irish traditional music: The Session + MusicBrainz for commercial recordings"
                }"""
            elif "jazz" in prompt_lower and "harmonic" in prompt_lower:
                response = """{
                    "ranked_datasets": ["dlt1000", "musicbrainz"],
                    "dataset_scores": {"dlt1000": 0.95, "musicbrainz": 0.7},
                    "concept_hints": ["jazz", "improvisation", "harmonic", "analysis"],
                    "reasoning": "Jazz analysis: DTL-1000 for transcriptions + MusicBrainz for recording metadata"
                }"""
            elif "beatles" in prompt_lower:
                response = """{
                    "ranked_datasets": ["musicbrainz"],
                    "dataset_scores": {"musicbrainz": 0.95},
                    "concept_hints": ["popular", "rock", "recordings", "beatles"],
                    "reasoning": "Popular music recordings: MusicBrainz comprehensive metadata"
                }"""
            elif "australian" in prompt_lower and "aboriginal" in prompt_lower:
                response = """{
                    "ranked_datasets": ["global-jukebox", "musicbrainz"],
                    "dataset_scores": {"global-jukebox": 0.9, "musicbrainz": 0.4},
                    "concept_hints": ["indigenous", "traditional", "ethnomusicology", "australia"],
                    "reasoning": "Indigenous music: Global Jukebox for ethnographic data + MusicBrainz for any commercial recordings"
                }"""
            else:
                response = """{
                    "ranked_datasets": ["diamm"],
                    "dataset_scores": {"diamm": 0.5},
                    "concept_hints": ["music", "general"],
                    "reasoning": "General music query - defaulting to DIAMM"
                }"""
        
        # Ontology agent responses
        elif "ontology specialist" in prompt_lower or "semantic mapping" in prompt_lower:
            response = """{
                "relevant_classes": ["foaf:Person", "mo:MusicArtist", "mo:Composition"],
                "relevant_properties": ["foaf:name", "mo:composer", "dct:created"],
                "suggested_filters": ["?composer a mo:MusicArtist", "?composition mo:composer ?composer"],
                "reasoning": "Mapped query to music ontology concepts for composer and composition relationships"
            }"""
        
        # Example agent responses  
        elif "example specialist" in prompt_lower or "sparql examples" in prompt_lower:
            response = """{
                "example_queries": [
                    "SELECT ?composer ?name WHERE { ?composer a mo:MusicArtist ; foaf:name ?name . FILTER(regex(?name, \\"Palestrina\\", \\"i\\")) }",
                    "SELECT ?composition ?title WHERE { ?composition a mo:Composition ; mo:composer ?composer ; dct:title ?title . ?composer foaf:name \\"Giovanni Pierluigi da Palestrina\\" }"
                ],
                "query_patterns": ["composer_search", "composition_by_composer"],
                "reasoning": "Found relevant SPARQL patterns for composer and composition queries"
            }"""
        
        # SPARQL generation responses
        else:
            response = """SELECT DISTINCT ?composer ?name ?composition ?title 
WHERE {
    ?composer a foaf:Person ;
              foaf:name ?name .
    ?composition mo:composer ?composer ;
                 dct:title ?title .
    FILTER(regex(?name, "Palestrina", "i"))
}
ORDER BY ?name ?title
LIMIT 100"""
        
        return MockLLMResponse(response)


async def run_comprehensive_test():
    """Run a full end-to-end test with comprehensive logging."""
    
    # Set up comprehensive logging
    setup_end_to_end_logging(verbose=True, log_file="end_to_end_test.log")
    logger = logging.getLogger(__name__)
    
    logger.info("🚀 Starting Comprehensive End-to-End Test")
    logger.info("=" * 80)
    
    try:
        # Initialize configuration
        logger.info("📋 Step 1: Loading Configuration")
        config = Config()
        
        # Create mock LLM client for testing
        logger.info("🤖 Step 2: Setting up Mock LLM Client")
        mock_provider = MockLLMProvider()
        
        # Initialize router with LLM agents enabled
        logger.info("🎯 Step 3: Initializing Query Router with Mock LLM")
        router = QueryRouter(config)
        
        # Monkey patch the router to use our mock for LLM agents
        if hasattr(router, '_llm_client'):
            router._llm_client = mock_provider
        
        # Test queries to demonstrate different routing scenarios
        test_queries = [
            {
                "query": "Find compositions by Palestrina",
                "expected_datasets": ["diamm"],
                "description": "Renaissance composer query"
            },
            {
                "query": "Show me Irish traditional tunes in D major", 
                "expected_datasets": ["session"],
                "description": "Irish traditional music query"
            },
            {
                "query": "Find jazz solos with harmonic analysis",
                "expected_datasets": ["dlt1000"],
                "description": "Jazz analysis query"
            },
            {
                "query": "Show me recordings by The Beatles",
                "expected_datasets": ["musicbrainz"],
                "description": "Modern recordings query"
            },
            {
                "query": "Find traditional Australian Aboriginal music",
                "expected_datasets": ["global-jukebox"],
                "description": "World music ethnographic query"
            }
        ]
        
        logger.info(f"🧪 Step 4: Running {len(test_queries)} Test Queries")
        logger.info("=" * 80)
        
        for i, test_case in enumerate(test_queries, 1):
            logger.info(f"🔍 TEST {i}: {test_case['description']}")
            logger.info(f"Query: '{test_case['query']}'")
            logger.info(f"Expected datasets: {test_case['expected_datasets']}")
            logger.info("-" * 60)
            
            try:
                # Process the query with full logging
                result = router.process_query(
                    nlq=test_case["query"],
                    provider="gemini",  # Will use mock
                    database="diamm",   # Starting database
                    ontology_file=None,
                    verbose=True,
                    use_llm_agents=True
                )
                
                logger.info(f"✅ Query {i} completed successfully")
                logger.info(f"Generated SPARQL:\n{result}")
                logger.info("=" * 60)
                
            except Exception as e:
                logger.error(f"❌ Query {i} failed: {e}", exc_info=True)
                logger.info("=" * 60)
        
        logger.info("🎉 End-to-End Test Completed")
        logger.info("📝 Full log saved to: end_to_end_test.log")
        
    except Exception as e:
        logger.error(f"💥 Test setup failed: {e}", exc_info=True)
        return False
    
    return True


def main():
    """Main entry point for the test."""
    print("Starting comprehensive end-to-end test...")
    print("This will show all LLM interactions, agent communications, and processing steps.")
    print("=" * 80)
    
    success = asyncio.run(run_comprehensive_test())
    
    if success:
        print("\n✅ Test completed successfully!")
        print("📝 Check 'end_to_end_test.log' for detailed logs")
    else:
        print("\n❌ Test failed - check the output above")
        sys.exit(1)


if __name__ == "__main__":
    main()
