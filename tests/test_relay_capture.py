import base64
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from relay_capture import validate, import_bundle, process, git, finalize
from relay_notes_backup import create_backup


def files(bundle="20261008-fixture", category="knowledge"):
    return {"manifest.json": json.dumps({"version": 1, "id": bundle, "ready": True,
            "title": "Fixture note", "category": category,
            "attachments": [{"path": "attachments/fixture.png"}]}).encode(),
            "note.md": b"# Fixture\n\n![[attachments/fixture.png]]\n",
            "attachments/fixture.png": b"synthetic-non-sensitive-image-bytes"}


class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.config = {"vault": str(self.root / "vault"), "staging_root": str(self.root / "stage"),
                       "state_path": str(self.root / "state.json"), "branch": "main"}
        Path(self.config["vault"]).mkdir()
    def tearDown(self):
        self.temporary.cleanup()
    def test_partial_upload_stays_pending(self):
        self.assertIsNone(validate("20261008-fixture", {"note.md": b"partial"}))
    def test_base64_and_checksum_preserve_original(self):
        data = files()
        manifest = json.loads(data["manifest.json"])
        image = data.pop("attachments/fixture.png")
        manifest["attachments"] = [{"path": "attachments/fixture.png.b64", "name": "fixture.png",
                                    "encoding": "base64", "sha256": hashlib.sha256(image).hexdigest()}]
        data["attachments/fixture.png.b64"] = base64.b64encode(image)
        data["manifest.json"] = json.dumps(manifest).encode()
        self.assertEqual(validate("20261008-fixture", data)["outputs"]["attachments/fixture.png"], image)
        manifest["attachments"][0]["sha256"] = "0" * 64
        data["manifest.json"] = json.dumps(manifest).encode()
        with self.assertRaises(ValueError): validate("20261008-fixture", data)
    def test_path_traversal_and_reserved_config_rejected(self):
        for path in ["attachments/../../outside", "attachments/.obsidian/data.json", "attachments/CON.png"]:
            data = files(); manifest = json.loads(data["manifest.json"])
            manifest["attachments"] = [{"path": path}];data[path] = b"fixture"
            data["manifest.json"] = json.dumps(manifest).encode()
            with self.assertRaises(ValueError): validate("20261008-fixture", data)
    def test_case_collision_and_missing_embed_rejected(self):
        data = files(); manifest = json.loads(data["manifest.json"])
        manifest["attachments"].append({"path": "attachments/Fixture.png"})
        data["attachments/Fixture.png"] = b"other";data["manifest.json"] = json.dumps(manifest).encode()
        with self.assertRaises(ValueError): validate("20261008-fixture", data)
        data = files();data["note.md"] = b"![[attachments/missing.png]]"
        with self.assertRaises(ValueError): validate("20261008-fixture", data)
    def test_bad_manifest_and_unlisted_attachment_rejected(self):
        with self.assertRaises(ValueError): validate("20261008-fixture", {"manifest.json": b"[]"})
        data = files();data["attachments/extra.png"] = b"unlisted"
        with self.assertRaises(ValueError): validate("20261008-fixture", data)
    def test_local_edits_preserved_and_same_id_cannot_be_changed(self):
        data = files(); checked = validate("20261008-fixture", data)
        record, added = import_bundle(self.config, "20261008-fixture", checked)
        note = Path(self.config["vault"]) / record["note"]
        note.write_text("personal edit", encoding="utf-8")
        _, added = import_bundle(self.config, "20261008-fixture", checked, record)
        self.assertFalse(added);self.assertEqual(note.read_text(), "personal edit")
        data["note.md"] = b"different content"
        with self.assertRaises(ValueError): import_bundle(self.config, "20261008-fixture", validate("20261008-fixture", data), record)
    def test_crash_recovery_and_destination_collision(self):
        checked = validate("20261008-fixture", files())
        record, _ = import_bundle(self.config, "20261008-fixture", checked)
        recovered, _ = import_bundle(self.config, "20261008-fixture", checked)
        self.assertEqual(record["outputs"], recovered["outputs"])
        (Path(self.config["vault"]) / record["note"]).write_text("existing local edit")
        with self.assertRaises(ValueError): import_bundle(self.config, "20261008-fixture", checked)
    def prepare_git(self):
        origin = self.root / "origin.git"; repo = self.root / "relay"
        git(self.root, "init", "--bare", str(origin))
        git(self.root, "init", "-b", "main", str(repo))
        git(repo, "config", "user.name", "Relay synthetic test")
        git(repo, "config", "user.email", "fixture@example.invalid")
        git(repo, "remote", "add", "origin", str(origin))
        folder = repo / "capture/items/20261008-fixture";folder.mkdir(parents=True)
        for name, data in files().items():
            p=folder/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        git(repo, "add", ".");git(repo, "commit", "-m", "Synthetic capture")
        git(repo, "push", "-u", "origin", "main")
        self.config["relay"] = str(repo)
        backup_config = self.root / "backup.json"
        backup_config.write_text(json.dumps({"vault": self.config["vault"], "backup_root": str(self.root/"backups")}))
        self.config["backup_config"] = str(backup_config)
        return repo, origin, folder
    def backup(self, config, verify_restore=False):
        return create_backup(config["vault"], config["backup_root"], verify_restore)
    def test_real_git_import_backup_cleanup_and_retry(self):
        repo, origin, folder = self.prepare_git()
        with patch("relay_capture.backup_local_setup", side_effect=self.backup):
            report = process(self.config)
            again = process(self.config)
        self.assertEqual(report["acknowledged"], ["20261008-fixture"])
        self.assertEqual(again["imported"], [])
        paths = git(origin, "ls-tree", "-r", "--name-only", "main")
        self.assertNotIn("capture/items", paths)
        self.assertIn("receipts/20261008-fixture.json", paths)
        self.assertEqual((Path(self.config["vault"])/"notes/01-Knowledge/20261008-fixture/attachments/fixture.png").read_bytes(), files()["attachments/fixture.png"])
    def test_backup_failure_retains_remote_original_and_retry_recovers(self):
        repo, origin, folder = self.prepare_git()
        with patch("relay_capture.backup_local_setup", side_effect=OSError("simulated disk full")):
            with self.assertRaises(OSError): process(self.config)
        self.assertIn("capture/items", git(origin, "ls-tree", "-r", "--name-only", "main"))
        with patch("relay_capture.backup_local_setup", side_effect=self.backup):
            report = process(self.config)
        self.assertEqual(report["acknowledged"], ["20261008-fixture"])
    def test_remote_changed_after_import_is_never_deleted(self):
        repo, origin, folder = self.prepare_git()
        with patch("relay_capture.backup_local_setup", side_effect=self.backup): process(self.config, cleanup=False)
        (folder/"note.md").write_text("Remote new edit")
        git(repo,"add",".");git(repo,"commit","-m","Concurrent phone edit");git(repo,"push","origin","main")
        state=json.loads(Path(self.config["state_path"]).read_text())
        self.assertEqual(finalize(self.config,state["bundles"]),[])
        self.assertIn("capture/items",git(origin,"ls-tree","-r","--name-only","main"))

    def test_push_race_preserves_remote_update_and_original(self):
        repo, origin, folder = self.prepare_git()
        original_git = git
        def race_git(repository, *args, **kwargs):
            if args[0] == "push" and "publish-" in str(repository):
                (repo / "concurrent.txt").write_text("concurrent owner update")
                original_git(repo, "add", "concurrent.txt")
                original_git(repo, "commit", "-m", "Remote racing update")
                original_git(repo, "push", "origin", "main")
            return original_git(repository, *args, **kwargs)
        with patch("relay_capture.backup_local_setup", side_effect=self.backup), patch("relay_capture.git", side_effect=race_git):
            report=process(self.config)
        self.assertIn("cleanup_pending", report)
        tree=git(origin,"ls-tree","-r","--name-only","main")
        self.assertIn("capture/items",tree)
        self.assertIn("concurrent.txt",tree)
        state=json.loads(Path(self.config["state_path"]).read_text())
        self.assertEqual(state["bundles"]["20261008-fixture"]["status"],"imported")


if __name__ == "__main__": unittest.main()
