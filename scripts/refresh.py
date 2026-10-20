"""Deterministic, revision-pinned scrape of the official VSC documentation.

Only Python's standard library is required. No upstream code is executed.
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import tarfile
import tempfile
import urllib.request
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "hpcleuven/VscDocumentation"
BRANCH = "master"
URL = f"https://github.com/{REPOSITORY}"
SNAPSHOT = "VSC Repository.txt"
MAX_FILE_BYTES = 4 * 1024 * 1024
MAX_DOWNLOAD_BYTES = 100 * 1024 * 1024
REQUIRED = (
    "LICENSE",
    "source/leuven/slurm_specifics.rst",
    "source/leuven/wice_quick_start.rst",
    "source/leuven/mindwell_quick_start.rst",
    "source/leuven/tier2_hardware/kuleuven_storage.rst",
    "source/compute/portal/index.rst",
)
BINARY_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".xlsx",
    ".woff", ".woff2", ".ttf", ".zip", ".gz",
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")


def assert_canonical(root: Path = ROOT) -> None:
    result = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--show-superproject-working-tree"],
        capture_output=True, text=True, check=False,
    )
    if result.returncode == 0 and result.stdout.strip():
        raise ValueError("This is a consumer submodule. Refresh only the canonical VSC Library checkout.")


def download(url: str, limit: int = MAX_DOWNLOAD_BYTES) -> bytes:
    request = urllib.request.Request(url, headers={
        "User-Agent": "VSC-Library-source-refresh",
        "Accept": "application/vnd.github+json" if url.startswith("https://api.github.com/") else "*/*",
    })
    with urllib.request.urlopen(request, timeout=90) as response:
        data = response.read(limit + 1)
    if len(data) > limit:
        raise ValueError(f"Download exceeds {limit} bytes: {url}")
    return data


def read_archive(data: bytes) -> dict[str, bytes]:
    """Read files without extracting paths, following links or running code."""
    result = {}
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
        for member in archive:
            path = PurePosixPath(member.name)
            if not member.isfile():
                continue
            if path.is_absolute() or ".." in path.parts or len(path.parts) < 2:
                raise ValueError(f"Unsafe archive path: {member.name}")
            relative = PurePosixPath(*path.parts[1:]).as_posix()
            if member.size > MAX_DOWNLOAD_BYTES:
                raise ValueError(f"Unexpected large upstream file: {relative}")
            if relative in result:
                raise ValueError(f"Duplicate archive path: {relative}")
            stream = archive.extractfile(member)
            if stream is None:
                raise ValueError(f"Unreadable archive member: {relative}")
            result[relative] = stream.read(MAX_DOWNLOAD_BYTES + 1)
    return result


def read_checkout(path: Path) -> tuple[dict[str, bytes], str, str]:
    def git(*args: str) -> str:
        return subprocess.check_output(["git", "-C", str(path), *args], text=True).strip()
    remote = git("remote", "get-url", "origin").rstrip("/").removesuffix(".git").lower()
    if remote != URL.lower():
        raise ValueError("The source checkout must have the official VSC repository as origin.")
    if git("status", "--porcelain", "--untracked-files=no"):
        raise ValueError("The source checkout contains modified tracked files.")
    commit = git("rev-parse", "HEAD")
    committed_at = git("show", "-s", "--format=%cI", "HEAD")
    paths = subprocess.check_output(["git", "-C", str(path), "ls-files", "-z"]).decode().split("\0")
    files = {name: subprocess.check_output(["git", "-C", str(path), "show", f"HEAD:{name}"])
             for name in paths if name}
    return files, commit, committed_at


def build_snapshot(files: dict[str, bytes], commit: str, committed_at: str) -> tuple[bytes, dict]:
    included = {}
    excluded = {}
    for name, raw in sorted(files.items()):
        record = {"sha256": digest(raw), "bytes": len(raw)}
        if PurePosixPath(name).suffix.lower() in BINARY_SUFFIXES or b"\0" in raw:
            excluded[name] = {**record, "reason": "binary asset; see upstream"}
            continue
        if len(raw) > MAX_FILE_BYTES:
            raise ValueError(f"Unexpected large upstream text file: {name}")
        try:
            value = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            excluded[name] = {**record, "reason": "not UTF-8 text; see upstream"}
            continue
        included[name] = (record, value.replace("\r\n", "\n"))
    missing = set(REQUIRED) - included.keys()
    if missing:
        raise ValueError(f"Required sources missing: {sorted(missing)}")
    if sum(name.startswith("source/") for name in included) < 200:
        raise ValueError("Fewer than 200 source documents; refusing an incomplete scrape.")
    chunks = [
        "VSC Repository - automatically scraped official VSC documentation\n",
        f"Repository: {URL}\nBranch: {BRANCH}\nCommit: {commit}\n",
        f"Upstream commit date: {committed_at}\n",
        "License: GPL-3.0 (upstream LICENSE is included below and retained at repository root).\n",
        "Content is upstream source, including historical pages and site-specific tabs.\n",
        "Read guides/ for current KU Leuven interpretation; consult live status before running jobs.\n",
        "Images, PDFs and other binary assets are inventoried in sources.json, not flattened.\n",
        "Cite FILE paths and RST labels, never dump line numbers.\n\n",
        "Included files:\n",
    ]
    chunks.extend(f"  {name}\n" for name in included)
    for name, (_, value) in included.items():
        chunks.extend(["\n" + "=" * 72 + f"\nFILE: {name}\n" + "=" * 72 + "\n", value.rstrip("\n") + "\n"])
    snapshot = "".join(chunks).encode("utf-8")
    if len(snapshot) > 95 * 1024 * 1024:
        raise ValueError("Snapshot exceeds the repository's 95 MiB limit.")
    manifest = {
        "schema_version": 1, "repository": URL, "branch": BRANCH,
        "commit": commit, "upstream_committed_at": committed_at,
        "snapshot": SNAPSHOT, "snapshot_sha256": digest(snapshot),
        "text_files": {name: record for name, (record, _) in included.items()},
        "excluded_assets": excluded,
    }
    return snapshot, manifest


def review_changes(manifest: dict, reviews: dict) -> dict[str, list[str]]:
    current = {name: info["sha256"] for name, info in manifest["text_files"].items()}
    changed = {}
    for guide, review in reviews.get("guides", {}).items():
        matches = {name: sha for name, sha in current.items()
                   if any(fnmatch.fnmatchcase(name, pattern) for pattern in review["patterns"])}
        before = review.get("reviewed_hashes", {})
        changes = [name for name in sorted(set(matches) | set(before))
                   if matches.get(name) != before.get(name)]
        if changes:
            changed[guide] = changes
    return changed


def render_review_report(manifest: dict, reviews: dict) -> bytes:
    changed = review_changes(manifest, reviews)
    lines = [
        "# Upstream changes and guide review\n\n",
        "Generated by the refresh/review tools. Do not edit this file by hand.\n\n",
        f"Current source: [{manifest['commit'][:12]}]({URL}/commit/{manifest['commit']})",
        f" (upstream date {manifest['upstream_committed_at']}).\n\n",
        "The source snapshot is refreshed automatically. Curated prose and Slurm templates require\n",
        "review when the source files they depend on change. A successful source refresh does not\n",
        "certify cluster availability, local environments or applications.\n\n",
        "| Guide or template group | Source review |\n|---|---|\n",
    ]
    for guide in sorted(reviews.get("guides", {})):
        state = f"REVIEW REQUIRED: {len(changed[guide])} changed source files" if guide in changed else "Matches reviewed source"
        lines.append(f"| [{guide}](<{guide}>) | {state} |\n")
    for guide, paths in changed.items():
        lines.append(f"\n## {guide}\n\n")
        review = reviews["guides"][guide]
        old_commit = review.get("reviewed_commit")
        if old_commit:
            lines.append(f"[Compare with the reviewed revision]({URL}/compare/{old_commit}...{manifest['commit']}).\n\n")
        lines.extend(f"- [{name}]({URL}/blob/{manifest['commit']}/{name})\n" for name in paths)
    return "".join(lines).encode()


def atomic_write(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(value)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def replace_bundle(root: Path, bundle: dict[str, bytes]) -> None:
    """Roll back earlier replacements if a later write fails."""
    previous = {name: (root / name).read_bytes() if (root / name).exists() else None for name in bundle}
    completed = []
    try:
        for name, value in bundle.items():
            atomic_write(root / name, value)
            completed.append(name)
    except BaseException:
        for name in reversed(completed):
            if previous[name] is None:
                (root / name).unlink(missing_ok=True)
            else:
                atomic_write(root / name, previous[name])
        raise


def changelog_update(content: str, manifest: dict) -> bytes:
    day = manifest["upstream_committed_at"][:10]
    entry = (f"- Refreshed the official documentation snapshot to "
             f"[{manifest['commit'][:12]}]({URL}/commit/{manifest['commit']}); "
             "recomputed source hashes and guide review flags.\n")
    heading = f"## {day}\n"
    if heading in content:
        content = content.replace(heading, heading + "\n" + entry, 1)
    else:
        title, _, rest = content.partition("\n")
        content = title + "\n\n" + heading + "\n" + entry + "\n" + rest.lstrip("\n")
    return content.encode()


def refresh(root: Path = ROOT, source_checkout: Path | None = None, allow_shrink: bool = False) -> bool:
    assert_canonical(root)
    old = json.loads((root / "sources.json").read_text()) if (root / "sources.json").exists() else None
    if source_checkout:
        files, commit, committed_at = read_checkout(source_checkout)
    else:
        # Git discovery avoids GitHub's shared anonymous REST API rate limit.
        revision = subprocess.check_output(
            ["git", "ls-remote", "--exit-code", URL + ".git", f"refs/heads/{BRANCH}"],
            text=True, timeout=90,
        )
        commit = revision.split()[0]
        if old and old["commit"] == commit:
            print(f"Already at official upstream {commit[:12]}; no files changed.")
            return False
        archive_bytes = download(f"https://codeload.github.com/{REPOSITORY}/tar.gz/{commit}")
        # GitHub's commit archive records the commit timestamp on its root entry.
        with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:gz") as archive:
            first = archive.next()
            if first is None:
                raise ValueError("Empty upstream archive.")
            committed_at = datetime.fromtimestamp(first.mtime, timezone.utc).isoformat()
        files = read_archive(archive_bytes)
    committed_at = datetime.fromisoformat(committed_at.replace("Z", "+00:00")).astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    snapshot, manifest = build_snapshot(files, commit, committed_at)
    existing = root / SNAPSHOT
    if existing.exists() and len(snapshot) < existing.stat().st_size * 0.5 and not allow_shrink:
        raise ValueError("Snapshot shrank by more than 50%; inspect upstream before using --allow-shrink.")
    reviews = json.loads((root / "guides/reviewed_sources.json").read_text())
    bundle = {
        SNAPSHOT: snapshot,
        "sources.json": json_bytes(manifest),
        "UPSTREAM_CHANGES.md": render_review_report(manifest, reviews),
        "LICENSE": files["LICENSE"].replace(b"\r\n", b"\n"),
    }
    changed = any(not (root / name).exists() or (root / name).read_bytes() != value for name, value in bundle.items())
    if not changed:
        print(f"Already at official upstream {commit[:12]}; no files changed.")
        return False
    if old is None or old["commit"] != manifest["commit"]:
        changelog = root / "CHANGELOG.md"
        bundle["CHANGELOG.md"] = changelog_update(changelog.read_text(encoding="utf-8") if changelog.exists() else "# Changelog\n", manifest)
    replace_bundle(root, bundle)
    warnings = review_changes(manifest, reviews)
    print(f"Scraped {len(manifest['text_files'])} text files at {commit[:12]}; {len(manifest['excluded_assets'])} binary assets inventoried.")
    print(f"{len(warnings)} guide/template groups need source review. See UPSTREAM_CHANGES.md.")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-checkout", type=Path, help="Use committed bytes from a clean clone of the official repository.")
    parser.add_argument("--allow-shrink", action="store_true", help="Accept a reviewed legitimate reduction exceeding one half.")
    args = parser.parse_args()
    try:
        refresh(source_checkout=args.source_checkout, allow_shrink=args.allow_shrink)
    except (ValueError, OSError, KeyError, subprocess.SubprocessError, tarfile.TarError) as error:
        parser.exit(1, f"Refresh failed; existing files preserved: {error}\n")


if __name__ == "__main__":
    main()
