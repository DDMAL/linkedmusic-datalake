# NLQ2SPARQL Test Suite

Lightweight test suite for the NLQ-to-SPARQL system using modern pytest.

## Test Files

- **test_config.py**: Configuration loading and validation
- **test_providers.py**: Provider base class and client tests  
- **test_integration.py**: CLI and end-to-end functionality
- **test_query_processing.py**: Query routing and processing
- **conftest.py**: Simple shared fixtures

## Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test categories  
pytest tests/test_config.py
pytest tests/test_providers.py

# Use Makefile commands
make test              # All tests
make test-unit         # Unit tests only  
make quick-test        # Fast tests (no slow/API tests)
```

## Test Approach

### Lightweight & Focused
- Simple mock fixtures without over-engineering
- Essential test coverage only
- No external dependencies or API keys required
- Fast execution with minimal setup

### What's Tested
- **Configuration**: Loading, validation, database/provider configs
- **Providers**: Base class, response cleaning, error handling
- **CLI**: Argument parsing, error handling, integration
- **Routing**: Provider selection and query processing

### Mock Strategy
- `mock_config`: Basic configuration mock
- `mock_llm_client`: Simple LLM client for testing
- `real_config`: Session-scoped real config for integration tests

## Test Results

Current: **31 tests passing** - all essential functionality covered.

```bash
================================ 31 passed in 0.03s ================================
```

## Development Integration

- Run `pytest tests/` before commits
- All core functionality tested without external dependencies
- Tests validate system structure and error handling
