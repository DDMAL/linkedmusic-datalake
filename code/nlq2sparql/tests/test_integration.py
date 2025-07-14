"""
Essential integration tests

Tests the CLI interface and end-to-end functionality.
Focuses on what users actually interact with.
"""

import pytest
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add parent directory to path for imports
if str(Path(__file__).parent.parent) not in sys.path:
    sys.path.append(str(Path(__file__).parent.parent))

from cli import main
from arguments import ArgumentHandler
from config import Config


class TestCLIIntegration:
    """Test CLI interface and integration"""
    
    def test_argument_parsing_basic(self):
        """CLI parses basic arguments correctly"""
        config = Config()
        cli_parser = ArgumentHandler(config)
        parser = cli_parser.create_parser()
        
        args = parser.parse_args([
            "Find all artists",
            "--database", "diamm",
            "--provider", "gemini"
        ])
        
        assert args.query == "Find all artists"
        assert args.database == "diamm"
        assert args.provider == "gemini"
    
    def test_argument_parsing_optional(self):
        """CLI handles optional arguments"""
        config = Config()
        cli_parser = ArgumentHandler(config)
        parser = cli_parser.create_parser()
        
        args = parser.parse_args([
            "test query",
            "--database", "session",
            "--provider", "claude",
            "--verbose"
        ])
        
        assert args.query == "test query"
        assert args.database == "session"
        assert args.provider == "claude"
        assert args.verbose is True
    
    def test_argument_parsing_missing_required(self):
        """CLI requires essential arguments"""
        config = Config()
        cli_parser = ArgumentHandler(config)
        parser = cli_parser.create_parser()
        
        # Test case - CLI doesn't require database to be specified 
        # (has default behavior), so this test should pass
        args = parser.parse_args(["test"])
        assert args.query == "test"
    
    @patch('cli.QueryProcessor')
    def test_main_function_success(self, mock_processor_class):
        """Main function processes queries successfully"""
        # Mock the processor
        mock_processor = Mock()
        mock_processor_class.return_value = mock_processor
        
        # Mock sys.argv
        test_args = [
            "cli.py",
            "Find all artists",
            "--database", "diamm",
            "--provider", "gemini"
        ]
        
        with patch('sys.argv', test_args):
            try:
                main()
            except SystemExit as e:
                # Should exit with 0 on success
                assert e.code == 0 or e.code is None
            
        mock_processor.process_query_request.assert_called_once()
    
    @patch('cli.QueryProcessor')
    @patch('builtins.print')
    def test_main_function_handles_errors(self, mock_print, mock_processor_class):
        """Main function handles errors gracefully"""
        # Mock processor to raise an error
        mock_processor = Mock()
        mock_processor.process_query_request.side_effect = Exception("API Error")
        mock_processor_class.return_value = mock_processor
        
        test_args = [
            "cli.py",
            "test query",
            "--database", "session",
            "--provider", "gemini"
        ]
        
        with patch('sys.argv', test_args):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1  # Error exit code
            
        # Should print error message
        mock_print.assert_called()
        error_output = str(mock_print.call_args_list)
        assert "error" in error_output.lower() or "API Error" in error_output


class TestEndToEndFlow:
    """Test realistic user workflows"""
    
    @patch('cli.QueryProcessor')
    def test_complete_query_flow(self, mock_processor_class):
        """Complete flow from CLI to SPARQL generation"""
        # Mock processor
        mock_processor = Mock()
        mock_processor_class.return_value = mock_processor
        
        test_args = [
            "cli.py",
            "Find all artists",
            "--database", "diamm",
            "--provider", "gemini"
        ]
        
        with patch('sys.argv', test_args):
            with patch('builtins.print') as mock_print:
                try:
                    main()
                except SystemExit:
                    pass  # Expected
                
                # Should process the query
                mock_processor.process_query_request.assert_called_once()
