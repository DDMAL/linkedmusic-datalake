# nlq2sparql Makefile
# Modern pytest-based development commands

.PHONY: test test-unit test-integration test-coverage test-verbose clean help install check debug-example format lint

# Default target
help:
	@echo "nlq2sparql Development Commands"
	@echo "================================"
	@echo ""
	@echo "test          Run all tests with pytest"
	@echo "test-unit     Run only unit tests"
	@echo "test-integration Run integration tests"
	@echo "test-coverage Run tests with coverage report"
	@echo "test-verbose  Run tests with verbose output" 
	@echo "quick-test    Run quick tests (no slow/API tests)"
	@echo "clean         Clean up cache and debug files"
	@echo "check         Check code without running tests"
	@echo "debug-example Run a debug example"
	@echo "install       Install dependencies (poetry)"
	@echo "format        Format code with black"
	@echo "lint          Lint code with flake8"
	@echo ""

# Run all tests with pytest
test:
	@echo "🧪 Running all tests with pytest..."
	@cd ../.. && poetry run pytest shared/nlq2sparql/tests/ -v

# Run only unit tests
test-unit:
	@echo "🔬 Running unit tests..."
	@cd ../.. && poetry run pytest shared/nlq2sparql/tests/ -v -m "unit"

# Run integration tests  
test-integration:
	@echo "🔗 Running integration tests..."
	@cd ../.. && poetry run pytest shared/nlq2sparql/tests/ -v -m "integration"

# Run tests with coverage
test-coverage:
	@echo "📊 Running tests with coverage..."
	@cd ../.. && poetry run pytest shared/nlq2sparql/tests/ --cov=shared/nlq2sparql --cov-report=html --cov-report=term

# Run tests with verbose Python output
test-verbose:
	@echo "🔍 Running tests with verbose output..."
	@cd ../.. && poetry run pytest shared/nlq2sparql/tests/ -v -s

# Quick test (excluding slow and API tests)
quick-test:
	@echo "⚡ Running quick tests..."
	@cd ../.. && poetry run pytest shared/nlq2sparql/tests/ -v -m "not slow and not requires_api_key"

# Clean up generated files
clean:
	@echo "🧹 Cleaning up..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@rm -rf .pytest_cache/ 2>/dev/null || true
	@rm -rf htmlcov/ 2>/dev/null || true
	@rm -rf .coverage 2>/dev/null || true
	@echo "✅ Cleanup complete!"

# Code formatting with black
format:
	@echo "🎨 Formatting code..."
	@cd ../.. && poetry run black shared/nlq2sparql/

# Code linting with flake8  
lint:
	@echo "🔍 Linting code..."
	@cd ../.. && poetry run flake8 shared/nlq2sparql/
	@find . -name "*.pyc" -delete 2>/dev/null || true
	@rm -f debug_prompts/*.txt 2>/dev/null || true
	@echo "✅ Cleanup complete!"

# Quick code check
check:
	@echo "🔍 Checking code structure..."
	@python -m py_compile cli.py
	@python -m py_compile config.py
	@python -m py_compile router.py
	@echo "✅ Code structure looks good!"

# Run a debug example
debug-example:
	@echo "🐛 Running debug example..."
	@python cli.py --debug-prompt --database diamm "Find works by anonymous composers"
	@echo ""
	@echo "📁 Debug prompt saved to debug_prompts/"

# Install dependencies
install:
	@echo "📦 Installing dependencies..."
	@poetry install
	@echo "✅ Dependencies installed!"
