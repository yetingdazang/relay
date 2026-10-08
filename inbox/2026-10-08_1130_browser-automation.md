---
status: unread
target_project: "blade-lab"
created_at: "2026-10-08T11:30:00+09:00"
execution_policy: review_only
source: mobile-chatgpt
---

# Browser automation: Playwright first, Browser Use fallback

## Summary

Evaluate how browser automation should be integrated into the current project and Codex workflow.

The preferred architecture is not a pure browser-agent stack. Browser automation is one capability inside the larger Codex/Agent workflow.

## Decisions

- Use Playwright / Playwright CLI Skill as the default path for deterministic browser automation.
- Use Browser Use only for unknown pages, semantic exploration, or tasks where the steps are not known in advance.
- Prefer `Explore -> Compile -> Replay`:
  - first successful run may use Browser Use to explore;
  - convert stable steps into reusable Playwright helpers;
  - future runs should use the helper instead of repeated LLM exploration.
- Browser Use and Playwright may share a Chrome/CDP session, but should not concurrently manipulate the same page.
- Reuse browser profiles or storage state for login sessions. Do not routinely expose credentials to the LLM.
- Stagehand is not a default dependency.
- Browser Harness is optional later if there is a concrete need to control an already-open logged-in browser.

## Requested actions

1. Inspect the target project's current browser automation/tooling.
2. Identify whether Playwright or another browser layer already exists.
3. Propose the smallest integration that supports:
   - deterministic Playwright helpers;
   - Browser Use fallback;
   - promotion of successful exploratory flows into helpers.
4. Suggest a directory/module layout.
5. List dependency changes.
6. Do not perform a large refactor yet.

## Constraints

- Preserve existing automation and tests.
- Prefer low maintenance and low token cost.
- Do not add frameworks merely because they are popular.
- Do not commit, push, deploy, or publish without explicit authorization.
- The target project's own `AGENTS.md` rules take precedence.

## Result

_Not processed yet._
