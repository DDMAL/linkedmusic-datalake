# NLQ2SPARQL System

An intelligent natural language to SPARQL conversion system with multi-agent architecture, supporting various LLM providers and external knowledge integration.

## Overview

The NLQ2SPARQL system provides a comprehensive platform for converting natural language queries into precise SPARQL queries. It combines:

- **🤖 Multi-Agent Architecture**: Specialized agents for different query processing tasks
- **🔧 Modular Tools**: Reusable components for Wikidata integration and entity resolution
- **🌐 Multiple LLM Providers**: Support for ChatGPT, Claude, and Gemini
- **📚 Knowledge Integration**: Automatic QID/PID resolution via Wikidata APIs
- **🎯 Database-Specific**: Optimized for music and cultural heritage databases
- **✅ Tested & Reliable**: Comprehensive test suite with 38 passing tests

## System Architecture

```
nlq2sparql/
├── agents/               # Intelligent agents for specialized tasks
│   ├── wikidata_agent.py    # Wikidata entity/property resolution
│   └── ontology_agent.py    # Ontology parsing and analysis
├── tools/                # Reusable tool components
│   └── wikidata_tool.py     # Core Wikidata API integration
├── providers/            # LLM provider integrations
│   ├── gemini_client.py     # Google Gemini client
│   ├── chatgpt_client.py    # OpenAI ChatGPT client
│   └── claude_client.py     # Anthropic Claude client
├── tests/                # Comprehensive test suite
└── docs/                 # System documentation
```

### Core Components

- **🎯 Query Router**: Intelligent routing between LLM providers
- **🔍 Wikidata Integration**: Automatic entity/property ID resolution
- **📋 Configuration System**: Flexible API key and parameter management
- **🛠️ Agent Framework**: Extensible architecture for specialized processing
- **⚡ Async Operations**: High-performance concurrent processing

## Quick Start

### Installation

1. Install dependencies using Poetry from the project root:
```bash
cd /path/to/linkedmusic-datalake
poetry install
```

2. Set up your API keys in the `.env` file in the project root:
```properties
gemini_api_key=your_gemini_api_key_here
openai_api_key=your_openai_api_key_here  # Optional, for ChatGPT
anthropic_api_key=your_anthropic_api_key_here  # Optional, for Claude
```

### Basic Usage

**All commands must be run from the `code` directory:**

```bash
cd code
```

**Simple Query Processing:**
```bash
# Basic natural language query
python -m nlq2sparql.cli "Find all compositions by Antonio il Verso" --database diamm

# Test mode with default queries
python -m nlq2sparql.cli --database diamm --test

# Using specific LLM provider
python -m nlq2sparql.cli "Return all traditional tunes" --database session --provider gemini
```

**Advanced Features:**
```bash
# With ontology context for better understanding
python -m nlq2sparql.cli "Show me all manuscripts" --database diamm --ontology-file path/to/ontology.ttl

# Debug mode to inspect generated prompts
python -m nlq2sparql.cli "Find works by Palestrina" --database diamm --debug-prompt

# Verbose output for detailed processing information
python -m nlq2sparql.cli "Find jazz tracks" --database dlt1000 --verbose
```

## System Capabilities

### 1. Natural Language Processing
- **Multi-Provider Support**: Seamlessly switch between ChatGPT, Claude, and Gemini
- **Context-Aware**: Incorporates database schemas and ontologies
- **Debug Mode**: Inspect and refine prompts without API calls

### 2. Intelligent Entity Resolution
- **Automatic QID/PID Lookup**: Resolves entities to Wikidata identifiers
- **Batch Processing**: Efficient concurrent lookups
- **Error Handling**: Graceful fallbacks for missing entities

### 3. Multi-Agent Architecture
- **Specialized Agents**: Different agents for different tasks (Wikidata, ontology parsing)
- **Tool Integration**: Reusable components across agents
- **Extensible Design**: Easy to add new agents and capabilities

## Command Line Interface

### Core Options

- `query`: Natural language query (optional - uses test query if not provided)
- `--provider`: LLM provider (`gemini`, `chatgpt`, `claude`) - default: `gemini`
- `--database`: Target database (`diamm`, `session`, `dlt1000`, `global-jukebox`) - **required**
- `--test`: Run with a default test query to verify setup
- `--verbose`: Enable detailed processing output
- `--debug-prompt`: Capture prompts without making API calls

### Advanced Options

- `--ontology-file`: Path to ontology file for enhanced context
- `--config`: Path to custom configuration file
- `--list-databases`: Show all available databases and test queries

### Example Workflows

**Database-Specific Queries:**

```bash
# DIAMM - Medieval and Renaissance manuscripts
python -m nlq2sparql.cli "Find all manuscripts by Josquin" --database diamm

# The Session - Traditional Irish music
python -m nlq2sparql.cli "Find all jigs in D major" --database session

# DLT1000 - Jazz recordings  
python -m nlq2sparql.cli "Find all bebop tracks" --database dlt1000

# Global Jukebox - World music cultures
python -m nlq2sparql.cli "Find all African vocal music" --database global-jukebox
```

**Development & Testing:**

```bash
# Capture prompts for analysis
python -m nlq2sparql.cli "Find sources by John Doe" --database diamm --debug-prompt

# Test with verbose output
python -m nlq2sparql.cli --database session --test --verbose

# List available databases
python -m nlq2sparql.cli --list-databases
```

## Agent & Tool Usage

Beyond the CLI, the system provides programmable agents and tools for integration into larger applications.

### Wikidata Integration

```python
from tools.wikidata_tool import find_entity_id, find_property_id
from agents.wikidata_agent import WikidataAgent

# Direct tool usage
qid = await find_entity_id("Guillaume Dufay")  # Returns: Q207717
pid = await find_property_id("composer")       # Returns: P86

# Agent usage for batch operations
agent = WikidataAgent()
results = await agent.lookup_entities_and_properties(
    entities=["Mozart", "Beethoven"],
    properties=["composer", "birth date"]
)
```

### Example Integration

```python
# Manager agent workflow
user_query = "Tell me about works by Guillaume Dufay"

# 1. Identify entities and properties in query
entities = ["Guillaume Dufay"]
properties = ["composer", "work"]

# 2. Resolve to Wikidata identifiers
entity_qid = await find_entity_id("Guillaume Dufay")  # Q207717
composer_pid = await find_property_id("composer")     # P86

# 3. Build SPARQL with resolved identifiers
sparql_fragment = f"?work wdt:{composer_pid} wd:{entity_qid} ."
# Result: ?work wdt:P86 wd:Q207717 .
```

## Configuration & Customization

### API Keys Setup

Set environment variables in your `.env` file in the project root:

```properties
# Required for basic functionality
gemini_api_key=your_gemini_api_key_here

# Optional - enables additional providers
openai_api_key=your_openai_api_key_here
anthropic_api_key=your_anthropic_api_key_here
```

### Provider Configuration

Customize model parameters via JSON configuration:

```json
{
  "gemini": {
    "model": "gemini-pro",
    "temperature": 0.1
  },
  "chatgpt": {
    "model": "gpt-3.5-turbo", 
    "max_tokens": 1000,
    "temperature": 0.1
  },
  "claude": {
    "model": "claude-3-sonnet-20240229",
    "max_tokens": 1000,
    "temperature": 0.1
  }
}
```

### Debug & Development

**Prompt Inspection:**
```bash
# Capture prompts without API calls
python -m nlq2sparql.cli "Find sources by John Doe" --database diamm --debug-prompt
```

Captured prompts are saved to `debug_prompts/` with timestamps, useful for:
- Understanding query processing
- Debugging unexpected results  
- Development without API costs
- Fine-tuning prompts

## Example Output

The system generates precise SPARQL queries with resolved Wikidata identifiers:

**Input Query:**
```
"Find all manuscripts by Josquin"
```

**Generated SPARQL:**
```sparql
PREFIX da: <https://www.diamm.ac.uk/archives/>
PREFIX dp: <https://www.diamm.ac.uk/people/>
PREFIX ds: <https://www.diamm.ac.uk/sources/>

SELECT ?source ?title WHERE {
  ?source a ds:Source ;
          ds:title ?title ;
          ds:composer ?composer .
  ?composer dp:name "Josquin" .
}
```

**With Wikidata Integration:**
```sparql
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>

SELECT ?work ?title WHERE {
  ?work wdt:P86 wd:Q26709 ;        # composer: Josquin des Prez
        wdt:P1476 ?title .         # title
}
```

## Testing & Quality Assurance

The system includes a comprehensive test suite ensuring reliability:

```bash
# Run all tests (38 tests)
poetry run pytest tests/

# Run specific test categories
poetry run pytest tests/test_wikidata_tool.py    # Tool functions
poetry run pytest tests/test_wikidata_agent.py   # Agent behavior
poetry run pytest tests/test_providers.py        # LLM providers
poetry run pytest tests/test_integration.py      # End-to-end flows

# Quick test run
poetry run pytest tests/ --tb=short
```

**Test Coverage:**
- ✅ **Tool Functions**: Wikidata API integration (mocked)
- ✅ **Agent Behavior**: Delegation and batch operations
- ✅ **Provider Integration**: LLM client functionality
- ✅ **Configuration**: Loading and validation
- ✅ **CLI Interface**: Argument parsing and workflows
- ✅ **Error Handling**: Graceful failure modes

**Result:** 38 tests passing - all core functionality validated

## System Architecture & Implementation

### Core Components

**🎯 Query Processing Pipeline:**
- **CLI Interface** (`cli.py`): User-facing command-line interface
- **Query Router** (`router.py`): Intelligent provider selection and coordination
- **Configuration System** (`config.py`): API keys, parameters, and database settings

**🤖 Multi-Agent Framework:**
- **WikidataAgent** (`agents/wikidata_agent.py`): Entity and property resolution
- **OntologyAgent** (`agents/ontology_agent.py`): Schema parsing and analysis
- **Tool Integration**: Reusable components across agents

**🔧 Tool Ecosystem:**
- **WikidataTool** (`tools/wikidata_tool.py`): Core Wikidata API integration
- **Async Operations**: High-performance concurrent processing
- **Rate Limiting**: Built-in compliance with API policies

**🌐 LLM Provider Integration:**
- **GeminiClient** (`providers/gemini_client.py`): Google Gemini integration
- **ChatGPTClient** (`providers/chatgpt_client.py`): OpenAI ChatGPT integration  
- **ClaudeClient** (`providers/claude_client.py`): Anthropic Claude integration

### Design Principles

- **🔄 Extensibility**: Easy to add new agents, tools, and providers
- **⚡ Performance**: Async operations and efficient caching
- **🛡️ Reliability**: Comprehensive error handling and fallbacks
- **🧪 Testability**: Full test coverage with minimal dependencies
- **📚 Documentation**: Clear documentation and examples

## Documentation

- **[Wikidata Tool Guide](docs/wikidata_tool.md)**: Complete tool documentation
- **[Test Suite Overview](tests/README.md)**: Testing approach and guidelines
- **[Examples](examples/)**: Integration examples and usage patterns

## Roadmap & Future Development

### Current Capabilities (v1.0)
- ✅ Multi-provider LLM integration
- ✅ Wikidata entity/property resolution
- ✅ Database-specific query optimization
- ✅ Debug and development tools
- ✅ Comprehensive testing

### Planned Features
- **🔄 Multi-step Query Clarification**: Interactive query refinement
- **✅ Query Validation & Correction**: Automatic SPARQL validation
- **💬 Conversational Interface**: Chat-based query building
- **🌐 Federated Queries**: Cross-database query coordination
- **🎯 Template-based Patterns**: Common query patterns and templates
- **📡 Web Service Interface**: REST API for integration

### Integration Opportunities
- **Function Calling**: Enhanced LLM integration with structured tool calls
- **Ontology Reasoning**: Advanced semantic understanding
- **Result Caching**: Performance optimization for common queries
- **Query Optimization**: SPARQL performance analysis and improvement
