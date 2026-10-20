"""Offline integrity, coverage, link, privacy and Slurm-template checks."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from urllib.parse import unquote

from refresh import ROOT, REQUIRED, SNAPSHOT, render_review_report, review_changes


def check(root: Path = ROOT, strict_review: bool = False) -> list[str]:
    errors = []
    manifest = json.loads((root / "sources.json").read_text(encoding="utf-8"))
    snapshot = (root / SNAPSHOT).read_bytes()
    if hashlib.sha256(snapshot).hexdigest() != manifest["snapshot_sha256"]:
        errors.append("Snapshot SHA-256 does not match sources.json.")
    text = snapshot.decode("utf-8")
    found = re.findall(r"^FILE: (.+)$", text, re.M)
    if sorted(found) != sorted(manifest["text_files"]):
        errors.append("Snapshot FILE sections do not match the source inventory.")
    if any(path not in found for path in REQUIRED):
        errors.append("Required documentation is missing.")
    if hashlib.sha256((root / "LICENSE").read_bytes()).hexdigest() != manifest["text_files"]["LICENSE"]["sha256"]:
        errors.append("Upstream LICENSE has changed or was not retained exactly.")
    reviews = json.loads((root / "guides/reviewed_sources.json").read_text())
    if (root / "UPSTREAM_CHANGES.md").read_bytes() != render_review_report(manifest, reviews):
        errors.append("UPSTREAM_CHANGES.md does not match source/review metadata.")
    stale = review_changes(manifest, reviews)
    if stale:
        message = f"{len(stale)} guide/template groups need source review; see UPSTREAM_CHANGES.md."
        if strict_review:
            errors.append(message)
        else:
            print("REVIEW REQUIRED:", message)
    for guide in reviews["guides"]:
        if not (root / guide).is_file():
            errors.append(f"Missing reviewed guide/template index: {guide}")
    for path in [*root.glob("*.md"), *root.glob("guides/*.md")]:
        content = path.read_text(encoding="utf-8")
        fence = chr(96) * 3
        prose = re.sub(fence + ".*?" + fence, "", content, flags=re.S)
        for destination in re.findall(r"\[[^\]]*\]\((<[^>]+>|[^)\s]+)\)", prose):
            destination = unquote(destination.strip("<>"))
            if re.match(r"[a-zA-Z][a-zA-Z0-9+.-]*:", destination) or destination.startswith("#"):
                continue
            target = destination.split("#")[0]
            if target and not (path.parent / target).exists():
                errors.append(f"{path.relative_to(root)}: broken local link {destination}")
        for source in re.findall(r"source/[A-Za-z0-9_./-]+\.(?:rst|md|py|sh)", prose):
            if source not in manifest["text_files"]:
                errors.append(f"{path.relative_to(root)}: upstream source path missing: {source}")
    templates = root / "slurm templates"
    bash = shutil.which("bash")
    if sys.platform == "win32":
        candidates = [Path(r"C:\Program Files\Git\bin\bash.exe"),
                      Path.home() / "AppData/Local/Programs/Git/bin/bash.exe"]
        bash = next((str(path) for path in candidates if path.exists()), bash)
    if not bash:
        errors.append("Bash unavailable: install Git for Windows or run checks on Linux for shell syntax validation.")
    files = sorted([*templates.glob("*.slurm"), *templates.glob("*.sh")])
    if len(files) < 10:
        errors.append("Expected the complete Slurm-template set.")
    for path in files:
        raw = path.read_bytes()
        if b"\r" in raw:
            errors.append(f"{path.name}: shell files require LF endings.")
        value = raw.decode("utf-8")
        if path.suffix == ".slurm":
            if not value.startswith("#!/bin/bash -l\n"):
                errors.append(f"{path.name}: login-shell shebang missing.")
            for directive in ("--clusters=", "--account=", "--partition=", "--time=", "--output="):
                if not re.search(r"^#SBATCH " + re.escape(directive), value, re.M):
                    errors.append(f"{path.name}: missing explicit {directive}")
            for line in value.splitlines():
                if line.startswith("#SBATCH") and "$" in line:
                    errors.append(f"{path.name}: shell variable in a literal Slurm directive.")
        if bash:
            result = subprocess.run([bash, "-n", str(path.relative_to(root))], cwd=root, capture_output=True, text=True)
            if result.returncode:
                errors.append(f"{path.name}: {result.stderr.strip()}")
    authored = [*root.glob("*.md"), *root.glob("guides/*.md"), *files, *root.glob("scripts/*.py")]
    for path in authored:
        value = path.read_text(encoding="utf-8")
        for pattern in (r"\bvsc\d{5}\b", r"\blp_verbekelab\b", r"\bstg_00211\b",
                        r"gh[pousr]_[A-Za-z0-9]{25,}", r"github_pat_[A-Za-z0-9_]{30,}"):
            if re.search(pattern, value) and path.name != "check.py":
                errors.append(f"{path.relative_to(root)}: private identifier or credential pattern.")
    if any(root.glob("PROJECT_SPECIFIC*")):
        errors.append("Consumer-specific notes belong in the consuming project's docs/VSC.md.")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict-review", action="store_true")
    args = parser.parse_args()
    errors = check(strict_review=args.strict_review)
    if errors:
        for error in errors:
            print("ERROR:", error)
        raise SystemExit(1)
    print("Offline source integrity, documentation links, privacy and Bash syntax checks passed.")
    print("This does not submit jobs or validate a live VSC environment.")


if __name__ == "__main__":
    main()
