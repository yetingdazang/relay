# Relay

Relay is a lightweight handoff bridge between mobile ChatGPT and desktop Codex.

## Goal

Capture decisions, plans, and implementation context on mobile, store them in GitHub, then let desktop Codex pull and continue the work later.

## Workflow

1. Discuss something in ChatGPT on your phone.
2. Say: `发到 Relay`.
3. ChatGPT turns the discussion into a concise handoff note and saves it under `inbox/`.
4. On the desktop, pull this repository.
5. Codex reads unread handoffs, works on the relevant project, then moves completed notes to `archive/`.

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
