#!/usr/bin/env python3
"""
Enhanced test runner for nlq2sparql tests
Runs all tests without requiring pytest with comprehensive reporting
"""

import subprocess
import sys
import time
import os
from pathlib import Path
from typing import List, Tuple, Optional
import argparse


class TestResult:
    """Data class for test results"""
    def __init__(self, name: str, success: bool, stdout: str, stderr: str, duration: float):
        self.name = name
        self.success = success
        self.stdout = stdout
        self.stderr = stderr
        self.duration = duration


class TestRunner:
    """Enhanced test runner with better error handling and reporting"""
    
    def __init__(self, verbose: bool = False, timeout: int = 30):
        self.verbose = verbose
        self.timeout = timeout
        self.results: List[TestResult] = []
    
    def discover_test_files(self, test_dir: Path) -> List[Path]:
        """Automatically discover test files"""
        if not test_dir.exists():
            raise FileNotFoundError(f"Test directory not found: {test_dir}")
        
        test_files = list(test_dir.glob("test_*.py"))
        if not test_files:
            raise RuntimeError(f"No test files found in {test_dir}")
        
        return sorted(test_files)
    
    def run_test_file(self, test_file: Path) -> TestResult:
        """Run a single test file and return detailed results"""
        start_time = time.time()
        
        try:
            # Ensure we're in the right directory
            cwd = test_file.parent.parent
            
            result = subprocess.run([
                sys.executable, str(test_file)
            ], capture_output=True, text=True, timeout=self.timeout, cwd=cwd)
            
            duration = time.time() - start_time
            success = result.returncode == 0
            
            return TestResult(
                name=test_file.name,
                success=success,
                stdout=result.stdout,
                stderr=result.stderr,
                duration=duration
            )
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return TestResult(
                name=test_file.name,
                success=False,
                stdout="",
                stderr=f"Test timed out after {self.timeout} seconds",
                duration=duration
            )
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                name=test_file.name,
                success=False,
                stdout="",
                stderr=f"Failed to run test: {e}",
                duration=duration
            )
    
    def run_all_tests(self, test_files: List[Path]) -> bool:
        """Run all tests and return overall success"""
        print("🧪 Running nlq2sparql test suite...\n")
        
        total_tests = len(test_files)
        passed = 0
        failed = 0
        
        for i, test_file in enumerate(test_files, 1):
            print(f"[{i}/{total_tests}] Running {test_file.name}...")
            
            result = self.run_test_file(test_file)
            self.results.append(result)
            
            if result.success:
                passed += 1
                print(f"✅ {test_file.name} PASSED ({result.duration:.2f}s)")
                
                if self.verbose and result.stdout.strip():
                    # Show summary line from test output
                    lines = result.stdout.strip().split('\n')
                    summary_line = next((line for line in reversed(lines) if 'test' in line.lower()), None)
                    if summary_line:
                        print(f"   {summary_line}")
                        
            else:
                failed += 1
                print(f"❌ {test_file.name} FAILED ({result.duration:.2f}s)")
                
                if result.stderr:
                    # Show more concise error information
                    error_lines = result.stderr.strip().split('\n')
                    relevant_errors = [line for line in error_lines if 'Error:' in line or 'FAILED' in line]
                    
                    if relevant_errors:
                        print(f"   Error: {relevant_errors[0]}")
                    else:
                        # Show first few lines if no clear error pattern
                        print(f"   Error: {error_lines[0] if error_lines else 'Unknown error'}")
                
                if self.verbose:
                    print(f"   Full stderr: {result.stderr}")
                    if result.stdout:
                        print(f"   Full stdout: {result.stdout}")
            
            print()
        
        self._print_summary(passed, failed, total_tests)
        return failed == 0
    
    def _print_summary(self, passed: int, failed: int, total: int) -> None:
        """Print test run summary"""
        total_duration = sum(r.duration for r in self.results)
        
        print("=" * 60)
        print(f"📊 Test Summary:")
        print(f"   Total tests: {total}")
        print(f"   Passed: {passed}")
        print(f"   Failed: {failed}")
        print(f"   Duration: {total_duration:.2f}s")
        print("=" * 60)
        
        if failed == 0:
            print("🎉 All tests passed!")
        else:
            print("💥 Some tests failed!")
            print("\nFailed tests:")
            for result in self.results:
                if not result.success:
                    print(f"  - {result.name}")


def main() -> int:
    """Main entry point with argument parsing"""
    parser = argparse.ArgumentParser(description="Run nlq2sparql tests")
    parser.add_argument("-v", "--verbose", action="store_true", 
                       help="Enable verbose output")
    parser.add_argument("-t", "--timeout", type=int, default=30,
                       help="Test timeout in seconds (default: 30)")
    parser.add_argument("--test-dir", type=Path, default=None,
                       help="Test directory (default: ./tests)")
    
    args = parser.parse_args()
    
    try:
        # Determine test directory
        if args.test_dir:
            test_dir = args.test_dir
        else:
            # Default to tests directory relative to this script
            script_dir = Path(__file__).parent
            test_dir = script_dir / "tests"
        
        # Validate working directory
        if not Path.cwd().name == "nlq2sparql":
            print("⚠️  Warning: Not running from nlq2sparql directory")
            print(f"   Current directory: {Path.cwd()}")
            print(f"   Expected to be in: .../code/nlq2sparql")
        
        # Create and run test runner
        runner = TestRunner(verbose=args.verbose, timeout=args.timeout)
        test_files = runner.discover_test_files(test_dir)
        
        print(f"� Found {len(test_files)} test files in {test_dir}")
        if args.verbose:
            for test_file in test_files:
                print(f"   - {test_file.name}")
            print()
        
        success = runner.run_all_tests(test_files)
        return 0 if success else 1
        
    except Exception as e:
        print(f"❌ Test runner failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 2


if __name__ == "__main__":
    sys.exit(main())
