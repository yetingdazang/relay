---
status: unread
target_project: relay
created_at: "2026-10-08T21:00:00+08:00"
execution_policy: execute
summary: "完成 Android 手机、平板与本地知识库的选择同步配对及实际验证"
decisions:
  - "Git 仅管理代码、规则与 Codex 任务；知识库本地保存并独立备份"
  - "电脑完整 Vault: E:/OBSIDIAN；Relay: E:/Relay"
  - "用手机同步、平板同步、共同同步文件夹控制下发"
requested_actions:
  - "先读 docs/LOCAL_NOTES_SYNC.md 和 config/notes_sync.local.json"
  - "获取真实 Android 设备 ID，先手机后平板配对"
  - "验证笔记、图片、离线补传、冲突保留、删除保护和取消下发"
  - "旧 Android Vault 停用 Obsidian Git 后再合入远程 main"
constraints:
  - "用户已全权授权此架构切换；已明确批准 Syncthing 仅在 Private 网络向本地网段开放 TCP 22000 与 UDP 21027/22000，规则已验证"
  - "只分享指定文件夹，不全库同步，不覆盖或删除旧移动 Vault"
  - "本机模拟节点成功不代表真实 Android 已验证"
  - "保留笔记、图片和旧备份，不改写 Git 历史或强制推送"
---

# Android 本地知识库配对与验收

## 已完成

- 214 文件迁移前完整备份及逐文件恢复验证。
- E:/Relay 与 E:/OBSIDIAN 本地分离，保留所有原始笔记与附件。
- Syncthing 2.1.6 官方安装包 SHA256 校验及 Windows 安装。
- 五个同步区域、移动收件箱安全导入、当前用户登录启动、每日独立磁盘备份。
- 8 项数据保护/恢复测试。
- 两台隔离本机节点：定向分发、共同区、图片哈希、上传导入、冲突保留、清理收件箱保留正式笔记、取消下发保留电脑原件。

## 待完成

实际 Android 安装/配对及局域网连通验证尚待完成。防火墙已按批准范围配置；以太网为 Private，WLAN 为 Public，未更改网络类型。
本地接口运行在 http://127.0.0.1:8384。
用 scripts/notes_sync_status.py 检查现状。
没有真实设备 ID 时不得假设已经配对完成。

## 原系统切换

保留旧手机/平板 Vault。先停用旧 Vault 的 Obsidian Git 自动同步，再处理远程 main 的 notes/.obsidian 停止跟踪。
本轮代码先保存在独立 Git 分支，避免旧 Android Pull 接到笔记删除。
