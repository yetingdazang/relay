from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
INBOX = ROOT / "inbox"

def extract(text, key):
    m = re.search(rf"^{re.escape(key)}:\s*[\"']?(.+?)[\"']?\s*$", text, re.M)
    return m.group(1).strip() if m else "unknown"

files = sorted(INBOX.glob("*.md"), reverse=True)

if not files:
    print("Relay inbox is empty.")
    raise SystemExit(0)

print(f"Relay inbox: {len(files)} handoff(s)\n")
for path in files:
    text = path.read_text(encoding="utf-8", errors="replace")
    title = next((line[2:].strip() for line in text.splitlines() if line.startswith("# ")), path.stem)
    target = extract(text, "target_project")
    policy = extract(text, "execution_policy")
    status = extract(text, "status")
    print(f"- {path.name}")
    print(f"  title: {title}")
    print(f"  target: {target}")
    print(f"  policy: {policy}")
    print(f"  status: {status}")
