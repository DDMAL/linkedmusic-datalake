# nlq2sparql Makefile
# Simple commands for common development tasks

.PHONY: test test-verbose clean help install check debug-example

# Default target
help:
	@echo "nlq2sparql Development Commands"
	@echo "================================"
	@echo ""
	@echo "test          Run all tests"
	@echo "test-verbose  Run tests with verbose output"
	@echo "clean         Clean up cache and debug files"
	@echo "check         Check code without running tests"
	@echo "debug-example Run a debug example"
	@echo "install       Install dependencies (poetry)"
	@echo ""

# Run all tests
test:
	@python run_tests.py

# Run tests with verbose Python output
test-verbose:
	@python -v run_tests.py

# Clean up generated files
clean:
	@echo "🧹 Cleaning up..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
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
