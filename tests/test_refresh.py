from __future__ import annotations

import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import refresh as subject

SHA = "1" * 40
DATE = "2026-10-20T07:19:20Z"


def source_files():
    files = {name: b"official source\n" for name in subject.REQUIRED}
    files.update({f"source/example/{n}.rst": b"Example\n" for n in range(210)})
    return files


class SourceRefreshTests(unittest.TestCase):
    def test_deterministic_sort_and_binary_inventory(self):
        files = source_files()
        files["source/image.png"] = b"\0binary"
        first, manifest = subject.build_snapshot(files, SHA, DATE)
        second, _ = subject.build_snapshot(dict(reversed(list(files.items()))), SHA, DATE)
        self.assertEqual(first, second)
        self.assertIn("source/image.png", manifest["excluded_assets"])
        self.assertNotIn(b"FILE: source/image.png", first)
        self.assertIn(b"FILE: source/leuven/slurm_specifics.rst", first)

    def test_missing_core_page_refuses_partial_scrape(self):
        files = source_files()
        del files["source/leuven/slurm_specifics.rst"]
        with self.assertRaisesRegex(ValueError, "Required sources missing"):
            subject.build_snapshot(files, SHA, DATE)

    def test_tiny_scrape_refused(self):
        with self.assertRaisesRegex(ValueError, "Fewer than 200"):
            subject.build_snapshot({name: b"text" for name in subject.REQUIRED}, SHA, DATE)

    def test_large_binary_is_inventoried_without_flattening(self):
        files = source_files()
        files["source/old.pdf"] = b"x" * (subject.MAX_FILE_BYTES + 1)
        snapshot, manifest = subject.build_snapshot(files, SHA, DATE)
        self.assertIn("source/old.pdf", manifest["excluded_assets"])
        self.assertLess(len(snapshot), subject.MAX_FILE_BYTES)

    def test_non_utf8_is_explicitly_excluded(self):
        files = source_files()
        files["source/bad.bin"] = b"\xff"
        _, manifest = subject.build_snapshot(files, SHA, DATE)
        self.assertIn("not UTF-8", manifest["excluded_assets"]["source/bad.bin"]["reason"])

    def test_archive_traversal_refused(self):
        buffer = io.BytesIO()
        with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
            entry = tarfile.TarInfo("repo/../escape")
            entry.size = 1
            archive.addfile(entry, io.BytesIO(b"x"))
        with self.assertRaisesRegex(ValueError, "Unsafe archive path"):
            subject.read_archive(buffer.getvalue())

    def test_symlinks_not_followed(self):
        buffer = io.BytesIO()
        with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
            entry = tarfile.TarInfo("repo/link")
            entry.type = tarfile.SYMTYPE
            entry.linkname = "/etc/passwd"
            archive.addfile(entry)
        self.assertEqual(subject.read_archive(buffer.getvalue()), {})

    def test_replacements_rollback_on_later_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "first").write_bytes(b"original")
            real_write = subject.atomic_write
            def fail_second(path, data):
                if path.name == "second":
                    raise OSError("simulated disk error")
                real_write(path, data)
            with mock.patch.object(subject, "atomic_write", side_effect=fail_second):
                with self.assertRaises(OSError):
                    subject.replace_bundle(root, {"first": b"changed", "second": b"new"})
            self.assertEqual((root / "first").read_bytes(), b"original")
            self.assertFalse((root / "second").exists())
            self.assertFalse(list(root.glob("*.tmp")))

    def test_added_changed_and_deleted_sources_stay_flagged(self):
        reviews = {"guides": {"guide": {"patterns": ["source/*"], "reviewed_hashes": {
            "source/changed.rst": "old", "source/deleted.rst": "gone",
        }}}}
        manifest = {"text_files": {
            "source/changed.rst": {"sha256": "new"},
            "source/added.rst": {"sha256": "added"},
        }}
        expected = ["source/added.rst", "source/changed.rst", "source/deleted.rst"]
        self.assertEqual(subject.review_changes(manifest, reviews)["guide"], expected)
        self.assertEqual(subject.review_changes(manifest, reviews)["guide"], expected)

    def test_network_failure_preserves_existing_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "VSC Repository.txt").write_bytes(b"retained snapshot")
            (root / "sources.json").write_text(json.dumps({"commit": "0" * 40}))
            with mock.patch.object(subject, "assert_canonical"), \
                 mock.patch.object(subject.subprocess, "check_output", return_value=SHA + "\trefs/heads/master"), \
                 mock.patch.object(subject, "download", side_effect=OSError("network down")):
                with self.assertRaises(OSError):
                    subject.refresh(root)
            self.assertEqual((root / "VSC Repository.txt").read_bytes(), b"retained snapshot")

    def test_unchanged_revision_does_not_download_or_write(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root / "sources.json"
            path.write_text(json.dumps({"commit": SHA}))
            before = path.stat().st_mtime_ns
            with mock.patch.object(subject, "assert_canonical"), \
                 mock.patch.object(subject.subprocess, "check_output", return_value=SHA + "\trefs/heads/master"), \
                 mock.patch.object(subject, "download") as download:
                self.assertFalse(subject.refresh(root))
                download.assert_not_called()
            self.assertEqual(path.stat().st_mtime_ns, before)

    def test_changelog_uses_refresh_date_not_older_upstream_date(self):
        content = "# Changelog\n\n## 2026-10-20\n\n- Newer authored change.\n"
        manifest = {"commit": SHA, "upstream_committed_at": "2026-09-01T00:00:00Z"}
        text = subject.changelog_update(content, manifest, day="2026-10-21").decode("utf-8")
        self.assertLess(text.index("## 2026-10-21"), text.index("## 2026-10-20"))
        self.assertNotIn("## 2026-09-01", text)
        self.assertIn("upstream commit date 2026-09-01", text)

    def test_changelog_sections_stay_newest_first(self):
        content = ("# Changelog\n\n## 2026-10-22\n\n- Future-dated entry.\n\n"
                   "## 2026-10-18\n\n- Older entry.\n")
        manifest = {"commit": SHA, "upstream_committed_at": DATE}
        text = subject.changelog_update(content, manifest, day="2026-10-20").decode("utf-8")
        days = [line[3:] for line in text.splitlines() if line.startswith("## ")]
        self.assertEqual(days, ["2026-10-22", "2026-10-20", "2026-10-18"])
        self.assertNotIn("\n\n\n", text)
        same_day = subject.changelog_update(text, manifest, day="2026-10-20").decode("utf-8")
        self.assertEqual(same_day.count("## 2026-10-20"), 1)
        self.assertEqual(same_day.count("Refreshed the official"), 2)

    def test_changelog_defaults_to_utc_today_and_creates_title(self):
        manifest = {"commit": SHA, "upstream_committed_at": "2020-01-01T00:00:00Z"}
        today = subject.datetime.now(subject.timezone.utc).date().isoformat()
        text = subject.changelog_update("", manifest).decode("utf-8")
        self.assertTrue(text.startswith(f"# Changelog\n\n## {today}\n\n- Refreshed"))

    def test_downstream_refresh_is_refused(self):
        result = subprocess.CompletedProcess([], 0, stdout="/a/consumer\n", stderr="")
        with mock.patch.object(subject.subprocess, "run", return_value=result):
            with self.assertRaisesRegex(ValueError, "consumer submodule"):
                subject.assert_canonical(Path("/a/consumer/vsc-library"))


if __name__ == "__main__":
    unittest.main()
