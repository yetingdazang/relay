# 本地知识库与手机全库同步

2026-10-08 用户明确要求清理测试资料，并将所有知识文件同步到手机；随后选择“全库双向同步，编辑和删除同步，保留备份”。本方案取代之前的三个选择同步区与收件箱导入。

## 位置与同步配置

| 用途 | 位置或设置 |
| --- | --- |
| 完整知识库 | E:/OBSIDIAN |
| Relay 代码与任务 | E:/Relay |
| 手机同步项 | relay-vault-phone，Relay 全库 |
| 两端类型 | Send & Receive |
| 电脑路径 | E:/OBSIDIAN |
| 手机路径 | 用户当前 Obsidian 打开的本地知识库根目录，不假定 Documents 路径 |
| 独立备份 | C:/Users/Administrator/RelayNotesBackups |
| 当前管理地址 | http://127.0.0.1:8384 |

笔记、图片、PDF、其他附件、首页、模板、Bases 列表与 Excalidraw 文件均包含。
电脑 `.stignore` 排除 `.obsidian`、`.git`、`.trash`、`.stversions`、本机 AGENTS 与系统临时文件。手机端建议采用相同忽略模式。插件、认证与默认目录不会从电脑覆盖手机。
GitHub main 保留原状，笔记不重新进入 Git。代码成果仍保存到 codex/local-notes-sync。

## 已执行的迁移

1. 清理前备份 notes-20261008-230512-925634：87 文件与 11 项运行设置验证通过；隔离恢复哈希一致。
2. 核对测试文件内容及备份后删除 21 个测试/过时文件，包括原 Git 同步测试、模拟节点测试、真实手机测试及其图片、三套旧入口与重复模板、未使用的空 Bases 视图。原知识笔记、原始大图、模板与分类列表保留。
3. 暂停并移除电脑旧五个 Syncthing 同步项的配置，不删手机本地资料；保存旧配置到清理前备份目录。
4. 移除旧收件箱中的四个测试暂存文件，先核对备份。
5. 新建 relay-vault-phone，分享给已配对手机。电脑类型 sendreceive，版本保留 simple/keep=20/cleanoutDays=0。
6. config/notes_sync.local.json 的 incoming 设为空。停止旧导入进程后重启；后台只做每日独立备份，防止旧暂存文件再写入全库。
7. 更新首页、本机规则与设备说明。真实手机全库接入待用户完成。
8. 清理后备份 notes-20261008-231759-864229：65 文件、11 项运行设置及隔离恢复验证通过；保留的 16 个原知识/附件文件 SHA256 与清理前一致。首页与设备说明目录链接验证通过，正式同步项无错误。

首次合并时手机旧测试副本可能重新进入电脑。确定清单保存在本机 RelayNotes/full-sync-cleanup-pending.json；只处理清单中的测试文件，手机其他资料保留。全库同步完成后再次清理并确认两端。

## 手机操作

1. Syncthing-Fork 中移除“手机同步、共同同步、手机收件箱”三个旧共享项；仅删除同步配置，保留本地文件。
2. 添加标签“Relay 全库”，ID relay-vault-phone，目录选择当前 Obsidian 的整个知识库根目录，类型“发送和接收”，共享给 Relay 电脑。
3. 忽略模式建议：/.obsidian、/.git、/.trash、/.stversions、/AGENTS.md。电脑已配置。
4. 两端先正常合并。看到完整首页、notes 分类、原始图片与模板后，由 Codex 再清理已确认的测试副本。
5. 手机新笔记位置仍可用 notes/00-Inbox/手机，附件 notes/00-Inbox/手机/附件。Templates 改为 notes/03-Resources/Templates，并启用内置 Bases。
6. 删除和移动会传播；有疑问先恢复到独立目录核对，而不对当前 Vault 使用覆盖按钮。

## 自动运行与恢复

当前用户登录后通过 Relay Notes Sync 启动 Syncthing 与后台备份助手，每 24 小时备份并核对 SHA256。错过时在下次运行补做。旧快照保留。
C: 磁盘 0，E: 磁盘 1，是两个物理磁盘。

```powershell
& 'C:/Program Files/Python313/python.exe' E:/Relay/scripts/notes_sync_status.py
& E:/Relay/scripts/start_notes_sync.ps1
& 'C:/Program Files/Python313/python.exe' E:/Relay/scripts/relay_notes_backup.py --verify-restore
& 'C:/Program Files/Python313/python.exe' E:/Relay/scripts/relay_notes_backup.py --restore 'C:/Users/Administrator/RelayNotesBackups/某次备份目录' --destination 'E:/Obsidian-Restore-Check'
```

runtime 设置备份包含本地认证材料，不上传 GitHub。恢复运行设置前正常关闭 Syncthing，并备份当前设置。版本保留仅覆盖收到的远端修改，不能代替独立快照。

## 验证与待办

旧选择同步阶段：8 项数据保护/恢复测试、两台隔离本机节点测试通过；真实手机笔记与 PNG 自动导入，哈希一致且电脑 Obsidian 显示正常；用户确认电脑下发文字和图片手机显示正常。
当前全库阶段：电脑配置、清理后文件哈希与备份验证；手机接入、最终合并清理与全库实际同步状态仍待完成。
旧 verify_notes_sync.py 仅适用于无真实设备的旧选择同步测试配置，不得用于当前正式 Vault。
平板尚未配对。后台持续运行、离线补传和真实设备恢复仍待验收。
当前只使用局域网发现；全球发现、中继与路由器映射关闭。不同网络远程同步尚未配置。

防火墙已明确批准并验证：仅 Syncthing 程序、Private 网络、本地网段入站 TCP 22000、UDP 21027/22000。以太网为 Private，WLAN 为 Public，未改网络类型；实际手机连接由电脑主动发起已成功。
旧 Android Git 自动同步停用仍需确认，之后才处理远程 main 合并，防止旧 Vault Pull 收到笔记删除。
