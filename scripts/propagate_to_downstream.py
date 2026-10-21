#!/usr/bin/env python
"""Discover consumers and pin only this library to its exact published HEAD.

Dry-run only reads Git state. Updates require a clean canonical library and an
origin-advertised commit (or a locally provable ancestor of an advertised ref).
Only the submodule path is committed; --push explicitly opts into downstream pushes.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path, PurePosixPath
import posixpath
import re
import subprocess
import sys
from urllib.parse import urlsplit

sys.dont_write_bytecode = True
_ROOT = Path(__file__).resolve().parents[1]


def git(*args: str, cwd: Path, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=str(cwd), check=check,
                          capture_output=True, text=True, encoding="utf-8", errors="replace",
                          env=dict(os.environ, GIT_OPTIONAL_LOCKS="0"))


def normalise_remote(url: str) -> str:
    """Match HTTPS/SSH spellings, while retaining host identity and local paths."""
    value = url.strip().rstrip("/")
    # Do not treat Windows drives as SSH hosts.
    if re.match(r"^[A-Za-z]:[\\/]", value):
        return re.sub(r"\.git$", "", str(Path(value).resolve()).replace("\\", "/"), flags=re.I).casefold()
    if re.match(r"^(?:[^/@:]+@)?[^/:]+:.+", value) and "://" not in value:
        value = re.sub(r"^(?:[^/@:]+@)?([^:]+):", r"ssh://\1/", value)
    parsed = urlsplit(value)
    if parsed.scheme and parsed.scheme != "file":
        host = (parsed.hostname or "").casefold()
        port = f":{parsed.port}" if parsed.port and parsed.port not in (22, 443) else ""
        return host + port + "/" + re.sub(r"\.git$", "", parsed.path.strip("/"), flags=re.I).casefold()
    path = parsed.path if parsed.scheme == "file" else value
    return re.sub(r"\.git$", "", str(Path(path).resolve()).replace("\\", "/"), flags=re.I).casefold()


def resolve_submodule_remote(url: str, parent_origin: str) -> str:
    if not url.startswith(("./", "../")):
        return url
    if "://" in parent_origin:
        parsed = urlsplit(parent_origin)
        return f"{parsed.scheme}://{parsed.netloc}" + posixpath.normpath(parsed.path.rstrip("/") + "/" + url)
    if re.match(r"^[^/]+@[^:]+:", parent_origin):
        prefix, path = parent_origin.split(":", 1)
        return prefix + ":" + posixpath.normpath(path.rstrip("/") + "/" + url)
    return str(Path(parent_origin) / url)


class Project:
    def __init__(self, repo: Path, sub_path: str) -> None:
        self.repo, self.sub_path = repo, sub_path
        self.status, self.detail = "pending", ""

    @property
    def sub_dir(self) -> Path:
        return self.repo / self.sub_path

    def pinned_sha(self) -> str | None:
        result = git("ls-tree", "HEAD", "--", self.sub_path, cwd=self.repo, check=False)
        match = re.match(r"^160000 commit ([0-9a-f]{40,64})\t", result.stdout)
        return match.group(1) if match else None


def discover(roots: list[Path], library_key: str, depth: int) -> list[Project]:
    found, seen = [], set()
    for root in roots:
        if not root.is_dir():
            continue
        patterns = ["/".join(["*"] * level + [".gitmodules"]) for level in range(depth + 1)]
        for module_file in sorted({path for pattern in patterns for path in root.glob(pattern)}):
            repo = module_file.parent.resolve()
            if repo == _ROOT.resolve():
                continue
            result = git("config", "--file", str(module_file), "--get-regexp", r"^submodule\..*\.(path|url)$", cwd=repo, check=False)
            records: dict[str, dict[str, str]] = {}
            for line in result.stdout.splitlines():
                key, _, value = line.partition(" ")
                match = re.match(r"^submodule\.(.*)\.(path|url)$", key)
                if match:
                    records.setdefault(match.group(1), {})[match.group(2)] = value.strip()
            parent_origin = git("remote", "get-url", "origin", cwd=repo, check=False).stdout.strip()
            for record in records.values():
                if not record.get("url") or not record.get("path"):
                    continue
                path = record["path"].replace("\\", "/")
                # Reject traversal or absolute paths before any later operation.
                if path in ("", ".") or PurePosixPath(path).is_absolute() or any(part in ("..", ".git") for part in PurePosixPath(path).parts) or re.match(r"^[A-Za-z]:", path):
                    continue
                resolved = (repo / path).resolve()
                if resolved == repo or not resolved.is_relative_to(repo):
                    continue
                if normalise_remote(resolve_submodule_remote(record["url"], parent_origin)) != library_key:
                    continue
                identity = (repo, path)
                if identity not in seen:
                    seen.add(identity)
                    found.append(Project(repo, path))
    return found


def published_on_origin(head: str) -> tuple[bool, str]:
    """Prove HEAD is reachable from a currently advertised origin ref, read-only."""
    result = git("ls-remote", "--heads", "--tags", "origin", cwd=_ROOT, check=False)
    if result.returncode:
        return False, "cannot query origin: " + result.stderr.strip()
    refs = [line.split()[0] for line in result.stdout.splitlines() if line.split()]
    for sha in refs:
        if sha == head:
            return True, "HEAD is advertised by origin"
        result = git("merge-base", "--is-ancestor", head, sha, cwd=_ROOT, check=False)
        if result.returncode == 0:
            return True, "HEAD is an ancestor of an advertised origin ref"
    return False, "HEAD is not provably published on origin; push it, or fetch origin if advertised newer objects are unavailable locally"


def readiness() -> tuple[str | None, list[str]]:
    result = git("rev-parse", "--verify", "HEAD", cwd=_ROOT, check=False)
    head = result.stdout.strip() if result.returncode == 0 else None
    issues = []
    if not head:
        issues.append("this library has no commit yet")
    status = git("status", "--porcelain", "--untracked-files=all", cwd=_ROOT, check=False)
    if status.returncode:
        issues.append("cannot inspect library status")
    elif status.stdout.strip():
        issues.append("this library has uncommitted changes")
    if head:
        published, reason = published_on_origin(head)
        if not published:
            issues.append(reason)
    return head, issues


def consumer_ready(project: Project) -> None:
    if not git("branch", "--show-current", cwd=project.repo).stdout.strip():
        raise ValueError("consumer HEAD is detached; select its intended branch first")
    if git("diff", "HEAD", "--", ".gitmodules", cwd=project.repo).stdout.strip():
        raise ValueError("consumer has pending .gitmodules changes; finish registration first")
    if git("diff", "--cached", "--name-only", "--", project.sub_path, cwd=project.repo).stdout.strip():
        raise ValueError("submodule path is already staged; preserve the owner's pending pin")
    if (project.sub_dir / ".git").exists():
        if git("status", "--porcelain", "--untracked-files=all", cwd=project.sub_dir).stdout.strip():
            raise ValueError("submodule contains local changes")
        if project.pinned_sha() != git("rev-parse", "HEAD", cwd=project.sub_dir).stdout.strip():
            raise ValueError("submodule checkout differs from the committed pin")


def push_project(project: Project) -> None:
    """Never publish unrelated, already-pending consumer commits."""
    branch = git("branch", "--show-current", cwd=project.repo).stdout.strip()
    if not branch:
        raise ValueError("cannot push a detached consumer")
    head = git("rev-parse", "HEAD", cwd=project.repo).stdout.strip()
    advertised = git("ls-remote", "--heads", "origin", f"refs/heads/{branch}", cwd=project.repo).stdout.split()
    if not advertised:
        raise ValueError("consumer branch is unpublished; publish its initial history explicitly")
    remote = advertised[0]
    if remote == head:
        return
    git("fetch", "origin", branch, cwd=project.repo)
    if git("merge-base", "--is-ancestor", remote, head, cwd=project.repo, check=False).returncode:
        raise ValueError("consumer branch is behind or diverged; reconcile it before pushing")
    commits = git("rev-list", f"{remote}..{head}", cwd=project.repo).stdout.split()
    for commit in commits:
        parents = git("rev-list", "--parents", "-n", "1", commit, cwd=project.repo).stdout.split()
        paths = set(git("diff-tree", "--no-commit-id", "--name-only", "-r", commit, cwd=project.repo).stdout.splitlines())
        if len(parents) != 2 or not paths or paths - {project.sub_path}:
            raise ValueError("unpublished consumer commits include unrelated changes; publish them explicitly")
    git("push", "origin", f"{head}:refs/heads/{branch}", cwd=project.repo)


def restore_pin(project: Project, old: str, previous_ref: str) -> None:
    """Undo a failed bump so no staged gitlink blocks the next run."""
    # The path was verified unstaged beforehand, so HEAD holds its prior entry.
    git("reset", "--quiet", "--", project.sub_path, cwd=project.repo)
    branch = previous_ref.removeprefix("refs/heads/") if previous_ref.startswith("refs/heads/") else ""
    if branch and git("rev-parse", "--verify", "--quiet", previous_ref, cwd=project.sub_dir, check=False).stdout.strip() == old:
        git("checkout", "--quiet", branch, cwd=project.sub_dir)
    else:
        git("checkout", "--quiet", "--detach", old, cwd=project.sub_dir)


def update_project(project: Project, head: str, *, message: str | None, push: bool) -> None:
    consumer_ready(project)
    sub_dir = project.sub_dir
    if not (sub_dir / ".git").exists():
        if sub_dir.exists() and any(sub_dir.iterdir()):
            raise ValueError("uninitialized submodule directory is not empty")
        git("submodule", "update", "--init", "--", project.sub_path, cwd=project.repo)
    library_origin = git("remote", "get-url", "origin", cwd=_ROOT).stdout.strip()
    submodule_origin = git("remote", "get-url", "origin", cwd=sub_dir).stdout.strip()
    if normalise_remote(submodule_origin) != normalise_remote(library_origin):
        raise ValueError("initialized submodule origin differs from the canonical library origin; inspect/sync it first")
    # A clean submodule protects local edits, untracked work and user-created branches.
    if git("status", "--porcelain", "--untracked-files=all", cwd=sub_dir).stdout.strip():
        raise ValueError("submodule contains local changes")
    if git("diff", "--cached", "--name-only", "--", project.sub_path, cwd=project.repo).stdout.strip():
        raise ValueError("submodule path is already staged; preserve the owner's pending pin")
    old = project.pinned_sha()
    checkout = git("rev-parse", "HEAD", cwd=sub_dir).stdout.strip()
    if old != checkout:
        raise ValueError("submodule checkout differs from the committed pin; preserve the owner's pending pin")
    git("fetch", "origin", cwd=sub_dir)
    git("cat-file", "-e", head + "^{commit}", cwd=sub_dir)
    previous_ref = git("symbolic-ref", "--quiet", "HEAD", cwd=sub_dir, check=False).stdout.strip()
    git("checkout", "--quiet", "--detach", head, cwd=sub_dir)
    commit_message = message or f"Bump {project.sub_path} pin to {head[:7]}"
    try:
        git("add", "--", project.sub_path, cwd=project.repo)
        # Path-limited commit preserves every unrelated staged/unstaged downstream file.
        git("commit", "-m", commit_message, "--", project.sub_path, cwd=project.repo)
    except subprocess.CalledProcessError as exc:
        if project.pinned_sha() == head:
            raise  # The pin commit exists; nothing to roll back.
        reason = (exc.stderr or exc.stdout or str(exc)).strip()
        try:
            restore_pin(project, old, previous_ref)
        except subprocess.CalledProcessError as undo:
            raise ValueError(f"pin commit failed ({reason}); rollback also failed, inspect manually: "
                             + (undo.stderr or str(undo)).strip()) from exc
        raise ValueError(f"pin commit failed; restored the previous pin and checkout: {reason}") from exc
    project.status, project.detail = "updated", f"committed {head[:7]}"
    if push:
        push_project(project)
        project.detail += " and pushed"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", action="append", metavar="DIR", help="consumer search root (repeatable; default is this repository's parent)")
    ap.add_argument("--project", action="append", help="exact consumer folder name or absolute path")
    ap.add_argument("--depth", type=int, default=3)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--push", action="store_true")
    ap.add_argument("--message", metavar="MSG")
    ap.add_argument("--allow-dirty", action="store_true", help="legacy spelling: permits discovery in dry-run only; never bypasses write safety")
    args = ap.parse_args(argv)
    if args.depth < 0:
        ap.error("--depth must be nonnegative")
    origin = git("remote", "get-url", "origin", cwd=_ROOT, check=False)
    if origin.returncode or not origin.stdout.strip():
        print("ERROR: this repository has no origin remote; consumer identity cannot be inferred.", file=sys.stderr)
        return 2
    if args.allow_dirty and not args.dry_run:
        print("ERROR: --allow-dirty is only supported with --dry-run; dirty/unpublished library updates are refused.", file=sys.stderr)
        return 2
    key = normalise_remote(origin.stdout.strip())
    head, issues = readiness()
    print(f"Library origin: {key}; target: {head or '(no commit yet)'}")
    for issue in issues:
        print(("[DISCOVERY ONLY] " if args.dry_run else "[REFUSING] ") + issue)
    if issues and not args.dry_run:
        return 2
    default_root = _ROOT.parent.parent if (_ROOT.parent / "scripts/workspace.py").is_file() else _ROOT.parent
    roots = [Path(root) for root in args.root] if args.root else [default_root]
    projects = discover(roots, key, args.depth)
    if args.project:
        projects = [p for p in projects if any(
            p.repo.name == selection or p.repo == Path(selection).resolve()
            for selection in args.project)]
    if not projects:
        print("No downstream consumers found in the selected search roots.")
    for project in projects:
        before = project.pinned_sha()
        label = f"{project.repo}/{project.sub_path}"
        if args.dry_run:
            action = "already pinned" if head and before == head else "would update" if head and not issues else "discovered; library not ready"
            print(f"[PLAN] {label}: {before or '(no gitlink)'} -> {head or '(no commit)'} ({action})")
            continue
        if before == head:
            project.status, project.detail = "current", "already pinned"
            # --push also supports resuming after a prior local-only update.
            if args.push:
                try:
                    consumer_ready(project)
                    push_project(project)
                    project.detail += " and pushed"
                except (ValueError, OSError, subprocess.CalledProcessError) as exc:
                    project.status, project.detail = "FAILED", (getattr(exc, "stderr", "") or str(exc)).strip()
        else:
            try:
                if not before:
                    raise ValueError("path is not a committed submodule gitlink")
                update_project(project, head, message=args.message, push=args.push)
            except (ValueError, OSError, subprocess.CalledProcessError) as exc:
                project.status = "FAILED"
                project.detail = (getattr(exc, "stderr", "") or str(exc)).strip()
        print(f"[{project.status}] {label}: {project.detail}")
    if args.dry_run:
        print("Dry run: no repository content, pins or commits changed.")
    return int(any(project.status == "FAILED" for project in projects))


if __name__ == "__main__":
    raise SystemExit(main())
