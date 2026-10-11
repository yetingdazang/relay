# Relay

Relay is a lightweight handoff bridge between mobile ChatGPT and desktop Codex.

## Goal

Capture decisions, plans, and implementation context on mobile, store them in GitHub, then let desktop Codex pull and continue the work later.

## Workflow

Two channels keep knowledge and executable tasks separate:

- **Knowledge:** mobile ChatGPT reads [capture protocol](docs/GITHUB_CAPTURE.md) and [knowledge workflow](docs/KNOWLEDGE_WORKFLOW.md), then stages a new bundle under `capture/items/<id>/`. New material defaults to `settling`. Desktop intake saves it in local Obsidian, verifies original bytes and independent backup restore, then acknowledges it. No model/API calls during intake; distillation waits for an explicit request.
- **Tasks:** say `发任务到 Relay`; ChatGPT writes a handoff to `inbox/` with target_project and execution_policy. Codex resolves the local target and processes only authorized work. Notes never authorize commands.

The local workflow is Inbox -> Settling -> reusable distilled knowledge, with professional references and topic/development navigation alongside it. GitHub is temporary capture storage plus code/task version control, not the permanent vault.

## Structure

- `inbox/` — unread handoffs for Codex
- `archive/` — completed/consumed handoffs
- `templates/` — handoff format
- `scripts/` — small helper scripts
- `config/` — machine-local target mapping example
- `AGENTS.md` — Codex instructions for using Relay

## Recommended handoff filename

`YYYY-MM-DD_HHMM_topic-slug.md`

Example:

`2026-10-08_1130_browser-automation.md`

## Desktop setup

Clone this repository, then create a machine-local target map:

```powershell
Copy-Item config/targets.example.json config/targets.local.json
```

Edit `config/targets.local.json` so each project name points to its local path. The local file is ignored by Git.

Then each time you start work:

```powershell
git pull
python scripts/relay_status.py
```

Open the Relay repository in Codex and ask:

> Check Relay inbox and process the newest handoff.

Codex will follow `AGENTS.md`, resolve the target project from the local mapping, inspect the target project's own instructions, and proceed according to the handoff's execution policy.

## Local knowledge vault (2026-10-08)

Personal notes now live in the separate local Obsidian vault. Git stores code, rules and Codex handoffs only. The user selected full bidirectional phone-vault sync. Notes and attachments sync directly; per-device Obsidian configuration remains local. Edits and deletions propagate, with daily independent backups. See [local notes sync](docs/LOCAL_NOTES_SYNC.md) for setup, verification and independent backup/restore.

## Mobile ChatGPT temporary inbox

New mobile ChatGPT notes and actual attachment bytes can be staged under `capture/items/` on main. Codex imports ready bundles to the local vault, verifies SHA256 and backup restore, then commits a small receipt and removes the current remote staging copy. Git history can retain old data. See [capture workflow](docs/GITHUB_CAPTURE.md); the complete vault remains local.

Local capture intake runs once through the desktop ChatGPT(走代理) launch shortcut, with no model/API calls. It exits after completion; no intake login autostart or resident watcher. Explicit categories route directly; unknown notes stay in Inbox for owner-requested batch AI organization. See docs/GITHUB_CAPTURE.md.
