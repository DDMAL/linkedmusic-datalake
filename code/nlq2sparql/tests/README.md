# NLQ2SPARQL Test Suite

This directory contains a comprehensive test suite for the NLQ-to-SPARQL system. All critical system components are tested here to ensure reliability and maintainability.

## Test Coverage

### Core System Tests
- **config.json loading and validation**: Verifies JSON structure, required fields, and data integrity
- **Config fallback behavior**: Tests behavior with missing or invalid configuration files
- **Configuration loading**: Tests that Config class properly loads and provides access to all settings
- **CLI invocation**: Tests both direct script execution and module execution modes
- **Base class functionality**: Tests shared logic in BaseLLMClient (prompt building, response cleaning, etc.)
- **Router functionality**: Tests provider routing and lazy loading of dependencies
- **Provider imports**: Verifies that providers can be imported without their optional dependencies
- **CLI functionality**: Tests argument parsing, database choices, and help system
- **Integration testing**: End-to-end testing with mock API responses

### Test Files

1. **test_config.py**: Configuration and settings tests
2. **test_providers.py**: Provider and base class tests  
3. **test_comprehensive.py**: Complete integration testing with CLI invocation tests
4. **run_tests.py**: Test runner that executes all modular tests

## Running Tests

### Run All Tests (Recommended)
```bash
# From nlq2sparql directory
python tests/run_tests.py

# Or run comprehensive tests directly
python tests/test_comprehensive.py
```

### Run Individual Test Modules
```bash
# Test configuration only
python tests/test_config.py

# Test providers only
python tests/test_providers.py

# Run specific comprehensive tests
python tests/test_comprehensive.py
```

## Test Features

### No External Dependencies Required
- All tests run without requiring API keys or external LLM services
- Uses mock implementations to test core logic
- Tests provider imports without requiring optional dependencies (google.generativeai, openai, anthropic)

### Both Direct and Module Execution
- Tests verify the system works when run as `python cli.py` (direct)
- Tests verify the system works when run as `python -m code.nlq2sparql.cli` (module)
- Import handling supports both execution modes

### Configuration Testing
- **config.json structure validation**: Ensures all required sections (databases, providers, prefixes) exist
- **Config class integration**: Verifies Config class correctly loads and interprets JSON data
- **Fallback behavior**: Tests what happens when config.json is missing or malformed
- **CLI configuration loading**: Tests that CLI correctly loads config at startup

### CLI Testing
- **Help system**: Tests `--help` option works in both execution modes
- **Database listing**: Tests `--list-databases` feature
- **Argument validation**: Tests proper error handling for invalid arguments
- **Database requirement**: Tests that `--database` is required except for listing
- **Error handling**: Tests graceful handling of missing API keys

### Provider Testing
- **Base class logic**: Tests all shared functionality across providers
- **Mock implementations**: Uses mock providers to test generate_sparql workflow
- **Lazy loading**: Tests that providers can be imported without their dependencies
- **Router functionality**: Tests provider selection and routing logic

## Test Results

When all tests pass, you'll see:
```
============================================================
TEST RESULTS: 9/9 passed
🎉 ALL TESTS PASSED!
============================================================
```

## Integration with Development

### Continuous Testing
- Run tests before committing changes
- All critical paths are covered in the test suite
- No need for separate manual CLI testing

### Configuration Changes
- When adding new databases, update config.json and tests will verify the integration
- When adding new providers, update config.json providers section
- Tests automatically discover and validate new configuration

### Code Changes
- Tests ensure refactoring doesn't break existing functionality
- Mock implementations allow testing without external dependencies
- Both direct script and module execution are tested

This comprehensive approach ensures the system remains reliable while providing a single place to verify all functionality.
- Provider configuration merging
- API key handling

### ✅ Provider Tests  
- Base class functionality
- Prompt building and response cleaning
- Configuration merging with defaults
- Lazy imports (no dependencies required)
- Mock API call handling

### ✅ Router Tests
- Router initialization
- Lazy loading of provider clients
- Error handling for missing API keys
- Invalid provider rejection

### ✅ Integration Tests
- End-to-end query generation with mocks
- CLI functionality validation
- Import system testing
- System robustness validation

## Test Requirements

The tests are designed to run **without any external dependencies** or API keys. They use:

- Mock implementations for API calls
- Configuration validation only
- Import testing without actual provider libraries
- Graceful error handling validation

## Expected Results

All tests should pass without requiring:
- ❌ API keys
- ❌ External provider dependencies (openai, anthropic, google-generativeai)
- ❌ Network connections
- ❌ Special environment setup

The tests validate that the system is properly structured and will work when real API keys and dependencies are provided.
