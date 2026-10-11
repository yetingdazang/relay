"""Import ready GitHub capture bundles, then acknowledge only verified backups.

No shell commands from manifests or handoffs are ever executed by this script.
"""
import argparse
import base64
import hashlib
import json
import os
import re
import subprocess
import uuid
from pathlib import Path, PurePosixPath
from relay_notes_backup import atomic_json, backup_local_setup, sha256
from relay_notes_import import exclusive_lock, safe_target

# Keep version-1 legacy routes stable; new producers opt into workflow categories.
CATEGORIES = {"inbox": "00-Inbox", "settling": "00-Settling",
              "refined": "01-Knowledge", "professional": "04-Professional",
              "knowledge": "01-Knowledge", "projects": "02-Projects",
              "resources": "03-Resources", "archive": "99-Archive"}
MAX_FILE = 25 * 1024 * 1024
MAX_BUNDLE = 100 * 1024 * 1024


def git(repo, *args, binary=False):
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, timeout=45,
                            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                            env={**os.environ, "GIT_TERMINAL_PROMPT": "0", "GCM_INTERACTIVE": "never"})
    if result.returncode:
        # Git output may contain credential URLs; never include it in diagnostics.
        raise RuntimeError("Git operation failed: " + args[0])
    return result.stdout if binary else result.stdout.decode("utf-8").strip()


def relative_path(value):
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError("Invalid bundle path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(x in {".", "..", ""} for x in value.split("/")):
        raise ValueError("Path traversal is forbidden")
    for part in path.parts:
        if re.search(r'[<>:"|?*\x00-\x1f]', part) or part.endswith((".", " ")):
            raise ValueError("Invalid Windows path")
        if part.startswith(".") or part.split(".")[0].upper() in {
            "CON", "PRN", "AUX", "NUL", *["COM"+str(i) for i in range(1,10)],
            *["LPT"+str(i) for i in range(1,10)]}:
            raise ValueError("Reserved destination")
    return path.as_posix()


def snapshot(repo, ref, prefix="capture/items/"):
    commit = git(repo, "rev-parse", ref + "^{commit}")
    packages = {}
    tree = git(repo, "ls-tree", "-r", "-l", "-z", commit, "--", prefix, binary=True)
    for entry in tree.split(b"\0"):
        if not entry:
            continue
        metadata, raw_path = entry.split(b"\t", 1)
        mode, kind, object_id, size = metadata.split()
        path = raw_path.decode("utf-8")
        rest = path[len(prefix):]
        parts = rest.split("/", 1)
        if len(parts) != 2:
            continue
        bundle, relative = parts
        files = packages.setdefault(bundle, {})
        if mode not in {b"100644", b"100755"} or kind != b"blob":
            files[relative] = None
        elif int(size) > MAX_FILE:
            files[relative] = None
        else:
            files[relative] = git(repo, "cat-file", "blob", object_id.decode(), binary=True)
    return commit, packages


def bundle_hash(files):
    if any(data is None for data in files.values()):
        raise ValueError("Unsupported links or oversized files")
    if sum(len(data) for data in files.values()) > MAX_BUNDLE:
        raise ValueError("Bundle too large")
    entries = {path: hashlib.sha256(data).hexdigest() for path, data in sorted(files.items())}
    return hashlib.sha256(json.dumps(entries, sort_keys=True).encode()).hexdigest(), entries


def validate(bundle, files):
    source_hash, source_files = bundle_hash(files)
    manifest = json.loads(files.get("manifest.json", b"{}"))
    if not isinstance(manifest, dict):
        raise ValueError("Manifest must be an object")
    if manifest.get("ready") is not True:
        return None
    if manifest.get("version") != 1 or manifest.get("id") != bundle or not re.fullmatch(r"[a-z0-9][a-z0-9-]{3,79}", bundle):
        raise ValueError("Invalid bundle ID or version")
    category = manifest.get("category", "inbox")
    classification = "manifest"
    if not isinstance(category, str) or category not in CATEGORIES:
        category = "inbox"
        classification = "inbox_fallback"
    if "note.md" not in files:
        raise ValueError("Ready bundle is missing note.md")
    note = files["note.md"].decode("utf-8-sig")
    if not note.strip():
        raise ValueError("Empty note")
    title = manifest.get("title", "")
    if not isinstance(title, str) or not title.strip():
        raise ValueError("Missing title")
    title = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "-", title).strip(" .")[:100]
    filename = relative_path(title + ".md")
    outputs = {filename: note.encode("utf-8")}
    declared = {"manifest.json", "note.md"}
    attachments = manifest.get("attachments", [])
    if not isinstance(attachments, list):
        raise ValueError("Invalid attachment manifest")
    for item in attachments:
        if not isinstance(item, dict):
            raise ValueError("Attachment must be an object")
        path = relative_path(item["path"])
        if not path.startswith("attachments/") or path in declared or path not in files:
            raise ValueError("Missing or duplicate declared attachment")
        declared.add(path)
        data = files[path]
        encoding = item.get("encoding", "binary")
        if encoding == "base64":
            # Decode actual uploaded bytes; never download an expiring chat URL.
            data = base64.b64decode(re.sub(rb"\s+", b"", data), validate=True)
            destination = "attachments/" + relative_path(item["name"])
        elif encoding == "binary":
            destination = path
        else:
            raise ValueError("Unsupported encoding")
        if len(data) > MAX_FILE or (item.get("sha256") and hashlib.sha256(data).hexdigest() != item["sha256"]):
            raise ValueError("Attachment checksum or size mismatch")
        if destination in outputs:
            raise ValueError("Attachment destination collision")
        outputs[destination] = data
    if declared != set(files):
        raise ValueError("Undeclared files: finish the manifest before setting ready")
    folded = [path.casefold() for path in outputs]
    if len(set(folded)) != len(folded):
        raise ValueError("Windows case-insensitive collision")
    # Package-relative embeds keep working because the attachment layout is preserved.
    for embed in re.findall(r"!\[\[([^]|#]+)(?:[^]]*)\]\]", note):
        if embed.startswith("attachments/") and embed not in outputs:
            raise ValueError("Unresolved attachment embed")
    for embed in re.findall(r"!\[[^]]*\]\((attachments/[^)]+)\)", note):
        if embed not in outputs:
            raise ValueError("Unresolved Markdown attachment")
    return {"source_hash": source_hash, "source_files": source_files,
            "category": category, "classification": classification, "outputs": outputs, "note": filename}


def import_bundle(config, bundle, validated, previous=None):
    if previous:
        if previous["source_hash"] != validated["source_hash"]:
            raise ValueError("A used bundle ID is immutable; upload a new ID")
        return previous, False
    vault = Path(config["vault"]).resolve()
    relative = Path("notes") / CATEGORIES[validated["category"]] / bundle
    destination = safe_target(vault, relative)
    if destination.exists():
        # Recover a crash after the directory rename without overwriting personal edits.
        actual = {p.relative_to(destination).as_posix(): sha256(p) for p in destination.rglob("*") if p.is_file()}
        expected = {path: hashlib.sha256(data).hexdigest() for path, data in validated["outputs"].items()}
        if actual != expected:
            raise ValueError("Destination already contains different local content")
    else:
        stage = Path(config["staging_root"]).resolve() / (bundle + "-" + uuid.uuid4().hex)
        if stage.is_relative_to(vault):
            raise ValueError("Staging must be outside the synced vault")
        stage.mkdir(parents=True)
        for path, data in validated["outputs"].items():
            target = safe_target(stage, path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            if sha256(target) != hashlib.sha256(data).hexdigest():
                raise RuntimeError("Staged file checksum mismatch")
        destination.parent.mkdir(parents=True, exist_ok=True)
        os.rename(stage, destination)
    record = {"source_hash": validated["source_hash"], "source_files": validated["source_files"],
              "category": validated["category"], "classification": validated.get("classification", "manifest"), "destination": relative.as_posix(),
              "outputs": {path: hashlib.sha256(data).hexdigest() for path, data in validated["outputs"].items()},
              "note": (relative / validated["note"]).as_posix(), "status": "imported", "reviewed": False}
    return record, True


def verify_backup(record):
    run = Path(record["backup"])
    verification = json.loads((run / "verification.json").read_text(encoding="utf-8"))
    if verification.get("result") != "PASS" or not verification.get("restore_test"):
        raise RuntimeError("An isolated restore test is required before cleanup")
    for relative, digest in record["outputs"].items():
        target = safe_target(run / "vault", Path(record["destination"]) / relative)
        if not target.is_file() or sha256(target) != digest:
            raise RuntimeError("Original imported file missing from verified backup")


def finalize(config, records):
    repo = Path(config["relay"])
    git(repo, "fetch", "origin", config["branch"])
    ref = "origin/" + config["branch"]
    commit, current = snapshot(repo, ref)
    selected = {}
    for bundle, record in records.items():
        if bundle not in current:
            continue
        try:
            verify_backup(record)
            digest, _ = bundle_hash(current[bundle])
            if digest == record["source_hash"]:
                selected[bundle] = record
        except (ValueError, RuntimeError, OSError):
            continue
    if not selected:
        return []
    publish = Path(config["staging_root"]).resolve().parent / ("publish-" + uuid.uuid4().hex)
    git(repo, "worktree", "add", "--detach", str(publish), commit)
    for bundle, record in selected.items():
        paths = ["capture/items/" + bundle + "/" + path for path in record["source_files"]]
        git(publish, "rm", "--", *paths)
        receipt = {"version": 1, "id": bundle, "source_hash": record["source_hash"],
                   "files": record["source_files"], "category": record["category"],
                   "result": "imported_and_backup_restore_verified"}
        receipt_path = publish / "receipts" / (bundle + ".json")
        if receipt_path.exists() and json.loads(receipt_path.read_text()) != receipt:
            raise RuntimeError("Existing receipt conflicts with bundle ID")
        atomic_json(receipt_path, receipt)
        git(publish, "add", "--", receipt_path.relative_to(publish).as_posix())
    git(publish, "commit", "-m", "Acknowledge verified local capture imports")
    # Normal fast-forward push; a racing remote update is preserved, never forced.
    git(publish, "push", "origin", "HEAD:refs/heads/" + config["branch"])
    git(repo, "worktree", "remove", str(publish))
    return list(selected)


def process(config, ref=None, cleanup=True):
    state_path = Path(config["state_path"])
    report = {"imported": [], "pending": [], "held": [], "acknowledged": []}
    with exclusive_lock(state_path.with_suffix(".lock")):
        state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {"bundles": {}}
        if ref is None:
            git(config["relay"], "fetch", "origin", config["branch"])
            ref = "origin/" + config["branch"]
        commit, packages = snapshot(config["relay"], ref)
        for bundle, files in packages.items():
            try:
                validated = validate(bundle, files)
                if validated is None:
                    report["pending"].append(bundle)
                    continue
                record, added = import_bundle(config, bundle, validated, state["bundles"].get(bundle))
                record.setdefault("source_commit", commit)
                state["bundles"][bundle] = record
                atomic_json(state_path, state)
                if added:
                    report["imported"].append(record["note"])
            except (ValueError, KeyError, UnicodeError, OSError) as error:
                report["held"].append({"id": bundle, "reason": type(error).__name__})
        needs_backup = {bundle: row for bundle, row in state["bundles"].items() if not row.get("backup")}
        if needs_backup:
            # Backup failure leaves the GitHub original intact and retries next session.
            backup = backup_local_setup(json.loads(Path(config["backup_config"]).read_text(encoding="utf-8")), verify_restore=True)
            for record in needs_backup.values():
                record["backup"] = str(Path(backup["snapshot"]).parent)
                verify_backup(record)
            atomic_json(state_path, state)
        cleanup_candidates = {key: row for key, row in state["bundles"].items() if key in packages}
        if cleanup and cleanup_candidates:
            try:
                report["acknowledged"] = finalize(config, cleanup_candidates)
                for bundle in report["acknowledged"]:
                    state["bundles"][bundle]["status"] = "acknowledged"
                atomic_json(state_path, state)
            except (RuntimeError, OSError, subprocess.TimeoutExpired) as error:
                report["cleanup_pending"] = type(error).__name__
        return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(Path(__file__).resolve().parents[1] / "config" / "capture.local.json"))
    parser.add_argument("--ref", help="Use an already-fetched immutable snapshot")
    parser.add_argument("--no-cleanup", action="store_true")
    parser.add_argument("--mark-reviewed", metavar="BUNDLE_ID")
    parser.add_argument("--pending", action="store_true", help="List pending batch notes without fetching or AI")
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    if args.pending:
        state_path = Path(config["state_path"])
        state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {"bundles": {}}
        pending = [{"id": key, "note": row["note"], "category": row["category"]}
                   for key, row in state["bundles"].items() if not row.get("reviewed")]
        print(json.dumps({"pending_count": len(pending), "notes": pending}, ensure_ascii=False))
    elif args.mark_reviewed:
        state_path = Path(config["state_path"])
        with exclusive_lock(state_path.with_suffix(".lock")):
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["bundles"][args.mark_reviewed]["reviewed"] = True
            atomic_json(state_path, state)
        print("Review cursor updated")
    else:
        print(json.dumps(process(config, args.ref, not args.no_cleanup), ensure_ascii=False))


if __name__ == "__main__":
    main()
