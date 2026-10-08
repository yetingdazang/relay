---
status: in_progress
target_project: relay
created_at: "2026-10-08T21:00:00+08:00"
execution_policy: execute
summary: "完成手机全库双向同步、清理确认的测试副本并验证备份；平板另行确定"
decisions:
  - "用户已明确选择完整知识库双向同步；手机编辑和删除也同步到电脑，保留备份"
  - "知识库 E:/OBSIDIAN；代码与任务 E:/Relay；GitHub main 暂不合并"
  - "新同步项 relay-vault-phone；旧三个手机共享项与旧导入模式已退休"
requested_actions:
  - "手机移除旧三个同步配置但保留本地文件；添加 relay-vault-phone，选择现有知识库根目录，Send & Receive"
  - "确认手机忽略设备配置，启用 Bases，模板目录改为 notes/03-Resources/Templates"
  - "首次合并后读取本机 RelayNotes/full-sync-cleanup-pending.json，只清理其中确认的测试副本，再验证两端目录和原图"
  - "验证手机后台运行、离线补传及恢复；平板同步范围需按用户后续选择配置"
  - "确认旧 Android Vault 停用 Git 自动同步后再处理远程 main"
constraints:
  - "用户授权删除测试资料，不删除其他原笔记和原附件；保留清理前快照"
  - "不共享 .obsidian/Git/回收站/版本缓存，不覆盖手机设备设置"
  - "不重新批量命名或整理历史知识文件，不改写 Git 历史或强制推送"
---

# 手机全库双向同步与清理

## 已完成

- 保留旧 Relay 任务系统、规则与 GitHub 主分支。
- 原选择同步已真实验证双向笔记/图片；用户确认手机显示正常。
- 切换前 87 文件与 11 项运行设置备份、隔离恢复验证通过。
- 清理 21 个测试/过时文件与四个暂存测试文件；原知识内容、模板与五个分类列表保留。
- 电脑旧五个同步项已移除配置，新 relay-vault-phone 分享给已配对手机，sendreceive、版本保留 20、按天清理关闭。
- 旧 incoming=[]，后台只备份，避免旧暂存再导入；首页与说明已更新。
- 清理后 65 文件及 11 项运行设置备份、隔离恢复验证通过；16 个保留原文件哈希一致，正式同步项无错误。

## 待完成

手机全库已实际接入，completion=100、remoteState=valid；首次合并回流的 11 个测试文件已核对原备份哈希后删除。仍需验收后台运行/离线补传，平板尚未配对。
配对身份存于忽略的 config/notes_sync_devices.local.json。手机旧共享项移除时只删配置、保留文件。
备份及清单见 docs/LOCAL_NOTES_SYNC.md；不把快照或运行认证材料提交到 Git。

## 手机全库验收更新

2026-10-08 23:32 用户确认配置后，电脑已观测全库 100%。首次合并删除测试前快照 notes-20261008-233228-351971（87 文件、11 设置，隔离恢复 PASS）。
