"""Report synchronization health without displaying configuration credentials."""
import json
import os
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path


def main():
    config_path = Path(__file__).resolve().parents[1] / "config" / "notes_sync.local.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    key = ET.parse(Path(config["syncthing_home"]) / "config.xml").findtext("gui/apikey")
    def api(endpoint):
        request = urllib.request.Request("http://127.0.0.1:8384/rest/" + endpoint, headers={"X-API-Key": key})
        with urllib.request.urlopen(request, timeout=5) as response:
            return json.load(response)
    system = api("system/status")
    own_id = system["myID"]
    devices = [device for device in api("config/devices") if device["deviceID"] != own_id]
    folders = api("config/folders")
    state_parent = Path(config["state_path"]).parent
    schedule = state_parent / "backup-schedule.json"
    last_backup = json.loads(schedule.read_text(encoding="utf-8")) if schedule.exists() else {}
    report = {"management_url": "http://127.0.0.1:8384", "desktop_device_id": own_id,
              "paired_devices": [{"name": device["name"], "id": device["deviceID"]} for device in devices],
              "vault_is_git_repository": (Path(config["vault"]) / ".git").exists(),
              "last_backup": last_backup.get("snapshot"), "folders": []}
    for folder in folders:
        folder_status = api("db/status?folder=" + folder["id"])
        report["folders"].append({"name": folder["label"], "type": folder["type"],
                                   "shared_remote_devices": len([device for device in folder["devices"] if device["deviceID"] != own_id]),
                                   "state": folder_status["state"], "errors": folder_status["errors"],
                                   "files": folder_status["localFiles"]})
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
