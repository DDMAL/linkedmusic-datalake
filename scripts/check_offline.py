"""Run every required offline suite in an isolated interpreter process."""

from pathlib import Path
import json
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SUITES = ("evaluation/tests", "rism/tests")

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
        with tempfile.TemporaryDirectory(prefix="linkedmusic-controls-") as directory:
            output = Path(directory) / "queries"
            subprocess.run(
                [
                    sys.executable,
                    "evaluation/run_queries.py",
                    "--fixture",
                    "--output-dir",
                    str(output),
                ],
                cwd=ROOT,
                check=True,
            )
            cases = json.loads((output / "report.json").read_text())["cases"]
            if (
                len(cases) != 14
                or {row["id"] for row in cases} != {f"cq{i:02d}" for i in range(1, 15)}
                or any(row["validation"] != "fixture_pass" for row in cases)
            ):
                raise ValueError("All 14 competency fixture cases are required")
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as error:
        print(f"Offline checks failed: {error}", file=sys.stderr)
        return 1
    print("All required offline suites passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
