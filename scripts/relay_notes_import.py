"""Import mobile captures without propagating deletions or overwriting desktop edits."""
import argparse
import hashlib
import json
import logging
import msvcrt
import os
import shutil
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from relay_notes_backup import atomic_json, backup_local_setup, sha256

EXCLUDED = {".stfolder", ".stversions", ".stignore", ".obsidian", ".git", ".trash", ".DS_Store", "Thumbs.db"}


def safe_target(root, relative):
    root = Path(root).resolve()
    relative = Path(relative)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("Invalid relative path")
    target = (root / relative).resolve()
    if not target.is_relative_to(root):
        raise ValueError("Path leaves the import destination")
    return target


@contextmanager
def exclusive_lock(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as handle:
        if handle.tell() == 0:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        try:
            yield
        finally:
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)


def stable_copy(source, target, expected_hash, expected_target_hash):
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name("." + target.name + ".relay-tmp")
    before = source.stat()
    try:
        shutil.copy2(source, temporary)
        after = source.stat()
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns) or sha256(temporary) != expected_hash:
            raise RuntimeError("Incoming file changed during import")
        actual_target_hash = sha256(target) if target.exists() else None
        if actual_target_hash != expected_target_hash:
            raise RuntimeError("Desktop destination changed during import")
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def import_once(config):
    state_path = Path(config["state_path"])
    with exclusive_lock(state_path.with_suffix(".lock")):
        state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {"files": {}}
        if not isinstance(state.get("files"), dict):
            raise ValueError("Invalid import state")
        result = {"imported": 0, "conflicts": 0, "unchanged": 0}
        for channel in config["incoming"]:
            source_root = Path(channel["source"]).resolve()
            destination = Path(channel["destination"]).resolve()
            if source_root == destination or destination.is_relative_to(source_root):
                raise ValueError("Incoming staging and permanent notes must be separate")
            for directory, subfolders, names in os.walk(source_root):
                subfolders[:] = [name for name in subfolders if name not in EXCLUDED
                                 and not (Path(directory) / name).is_symlink()
                                 and not (Path(directory) / name).is_junction()]
                for name in names:
                    source = Path(directory) / name
                    if name in EXCLUDED or name.startswith((".syncthing.", "~")) or name.endswith((".tmp", ".relay-tmp")) or source.is_symlink():
                        continue
                    relative = source.relative_to(source_root)
                    source_hash = sha256(source)
                    key = channel["device"] + ":" + relative.as_posix()
                    previous = state["files"].get(key)
                    if previous and previous["source_hash"] == source_hash:
                        result["unchanged"] += 1
                        continue
                    target_relative = previous["target_path"] if previous else relative.as_posix()
                    target = safe_target(destination, target_relative)
                    conflict = False
                    expected_target_hash = sha256(target) if target.exists() else None
                    if target.exists():
                        current_hash = sha256(target)
                        if current_hash != source_hash and (not previous or current_hash != previous["target_hash"]):
                            conflict = True
                            conflict_name = relative.stem + "-同步冲突-" + channel["device"] + "-" + source_hash[:10] + relative.suffix
                            target_relative = (relative.parent / conflict_name).as_posix()
                            target = safe_target(destination, target_relative)
                            expected_target_hash = sha256(target) if target.exists() else None
                            if target.exists() and sha256(target) != source_hash:
                                raise RuntimeError("Conflict destination already contains different content")
                    if not target.exists() or sha256(target) != source_hash:
                        stable_copy(source, target, source_hash, expected_target_hash)
                        result["imported"] += 1
                    result["conflicts"] += int(conflict)
                    state["files"][key] = {"source_hash": source_hash, "target_hash": source_hash, "target_path": target_relative}
        atomic_json(state_path, state)
        return result


def watch(config):
    state_path = Path(config["state_path"])
    logging.basicConfig(filename=state_path.parent / "import.log", level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s", encoding="utf-8")
    schedule_path = state_path.parent / "backup-schedule.json"
    with exclusive_lock(state_path.parent / "watch.lock"):
        while True:
            try:
                result = import_once(config)
                if result["imported"] or result["conflicts"]:
                    logging.info("Import result: %s", result)
                schedule = json.loads(schedule_path.read_text(encoding="utf-8")) if schedule_path.exists() else {}
                if time.time() - schedule.get("last_success", 0) >= 86400:
                    report = backup_local_setup(config)
                    atomic_json(schedule_path, {"last_success": time.time(), "snapshot": report["snapshot"]})
                    logging.info("Daily backup verified: %s", report["snapshot"])
            except Exception as error:
                logging.error("Sync helper failed: %s", type(error).__name__)
            time.sleep(15)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(Path(__file__).resolve().parents[1] / "config" / "notes_sync.local.json"))
    parser.add_argument("--watch", action="store_true")
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    if args.watch:
        watch(config)
    else:
        print(json.dumps(import_once(config), ensure_ascii=False))


if __name__ == "__main__":
    main()
