---
title: ChatGPT 与 Obsidian 双向同步测试
date: 2026-10-08
tags:
  - relay
  - sync-test
status: testing
---

# ChatGPT 与 Obsidian 双向同步测试

这条笔记由手机 ChatGPT 通过 GitHub Relay 写入，用于测试 **ChatGPT → GitHub → 安卓 Obsidian** 的同步。

## 第一步：拉取验证

在安卓 Obsidian Git 插件中执行 **Git: Pull**，确认你能在 `notes/00-Inbox/` 看到这篇笔记。

## 第二步：反向写入验证

请在本文件末尾增加这一行（不要修改上面的内容）：

> 来自安卓 Obsidian：双向同步测试成功

然后执行 Git 插件的提交与推送（Commit-and-sync 或 Backup/Push；具体命令以插件中实际显示为准）。

返回 ChatGPT 后告诉我「已推送」，我会读取 GitHub 上的这篇笔记核验。

---
注意：本笔记仅用于测试，后续可删除或归档。
