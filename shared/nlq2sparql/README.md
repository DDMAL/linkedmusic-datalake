# NLQ2SPARQL Module

This module provides Natural Language Query to SPARQL translation capabilities for music datasets.

## Structure

```
nlq2sparql/
├── agents/              # LLM-powered and traditional agents
│   ├── base.py         # Base agent interfaces
│   ├── llm_*.py        # LLM-powered agents (Router, Ontology, Example, Supervisor)
│   ├── supervisor.py   # Traditional supervisor agent
│   └── wikidata_agent.py # Wikidata integration
├── llm/                # LLM provider infrastructure
│   ├── client.py       # Provider-agnostic LLM client
│   └── providers/      # LLM provider implementations
├── debug/              # Debug utilities and test outputs
│   ├── debug_router.py # Router debugging script
│   └── debug_prompts/  # Captured prompts for analysis
├── tests/              # Test suite
│   ├── test_*.py       # Integration and unit tests
│   └── __init__.py     # Test package initialization
├── tools/              # Utility tools
├── catalog/            # Dataset catalog and capabilities
├── integrations/       # External service integrations
├── cli.py              # Command-line interface
├── router.py           # Main query router
├── config.py           # Configuration management
├── logging_config.py   # Comprehensive logging setup
└── README.md           # This file
```

## Usage

### Basic CLI Usage

```bash
# Process a query with traditional agents
poetry run python shared/nlq2sparql/cli.py --database diamm "Find compositions by Palestrina"

# Use LLM-powered agents (requires API key)
poetry run python shared/nlq2sparql/cli.py --llm-agents --database diamm "Find compositions by Palestrina"

# Enable comprehensive logging
poetry run python shared/nlq2sparql/cli.py --debug-logging --llm-agents "Find Irish traditional music"

# Debug mode (capture prompts without API calls)
poetry run python shared/nlq2sparql/cli.py --debug-prompt --database diamm "Find manuscripts"
```

### Available Databases

- **diamm**: Medieval and Renaissance manuscripts
- **session**: Irish traditional music 
- **dlt1000**: Jazz improvisation analysis
- **global-jukebox**: World music ethnography

### Agent Types

#### Traditional Agents
- **SupervisorAgent**: Coordinates query processing
- **WikidataAgent**: Entity linking and enrichment

#### LLM-Powered Agents (require API key)
- **LLMRouterAgent**: Multi-database routing with semantic understanding
- **LLMOntologyAgent**: Ontology mapping and semantic enrichment  
- **LLMExampleAgent**: Example-based query pattern matching
- **LLMSupervisor**: Orchestrates the full LLM agent pipeline

## Development

### Running Tests

```bash
# Run the full test suite
poetry run pytest shared/nlq2sparql/tests/

# Run integration tests with debugging
python shared/nlq2sparql/tests/test_full_pipeline.py

# Debug router behavior
python shared/nlq2sparql/debug/debug_router.py
```

### Adding New Providers

1. Create a provider class in `llm/providers/`
2. Implement the `BaseLLMProvider` interface
3. Add configuration support in `config.py`
4. Update the provider factory in `llm/client.py`

### Logging

The module includes comprehensive logging capabilities:

- **Basic logging**: Use `--verbose` flag
- **Debug logging**: Use `--debug-logging` flag for full LLM interaction logs
- **Log files**: Use `--log-file path.log` to save logs to file

## Configuration

Configuration is managed through:
- `config.json`: Main configuration file
- Environment variables: API keys and runtime settings
- CLI arguments: Override defaults for specific runs

## API Keys

Set environment variables for LLM providers:
- `GEMINI_API_KEY`: For Google Gemini
- `OPENAI_API_KEY`: For ChatGPT (when implemented)
- `ANTHROPIC_API_KEY`: For Claude (when implemented)
