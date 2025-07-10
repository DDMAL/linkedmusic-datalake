#!/usr/bin/env python3
"""
Test runner for nlq2sparql test suite
Runs all tests and provides a summary
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import test modules
from tests.test_config import TestConfig
from tests.test_providers import TestProviders, TestRouter


def run_test_suite():
    """Run the complete test suite"""
    
    print("🚀 Running nlq2sparql test suite")
    print("=" * 60)
    
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    # Define all test classes and their test methods
    test_suites = [
        (TestConfig(), [
            'test_config_initialization',
            'test_available_databases', 
            'test_default_queries',
            'test_provider_configs',
            'test_prefixes',
            'test_api_key_handling'
        ]),
        (TestProviders(), [
            'test_base_class_prompt_building',
            'test_base_class_response_cleaning',
            'test_provider_config_merging',
            'test_generate_sparql_method',
            'test_provider_imports_without_dependencies'
        ]),
        (TestRouter(), [
            'test_router_initialization',
            'test_router_lazy_loading',
            'test_router_invalid_provider'
        ])
    ]
    
    # Run all tests
    for test_instance, test_methods in test_suites:
        class_name = test_instance.__class__.__name__
        print(f"\n🧪 Running {class_name} tests...")
        
        for method_name in test_methods:
            total_tests += 1
            try:
                test_method = getattr(test_instance, method_name)
                test_method()
                print(f"   ✓ {method_name}")
                passed_tests += 1
            except Exception as e:
                print(f"   ✗ {method_name} - {e}")
                failed_tests.append(f"{class_name}.{method_name}: {e}")
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"TEST SUMMARY: {passed_tests}/{total_tests} tests passed")
    
    if failed_tests:
        print(f"\n❌ {len(failed_tests)} tests failed:")
        for failure in failed_tests:
            print(f"   - {failure}")
        print(f"\n{'='*60}")
        return False
    else:
        print("\n🎉 ALL TESTS PASSED!")
        print("\n✅ The nlq2sparql system is working correctly!")
        print("\n📝 To use with real API keys:")
        print("   1. Set API keys in environment or .env file")
        print("   2. Install dependencies: poetry install")  
        print("   3. Run: python cli.py --test --database diamm --provider gemini --verbose")
        print(f"\n{'='*60}")
        return True


def main():
    """Main entry point"""
    try:
        success = run_test_suite()
        return 0 if success else 1
    except Exception as e:
        print(f"\n💥 Test runner crashed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
