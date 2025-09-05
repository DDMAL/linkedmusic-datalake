# NLQ2SPARQL Examples and Demos

This directory contains example scripts and demonstrations of the NLQ2SPARQL system capabilities.

## Tracing Examples

The `tracing/` directory contains scripts that demonstrate the system's tracing and execution flow capabilities:

### Running Examples

From the `shared/` directory, run any example using:

```bash
# Set your API key
export GEMINI_API_KEY=your_api_key_here

# Run a specific example
poetry run python -m nlq2sparql.examples.tracing.enhanced_demo
poetry run python -m nlq2sparql.examples.tracing.complete_flow_demo
poetry run python -m nlq2sparql.examples.tracing.palestrina_demo
poetry run python -m nlq2sparql.examples.tracing.test_multi_function_fix
```

### Available Examples

#### `enhanced_demo.py`
Comprehensive demonstration of the tracing system with multiple musical queries.

#### `complete_flow_demo.py`
Shows complete end-to-end workflow from natural language to SPARQL execution.

#### `palestrina_demo.py`
Focused demo on Renaissance composer Giovanni Pierluigi da Palestrina.

#### `test_multi_function_fix.py`
**Test script for multi-function call processing** - verifies that the system can handle queries requiring multiple entity lookups (like "find madrigals in Florence").

## Key Features Demonstrated

- ✅ **Multi-function call processing** - Complex queries with multiple entity lookups
- ✅ **Real-time tracing** - Complete execution flow monitoring  
- ✅ **SPARQL generation** - From natural language to production-ready queries
- ✅ **Error handling** - Graceful handling of API issues and edge cases
- ✅ **Performance monitoring** - Timing and efficiency analysis

## Requirements

- Valid Gemini API key set in environment
- Poetry environment activated
- Run from the `shared/` directory

## Latest Enhancement

The system now supports **multi-function call processing**, enabling complex musical research queries that require multiple Wikidata entity lookups. This was a critical enhancement that transforms simple single-entity queries into sophisticated multi-entity musical research capabilities.

#### 2. Complete Flow Demo
Shows complete execution flow with detailed breakdown:
```bash
cd shared
poetry run python -m nlq2sparql.examples.tracing.complete_flow_demo
```

#### 3. Palestrina Demo
Simple focused example for SPARQL generation:
```bash
cd shared
poetry run python -m nlq2sparql.examples.tracing.palestrina_demo
```

## What You'll See

The tracing examples will show you:

- **🔧 LLM API Calls**: Full input/output for every API call
- **📊 Function Calls**: Arguments, results, and timing for each function
- **⏱️ Performance Data**: Execution timing and duration metrics
- **🔍 Debugging Info**: Detailed execution flow and state information
- **📁 Export Options**: JSON files with complete trace data

## Output Files

Trace logs are automatically saved to the `logs/` directory in the project root:
- `nlq2sparql_enhanced_demo.json`
- `complete_execution_trace.json`
- Error traces (if any failures occur)

## Example Output

```
🧪 TEST: Complex SPARQL Query Generation
--------------------------------------------------
📥 LLM Input: "Write a SPARQL query for Palestrina compositions..."
🔧 Function Call: find_entity_id("Palestrina composer") → Q179277
📤 LLM Output: "Here is the SPARQL query: SELECT ?work..."
⏱️ Total Duration: 2.1 seconds
```

## Understanding the Traces

Each trace event includes:
- **Timestamp**: Exact time of the event
- **Operation**: Type of operation (llm_api_call, function_call, etc.)
- **Input/Output**: Full text for LLM calls
- **Arguments/Results**: Complete data for function calls
- **Performance**: Duration and timing information
- **Context**: Module and component information

This gives you complete visibility into how natural language queries are transformed into SPARQL queries.
