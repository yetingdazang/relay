"""Verify selective sync with two disposable local peers, never real Android devices."""
import argparse
import copy
import json
import os
import subprocess
import time
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path
from relay_notes_import import import_once
from relay_notes_backup import sha256, atomic_json


class Node:
    def __init__(self, home, port):
        self.home = Path(home)
        self.port = port
        self.key = ET.parse(self.home / "config.xml").findtext("gui/apikey")
    def api(self, endpoint, value=None, method=None):
        request = urllib.request.Request(
            "http://127.0.0.1:" + str(self.port) + "/rest/" + endpoint,
            data=None if value is None else json.dumps(value).encode(),
            headers={"X-API-Key": self.key, "Content-Type": "application/json"},
            method=method or ("GET" if value is None else "PUT"))
        with urllib.request.urlopen(request, timeout=5) as response:
            data = response.read()
            return json.loads(data) if data else None
    def scan(self, folder):
        self.api("db/scan?folder=" + urllib.parse.quote(folder), method="POST")


def wait_for(predicate, description):
    limit = time.monotonic() + 45
    while time.monotonic() < limit:
        if predicate():
            return
        time.sleep(0.3)
    raise RuntimeError("Timed out: " + description)


def temporary_node(binary, directory, gui_port, sync_port):
    directory.mkdir(parents=True)
    subprocess.run([binary, "generate", "--home=" + str(directory), "--no-port-probing"],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                   creationflags=subprocess.CREATE_NO_WINDOW)
    config_path = directory / "config.xml"
    tree = ET.parse(config_path)
    root = tree.getroot()
    for folder in list(root.findall("folder")):
        root.remove(folder)
    root.find("gui/address").text = "127.0.0.1:" + str(gui_port)
    options = root.find("options")
    for element in list(options.findall("listenAddress")):
        options.remove(element)
    ET.SubElement(options, "listenAddress").text = "tcp://127.0.0.1:" + str(sync_port)
    for name in ["globalAnnounceEnabled", "localAnnounceEnabled", "relaysEnabled", "natEnabled", "startBrowser"]:
        options.find(name).text = "false"
    options.find("urAccepted").text = "-1"
    options.find("autoUpgradeIntervalH").text = "0"
    tree.write(config_path, encoding="utf-8", xml_declaration=True)
    process = subprocess.Popen(
        [binary, "serve", "--home=" + str(directory), "--no-browser", "--no-console", "--no-restart", "--no-upgrade"],
        stdout=(directory / "process.out").open("wb"), stderr=(directory / "process.err").open("wb"),
        creationflags=subprocess.CREATE_NO_WINDOW)
    node = Node(directory, gui_port)
    def ready():
        try:
            node.api("system/status")
            return True
        except Exception:
            return False
    wait_for(ready, "temporary node startup")
    return node, process


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(Path(__file__).resolve().parents[1] / "config" / "notes_sync.local.json"))
    parser.add_argument("--output-root", required=True)
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    output_root = Path(args.output_root).resolve()
    if output_root.exists():
        raise ValueError("Use a new verification output directory")
    output_root.mkdir(parents=True)
    main_node = Node(config["syncthing_home"], 8384)
    own_id = main_node.api("system/status")["myID"]
    original_devices = main_node.api("config/devices")
    if any(device["deviceID"] != own_id for device in original_devices):
        raise ValueError("Local verification requires zero paired real devices")
    original_folders = main_node.api("config/folders")
    peers = {}
    peer_ids = {}
    checks = []
    try:
        for device, gui_port, sync_port in [("phone", 8385, 22001), ("tablet", 8386, 22002)]:
            node, process = temporary_node(config["syncthing_binary"], output_root / (device + "-state"), gui_port, sync_port)
            peers[device] = (node, process, output_root / (device + "-vault"))
            peers[device][2].mkdir()
            peer_id = node.api("system/status")["myID"]
            peer_ids[device] = peer_id
            local_device = main_node.api("config/defaults/device")
            local_device.update({"deviceID": peer_id, "name": "TEMP-local-test-" + device,
                                 "addresses": ["tcp://127.0.0.1:" + str(sync_port)],
                                 "introducer": False, "autoAcceptFolders": False})
            main_node.api("config/devices/" + peer_id, local_device)
            desktop = node.api("config/defaults/device")
            desktop.update({"deviceID": own_id, "name": "Relay desktop",
                            "addresses": ["tcp://127.0.0.1:22000"], "introducer": False, "autoAcceptFolders": False})
            node.api("config/devices/" + own_id, desktop)
        for folder in config["folders"]:
            main_folder = next(copy.deepcopy(item) for item in original_folders if item["id"] == folder["id"])
            main_folder["devices"] = [{"deviceID": own_id}] + [{"deviceID": peer_ids[device]} for device in folder["audience"]]
            main_node.api("config/folders/" + folder["id"], main_folder)
            for device in folder["audience"]:
                node, _, mobile_vault = peers[device]
                mobile_path = mobile_vault / ("notes/00-Inbox/" + ("手机" if device == "phone" else "平板") if folder["type"] == "receiveonly" else folder["label"])
                item = node.api("config/defaults/folder")
                item.update({"id": folder["id"], "label": folder["label"], "path": str(mobile_path),
                             "type": "sendonly" if folder["type"] == "receiveonly" else "receiveonly",
                             "devices": [{"deviceID": node.api("system/status")["myID"]}, {"deviceID": own_id}],
                             "rescanIntervalS": 1, "fsWatcherEnabled": True, "ignorePerms": True})
                node.api("config/folders/" + folder["id"], item)
        vault = Path(config["vault"])
        for folder in config["folders"]:
            main_node.scan(folder["id"])
        for device in ["phone", "tablet"]:
            mobile_vault = peers[device][2]
            area = "手机同步" if device == "phone" else "平板同步"
            expected = mobile_vault / area / ("同步测试-" + area + ".md")
            image = mobile_vault / area / "附件" / "同步测试图片.png"
            wait_for(lambda: expected.is_file() and image.is_file(), device + " selected note and image")
            assert sha256(image) == sha256(vault / area / "附件" / "同步测试图片.png")
            common_image = mobile_vault / "共同同步" / "附件" / "同步测试图片.png"
            wait_for(common_image.is_file, device + " common folder")
            assert sha256(common_image) == sha256(vault / "共同同步" / "附件" / "同步测试图片.png")
            assert not (mobile_vault / ("平板同步" if device == "phone" else "手机同步")).exists()
            assert not (mobile_vault / "notes/01-Knowledge").exists()
            checks.append(device + ": selective files and image hashes PASS")
        print("SELECTIVE_SYNC_PASS", flush=True)
        for device in ["phone", "tablet"]:
            node, _, mobile_vault = peers[device]
            label = "手机" if device == "phone" else "平板"
            capture = mobile_vault / "notes/00-Inbox" / label
            attachment = capture / "附件" / "本机验证图片.png"
            attachment.parent.mkdir(parents=True, exist_ok=True)
            attachment.write_bytes((vault / "共同同步" / "附件" / "同步测试图片.png").read_bytes())
            note = capture / ("本机验证-" + label + "新笔记.md")
            content = "# 本机同步验证\n\n> [!summary] 提要\n> 这是电脑模拟移动端产生的非敏感测试笔记，真实设备尚未配对。\n\n## 目录\n\n- [[#原始附件|原始附件]]\n\n## 原始附件\n\n![[notes/00-Inbox/" + label + "/附件/本机验证图片.png]]\n"
            note.write_text(content, encoding="utf-8")
            folder_id = "relay-inbox-" + device
            node.scan(folder_id)
            staging = Path(next(channel["source"] for channel in config["incoming"] if channel["device"] == device))
            wait_for(lambda: (staging / note.name).is_file() and (staging / "附件" / attachment.name).is_file(), device + " inbound transfer")
            imported = import_once(config)
            permanent = Path(next(channel["destination"] for channel in config["incoming"] if channel["device"] == device))
            assert sha256(permanent / note.name) == sha256(note)
            assert sha256(permanent / "附件" / attachment.name) == sha256(attachment)
            desktop_content = content + "\n电脑修改保留测试。\n"
            (permanent / note.name).write_text(desktop_content, encoding="utf-8")
            note.write_text(content + "\n移动端第二次修改。\n", encoding="utf-8")
            node.scan(folder_id)
            wait_for(lambda: sha256(staging / note.name) == sha256(note), device + " new revision")
            conflict_result = import_once(config)
            assert conflict_result["conflicts"] == 1
            assert (permanent / note.name).read_text(encoding="utf-8") == desktop_content
            assert list(permanent.glob(note.stem + "-同步冲突-*"))
            note.unlink()
            node.scan(folder_id)
            wait_for(lambda: not (staging / note.name).exists(), device + " inbox deletion")
            import_once(config)
            assert (permanent / note.name).is_file()
            checks.append(device + ": import, conflict preservation and deletion protection PASS")
            print(device.upper() + "_IMPORT_PROTECTION_PASS", flush=True)
        selected = vault / "手机同步" / "同步测试-手机同步.md"
        mobile_selected = peers["phone"][2] / "手机同步" / selected.name
        original_content = selected.read_bytes()
        archive = vault / "notes/99-Archive" / "本机同步验证"
        archive.mkdir(parents=True, exist_ok=True)
        retained = archive / selected.name
        assert not retained.exists()
        selected.rename(retained)
        try:
            main_node.scan("relay-notes-phone")
            wait_for(lambda: not mobile_selected.exists(), "unpublishing from phone")
            assert retained.read_bytes() == original_content
            checks.append("unpublish: mobile removal and desktop original retained PASS")
        finally:
            retained.rename(selected)
            main_node.scan("relay-notes-phone")
        report = {"result": "PASS", "kind": "two temporary loopback peers; NOT actual Android validation", "checks": checks}
        atomic_json(output_root / "verification.json", report)
        print(json.dumps(report, ensure_ascii=False), flush=True)
    finally:
        for folder in original_folders:
            main_node.api("config/folders/" + folder["id"], folder)
        for peer_id in peer_ids.values():
            main_node.api("config/devices/" + peer_id, method="DELETE")
        for node, process, _ in peers.values():
            try:
                node.api("system/shutdown", method="POST")
                process.wait(timeout=10)
            except Exception:
                pass


if __name__ == "__main__":
    main()
