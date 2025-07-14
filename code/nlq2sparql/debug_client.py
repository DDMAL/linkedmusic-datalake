"""
Debug client for capturing prompts instead of making API calls
"""

import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

try:
    from .providers.base import BaseLLMClient
except ImportError:
    from providers.base import BaseLLMClient


class PromptDebugClient(BaseLLMClient):
    """Debug client that captures prompts instead of calling APIs"""
    
    def __init__(self, config):
        super().__init__(config)
        self.captured_prompt = None
        self.last_query_info = {}
    
    def _call_llm_api(self, prompt: str, verbose: bool = False) -> str:
        """Capture the prompt instead of calling an API"""
        self.captured_prompt = prompt
        
        # Save prompt to file immediately when captured
        self._save_prompt_to_file()
        
        return "DEBUG_MODE_NO_API_CALL"
    
    def generate_sparql(self, nlq: str, database: str, ontology_context: str = "", verbose: bool = False) -> str:
        """Override to store query info before calling parent method"""
        # Store info for filename generation
        self.last_query_info = {
            'nlq': nlq,
            'database': database,
            'ontology_context': ontology_context
        }
        
        # Call parent method which will trigger _call_llm_api where we capture the prompt
        return super().generate_sparql(nlq, database, ontology_context, verbose)
    
    def _extract_keywords(self, text: str, max_words: int = 4) -> str:
        """Extract key terms from natural language query for filename"""
        # Common English stop words to remove
        stop_words = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from', 'has', 
            'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the', 'to', 'was', 
            'will', 'with', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 
            'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 
            'so', 'than', 'too', 'very', 'can', 'will', 'just', 'should', 'now',
            'show', 'me', 'get', 'find', 'return', 'give', 'list', 'display'
        }
        
        # First, handle special compound terms (like musical keys)
        text_lower = text.lower()
        
        # Look for musical keys and preserve them as single terms
        # Match patterns like "D major", "C# minor", "Bb major", etc.
        key_pattern = r'\b([a-g][#b]?)\s+(major|minor)\b'
        keys = re.findall(key_pattern, text_lower)
        key_terms = [f"{note}{mode}" for note, mode in keys]
        
        # Remove the matched key patterns from text to avoid double-processing
        text_cleaned = re.sub(key_pattern, '', text_lower)
        
        # Clean and split the remaining text
        words = text_cleaned.replace('-', ' ').split()
        
        # Filter out stop words and keep meaningful terms
        keywords = []
        
        # Add preserved key terms first
        for key_term in key_terms:
            keywords.append(key_term)
            if len(keywords) >= max_words:
                break
        
        # Add other meaningful words
        if len(keywords) < max_words:
            for word in words:
                # Remove punctuation and keep only alphanumeric
                clean_word = ''.join(c for c in word if c.isalnum())
                if clean_word and clean_word not in stop_words and len(clean_word) > 1:
                    keywords.append(clean_word)
                    if len(keywords) >= max_words:
                        break
        
        # Join with underscores, limit total length
        result = '_'.join(keywords)
        return result[:30] if result else 'query'  # Fallback and length limit
    
    def _save_prompt_to_file(self) -> str:
        """Save the captured prompt to a file"""
        if not self.captured_prompt or not self.last_query_info:
            return ""
        
        # Create output directory
        output_dir = Path("debug_prompts")
        output_dir.mkdir(exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        keywords = self._extract_keywords(self.last_query_info['nlq'])
        filename = f"prompt_{self.last_query_info['database']}_{keywords}_{timestamp}.txt"
        
        # Save prompt to file
        output_file = output_dir / filename
        with open(output_file, 'w', encoding='utf-8') as f:
            # Format timestamp with timezone shown separately
            dt_with_tz = datetime.now().astimezone()
            timezone_name = dt_with_tz.strftime("%Z")  # e.g., "EDT", "PDT", "UTC"
            timestamp_formatted = dt_with_tz.strftime("%Y-%m-%d %H:%M:%S")
            
            f.write(f"Database: {self.last_query_info['database']}\n")
            f.write(f"Query: {self.last_query_info['nlq']}\n")
            f.write(f"Ontology context: {'Yes' if self.last_query_info['ontology_context'] else 'None'}\n")
            f.write(f"Timestamp ({timezone_name}): {timestamp_formatted}\n")
            f.write("=" * 80 + "\n")
            f.write("PROMPT SENT TO LLM:\n")
            f.write("=" * 80 + "\n")
            f.write(self.captured_prompt)
        
        return str(output_file)
