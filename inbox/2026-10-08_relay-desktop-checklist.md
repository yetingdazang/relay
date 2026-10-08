---
status: unread
target_project: relay
created_at: "2026-10-08T18:55:00+08:00"
execution_policy: review_only
source: mobile-chatgpt
---

# Relay desktop integration — full Codex review checklist

## Goal and decisions
Retain the existing GitHub-only Relay setup. Obsidian on Android and Windows is the user-facing note editor; GitHub private repo is the authoritative synchronization and task-handoff source. ChatGPT edits notes through the existing GitHub connection. Codex reads the cloned repo and handles approved tasks. ChatGPT Library is an optional reference collection, not an Obsidian or Codex shared filesystem. Do not implement R2, Dropbox, Remotely Save, cloud MCP, or a new database unless the owner later explicitly changes this decision.

## Priority P0 — repository and credential safety
- Before any pull or change, inspect the local working directory, branch, remote URL, and git status. Preserve uncommitted changes; no forced resets.
- Review tracked Obsidian plugin configuration for secrets **without displaying values**. Existing tracked plugin settings require a security review.
- Recommend a safe plan to rotate exposed credentials, back up local settings, stop tracking sensitive local data, and update ignore rules. Explain why removing a tracked file from Git may affect other devices on the next pull.
- Do not perform any credential changes, deletion, history rewriting, or remote push without separate user approval.

## Priority P1 — Android/Windows sync validation
- Confirm both Obsidian vaults refer to the same Relay repository and expected branch.
- Plan a small non-sensitive Markdown round-trip: Android edit + Commit-and-sync -> GitHub -> Codex pull/read -> approved Codex edit + push -> Android pull.
- Separately validate ChatGPT GitHub note edit -> Obsidian pull. Treat auto-pull and auto-push settings separately; never assume changes are already synced.
- If there are divergent local changes or conflicts, describe them and ask before resolution.

## Priority P2 — Codex handoff execution
- Read repository AGENTS.md and README.md, then inspect every unread root-level inbox/ handoff; run python scripts/relay_status.py if available.
- Keep root inbox/ (Codex tasks) distinct from notes/00-Inbox/ (knowledge notes).
- Check config/targets.local.json for target-project mapping. This file is local-only; do not guess missing project paths.
- Review each handoff's execution_policy. The separate browser automation review for blade-lab is review_only; do not silently implement it or alter its priority.
- Propose a standard loop: inspect -> summarize plan -> request permission -> implement -> test -> report -> archive only when complete or explicitly deferred.

## Priority P3 — notes, images and optional ChatGPT Library
- New notes follow docs/NOTE_FORMAT.md: summary first, clickable TOC, organized body, original source embeds at the end.
- Follow docs/KNOWLEDGE_FILE_NAMING.md only for genuinely newly-added default-named items; no automatic rescanning of all historic files.
- Keep docs/IMAGE_PREVIEW_BRIDGE.md and related Actions working until an approved replacement is tested; clean temporary preview tiles only after successful analysis, never delete original attachments.
- Do not pretend ChatGPT Library automatically syncs to GitHub or can be mounted by Codex; only use it for selected reference files and explicit handoff/export.

## Priority P4 — maintenance, backup, acceptance
- Recommend a small, restorable offline backup and a documented recovery test; GitHub history alone is not a full backup.
- Report which links were actually verified (Android, Windows, ChatGPT, Codex) and which remain untested. Avoid unnecessary new infrastructure.
- Provide the owner a concise report with findings, ordered action items, exact commands for safe next steps, and approvals needed.

## Execution constraints
Inspection and recommendations ONLY. No commits, pushes, repository edits, plugin changes, cloud-service deployments, or destructive operations. Read AGENTS.md and any target project's AGENTS.md first. Never print secrets.

## One-line Codex instruction
Read AGENTS.md and inbox/2026-10-08_relay-desktop-checklist.md, then inspect Relay and report P0-P4 in order. Do not make changes until I confirm.
