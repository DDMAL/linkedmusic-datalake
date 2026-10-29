"""Run the preservation tests and synthetic query controls without source dumps."""

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUITES = (
    "shared/tests",
    "rism/tests",
    "musicbrainz/tests",
    "diamm/tests",
    "ckg-apsearch/tests",
    "evaluation/tests",
)


def check(output_dir):
    # Separate processes avoid collisions between dataset modules with names
    # such as convert_to_rdf. Always use the caller's Python environment.
    for suite in SUITES:
        if not any((ROOT / suite).glob("test_*.py")):
            raise ValueError(f"No tests found in required suite: {suite}")
        print(f"\nRunning {suite}", flush=True)
        subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", suite, "-v"],
            cwd=ROOT,
            check=True,
        )
    print("\nChecking all competency queries against synthetic answers", flush=True)
    subprocess.run(
        [
            sys.executable,
            "evaluation/run_queries.py",
            "--fixture",
            "--output-dir",
            str(output_dir),
        ],
        cwd=ROOT,
        check=True,
    )
    print("\nAll offline checks passed.", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Retain query reports in a new directory; otherwise use temporary files.",
    )
    args = parser.parse_args()
    try:
        if args.output_dir is not None:
            output_dir = args.output_dir.resolve()
            if output_dir.exists():
                raise FileExistsError(f"Report directory already exists: {output_dir}")
            check(output_dir)
            print(f"Query reports: {output_dir}")
        else:
            with tempfile.TemporaryDirectory(
                prefix="linkedmusic-offline-"
            ) as directory:
                check(Path(directory) / "queries")
    except subprocess.CalledProcessError as error:
        print(f"Offline checks failed (exit {error.returncode}).", file=sys.stderr)
        return 1
    except (OSError, ValueError) as error:
        print(f"Offline checks could not complete: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
