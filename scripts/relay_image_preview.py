#!/usr/bin/env python3
"""Incrementally export compact, text-readable previews for private Relay images.

Designed for GitHub Actions. It only processes image files ADDED in the
triggering push (or one explicitly requested workflow_dispatch path).
On first installation, it backfills exactly one known already-uploaded image.
No OCR, AI inference, external upload service, or secrets are required.
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import os
import subprocess
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "config" / "image-bridge"
WORKFLOW = ".github/workflows/relay-image-preview.yml"
INITIAL_IMAGE = "notes/03-Resources/Attachments/小黑盒-半年超深度使用Agent攻略-生产力实践.jpg"
EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}
PREVIEW_WIDTH = 960
TILE_HEIGHT = 1024
MAX_TILES = 96
MAX_TILE_BYTES = 240 * 1024
MAX_SOURCE_BYTES = 40 * 1024 * 1024
Image.MAX_IMAGE_PIXELS = 150_000_000


def git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=ROOT, text=True, stderr=subprocess.PIPE
    ).strip()


def changed_added_files(before: str, after: str) -> list[str]:
    if not before or before == "0" * 40:
        # For the initial commit use only files added by the commit; never scan the vault.
        return git("diff-tree", "--root", "--no-commit-id", "--name-only",
                   "--diff-filter=A", "-r", after).splitlines()
    try:
        return git("diff", "--name-only", "--diff-filter=A",
                   before, after).splitlines()
    except subprocess.CalledProcessError as exc:
        raise RuntimeError("Cannot compare push commits; refusing full-repo fallback") from exc


def input_paths() -> list[str]:
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path:
        raise RuntimeError("GITHUB_EVENT_PATH is required")
    event = json.loads(Path(event_path).read_text(encoding="utf-8"))
    event_type = os.environ.get("GITHUB_EVENT_NAME", "")
    if event_type == "workflow_dispatch":
        explicit_path = (event.get("inputs") or {}).get("image_path", "").strip()
        return [explicit_path] if explicit_path else []
    if event_type != "push":
        return []
    changed = changed_added_files(event.get("before", ""), event.get("after", "HEAD"))
    candidates = [p for p in changed if p.startswith("notes/")]
    # This one legacy image is allowed *only* on the workflow's initial installation.
    if WORKFLOW in changed:
        candidates.append(INITIAL_IMAGE)
    return list(dict.fromkeys(candidates))


def output_dir(relative_path: str) -> Path:
    key = hashlib.sha256(relative_path.encode("utf-8")).hexdigest()[:20]
    return CACHE / key


def is_valid(relative_path: str) -> bool:
    p = Path(relative_path)
    if not relative_path.startswith("notes/") or p.suffix.lower() not in EXTENSIONS:
        return False
    if p.is_absolute() or ".." in p.parts:
        return False
    return True


def compress_tile(tile: Image.Image) -> bytes:
    """Keep each base64 payload below GitHub's 1-MB Contents API limit."""
    for quality in (77, 65, 53, 42):
        buffer = io.BytesIO()
        tile.save(buffer, format="JPEG", quality=quality, optimize=True)
        if buffer.tell() <= MAX_TILE_BYTES:
            return buffer.getvalue()
    # Exceptionally detailed images: downsample only that tile.
    while min(tile.size) > 300:
        tile = tile.resize((max(1, int(tile.width * .8)),
                            max(1, int(tile.height * .8))), Image.Resampling.LANCZOS)
        for quality in (52, 40):
            buffer = io.BytesIO()
            tile.save(buffer, format="JPEG", quality=quality, optimize=True)
            if buffer.tell() <= MAX_TILE_BYTES:
                return buffer.getvalue()
    raise ValueError("Preview tile remains larger than the safety bound")


def encode_one(relative_path: str) -> bool:
    if not is_valid(relative_path):
        return False
    resolved = (ROOT / relative_path).resolve()
    if not resolved.is_relative_to(ROOT) or not resolved.is_file():
        print(f"SKIP missing/outside repo: {relative_path}")
        return False
    size = resolved.stat().st_size
    if size > MAX_SOURCE_BYTES:
        print(f"SKIP >40MB: {relative_path}")
        return False

    folder = output_dir(relative_path)
    if (folder / "manifest.json").exists():
        print(f"SKIP already converted: {relative_path}")
        return False

    tile_payloads: list[tuple[str, bytes, int, int]] = []
    try:
        with Image.open(resolved) as source:
            oriented = ImageOps.exif_transpose(source)
            source_size = [oriented.width, oriented.height]
            if oriented.width > PREVIEW_WIDTH:
                new_h = max(1, round(oriented.height * PREVIEW_WIDTH / oriented.width))
                oriented = oriented.resize(
                    (PREVIEW_WIDTH, new_h), Image.Resampling.LANCZOS
                )
            converted = oriented.convert("RGB")
            preview_size = [converted.width, converted.height]
            total = (converted.height + TILE_HEIGHT - 1) // TILE_HEIGHT
            for index in range(min(total, MAX_TILES)):
                top = index * TILE_HEIGHT
                bottom = min((index + 1) * TILE_HEIGHT, converted.height)
                tile = converted.crop((0, top, converted.width, bottom))
                payload = compress_tile(tile)
                tile_payloads.append((f"tile-{index + 1:03d}.b64.txt",
                                      payload, top, bottom))
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as e:
        print(f"SKIP unreadable/unsupported image {relative_path}: {type(e).__name__}")
        return False

    folder.mkdir(parents=True, exist_ok=True)
    tiles = []
    for name, payload, top, bottom in tile_payloads:
        (folder / name).write_text(
            base64.b64encode(payload).decode("ascii") + "\n", encoding="ascii"
        )
        tiles.append({"file": name, "top_px": top, "bottom_px": bottom,
                      "jpeg_bytes": len(payload)})

    manifest = {
        "schema": 1,
        "source": relative_path,
        "source_sha256": hashlib.sha256(resolved.read_bytes()).hexdigest(),
        "source_bytes": size,
        "original_pixels": source_size,
        "preview_pixels": preview_size,
        "tile_count": len(tiles),
        "truncated": total > MAX_TILES,
        "tiles": tiles,
        "readme": "Each tile is a Base64 JPEG text file. Decode or display in order.",
    }
    (folder / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"EXPORTED {relative_path}: {len(tiles)} tile(s), "
          f"truncated={total > MAX_TILES}, cache=config/image-bridge/{folder.name}/")
    return True


def main() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    selected = input_paths()
    print(f"Image-bridge candidates: {len(selected)} (new only, except explicit backfill)")
    completed = 0
    for path in selected:
        if encode_one(path):
            completed += 1
    print(f"Preview sets generated: {completed}")


if __name__ == "__main__":
    main()
