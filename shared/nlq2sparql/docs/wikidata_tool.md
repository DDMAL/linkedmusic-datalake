# Wikidata Tool Documentation

## Overview

The Wikidata Tool provides a clean, efficient interface for looking up Wikidata entity IDs (QIDs) and property IDs (PIDs) from human-readable labels. This tool is designed to be used by other agents in the multi-agent NLQ-to-SPARQL system.

The system includes both low-level tool functions and a higher-level agent with input validation, error handling, and concurrent batch processing.

## Architecture

```
tools/
├── wikidata_tool.py      # Core tool functions and class
└── __init__.py

agents/
├── wikidata_agent.py     # Agent wrapper with validation and batch processing
└── __init__.py

examples/
└── manager_agent_example.py  # Example usage for other agents

tests/
├── test_wikidata_tool.py    # Tool function tests (5 tests)
└── test_wikidata_agent.py   # Agent behavior tests (2 tests)
```

**Current Status:** ✅ All 38 tests passing

## Core Functions

### `find_entity_id(entity_label: str) -> Optional[str]`

Finds the Wikidata QID for a given entity label.

**Example:**
```python
from tools.wikidata_tool import find_entity_id

qid = await find_entity_id("Guillaume Dufay")
# Returns: "Q207717"
```

### `find_property_id(property_label: str) -> Optional[str]`

Finds the Wikidata PID for a given property label.

**Example:**
```python
from tools.wikidata_tool import find_property_id

pid = await find_property_id("composer")
# Returns: "P86"
```

## Usage Patterns

### 1. Direct Function Usage (Recommended for Manager Agents)

```python
from tools.wikidata_tool import find_entity_id, find_property_id

# Single lookups
entity_qid = await find_entity_id("Mozart")
composer_pid = await find_property_id("composer")

# Use in SPARQL construction
sparql_fragment = f"?work wdt:{composer_pid} wd:{entity_qid} ."
```

### 2. Class-based Usage

```python
from tools.wikidata_tool import WikidataTool

tool = WikidataTool()
qid = await tool.find_entity_id("Bach")
pid = await tool.find_property_id("composer")
```

### 3. Agent Wrapper Usage (Recommended for Complex Workflows)

```python
from agents.wikidata_agent import WikidataAgent

agent = WikidataAgent()

# Single lookups with validation
try:
    qid = await agent.find_entity_id("Mozart")
    pid = await agent.find_property_id("composer")
except ValueError as e:
    print(f"Validation error: {e}")

# Concurrent batch lookup
results = await agent.lookup_entities_and_properties(
    entities=["Mozart", "Beethoven"],
    properties=["composer", "birth date"]
)
# Returns: {
#   "entity:Mozart": "Q254",
#   "entity:Beethoven": "Q255", 
#   "property:composer": "P86",
#   "property:birth date": "P569"
# }
```

## Agent Features

### Input Validation
The WikidataAgent provides robust input validation:

```python
# These will raise ValueError
await agent.find_entity_id("")           # Empty string
await agent.find_entity_id(None)         # None value
await agent.find_entity_id("   ")        # Whitespace only

# Batch operations require at least one input
await agent.lookup_entities_and_properties([], [])  # ValueError
```

### Concurrent Processing
The agent performs concurrent lookups for optimal performance:

```python
# These lookups happen simultaneously, not sequentially
results = await agent.lookup_entities_and_properties(
    entities=["Bach", "Mozart", "Beethoven"],      # 3 concurrent entity lookups
    properties=["composer", "performer", "genre"]   # 3 concurrent property lookups
)
# Total time ≈ slowest single lookup, not sum of all lookups
```

### Error Handling
The agent gracefully handles individual lookup failures:

```python
results = await agent.lookup_entities_and_properties(
    entities=["Valid Entity", "NonExistent Entity"],
    properties=["composer", "invalid_property"]
)
# Returns partial results - valid lookups succeed, invalid ones return None
# Errors are logged but don't stop the entire batch
```

## Integration with Manager Agents

The tool functions are designed to be easily callable by manager agents that use function calling (e.g., with Gemini API). The manager agent can:

1. Analyze user queries to identify entities and properties
2. Call the appropriate tool functions to get QIDs/PIDs
3. Use the results to construct SPARQL queries

## Technical Details

- **Rate Limiting**: Built-in rate limiting complies with Wikidata usage policies
- **Error Handling**: Robust error handling with logging
- **Async Support**: Fully asynchronous for efficient concurrent lookups
- **Session Management**: Proper aiohttp session management for each request

## Testing

### Run Individual Components

```bash
# Test the tool directly
cd /path/to/linkedmusic-datalake
poetry run python code/nlq2sparql/tools/wikidata_tool.py

# Test the agent directly  
poetry run python code/nlq2sparql/agents/wikidata_agent.py

# Run the manager agent example
poetry run python code/nlq2sparql/examples/manager_agent_example.py
```

### Run the Test Suite

```bash
cd /path/to/linkedmusic-datalake/code/nlq2sparql

# Run all Wikidata tests
poetry run pytest tests/test_wikidata_* -v

# Run specific test files
poetry run pytest tests/test_wikidata_tool.py -v     # 5 tool tests
poetry run pytest tests/test_wikidata_agent.py -v    # 2 agent tests

# Run all tests (38 tests total)
poetry run pytest tests/ -v
```

**Current Test Status:** ✅ All 38 tests passing

## Dependencies

- `aiohttp`: HTTP client
- `aiolimiter`: Rate limiting (via WikidataAPIClient)
- `wikidata_utils.client`: Custom Wikidata API client

## Future Extensions

The tool can be extended with:
- **Caching**: Cache frequently looked up entities/properties
- **Batch Optimization**: More efficient batch processing algorithms  
- **Fuzzy Matching**: Improved matching for ambiguous entity names
- **Language Support**: Multi-language label support
- **Result Ranking**: Score and rank multiple matches
- **Performance Monitoring**: Track lookup success rates and response times

## Best Practices

### When to Use Each Component

- **Tool Functions** (`find_entity_id`, `find_property_id`): Simple, direct lookups in manager agents
- **Tool Class** (`WikidataTool`): When you need an object-oriented interface
- **Agent** (`WikidataAgent`): Complex workflows requiring validation, batch processing, or error handling

### Performance Tips

- Use batch lookups for multiple entities/properties
- The agent performs concurrent lookups automatically
- Consider caching results for frequently accessed entities
- Monitor API rate limits for high-volume usage

### Error Handling

- Tool functions return `None` for not found (no exceptions)
- Agent methods raise `ValueError` for invalid input
- Batch operations continue even if individual lookups fail
- Check logs for detailed error information
