# NLQ to SPARQL Generator

A command-line tool for converting natural language queries to SPARQL queries using various LLM providers (ChatGPT, Claude, Gemini).

## Installation

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

## Usage

**All commands must be run from the `code` directory:**

```bash
cd code
```

Basic usage:
```bash
poetry run python -m nlq2sparql "Find all compositions by Antonio il Verso" --database diamm
```

Test mode (uses default queries):
```bash
poetry run python -m nlq2sparql --database diamm --test
```

With specific LLM provider:
```bash
poetry run python -m nlq2sparql "Return all traditional tunes" --database session --llm gemini
```

With ontology context:
```bash
poetry run python -m nlq2sparql "Show me all manuscripts" --database diamm --ontology-file path/to/ontology.ttl
```

With custom configuration:
```bash
poetry run python -m nlq2sparql "Find jazz tracks" --database dlt1000 --config nlq2sparql/config.json --verbose
```

## Command Line Options

- `query`: Natural language query (optional - uses test query if not provided)
- `--llm`: LLM provider to use (`gemini`, `chatgpt`, `claude`) - default: `gemini`
- `--database`: Target database (`diamm`, `session`, `dlt1000`, `global-jukebox`) - required
- `--test`: Run with a default test query to verify setup
- `--ontology-file`: Path to ontology file for additional context
- `--config`: Path to custom configuration file
- `--verbose`: Enable verbose output
- `--debug-prompt`: Capture and save the prompt that would be sent to the LLM instead of executing the query
- `--list-databases`: Show all available databases and their default test queries

## Configuration

The tool supports configuration via:
1. Environment variables (in `.env` file)
2. JSON configuration file (see `config.json` for example)

### API Keys

Set the following environment variables or include them in your `.env` file:
- `gemini_api_key`: Google Gemini API key
- `openai_api_key`: OpenAI API key (for ChatGPT)
- `anthropic_api_key`: Anthropic API key (for Claude)

### Provider Configuration

You can customize model parameters in the configuration file:

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

## Debugging and Prompt Inspection

The tool includes a debug mode that allows you to capture and inspect the exact prompt that would be sent to the LLM, without making an API call:

```bash
# Capture the prompt for a specific query
poetry run python -m nlq2sparql "Find sources by John Doe" --database diamm --debug-prompt

# Capture the prompt for a test query
poetry run python -m nlq2sparql --database session --test --debug-prompt
```

The captured prompts are saved to the `debug_prompts/` directory with filenames that include:
- Database name
- Cleaned query text
- Timestamp

This is useful for:
- Understanding how your natural language query is being processed
- Debugging unexpected results
- Fine-tuning your queries
- Development and testing without API costs

## Examples

**Note**: All examples assume you're in the `code` directory (`cd code`)

### DIAMM Queries
```bash
# Find manuscripts by a specific composer
poetry run python -m nlq2sparql "Find all manuscripts by Josquin" --database diamm

# Find sources from a specific location
poetry run python -m nlq2sparql "Show me all sources from Paris" --database diamm
```

### The Session Queries
```bash
# Find traditional Irish tunes
poetry run python -m nlq2sparql "Find all jigs in D major" --database session

# Find recordings by a specific musician
poetry run python -m nlq2sparql "Show me recordings by Kevin Burke" --database session
```

### DLT1000 Queries
```bash
# Find jazz tracks
poetry run python -m nlq2sparql "Find all bebop tracks" --database dlt1000

# Find tracks with specific characteristics
poetry run python -m nlq2sparql "Show me tracks with swing rhythm" --database dlt1000
```

### Global Jukebox Queries
```bash
# Find cultural recordings
poetry run python -m nlq2sparql "Find all African vocal music" --database global-jukebox

# Find songs by characteristics
poetry run python -m nlq2sparql "Show me pentatonic melodies" --database global-jukebox
```

## Output

The tool generates SPARQL queries that can be executed against your SPARQL endpoint. Example output:

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
}
```

## Error Handling

Currently, the tool returns whatever SPARQL is generated by the LLM, even if it contains errors. Error validation and correction will be added in future versions.

## Architecture

The system consists of:
- **CLI Interface** (`cli.py`): Command-line interface
- **Router** (`router.py`): Coordinates between different LLM providers
- **Configuration** (`config.py`): Manages API keys and settings
- **Providers** (`providers/`): Individual client modules for each LLM
  - `gemini_client.py`: Google Gemini client
  - `chatgpt_client.py`: OpenAI ChatGPT client  
  - `claude_client.py`: Anthropic Claude client

## Future Features

- Multi-step query clarification
- Query validation and error correction
- Conversational interface
- Federated queries across multiple databases
- Template-based clarification patterns
- Web service interface
