"""
Demonstration tests showing enhanced fixture parameterization

These tests demonstrate the new flexible, non-hardcoded fixtures
"""

import pytest
import sys
from pathlib import Path

# Add current directory to path for conftest imports
sys.path.insert(0, str(Path(__file__).parent))

from conftest import assert_valid_sparql, create_mock_response, get_sample_queries


class TestParameterizedFixtures:
    """Test the enhanced parameterizable fixtures"""
    
    def test_default_mock_config(self, mock_config):
        """Test mock_config with default values"""
        databases = mock_config.get_available_databases()
        assert isinstance(databases, list)
        assert len(databases) > 0
        # Should use new defaults, not hardcoded values
        assert "diamm" in databases
    
    @pytest.mark.parametrize("mock_config", [
        {"databases": ["custom_db_1", "custom_db_2"], "api_key": "custom_key_123"}
    ], indirect=True)
    def test_custom_mock_config(self, mock_config):
        """Test mock_config with custom parameters"""
        databases = mock_config.get_available_databases()
        api_key = mock_config.get_api_key("test_provider")
        
        assert databases == ["custom_db_1", "custom_db_2"]
        assert api_key == "custom_key_123"
    
    @pytest.mark.parametrize("mock_config", [
        {"providers": {"custom_provider": {"model": "custom_model"}}}
    ], indirect=True)
    def test_custom_providers(self, mock_config):
        """Test mock_config with custom provider configuration"""
        provider_config = mock_config.get_provider_config("custom_provider")
        assert provider_config == {"model": "custom_model"}
    
    @pytest.mark.parametrize("mock_llm_client", [
        {"response": "SELECT ?artist WHERE { ?artist a dbo:Musician }", "provider_name": "custom_provider"}
    ], indirect=True)
    def test_custom_llm_client(self, mock_llm_client):
        """Test mock LLM client with custom response"""
        assert mock_llm_client.provider_name == "custom_provider"
        
        response = mock_llm_client._call_llm_api("test prompt")
        assert "dbo:Musician" in response
        assert_valid_sparql(response, expected_type="SELECT")
    
    @pytest.mark.parametrize("mock_llm_client", [
        {"should_fail": True}
    ], indirect=True)
    def test_failing_llm_client(self, mock_llm_client):
        """Test mock LLM client configured to fail"""
        from providers.base import APIError
        
        with pytest.raises(APIError, match="Mock API failure"):
            mock_llm_client._call_llm_api("test prompt")


class TestEnhancedUtilities:
    """Test the enhanced utility functions"""
    
    def test_flexible_sample_queries(self):
        """Test the new flexible query generation"""
        all_queries = get_sample_queries()
        music_queries = get_sample_queries(domain="music")
        historical_queries = get_sample_queries(domain="historical")
        
        assert len(all_queries) > len(music_queries)
        assert len(all_queries) > len(historical_queries)
        assert any("artist" in q.lower() for q in music_queries)
        assert any("manuscript" in q.lower() for q in historical_queries)
    
    def test_enhanced_sparql_validation(self):
        """Test enhanced SPARQL validation with type checking"""
        select_query = "SELECT ?x WHERE { ?x a owl:Thing }"
        construct_query = "CONSTRUCT { ?x a ex:Thing } WHERE { ?x a owl:Thing }"
        
        # Basic validation
        assert_valid_sparql(select_query)
        assert_valid_sparql(construct_query)
        
        # Type-specific validation
        assert_valid_sparql(select_query, expected_type="SELECT")
        assert_valid_sparql(construct_query, expected_type="CONSTRUCT")
        
        # Should fail if wrong type expected
        with pytest.raises(AssertionError, match="Expected CONSTRUCT"):
            assert_valid_sparql(select_query, expected_type="CONSTRUCT")
    
    def test_flexible_mock_responses(self):
        """Test flexible mock response creation"""
        content = "SELECT ?x WHERE { ?x a ex:Thing }"
        
        # Default markdown
        markdown_response = create_mock_response(content)
        assert "```sparql" in markdown_response
        assert content in markdown_response
        
        # Custom response type
        sql_response = create_mock_response("SELECT * FROM table", response_type="sql")
        assert "```sql" in sql_response
        
        # No markdown
        plain_response = create_mock_response(content, with_markdown=False)
        assert plain_response == content
        assert "```" not in plain_response
    
    def test_sample_sparql_queries_fixture(self, sample_sparql_queries):
        """Test the session-scoped SPARQL queries fixture"""
        assert "select" in sample_sparql_queries
        assert "construct" in sample_sparql_queries
        assert "ask" in sample_sparql_queries
        assert "describe" in sample_sparql_queries
        assert "complex" in sample_sparql_queries
        
        # Validate all provided queries
        for query_type, query in sample_sparql_queries.items():
            assert_valid_sparql(query)
            if query_type != "complex":  # complex might have multiple types
                assert_valid_sparql(query, expected_type=query_type.upper())


class TestBackwardCompatibility:
    """Test that old constants still work (backward compatibility)"""
    
    def test_old_constants_still_available(self):
        """Test that the old hardcoded constants are still available"""
        from conftest import SAMPLE_QUERIES, SAMPLE_DATABASES, PROVIDER_TEST_DATA
        
        assert isinstance(SAMPLE_QUERIES, list)
        assert isinstance(SAMPLE_DATABASES, list)
        assert isinstance(PROVIDER_TEST_DATA, list)
        
        # Should have content
        assert len(SAMPLE_QUERIES) > 0
        assert len(SAMPLE_DATABASES) > 0
        assert len(PROVIDER_TEST_DATA) > 0
