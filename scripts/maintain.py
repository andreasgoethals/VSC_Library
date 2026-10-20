"""One entry point for local maintenance; check-only never refreshes."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--strict-review", action="store_true")
    args = parser.parse_args()
    if not args.check_only:
        subprocess.run([sys.executable, "scripts/refresh.py"], cwd=ROOT, check=True)
    command = [sys.executable, "scripts/check.py"]
    if args.strict_review:
        command.append("--strict-review")
    subprocess.run(command, cwd=ROOT, check=True)
    subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
