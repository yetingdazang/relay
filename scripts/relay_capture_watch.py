"""Windows Codex launch intake. Standard library only; never invokes an AI model."""
import argparse
import ctypes
from ctypes import wintypes
from datetime import datetime
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import time
from relay_capture import process
from relay_notes_backup import atomic_json
from relay_notes_import import exclusive_lock


class LaunchTracker:
    """Run once per observed root-process lifetime, with retry after failures."""
    def __init__(self, retry_seconds=60, maximum_retry_seconds=600):
        self.sessions = {}
        self.retry_seconds = retry_seconds
        self.maximum_retry_seconds = maximum_retry_seconds
    def due(self, active, now):
        active = set(active)
        self.sessions = {key: value for key, value in self.sessions.items() if key in active}
        for key in active:
            self.sessions.setdefault(key, {"done": False, "attempts": 0, "next": now})
        return sorted(key for key, value in self.sessions.items() if not value["done"] and value["next"] <= now)
    def finish(self, key, now, success):
        value = self.sessions[key]
        value["done"] = success
        value["attempts"] += 1
        value["next"] = now + min(self.maximum_retry_seconds,
                                   self.retry_seconds * 2 ** min(value["attempts"] - 1, 6))


def desktop_roots(rows):
    eligible = {row["pid"]: row for row in rows if
                row["name"].lower() in {"chatgpt.exe", "codex.exe"} and
                "\\openai.codex_" in row["path"].lower()}
    return {str(row["pid"]) + ":" + str(row["created"])
            for row in eligible.values() if row["parent"] not in eligible}


def running_desktop_roots():
    if not hasattr(ctypes, "WinDLL"):
        raise RuntimeError("This launch watcher requires Windows")
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    class ProcessEntry(ctypes.Structure):
        _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD),
                    ("th32ProcessID", wintypes.DWORD), ("th32DefaultHeapID", ctypes.c_size_t),
                    ("th32ModuleID", wintypes.DWORD), ("cntThreads", wintypes.DWORD),
                    ("th32ParentProcessID", wintypes.DWORD), ("pcPriClassBase", wintypes.LONG),
                    ("dwFlags", wintypes.DWORD), ("szExeFile", wintypes.WCHAR * 260)]
    kernel.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    kernel.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    kernel.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(ProcessEntry)]
    kernel.Process32FirstW.restype = wintypes.BOOL
    kernel.Process32NextW.argtypes = kernel.Process32FirstW.argtypes
    kernel.Process32NextW.restype = wintypes.BOOL
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    kernel.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD,
                                                 wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    kernel.QueryFullProcessImageNameW.restype = wintypes.BOOL
    kernel.GetProcessTimes.argtypes = [wintypes.HANDLE, *[ctypes.POINTER(wintypes.FILETIME)] * 4]
    kernel.GetProcessTimes.restype = wintypes.BOOL
    snapshot = kernel.CreateToolhelp32Snapshot(2, 0)
    if snapshot == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    rows = []
    try:
        entry = ProcessEntry()
        entry.dwSize = ctypes.sizeof(entry)
        available = kernel.Process32FirstW(snapshot, ctypes.byref(entry))
        while available:
            if entry.szExeFile.lower() in {"chatgpt.exe", "codex.exe"}:
                handle = kernel.OpenProcess(0x1000, False, entry.th32ProcessID)
                if handle:
                    try:
                        path = ctypes.create_unicode_buffer(32768)
                        size = wintypes.DWORD(len(path))
                        created, ended, system, user = [wintypes.FILETIME() for _ in range(4)]
                        if kernel.QueryFullProcessImageNameW(handle, 0, path, ctypes.byref(size)) and kernel.GetProcessTimes(handle, *[ctypes.byref(x) for x in [created, ended, system, user]]):
                            rows.append({"name": entry.szExeFile, "path": path.value,
                                         "pid": entry.th32ProcessID, "parent": entry.th32ParentProcessID,
                                         "created": (created.dwHighDateTime << 32) | created.dwLowDateTime})
                    finally:
                        kernel.CloseHandle(handle)
            available = kernel.Process32NextW(snapshot, ctypes.byref(entry))
    finally:
        kernel.CloseHandle(snapshot)
    return desktop_roots(rows)


def receive(config, state_directory, trigger):
    started = datetime.now().astimezone().isoformat()
    try:
        report = process(config)
        outcome = {"result": "PASS", "started_at": started,
                   "finished_at": datetime.now().astimezone().isoformat(), "trigger": trigger,
                   "ai_calls": 0, "capture": report}
        # Partial/unready/invalid bundles await the next launch. Network/cleanup failures retry.
        success = "cleanup_pending" not in report
        if not success:
            outcome["result"] = "RETRY"
        logging.info("Local intake %s: imported=%s acknowledged=%s held=%s pending=%s",
                     outcome["result"], len(report["imported"]), len(report["acknowledged"]),
                     len(report["held"]), len(report["pending"]))
    except Exception as error:
        outcome = {"result": "RETRY", "started_at": started,
                   "finished_at": datetime.now().astimezone().isoformat(), "trigger": trigger,
                   "ai_calls": 0, "error": type(error).__name__}
        success = False
        logging.error("Local intake failed: %s; remote originals preserved", type(error).__name__)
    atomic_json(state_directory / "capture-last-run.json", outcome)
    return success, outcome


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(Path(__file__).resolve().parents[1] / "config" / "capture.local.json"))
    parser.add_argument("--once", action="store_true", help="Receive now without AI and exit")
    parser.add_argument("--detect", action="store_true", help="Read currently running desktop roots")
    args = parser.parse_args()
    if args.detect:
        print(json.dumps(sorted(running_desktop_roots())))
        return 0
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    state_directory = Path(config["state_path"]).parent
    state_directory.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(state_directory / "capture-watch.log", maxBytes=1024*1024,
                                  backupCount=3, encoding="utf-8")
    logging.basicConfig(handlers=[handler], level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    if args.once:
        success, outcome = receive(config, state_directory, "manual")
        print(json.dumps(outcome, ensure_ascii=False))
        return 0 if success else 1
    options = config.get("watch", {})
    tracker = LaunchTracker(options.get("retry_seconds", 60), options.get("maximum_retry_seconds", 600))
    try:
        with exclusive_lock(state_directory / "capture-watch.lock"):
            atomic_json(state_directory / "capture-watch-status.json",
                        {"started_at": datetime.now().astimezone().isoformat(),
                         "mode": "codex_desktop_launch", "ai_calls": 0,
                         "poll_seconds": options.get("poll_seconds", 5)})
            logging.info("Codex launch intake watcher started; no model calls")
            while True:
                try:
                    for key in tracker.due(running_desktop_roots(), time.monotonic()):
                        success, _ = receive(config, state_directory, "codex_desktop:" + key)
                        tracker.finish(key, time.monotonic(), success)
                except Exception as error:
                    logging.error("Launch observation failed: %s", type(error).__name__)
                time.sleep(max(2, options.get("poll_seconds", 5)))
    except OSError:
        # A second startup invocation is harmless; the existing watcher retains the lock.
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
