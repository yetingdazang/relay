"""Pair a named Android device with only its designated folders."""
import argparse
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from relay_notes_backup import atomic_json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--role", choices=["phone", "tablet"], required=True)
    parser.add_argument("--device-id", required=True)
    parser.add_argument("--config", default=str(Path(__file__).resolve().parents[1] / "config" / "notes_sync.local.json"))
    args = parser.parse_args()
    device_id = args.device_id.upper()
    if not re.fullmatch(r"[A-Z2-7]{7}(?:-[A-Z2-7]{7}){7}", device_id):
        parser.error("Invalid Syncthing device ID")
    config_path = Path(args.config)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    pairing_path = config_path.with_name("notes_sync_devices.local.json")
    paired = json.loads(pairing_path.read_text(encoding="utf-8")) if pairing_path.exists() else {}
    if args.role in paired and paired[args.role] != device_id:
        parser.error("Role already paired; inspect the current device before replacing it")
    if any(role != args.role and value == device_id for role, value in paired.items()):
        parser.error("This ID is already assigned to the other role")
    key = ET.parse(Path(config["syncthing_home"]) / "config.xml").findtext("gui/apikey")
    def api(path, value=None):
        request = urllib.request.Request("http://127.0.0.1:8384/rest/" + path,
            data=None if value is None else json.dumps(value).encode(),
            headers={"X-API-Key": key, "Content-Type": "application/json"},
            method="GET" if value is None else "PUT")
        with urllib.request.urlopen(request, timeout=5) as response:
            data = response.read()
            return json.loads(data) if data else None
    own_id = api("system/status")["myID"]
    if device_id == own_id:
        parser.error("The desktop cannot be paired as its own Android device")
    device = next((item for item in api("config/devices") if item["deviceID"] == device_id), None)
    if device is None:
        device = api("config/defaults/device")
        device.update({"deviceID": device_id, "name": "Android " + args.role, "addresses": ["dynamic"],
                       "introducer": False, "autoAcceptFolders": False})
        api("config/devices/" + device_id, device)
    shared = []
    folders = api("config/folders")
    for channel in config["folders"]:
        if args.role not in channel["audience"]:
            continue
        folder = next(item for item in folders if item["id"] == channel["id"])
        if not any(item["deviceID"] == device_id for item in folder["devices"]):
            folder["devices"].append({"deviceID": device_id})
            api("config/folders/" + channel["id"], folder)
        shared.append(channel["id"])
    paired[args.role] = device_id
    atomic_json(pairing_path, paired)
    print(json.dumps({"role": args.role, "shared_folders": shared, "paired": True}, ensure_ascii=False))


if __name__ == "__main__":
    main()
