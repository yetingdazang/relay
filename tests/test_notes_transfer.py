import sys
import tempfile
import unittest
from unittest.mock import patch
import shutil
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from relay_notes_import import import_once, safe_target
from relay_notes_backup import create_backup, restore_snapshot

class MobileImportTests(unittest.TestCase):
    def setUp(self):
        self.sandbox = tempfile.TemporaryDirectory()
        self.root = Path(self.sandbox.name)
        self.incoming = self.root / "incoming"
        self.destination = self.root / "vault" / "notes" / "00-Inbox" / "手机"
        self.incoming.mkdir()
        self.config = {"state_path": str(self.root / "state.json"), "incoming": [
            {"device": "phone", "source": str(self.incoming), "destination": str(self.destination)}]}
    def tearDown(self):
        self.sandbox.cleanup()
    def test_note_attachment_idempotence_and_remote_deletion(self):
        note = self.incoming / "测试.md"
        note.write_text("![[notes/00-Inbox/手机/附件/测试.png]]", encoding="utf-8")
        (self.incoming / "附件").mkdir()
        (self.incoming / "附件" / "测试.png").write_bytes(b"fixture")
        self.assertEqual(import_once(self.config)["imported"], 2)
        self.assertEqual((self.destination / "测试.md").read_text(encoding="utf-8"), note.read_text(encoding="utf-8"))
        self.assertEqual((self.destination / "附件" / "测试.png").read_bytes(), b"fixture")
        self.assertEqual(import_once(self.config)["imported"], 0)
        note.unlink()
        import_once(self.config)
        self.assertTrue((self.destination / "测试.md").is_file())
    def test_desktop_edit_is_preserved_and_mobile_change_gets_a_conflict_copy(self):
        note = self.incoming / "测试.md"
        note.write_text("mobile v1", encoding="utf-8")
        import_once(self.config)
        desktop = self.destination / "测试.md"
        desktop.write_text("desktop edit", encoding="utf-8")
        note.write_text("mobile v2", encoding="utf-8")
        self.assertEqual(import_once(self.config)["conflicts"], 1)
        self.assertEqual(desktop.read_text(encoding="utf-8"), "desktop edit")
        conflicts = list(self.destination.glob("*同步冲突*"))
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0].read_text(encoding="utf-8"), "mobile v2")
        self.assertEqual(import_once(self.config)["imported"], 0)
    def test_existing_desktop_file_is_not_overwritten_on_first_import(self):
        self.destination.mkdir(parents=True)
        (self.destination / "已有.md").write_text("desktop", encoding="utf-8")
        (self.incoming / "已有.md").write_text("mobile", encoding="utf-8")
        self.assertEqual(import_once(self.config)["conflicts"], 1)
        self.assertEqual((self.destination / "已有.md").read_text(encoding="utf-8"), "desktop")
    def test_syncthing_internal_files_are_not_imported(self):
        (self.incoming / ".stversions").mkdir()
        (self.incoming / ".stversions" / "old.md").write_text("old", encoding="utf-8")
        (self.incoming / ".stignore").write_text("*", encoding="utf-8")
        self.assertEqual(import_once(self.config)["imported"], 0)
    def test_desktop_edit_during_copy_is_preserved(self):
        note = self.incoming / "race.md"
        note.write_text("mobile v1", encoding="utf-8")
        import_once(self.config)
        desktop = self.destination / "race.md"
        note.write_text("mobile v2", encoding="utf-8")
        copy = shutil.copy2
        def concurrent_edit(source, target):
            result = copy(source, target)
            desktop.write_text("desktop concurrent edit", encoding="utf-8")
            return result
        with patch("relay_notes_import.shutil.copy2", side_effect=concurrent_edit):
            with self.assertRaises(RuntimeError):
                import_once(self.config)
        self.assertEqual(desktop.read_text(encoding="utf-8"), "desktop concurrent edit")
        self.assertEqual(import_once(self.config)["conflicts"], 1)
    def test_escape_path_is_rejected(self):
        with self.assertRaises(ValueError):
            safe_target(self.destination, "../outside.md")

class BackupTests(unittest.TestCase):
    def test_restore_and_hash_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            vault = root / "vault"
            vault.mkdir()
            (vault / "笔记.md").write_text("keep", encoding="utf-8")
            report = create_backup(vault, root / "backups", verify_restore=True)
            snapshot = Path(report["snapshot"])
            self.assertEqual((Path(report["restore_test"]) / "笔记.md").read_text(encoding="utf-8"), "keep")
            (snapshot / "笔记.md").write_text("tampered", encoding="utf-8")
            with self.assertRaises(RuntimeError):
                restore_snapshot(snapshot.parent, root / "another-restore")
    def test_live_vault_is_never_overwritten_by_restore(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            vault = root / "vault"
            vault.mkdir()
            (vault / "a.md").write_text("keep", encoding="utf-8")
            report = create_backup(vault, root / "backups")
            with self.assertRaises(ValueError):
                restore_snapshot(Path(report["snapshot"]).parent, vault)

if __name__ == "__main__":
    unittest.main()
