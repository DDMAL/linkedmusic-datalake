"""Run every required offline suite in an isolated interpreter process."""

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SUITES = ("evaluation/tests",)

# Discovery must fail even when a test_*.py file exists but contains no tests.
DISCOVER = """
import sys
import unittest
suite = unittest.defaultTestLoader.discover(sys.argv[1])
if not suite.countTestCases():
    sys.exit('Required suite is empty: ' + sys.argv[1])
result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(0 if result.wasSuccessful() else 1)
"""


def main():
    try:
        for suite in SUITES:
            if not (ROOT / suite).is_dir():
                raise ValueError(f"Missing required suite: {suite}")
            print(f"Running {suite}", flush=True)
            subprocess.run(
                [sys.executable, "-c", DISCOVER, suite], cwd=ROOT, check=True
            )
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"Offline checks failed: {error}", file=sys.stderr)
        return 1
    print("All required offline suites passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
