---
status: unread
target_project: "codex-global-instructions"
created_at: "2026-10-11T21:10:00+08:00"
execution_policy: safe_changes
source: mobile-chatgpt
---

# 为小游戏与小工具开发设置 Codex 默认行为规则

## Summary

用户主要使用 Codex 开发小游戏、小工具。当前的主要问题：修改一处游戏机制或功能之后，Codex 经常擅自在游戏 UI 中添加解释性小字、备注、标签、公告或更新提示，并在后续开发和对话中反复强调这次修改。用户不希望因此增加繁琐的审查、完整 diff 审查、PR 审查、重复自检等流程。

目标：让 Codex 将开发需求视为实现指令，而不是游戏里需要展示的文案；保持原有 UI 风格，只添加功能真正需要的反馈；开发和最终回复简洁、真实，验证与变更规模相称。

## Decisions

- 这是一套面向用户日常 **小游戏与小工具项目** 的通用 Codex 行为规范，而非仅为 Relay 项目服务。
- 优先把规则合并至本机真正生效的 Codex 用户级全局 `AGENTS.md`（定位实际路径，通常在 Codex 用户配置目录内）；不要因为任务经由 Relay 传递，就把这套通用开发规则塞进 Relay 项目的 `AGENTS.md`。
- 保留已有有效的全局/项目级规则，不覆盖无关内容；出现直接冲突时说明冲突。
- 不引入额外的强制审查阶段、重复自检或无关测试；必要的轻量验证和真实错误报告仍要保留。

## Requested actions

1. 在本机确认 Codex 正在使用的用户级全局指令文件的实际路径，并读取已有内容。不要猜测或覆盖未知文件。
2. 将下方规则合并为单个简洁的通用章节，保持原有规则；如已有等价规则则精简合并，避免重复。
3. 对这一配置变更只做必要的检查以确认文件可读取且规则已正确写入；不要扩展为代码重构、全项目审查或额外的自动化流程。
4. 用简短中文向用户说明更改的文件路径、规则作用，以及任何未完成事项。

## Rules to add

### Development Principles
- Treat user requests as implementation instructions, not content to display in the product.
- Focus on implementing the requested functionality.
- Preserve existing behavior and design unless changes are necessary or explicitly requested.
- Avoid unrelated modifications and overengineering.

### UI and In-Game Text
- Do not add explanatory small print, footnotes, annotations, badges, notices, or update announcements unless needed for actual use.
- Never add UI text merely to highlight, explain, or advertise a recent change.
- Do not repeat development instructions in the game interface or overemphasize earlier modifications in later tasks.
- Avoid redundant descriptions, reminders, labels, and tooltips.
- Keep player-facing text natural, concise, and consistent with the product's intended style.
- Preserve necessary gameplay feedback, controls, accessibility information, and error messages.
- Do not remove existing useful text without reason.
- When the user explicitly requests story text, narrative, copywriting, help text, or UI content, implement it normally rather than suppressing it.

### Code Quality
- Comment only on non-obvious intent, constraints, or reasons.
- Remove temporary experiments, obsolete comments, and abandoned implementations.
- Prefer simple, maintainable solutions.
- Avoid unnecessary abstractions and unrequested features.

### Workflow and Communication
- Do not introduce additional review stages, mandatory full-diff audits, repeated self-audits, PR checklists, or redundant process.
- Perform only validation appropriate to the change.
- Keep final responses concise and factual.
- Report actual errors, limitations, unfinished work, and tests actually run.
- Do not repeatedly emphasize previous modifications.

## Constraints

- These rules govern unrequested explanatory text; **they must not prohibit** legitimate game narrative, deliberate design copy, required UI and accessibility feedback, or functionality explicitly requested by the user.
- Do not modify any existing game or utility project in this task.
- No extra lint/test/PR pipelines or automatic review gates.
- Do not erase existing settings, credentials, or other instructions.
- Do not commit, push, or deploy any local project as part of this configuration task.
- If global instructions cannot safely be located/changed, report the blocker rather than modifying an unrelated file.

## Useful context

用户的典型诉求：例如只要求调整 Boss 的攻击频率，Codex 应改变实际游戏行为，而**不应**顺手增加“攻击频率已优化”“本次更新”等游戏内小字、标注或公告。对话中也不需要以后每次都重新强调该变化。用户不追求额外审查；只要足够的正常验证。

## Result

_Not processed yet._
