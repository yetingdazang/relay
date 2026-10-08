# 本地知识库与选择同步

当前方案确认于 2026-10-08。电脑保存完整知识库，Android 手机和平板仅保存选定内容。Git 用于代码、规则和 Codex 任务，笔记另做独立备份。R2 本轮不接入。

## 实际位置

| 用途 | 位置 |
| --- | --- |
| 完整知识库 | E:/OBSIDIAN |
| Relay 任务与代码仓库 | E:/Relay |
| 手机接收暂存 | E:/RelaySync/Incoming/手机 |
| 平板接收暂存 | E:/RelaySync/Incoming/平板 |
| 正式导入笔记 | E:/OBSIDIAN/notes/00-Inbox/手机、平板 |
| 初始完整备份及本机模拟验证 | E:/RelayBackups/20261008-212103 |
| 每日独立备份 | C:/Users/Administrator/RelayNotesBackups |

C: 位于磁盘 0，E: 位于磁盘 1，已确认是两个物理磁盘。每日备份同时保存笔记、插件配置和本地同步运行设置。备份不上传 GitHub。

## 怎样选择给移动端的内容

把笔记和关联附件放入知识库根目录下的以下文件夹：

- 手机同步：仅手机接收。
- 平板同步：仅平板接收。
- 共同同步：两台移动设备接收。
- notes 下其他分类：仅电脑保存，除非你主动放入同步区。

每个同步区都可建子文件夹。图片、PDF、音频等附件必须随笔记放进目标同步区。引用其他未选择的笔记，移动端可能无法打开；需要一起同步相关资料，或保留普通文本说明。

跨目录移动笔记时，优先使用 Obsidian 的移动功能，以更新内部链接。取消下发时，把内容移回电脑专用分类，电脑保留原件，移动端当前同步副本将移除。移动端历史版本可能仍保留旧副本，这不等于安全擦除。

三个下发区域：电脑 Send Only，移动端 Receive Only，先用于阅读。移动端新笔记、截图和需要回传的修改进入本设备收件箱。需要多端直接编辑下发笔记时，另行改为双向并验证冲突处理。

## 手机和平板新笔记怎样汇入电脑

手机的新建笔记目录：notes/00-Inbox/手机。
平板的新建笔记目录：notes/00-Inbox/平板。
每台设备把附件也放进自己的收件箱，例如 notes/00-Inbox/手机/附件。

对应收件箱的 Syncthing 模式：移动端 Send Only，电脑 Receive Only。
电脑接收暂存区与正式笔记区分开。导入工具每 15 秒检查接收区：

- 新笔记和附件复制到正式笔记区，保留路径与附件引用。
- 未变动的文件不重复复制。
- 电脑修改过的文件与移动端新版本冲突时，另存带“同步冲突”的副本。
- 复制时检测电脑目标是否发生变化，检测到变化则保留电脑版本并等待后续导入。
- 移动端删除或清空收件箱，不删除已经导入的正式笔记。
- 不自动整理、改名或重排历史笔记。

电脑离线时移动端继续本地保存；电脑和设备同时在线、能互相连接时补传。当前先配置局域网发现，全球发现、中继和路由器端口映射均关闭。不同网络远程同步尚未配置。

## Android 初次接入

1. 从 Syncthing-Fork 官方发布页安装当前 Android 客户端：
   https://github.com/researchxxl/syncthing-android/releases/latest
2. 先完整保留原 Relay Vault。为新的本地同步方式建立单独的本地 Vault，例如：
   手机：/storage/emulated/0/Documents/Obsidian-Mobile
   平板：/storage/emulated/0/Documents/Obsidian-Tablet
3. 新 Vault 不启用 Obsidian Git。原 Relay Vault 的 Git 自动 Pull/Push 也需在最终切换前停用。
4. 在 Syncthing-Fork 的“显示设备 ID”页面取得该设备 ID。将电脑添加为设备，并在电脑运行配对工具；两端互相确认。
5. 接受电脑提供的三个文件夹，按下表映射路径与模式。不要将完整电脑知识库作为共享文件夹。
6. Obsidian 打开刚创建的本地 Vault。新建笔记默认目录按本设备收件箱设置，附件也放入本设备收件箱。
7. 开启内置 Bases，模板目录可设为共同同步/模板。
8. Android 系统允许同步应用访问这个本地目录；需要可靠后台同步时，按系统提示允许后台运行。

| 角色 | Folder ID | 移动端 Vault 内路径 | 移动端模式 |
| --- | --- | --- | --- |
| 手机 | relay-inbox-phone | notes/00-Inbox/手机 | Send Only |
| 手机 | relay-notes-phone | 手机同步 | Receive Only |
| 手机 | relay-notes-common | 共同同步 | Receive Only |
| 平板 | relay-inbox-tablet | notes/00-Inbox/平板 | Send Only |
| 平板 | relay-notes-tablet | 平板同步 | Receive Only |
| 平板 | relay-notes-common | 共同同步 | Receive Only |

电脑管理地址：http://127.0.0.1:8384。
电脑设备 ID 存在本机 RelayNotes/desktop-device-id.txt，也可在管理页面“操作 → 显示 ID”查看。
配对工具只分享本设备对应区域，不分享另一台设备专用区域。

## 验证顺序

先手机，再平板。每台设备验证：

1. 只收到本设备同步区和共同区，没有另一台设备专用区或电脑专用资料。
2. 打开同步测试笔记和图片，确认附件显示。
3. 在收件箱创建一篇明确命名的新笔记，并贴一张非敏感图片。
4. 在电脑确认相同路径的正式笔记和图片都出现。
5. 在电脑与移动端分别修改测试笔记，确认两份版本被保留。
6. 清理移动端测试收件箱，确认电脑已导入的原件仍存在。
7. 把一篇下发测试笔记移回电脑专用区，确认目标设备移除当前副本，电脑原件仍存在。

2026-10-08 本机两台隔离模拟节点已验证这些传输和保护行为。
8 项数据保护/恢复单元测试通过。真实 Android 设备配对与后台运行尚待验证，不将本机模拟测试当作实际设备成功。

## 自动运行与备份

当前用户登录后通过“Relay Notes Sync”启动项运行：

- Syncthing 后台服务。
- 移动收件箱导入工具。
- 每 24 小时一次完整知识库备份，并逐文件核对 SHA256。
- 电脑离线错过的备份，在下次运行时补做一次。

旧版本备份不自动删除。同步接收暂存区另外保留最多 20 个远端旧版本，清理期 30 天。正式笔记的恢复以独立备份为准。

初始 214 文件完整备份已复制到隔离恢复目录，全部 SHA256 一致。
切换后的最新 84 文件知识库备份也已恢复验证，并备份核对了 10 个本地运行设置文件。
恢复时先恢复到新目录并核对内容，不直接覆盖正在使用的知识库。

## 桌面管理命令

从 PowerShell 7 运行，Python 使用 C:/Program Files/Python313/python.exe。

```powershell
# 查看同步状态，不显示认证值
& 'C:/Program Files/Python313/python.exe' E:/Relay/scripts/notes_sync_status.py

# 指定设备角色进行配对；DEVICE_ID 替换为 Android 显示的 ID
& 'C:/Program Files/Python313/python.exe' E:/Relay/scripts/pair_notes_device.py --role phone --device-id DEVICE_ID
& 'C:/Program Files/Python313/python.exe' E:/Relay/scripts/pair_notes_device.py --role tablet --device-id DEVICE_ID

# 手工启动后台服务
& E:/Relay/scripts/start_notes_sync.ps1

# 立即备份并验证恢复
& 'C:/Program Files/Python313/python.exe' E:/Relay/scripts/relay_notes_backup.py --verify-restore

# 只恢复到一个不存在的新目录，不覆盖正式知识库
& 'C:/Program Files/Python313/python.exe' E:/Relay/scripts/relay_notes_backup.py --restore 'C:/Users/Administrator/RelayNotesBackups/某次备份目录' --destination 'E:/Obsidian-Restore-Check'
```

本地认证材料存于 Windows 用户的 RelayNotes/syncthing 目录。恢复笔记后，本地同步运行设置可从该次备份的 runtime 子目录单独恢复；恢复前先正常关闭同步服务，保留当前运行设置的副本。

## 尚未完成的步骤

- 真实手机、平板安装/配对/同步验证。
- Windows 防火墙已获用户明确授权并完成验证：仅 Syncthing 程序、Private 专用网络、本地网段入站 TCP 22000 与 UDP 21027/22000。真实局域网设备连接仍待验证；当前以太网为专用网络，WLAN 为公共网络，未更改网络类型。
- 旧移动 Vault 停用 Git 自动同步后，再将 Git 分离变更合入远程 main。
- 可选：额外离线备份、跨网络同步、多端直接编辑模式。

原 GitHub main 和历史笔记暂保留，以防旧 Android Git Pull 提前移除笔记。新实现先使用独立代码分支保存。
