# Relay × Obsidian（Android）配置指南

## 设计

Relay 仓库整体作为 Obsidian Vault；仅 `notes/` 用于知识笔记。原有根目录 `inbox/`、`archive/`、`AGENTS.md`、`scripts/` 等仍归 Codex 工作流使用，不要在 Obsidian 中移动或删除。

## 安卓端初次配置

1. 在 Obsidian Android 中开启 **Settings → Community plugins**，关闭 Restricted mode（如有），浏览并安装 **Obsidian Git**。安卓兼容性随插件版本、系统权限和 Git 认证方式而变化。
2. 推荐先备份已有 Vault。不要直接将已有笔记库覆盖为 Relay。
3. 使用插件提供的 Clone 功能（若当前版本支持）克隆 `https://github.com/yetingdazang/relay.git` 到一个新的本地 Vault；若插件无法克隆，则先使用 Android Git 客户端（如 Termux）克隆，再用 Obsidian 的“打开文件夹作为仓库/Vault”打开克隆目录。具体目录访问权限取决于 Android 版本。
4. 私有仓库通过 GitHub Personal Access Token (fine-grained，限定 Relay 仓库的 Contents 读写权限) 或支持的 SSH 方式认证。**令牌仅保存在手机的凭据设置中，绝不写进笔记、仓库或聊天消息。**
5. 初次先手动 Pull，确认能打开 `notes/README.md`，再创建 `notes/00-Inbox/mobile-sync-test.md`，手动 Commit/Push，检查 GitHub 是否出现文件。
6. Git 同步成功后再按需设置定时 Pull/Push。移动网络、后台限制和多设备并发编辑可能导致冲突，建议每次编辑前 Pull、结束后 Push。

## ChatGPT 和 Codex

- ChatGPT 新笔记写入 `notes/00-Inbox/`，长期整理内容放 `notes/01-Knowledge/` 或 `notes/02-Projects/`。
- ChatGPT 读取/更新已有文件时先获取最新版本；修改前确认用户意图，不覆盖未同步的手机本地变更。
- Codex 任务交接仍用根目录 `inbox/`，执行权限仍遵循根目录 `AGENTS.md`。
- Codex 在电脑上克隆仓库后可直接阅读 `notes/`；修改笔记后需 Git 提交并推送，手机端 Pull 才能看到。

## 注意事项

- GitHub 私有仓库不等于端到端加密存储，不要上传账号密码、API Token、Cookie 或敏感个人记录。
- Obsidian 可能会显示仓库根目录的 Markdown 文件，这是预期行为；主要笔记位于 `notes/`。
- 建议在 `.gitignore` 忽略 Obsidian 的工作区与缓存等设备特定文件；不强制共享 `.obsidian/` 配置。
- 同一文件在不同设备上同时修改可能产生 Git 冲突，切勿在未核对差异时强制覆盖。
