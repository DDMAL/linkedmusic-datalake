#!/usr/bin/env python3
"""
Simple test runner for nlq2sparql tests
Runs all tests without requiring pytest
"""

import subprocess
import sys
from pathlib import Path


def run_test_file(test_file):
    """Run a single test file and return (success, output)"""
    try:
        result = subprocess.run([
            sys.executable, test_file
        ], capture_output=True, text=True, timeout=30)
        
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Test timed out"


def main():
    """Run all tests"""
    print("🧪 Running nlq2sparql test suite...\n")
    
    test_files = [
        "tests/test_config.py",
        "tests/test_providers.py", 
        "tests/test_comprehensive.py"
    ]
    
    all_passed = True
    
    for test_file in test_files:
        print(f"Running {test_file}...")
        success, stdout, stderr = run_test_file(test_file)
        
        if success:
            print(f"✅ {test_file} PASSED")
            if stdout.strip():
                # Show last line of output for summary
                last_line = stdout.strip().split('\n')[-1]
                print(f"   {last_line}")
        else:
            print(f"❌ {test_file} FAILED")
            if stderr:
                print(f"   Error: {stderr}")
            if stdout:
                print(f"   Output: {stdout}")
            all_passed = False
        
        print()
    
    if all_passed:
        print("🎉 All tests passed!")
        return 0
    else:
        print("💥 Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
