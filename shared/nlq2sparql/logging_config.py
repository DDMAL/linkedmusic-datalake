"""
Comprehensive logging configuration for end-to-end testing and debugging.
Shows all LLM interactions, agent communications, and processing steps.
"""

import logging
import sys
from typing import Optional
from datetime import datetime
import json


class LLMInteractionFormatter(logging.Formatter):
    """Custom formatter for LLM interactions and agent communications"""
    
    def __init__(self):
        super().__init__()
        self.colors = {
            'DEBUG': '\033[36m',    # Cyan
            'INFO': '\033[32m',     # Green
            'WARNING': '\033[33m',  # Yellow
            'ERROR': '\033[31m',    # Red
            'CRITICAL': '\033[35m', # Magenta
            'RESET': '\033[0m'      # Reset
        }
    
    def format(self, record):
        # Add color based on level
        color = self.colors.get(record.levelname, self.colors['RESET'])
        reset = self.colors['RESET']
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S.%f')[:-3]
        
        # Format the basic message
        message = record.getMessage()
        
        # Add special formatting for LLM interactions
        if hasattr(record, 'llm_prompt'):
            llm_prompt = getattr(record, 'llm_prompt', '')
            message = f"{message}\n{'='*60}\nPROMPT:\n{llm_prompt}\n{'='*60}"
        
        if hasattr(record, 'llm_response'):
            llm_response = getattr(record, 'llm_response', '')
            try:
                # Try to pretty-print JSON responses
                if llm_response.startswith('{'):
                    parsed = json.loads(llm_response)
                    formatted_response = json.dumps(parsed, indent=2)
                else:
                    formatted_response = llm_response
            except:
                formatted_response = llm_response
            
            message = f"{message}\n{'-'*40}\nRESPONSE:\n{formatted_response}\n{'-'*40}"
        
        if hasattr(record, 'agent_step'):
            agent_step = getattr(record, 'agent_step', '')
            message = f"{message}\n🤖 AGENT STEP: {agent_step}"
        
        # Combine everything
        formatted = f"{color}[{timestamp}] {record.name} | {record.levelname}{reset}: {message}"
        
        return formatted


def setup_end_to_end_logging(verbose: bool = False, log_file: Optional[str] = None) -> None:
    """
    Set up comprehensive logging for end-to-end testing.
    
    Args:
        verbose: Enable debug-level logging
        log_file: Optional file to write logs to (in addition to console)
    """
    # Set root logger level
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    
    # Clear any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler with custom formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(LLMInteractionFormatter())
    console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    root_logger.addHandler(console_handler)
    
    # Create file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(message)s'
        ))
        file_handler.setLevel(logging.DEBUG)
        root_logger.addHandler(file_handler)
    
    # Set specific logger levels for key components
    logging.getLogger('shared.nlq2sparql.llm.client').setLevel(logging.DEBUG)
    logging.getLogger('shared.nlq2sparql.agents').setLevel(logging.DEBUG)
    logging.getLogger('LLMRouterAgent').setLevel(logging.DEBUG)
    logging.getLogger('LLMOntologyAgent').setLevel(logging.DEBUG)
    logging.getLogger('LLMExampleAgent').setLevel(logging.DEBUG)
    logging.getLogger('LLMSupervisor').setLevel(logging.DEBUG)
    
    # Set up request/response logging for external components
    if verbose:
        logging.getLogger('urllib3').setLevel(logging.INFO)
        logging.getLogger('aiohttp').setLevel(logging.INFO)


def log_llm_interaction(logger: logging.Logger, agent_name: str, prompt: str, response: str, step: str = "") -> None:
    """
    Log an LLM interaction with proper formatting.
    
    Args:
        logger: Logger instance to use
        agent_name: Name of the agent making the call
        prompt: The prompt sent to the LLM
        response: The response received from the LLM
        step: Description of the processing step
    """
    logger.info(
        f"{agent_name} LLM interaction",
        extra={
            'llm_prompt': prompt,
            'llm_response': response,
            'agent_step': step or f"{agent_name} processing"
        }
    )


def log_agent_step(logger: logging.Logger, agent_name: str, step_description: str, data: Optional[dict] = None) -> None:
    """
    Log an agent processing step.
    
    Args:
        logger: Logger instance to use
        agent_name: Name of the agent
        step_description: Description of what the agent is doing
        data: Optional data to include in the log
    """
    message = f"{agent_name}: {step_description}"
    if data:
        try:
            formatted_data = json.dumps(data, indent=2)
            message = f"{message}\nData: {formatted_data}"
        except:
            message = f"{message}\nData: {str(data)}"
    
    logger.info(message, extra={'agent_step': step_description})


def log_query_flow(logger: logging.Logger, stage: str, details: dict) -> None:
    """
    Log the overall query processing flow.
    
    Args:
        logger: Logger instance to use
        stage: Stage of query processing (routing, ontology, generation, etc.)
        details: Details about the stage
    """
    logger.info(
        f"🔄 QUERY FLOW - {stage.upper()}",
        extra={'agent_step': f"Query flow: {stage}"}
    )
    
    if details:
        try:
            formatted_details = json.dumps(details, indent=2)
            logger.info(f"Details:\n{formatted_details}")
        except:
            logger.info(f"Details: {str(details)}")


# Convenience function for quick setup
def enable_full_logging(log_to_file: bool = True) -> None:
    """
    Enable full end-to-end logging with default settings.
    
    Args:
        log_to_file: Whether to also log to a timestamped file
    """
    log_file = None
    if log_to_file:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = f"nlq2sparql_debug_{timestamp}.log"
    
    setup_end_to_end_logging(verbose=True, log_file=log_file)
    
    # Log the startup
    logger = logging.getLogger(__name__)
    logger.info("🚀 NLQ2SPARQL End-to-End Logging Enabled")
    if log_file:
        logger.info(f"📝 Also logging to file: {log_file}")
