#!/usr/bin/env python3
"""Make private, text-transportable JPEG previews of new Obsidian images.

Run inside GitHub Actions after checkout. No OCR or external AI services.
Each JPEG preview tile is base64 in a UTF-8 text file, for approved
read-only GitHub connectors that cannot return binary image bytes.
"""
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "config" / "image-bridge"
ALLOWED = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}
BOOTSTRAP_IMAGE = (
    "notes/03-Resources/Attachments/"
    "小黑盒-半年超深度使用Agent攻略-生产力实践.jpg"
)
MAX_WIDTH = 960
TILE_HEIGHT = 1280
MAX_TILES = 40


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def candidates():
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    event_type = os.environ.get("GITHUB_EVENT_NAME", "push")
    if event_type == "workflow_dispatch":
        chosen = event.get("inputs", {}).get("image_path", "")
        return [chosen] if chosen else []
    before = event.get("before") or ""
    after = os.environ.get("GITHUB_SHA", "HEAD")
    if before and before != "0" * 40:
        try:
            paths = git("diff", "--name-only", "--diff-filter=A", before, after, "--", "notes/").splitlines()
        except subprocess.CalledProcessError:
            paths = git("diff-tree", "--no-commit-id", "--name-only", "--diff-filter=A", "-r", after).splitlines()
    else:
        paths = git("diff-tree", "--no-commit-id", "--name-only", "--diff-filter=A", "-r", after).splitlines()
    # Single explicitly requested backfill when the bridge is first installed:
    if not paths and not (OUTPUT / hashlib.sha256(BOOTSTRAP_IMAGE.encode()).hexdigest()[:16] / "manifest.json").exists():
        paths = [BOOTSTRAP_IMAGE]
    return paths


def process(rel):
    if not rel.startswith("notes/") or Path(rel).suffix.lower() not in ALLOWED:
        return False
    path = (ROOT / rel).resolve()
    if not path.is_file() or not path.is_relative_to(ROOT):
        return False
    folder = OUTPUT / hashlib.sha256(rel.encode()).hexdigest()[:16]
    if (folder / "manifest.json").exists():
        print(f"SKIP already processed: {rel}")
        return False
    folder.mkdir(parents=True, exist_ok=True)
    src_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    with Image.open(path) as original:
        image = ImageOps.exif_transpose(original)
        width, height = image.size
        ratio = min(1.0, MAX_WIDTH / width)
        if ratio < 1:
            image = image.resize((round(width * ratio), round(height * ratio)), Image.Resampling.LANCZOS)
        image = image.convert("RGB")
        scaled_width, scaled_height = image.size
        tile_count = min(MAX_TILES, (scaled_height + TILE_HEIGHT - 1) // TILE_HEIGHT)
        tiles = []
        for i in range(tile_count):
            top = i * TILE_HEIGHT
            bottom = min(scaled_height, top + TILE_HEIGHT)
            crop = image.crop((0, top, scaled_width, bottom))
            buffer = io.BytesIO()
            crop.save(buffer, "JPEG", quality=76, optimize=True)
            name = f"tile-{i+1:02d}.b64.txt"
            (folder / name).write_text(base64.b64encode(buffer.getvalue()).decode("ascii") + "\n")
            tiles.append({
                "file": name,
                "mime_type": "image/jpeg",
                "top": top,
                "bottom": bottom,
                "base64_characters": (folder / name).stat().st_size - 1,
            })
    manifest = {
        "version": 1,
        "original_path": rel,
        "original_sha256": src_hash,
        "original_size_bytes": path.stat().st_size,
        "original_dimensions": [width, height],
        "preview_dimensions": [scaled_width, scaled_height],
        "tiles": tiles,
        "truncated": scaled_height > len(tiles) * TILE_HEIGHT,
        "privacy": "Derived previews are stored in the same private GitHub repository.",
    }
    (folder / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(f"OK: {rel}: {len(tiles)} preview tiles -> {folder.relative_to(ROOT)}")
    return True


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    paths = candidates()
    print(f"Checking {len(paths)} newly added or explicitly requested images")
    written = sum(process(p) for p in dict.fromkeys(paths))
    print(f"Generated preview sets: {written}")


if __name__ == "__main__":
    main()
