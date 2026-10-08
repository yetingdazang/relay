#!/usr/bin/env python3
"""Prune Relay's generated image preview tiles without touching original media.

Automatic mode: delete preview sets whose manifest commit is >= 7 days old.
Explicit mode: delete only the cache for an already-processed source image.
No full-vault scan and no force-push. The source image under notes/ is untouched.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "config" / "image-bridge"
MAX_DIRS = 2000


def source_folder(relative: str) -> Path:
    slug = hashlib.sha256(relative.encode("utf-8")).hexdigest()[:20]
    return CACHE / slug


def git_commit_timestamp(manifest: Path) -> int | None:
    rel = manifest.relative_to(ROOT).as_posix()
    result = subprocess.run(
        ["git", "log", "-1", "--format=%ct", "--", rel],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    if result.returncode != 0 or not result.stdout.strip().isdigit():
        return None
    return int(result.stdout.strip())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expire-days", type=int, default=7,
                        help="Fallback retention for unread cache sets")
    parser.add_argument("--completed-source", default="",
                        help="One successfully analyzed notes/ image to purge now")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not (1 <= args.expire_days <= 365):
        parser.error("--expire-days must be 1..365")
    completed = args.completed_source.strip()
    if completed:
        if not completed.startswith("notes/") or ".." in Path(completed).parts:
            parser.error("--completed-source must be a safe notes/ relative path")

    if not CACHE.is_dir():
        print("No preview cache directory. Nothing to prune.")
        return

    manifests = sorted(CACHE.glob("*/manifest.json"))
    if len(manifests) > MAX_DIRS:
        raise RuntimeError("Too many preview cache sets; refusing unsafe bulk prune")

    removed = 0
    now = time.time()
    for manifest in manifests:
        folder = manifest.parent
        if folder.is_symlink() or manifest.is_symlink():
            print(f"SKIP symlink cache: {folder}")
            continue
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
            source = data["source"]
            if not isinstance(source, str) or not source.startswith("notes/"):
                raise ValueError("invalid source")
            if ".." in Path(source).parts or folder != source_folder(source):
                raise ValueError("preview directory does not match source")
        except (OSError, ValueError, KeyError, TypeError) as e:
            print(f"SKIP malformed manifest: {folder}: {e}")
            continue

        selected = bool(completed) and source == completed
        created_at = git_commit_timestamp(manifest)
        expired = (
            created_at is not None and
            now - created_at >= args.expire_days * 86400
        )
        if not selected and not expired:
            continue
        reason = "confirmed processed" if selected else f"older than {args.expire_days} days"
        print(f"{'WOULD REMOVE' if args.dry_run else 'REMOVE'} {folder.relative_to(ROOT)} ({reason})")
        if not args.dry_run:
            shutil.rmtree(folder)
        removed += 1

    print(f"Preview sets {'selected' if args.dry_run else 'removed'}: {removed}.")
    print("Original notes/ image files were not changed.")


if __name__ == "__main__":
    main()
