import contextlib
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from relay_capture_watch import LaunchTracker, desktop_roots, receive
from relay_capture import validate
from relay_session_start import main


class StartupTests(unittest.TestCase):
    def test_launcher_once_children_do_not_retrigger(self):
        tracker=LaunchTracker()
        path=r"C:\Program Files\WindowsApps\OpenAI.Codex_26.1002.0_x64\app\ChatGPT.exe"
        root={"pid":100,"parent":9,"created":123,"name":"ChatGPT.exe","path":path}
        child={"pid":101,"parent":100,"created":456,"name":"ChatGPT.exe","path":path}
        active=desktop_roots([root,child])
        self.assertEqual(active,{"100:123"})
        self.assertEqual(tracker.due(active,0),["100:123"])
        tracker.finish("100:123",1,True)
        self.assertEqual(tracker.due(active,100),[])
        self.assertEqual(tracker.due(desktop_roots([root]),200),[])
    def test_relaunch_and_pid_reuse_trigger_new_intake(self):
        tracker=LaunchTracker()
        tracker.due({"100:1"},0);tracker.finish("100:1",1,True)
        self.assertEqual(tracker.due(set(),2),[])
        self.assertEqual(tracker.due({"100:2"},3),["100:2"])
    def test_failure_backoff_retries_and_success_stops_retry(self):
        tracker=LaunchTracker(retry_seconds=60,maximum_retry_seconds=120)
        tracker.due({"100:1"},0);tracker.finish("100:1",10,False)
        self.assertEqual(tracker.due({"100:1"},69),[])
        self.assertEqual(tracker.due({"100:1"},70),["100:1"])
        tracker.finish("100:1",71,False)
        self.assertEqual(tracker.due({"100:1"},190),[])
        self.assertEqual(tracker.due({"100:1"},191),["100:1"])
        tracker.finish("100:1",192,True)
        self.assertEqual(tracker.due({"100:1"},1000),[])
    def test_unrelated_chatgpt_and_cli_workers_are_excluded(self):
        rows=[{"pid":1,"parent":0,"created":1,"name":"ChatGPT.exe","path":r"C:\other\ChatGPT.exe"},
              {"pid":2,"parent":1,"created":2,"name":"codex.exe","path":r"C:\Users\a\AppData\Local\OpenAI\Codex\bin\codex.exe"}]
        self.assertEqual(desktop_roots(rows),set())
    def test_quiet_and_hook_never_emit_model_context(self):
        for argument in ["--quiet","--hook"]:
            output=io.StringIO()
            with patch("sys.argv",["relay_session_start.py",argument]),patch("relay_session_start.start",return_value={"private_note":"must not reach model"}),contextlib.redirect_stdout(output):
                self.assertEqual(main(),0)
            self.assertEqual(output.getvalue(),"")
        output=io.StringIO()
        with patch("sys.argv",["relay_session_start.py","--quiet"]),patch("relay_session_start.start",side_effect=OSError("private error")),contextlib.redirect_stdout(output):
            self.assertEqual(main(),1)
        self.assertEqual(output.getvalue(),"")
    def test_missing_or_unknown_category_goes_to_inbox_without_ai(self):
        for category in [None,"not-a-category",["malformed"]]:
            manifest={"version":1,"id":"20261009-note","ready":True,"title":"New note","attachments":[]}
            if category is not None:manifest["category"]=category
            files={"manifest.json":json.dumps(manifest).encode(),"note.md":b"# Note\n\nPreserve original text"}
            self.assertEqual(validate("20261009-note",files)["category"],"inbox")
    def test_receive_reports_retry_and_calls_no_model(self):
        with patch("relay_capture_watch.process",side_effect=OSError("offline")),patch("relay_capture_watch.atomic_json") as saved:
            success,report=receive({},Path("fixture-state"),"fixture-launch")
        self.assertFalse(success)
        self.assertEqual(report["ai_calls"],0)
        self.assertEqual(report["error"],"OSError")
        self.assertTrue(saved.called)


if __name__=="__main__":unittest.main()
