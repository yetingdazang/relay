# Relay agent instructions

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
