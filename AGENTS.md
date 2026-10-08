# Relay agent instructions

## Current local-first architecture (2026-10-08)

- Relay lives at `E:/Relay` and contains code, rules, and Codex handoffs only.
- The complete local knowledge vault lives at `E:/OBSIDIAN`; it is not tracked by Git.
- Consult `config/targets.local.json` for exact machine-local mappings.
- Mobile notes enter separate staging folders and are imported with `scripts/relay_notes_import.py`.
- See `docs/LOCAL_NOTES_SYNC.md` for selective device folders and backup/restore.
- Do not commit personal notes, Obsidian plugin settings, or synchronization credentials.
- Older Git-based note naming and preview workflows below are retained as historical guidance. They are not the ingestion workflow for the new local vault and must not run automatically against old notes.
- New-file naming remains explicit, incremental, and limited to newly added default-named files; do not bulk process existing notes.


Relay is a cross-device handoff inbox between mobile ChatGPT and desktop Codex.

## Session start behavior

At the beginning of a Codex session in this repository:

1. Inspect `inbox/` for Markdown handoff files.
2. If there are no handoffs, report that the Relay inbox is empty.
3. If there are handoffs, list them newest first with:
   - title
   - target project
   - requested action
   - whether execution is authorized
4. Do not execute a handoff against a target project until you have identified the correct local repository/worktree.
5. Never guess a target repository path.

## Handoff semantics

Every handoff should contain:

- `status`
- `target_project`
- `created_at`
- `summary`
- `decisions`
- `requested_actions`
- `constraints`
- `execution_policy`

`execution_policy` values:

- `review_only` — inspect and propose; do not modify target project
- `safe_changes` — small reversible changes are allowed
- `execute` — carry out the requested work, still respecting project-level AGENTS.md and user instructions

If the handoff conflicts with the target project's `AGENTS.md`, the target project's rules win.

## Processing a handoff

For each handoff:

1. Read it fully.
2. Restate the intended outcome briefly.
3. Locate the target project.
4. Read the target project's `AGENTS.md` and relevant docs.
5. Inspect current state before editing.
6. Make only changes authorized by `execution_policy`.
7. Run relevant checks/tests.
8. Update the handoff with a short result note.
9. Move the handoff from `inbox/` to `archive/` only after the user-requested task is complete or explicitly deferred.

## Safety

- Never commit, push, open a PR, publish, deploy, or delete remote resources unless the handoff explicitly authorizes it or the user asks in the active Codex session.
- Never expose secrets in Relay.
- Do not store passwords, tokens, cookies, or private keys in handoff files.
- Prefer concise distilled context over raw chat transcripts.

## Local target mapping

If `config/targets.local.json` exists, use it to map `target_project` names to local repository paths.
This file is intentionally ignored by Git and may contain machine-local paths.

Example:

```json
{
  "blade-lab": "D:/Projects/blade-lab"
}
```

If a target is not mapped, ask for or discover the correct local path before editing anything.

## Suggested desktop command

From the Relay repository:

`python scripts/relay_status.py`

This prints unread handoffs in `inbox/`.

## Obsidian note and attachment naming policy (NEW FILES ONLY)

Follow `docs/KNOWLEDGE_FILE_NAMING.md` when processing newly added knowledge files. This is a bounded, incremental workflow, **not** a vault-wide recurring scan.

- **Scope: only newly added files** under `notes/`, starting after the cursor saved in `config/knowledge_naming_cursor.json`. Compare that commit with the latest remote `main` commit and inspect only files with Git change status `added`; ignore `modified`, `renamed`, and existing files. Do not enumerate/read old notes or attachments to find naming candidates. Exceptions require an explicit user request targeting specific older files.
- Among new files, only default/generated names (Untitled, 未命名, Pasted image, IMG, Screenshot, UUID-like names) are candidates. Respect deliberate names.
- Before renaming a candidate, inspect its actual content; do not infer image contents from the filename. If content is inaccessible, leave the file untouched and note that inspection was unavailable.
- For any candidate rename, inspect only the required inbound references, preserve Obsidian embeds and Markdown links, avoid collisions, and add concise Chinese captions/descriptions. Do not rename project files outside `notes/`.
- After each explicit naming-review run, advance the cursor to the remote commit **that was reviewed**, even when there are no candidates. Advance only after any approved renames and reference updates are successfully committed, or skipped with a clear report. Prevent Git races by reading the current cursor and remote head before writing; never force-push or overwrite concurrent changes.
- Do not reprocess already checked files just because a newer commit was pushed. Do not perform this check on every Codex thought/tool action, or as an always-on background service. Run when requested or as a specifically configured new-files ingestion step.

## Reading image attachments from GitHub

For image files newly added under `notes/` that a text-only GitHub connector cannot read as binary, consult `docs/IMAGE_PREVIEW_BRIDGE.md`. An automatically generated preview manifest and small Base64 JPEG tiles live in `config/image-bridge/`; read the manifest first, then fetch only the tiles needed for the task and present decoded JPEG tiles to a vision-capable model. The `Relay image previews` GitHub Action generates these on the first image-add push without altering the original image. Do not read all preview tiles on every agent session, and never claim to have examined a whole long screenshot after reading just one tile. Desktop Codex with a local cloned image should read the original directly.

This preview cache is separate from the naming workflow, which remains **new-files-only** and is not an always-on ChatGPT background process.

After the image's content has been reviewed and the note/analysis successfully saved, remove only its generated preview cache directory under `config/image-bridge/`. The script `scripts/cleanup_image_previews.py` and `.github/workflows/relay-preview-cleanup.yml` provide immediate per-image cleanup and a 7-day scheduled expiry fallback; see `docs/IMAGE_PREVIEW_BRIDGE.md`. Preserve original `notes/` images and do not rewrite Git history or force-push merely to clean previews.

## Standard structure for future Obsidian knowledge notes

For future new notes and user-requested revisions in `notes/`, follow `docs/NOTE_FORMAT.md` and the template `notes/03-Resources/Templates/标准知识笔记模板.md`:

1. Title then a short `> [!summary] 提要` at the top.
2. An actual clickable `## 目录` with exact Obsidian headings using `[[#heading|label]]`, including appropriate nested sections.
3. The full organized substantive content, with source and analysis distinguished.
4. Original screenshots/images/source attachments **at the end** with a TOC entry, rather than before the summary.

Verify that every table-of-contents entry resolves to an existing heading and the original embeds remain valid. For short informal notes, simplify proportionately; do not generate empty sections. Do not reformat old notes in bulk without an explicit request. This formatting rule is independent of the new-files-only image/file naming policy.
