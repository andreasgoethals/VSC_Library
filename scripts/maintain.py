#!/usr/bin/env python
"""Run configured library maintenance; check-only never writes library content."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

# Set this before importing local modules, including on direct invocation.
sys.dont_write_bytecode = True
_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS = _ROOT / "scripts"
sys.path.insert(0, str(_SCRIPTS))
CONFIG = json.loads((_SCRIPTS / "library.json").read_text(encoding="utf-8"))
LIBRARY_NAME = CONFIG["name"]
STAGES = {
    name: ([sys.executable, "-B", *stage["command"]], stage.get("mutating", False), stage["description"])
    for name, stage in CONFIG["stages"].items()
}
CHECK_ONLY_OVERRIDE = {
    name: [sys.executable, "-B", *stage["check_command"]]
    for name, stage in CONFIG["stages"].items() if "check_command" in stage
}


def run_stage(name: str, argv: list[str]) -> tuple[int, float, str]:
    started = time.monotonic()
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8", GIT_OPTIONAL_LOCKS="0")
    try:
        proc = subprocess.run(argv, cwd=_ROOT, env=env, capture_output=True,
                              text=True, encoding="utf-8", errors="replace")
        return proc.returncode, time.monotonic() - started, (proc.stdout or "") + (proc.stderr or "")
    except OSError as exc:
        return 2, time.monotonic() - started, str(exc)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check-only", action="store_true", help="report only; skip snapshot refresh and check extraction parity")
    ap.add_argument("--skip", action="append", default=[], choices=list(STAGES), metavar="STAGE")
    ap.add_argument("--only", action="append", default=[], choices=list(STAGES), metavar="STAGE")
    ap.add_argument("--strict-review", action="store_true", help="fail unresolved source reviews where supported")
    ap.add_argument("--quiet", action="store_true", help="suppress stage output and print the result summary")
    args = ap.parse_args(argv)
    selected = [s for s in STAGES if (not args.only or s in args.only) and s not in args.skip]
    excluded = [s for s in selected if args.check_only and STAGES[s][1] and s not in CHECK_ONLY_OVERRIDE]
    selected = [s for s in selected if s not in excluded]
    print(f"{LIBRARY_NAME} maintenance" + (" (read-only)" if args.check_only else ""))
    print("Stages: " + (", ".join(selected) or "(none)"))
    if excluded:
        print("Skipped mutating stages: " + ", ".join(excluded))
    if not args.check_only and any(STAGES[name][1] for name in selected):
        probe = subprocess.run(["git", "rev-parse", "--show-superproject-working-tree"],
                               cwd=_ROOT, capture_output=True, text=True,
                               env=dict(os.environ, GIT_OPTIONAL_LOCKS="0"))
        if probe.returncode or probe.stdout.strip():
            print("ERROR: refresh requires an independent canonical Git checkout.", file=sys.stderr)
            return 2
    results = []
    for name in selected:
        cmd = CHECK_ONLY_OVERRIDE.get(name, STAGES[name][0]) if args.check_only else STAGES[name][0]
        print(f"\n>>> [{name}] {STAGES[name][2]}", flush=True)
        if args.strict_review and CONFIG["stages"][name].get("strict_review"):
            cmd = [*cmd, "--strict-review"]
        code, elapsed, output = run_stage(name, cmd)
        if not args.quiet and output.strip():
            print(output.rstrip())
        print(f"[{name}] {'OK' if code == 0 else 'ATTENTION'} (exit {code}, {elapsed:.1f}s)", flush=True)
        results.append((name, code))
        # Refresh may invalidate curated references; recheck the selected outputs.
        if code == 0 and not args.check_only:
            for post in CONFIG["stages"][name].get("post_checks", []):
                if post in args.skip:
                    continue
                post_code, elapsed, output = run_stage(post, STAGES[post][0])
                if (not args.quiet or post_code) and output.strip():
                    print(output.rstrip())
                print(f"[{post} after {name}] {'OK' if post_code == 0 else 'ATTENTION'} (exit {post_code}, {elapsed:.1f}s)")
                results.append((f"{post} after {name}", post_code))
    failed = [name for name, code in results if code != 0]
    print("\n" + ("Needs attention: " + ", ".join(failed) if failed else "All selected stages passed."))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
