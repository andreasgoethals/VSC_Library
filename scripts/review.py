"""Record a completed source review, after updating the named guides."""
from __future__ import annotations

import argparse
import fnmatch
import json

from refresh import ROOT, assert_canonical, json_bytes, render_review_report, replace_bundle


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("guides", nargs="*", help="Repository-relative guide names.")
    parser.add_argument("--all", action="store_true", help="Record that every guide/template group has been reviewed.")
    parser.add_argument("--note", required=True, help="What was checked or changed; retained in review metadata.")
    args = parser.parse_args()
    assert_canonical()
    manifest = json.loads((ROOT / "sources.json").read_text())
    reviews = json.loads((ROOT / "guides/reviewed_sources.json").read_text())
    selected = list(reviews["guides"]) if args.all else args.guides
    if not selected or any(guide not in reviews["guides"] for guide in selected):
        parser.error("Select known guides, or --all. See guides/reviewed_sources.json.")
    for guide in selected:
        record = reviews["guides"][guide]
        record["reviewed_commit"] = manifest["commit"]
        record["review_note"] = args.note
        record["reviewed_hashes"] = {
            name: info["sha256"] for name, info in manifest["text_files"].items()
            if any(fnmatch.fnmatchcase(name, pattern) for pattern in record["patterns"])
        }
    replace_bundle(ROOT, {
        "guides/reviewed_sources.json": json_bytes(reviews),
        "UPSTREAM_CHANGES.md": render_review_report(manifest, reviews),
    })
    print(f"Recorded review of {len(selected)} guide/template groups at {manifest['commit'][:12]}.")


if __name__ == "__main__":
    main()
