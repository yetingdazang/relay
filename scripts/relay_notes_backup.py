"""Create and verify independent snapshots of the local Obsidian vault."""
import argparse
import hashlib
import json
import os
import shutil
import time
from datetime import datetime
from pathlib import Path


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def create_backup(vault, backup_root, verify_restore=False):
    vault = Path(vault).resolve()
    backup_root = Path(backup_root).resolve()
    if backup_root.is_relative_to(vault):
        raise ValueError("Backup must be outside the vault")
    run = backup_root / ("notes-" + datetime.now().strftime("%Y%m%d-%H%M%S-%f"))
    snapshot = run / "vault"
    snapshot.mkdir(parents=True)
    records = []
    for directory, subfolders, names in os.walk(vault):
        for name in subfolders:
            child = Path(directory) / name
            if child.is_symlink() or child.is_junction():
                raise ValueError("Linked directories require explicit backup handling")
        for name in names:
            source = Path(directory) / name
            if source.is_symlink() or name.startswith(".syncthing.") or name.endswith(".relay-tmp"):
                continue
            relative = source.relative_to(vault)
            target = snapshot / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            for attempt in range(3):
                before = source.stat()
                shutil.copy2(source, target)
                after = source.stat()
                if (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns):
                    original_hash = sha256(source)
                    if sha256(target) == original_hash:
                        break
                time.sleep(0.1)
            else:
                raise RuntimeError("Vault changed repeatedly during snapshot")
            records.append({"path": relative.as_posix(), "size": after.st_size, "sha256": original_hash})
    atomic_json(run / "manifest.json", {"source": str(vault), "created_at": datetime.now().isoformat(), "files": records})
    report = {"result": "PASS", "snapshot": str(snapshot), "files": len(records), "bytes": sum(row["size"] for row in records)}
    if verify_restore:
        restore = run / "restore-verification"
        restore_snapshot(run, restore)
        report["restore_test"] = str(restore)
    atomic_json(run / "verification.json", report)
    return report


def restore_snapshot(run, destination):
    run = Path(run).resolve()
    destination = Path(destination).resolve()
    manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    original = Path(manifest["source"]).resolve()
    if destination.exists() or destination.is_relative_to(original):
        raise ValueError("Restore into a new directory outside the live vault")
    snapshot = run / "vault"
    for row in manifest["files"]:
        relative = Path(row["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Invalid manifest path")
        source = snapshot / relative
        if source.stat().st_size != row["size"] or sha256(source) != row["sha256"]:
            raise RuntimeError("Snapshot hash mismatch")
    shutil.copytree(snapshot, destination)
    for row in manifest["files"]:
        if sha256(destination / row["path"]) != row["sha256"]:
            raise RuntimeError("Restored hash mismatch")
    return destination


def backup_local_setup(config, verify_restore=False):
    report = create_backup(config["vault"], config["backup_root"], verify_restore)
    run = Path(report["snapshot"]).parent
    profile = Path(config["syncthing_home"])
    settings = Path(config["relay"]) / "config"
    state_parent = Path(config["state_path"]).parent
    sources = {
        "notes-sync-settings.json": settings / "notes_sync.local.json",
        "target-mapping.json": settings / "targets.local.json",
        "paired-devices.json": settings / "notes_sync_devices.local.json",
        "import-state.json": Path(config["state_path"]),
        "desktop-device-id.txt": state_parent / "desktop-device-id.txt",
        "obsidian-vault-registration.json": Path(os.environ["APPDATA"]) / "obsidian" / "obsidian.json",
    }
    for name in ["config.xml", "cert.pem", "key.pem", "https-cert.pem", "https-key.pem"]:
        sources["syncthing-" + name] = profile / name
    records = []
    for name, source in sources.items():
        if not source.exists():
            continue
        target = run / "runtime" / name
        target.parent.mkdir(exist_ok=True)
        for attempt in range(3):
            before = source.stat()
            shutil.copy2(source, target)
            after = source.stat()
            content_hash = sha256(source)
            if (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns) and sha256(target) == content_hash:
                break
            time.sleep(0.1)
        else:
            raise RuntimeError("Runtime settings changed repeatedly during snapshot")
        records.append({"path": name, "size": after.st_size, "sha256": content_hash})
    atomic_json(run / "runtime-manifest.json", {"files": records})
    report["runtime_files_verified"] = len(records)
    atomic_json(run / "verification.json", report)
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(Path(__file__).resolve().parents[1] / "config" / "notes_sync.local.json"))
    parser.add_argument("--verify-restore", action="store_true")
    parser.add_argument("--restore")
    parser.add_argument("--destination")
    args = parser.parse_args()
    if args.restore:
        if not args.destination:
            parser.error("--restore requires --destination")
        print(json.dumps({"restored": str(restore_snapshot(args.restore, args.destination))}, ensure_ascii=False))
        return
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    print(json.dumps(backup_local_setup(config, args.verify_restore), ensure_ascii=False))


if __name__ == "__main__":
    main()
