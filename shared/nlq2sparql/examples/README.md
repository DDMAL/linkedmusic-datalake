# NLQ2SPARQL Examples

This directory contains example scripts and demonstrations of the NLQ2SPARQL system.

## Prerequisites

1. **API Key**: Set your Gemini API key in the environment:
   ```bash
   export GEMINI_API_KEY=your_api_key_here
   ```

2. **Dependencies**: Ensure all dependencies are installed:
   ```bash
   poetry install
   ```

## Running Examples

### Tracing Examples

The tracing examples demonstrate the comprehensive logging and monitoring capabilities:

#### 1. Enhanced Demo
Comprehensive tracing demonstration with multiple test cases:
```bash
cd shared
poetry run python -m nlq2sparql.examples.tracing.enhanced_demo
```

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
