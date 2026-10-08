# GitHub 临时投递与本地知识库

手机 ChatGPT 生成的新笔记/图片只在这里临时排队。正式知识库是 E:/OBSIDIAN，代码和 Codex 任务在 Relay。不要将完整本地 Vault 推回 GitHub。

## 手机端约定

请手机 ChatGPT 先读取 AGENTS.md 和 docs/GITHUB_CAPTURE.md；使用 main 分支。
每次新增一个 capture/items/<唯一ID>/ 投递包。不要把知识笔记写进 inbox/；inbox/ 是 Codex 任务。

投递包包含 note.md、attachments/（可选）和 manifest.json。
ID 用日期时间与简短英文后缀，例如 20261008-235000-ai-notes，不重复使用旧 ID。
先上传笔记和实际附件字节，最后写 ready=true 的 manifest.json；未完成的包不会导入。

```json
{
  "version": 1,
  "id": "20261008-235000-ai-notes",
  "ready": true,
  "title": "AI 使用经验",
  "category": "knowledge",
  "attachments": [{"path": "attachments/经验截图.png"}]
}
```

note.md 按 docs/NOTE_FORMAT.md 写：提要、可点击目录、正文、文末原始附件。
包内图片用 ![[attachments/经验截图.png]] 或 ![](attachments/经验截图.png)。导入后同一相对目录结构保留。
分类：inbox（待整理）、knowledge（长期知识）、projects（项目笔记）、resources（参考资料）、archive（归档）。不确定就 inbox。

## 图片上传能力边界

Markdown 写入、二进制图片上传需要分别实际验证，不能根据“有 GitHub 应用”推定全部可用。
若手机端可创建 GitHub blob/tree/commit，上传真实字节，再提交投递包。
若仅支持文本文件且能取得附件真实 Base64 字节，可以上传 attachments/经验截图.png.b64：

```json
{"path":"attachments/经验截图.png.b64","encoding":"base64","name":"经验截图.png"}
```

该对象代替 attachments 数组中的二进制对象，桌面接收后还原原始字节。可填 sha256，桌面会额外校验。
不能读取真实图片字节时，保持 ready=false，报告缺失附件；可把下载到手机的原图直接放入当前本地 Vault，经 Syncthing 同步。
不要把 ChatGPT 临时图片 URL 当作已上传附件。不要捏造 Base64/校验值或将未知图像内容按文件名猜测命名。
每文件上限 25 MiB、每包 100 MiB，大视频/音频暂不走本通道；R2 未启用。

## 自动接收：不消耗 AI token

本机采用启动时执行一次的本地 Python 程序 `scripts/relay_capture_watch.py --once --quiet`，不调用模型/API，不创建 Codex 自动 AI 任务，也不把笔记正文或接收报告放进模型上下文。

1. 从桌面“ChatGPT(走代理)”入口打开 Codex 时，start_codex_relay.ps1 沿用原代理启动器并附带执行一次收信。收信结束即退出，不登录自启、不常驻检测。原有 Syncthing/备份登录入口不包含收信。
2. 拉取 origin/main 最新快照，只接收 capture/items/ 的 ready=true 新包。保留正文与原始图片字节，哈希验证、防重复和不覆盖本地编辑继续生效。
3. 支持的明确 category 直接对应五个 notes/ 分类；缺失、未知或无效分类统一放 notes/00-Inbox/，不调用模型猜测分类。格式清单和附件路径可以用代码检查；图像含义、长文本分析和语义重命名不自动执行。
4. 独立快照、SHA256 和隔离恢复 PASS 后，普通 Git 提交清理当前 main 投递包并留回执。网络/清理失败保留本机结果和云端原件，下次使用启动入口或手动接收时重试，不强推、不删除未验证原件。未 ready 的包与格式错误等待下一次启动或手动接收。
5. 无新包时不重新备份全部知识库，也不重复读取历史笔记；完成后只在本机日志记录结果。
6. 待整理的导入资料保留在本机状态清单，攒多后用户可以说“整理新收到的笔记”。届时才调用 AI 读取 `relay_capture.py --pending` 清单并批量审阅，完成后逐个 --mark-reviewed。已有历史笔记不批量重扫。
7. Codex 的 inbox/ 任务仍遵循 execution_policy 和目标 AGENTS；收信程序不执行任务。AI 任务执行和深度整理本身会消耗 token，不能归为零 token 收信流程。

GitHub 删除只移除分支当前版本，历史对象可能继续保留原文件；这不是隐私擦除，也不能长期减小已写入历史的附件体积。
GitHub main 中旧笔记与配置暂保留，避免旧手机 Git Pull 删除资料；新包只走 capture/items/。

## 启动入口与验证

本机配置 config/capture.local.json、config/codex_launch.local.json 均被 Git 忽略。桌面“ChatGPT(走代理)”已改为 PowerShell 7 调用 start_codex_relay.ps1，现有代理参数不变。原快捷方式和配置备份在 RelayNotes/before-on-demand-intake-20261009。
收信器没有登录自启和常驻进程。Windows Relay Notes Sync 仍只启动原有手机同步与备份。普通开始菜单/任务栏原生 App 入口不经过此脚本；需要自动收信时使用桌面上述入口。重复点击不会并发启动多个一次性接收器。
旧 SessionStart 模型报告 hook 保持移除；不会自动让 AI 审阅笔记。失败下次启动/手动接收重试，不在后台持续轮询。

```powershell
# 手动立即接收，仍然不调用 AI
& 'C:/Program Files/Python313/python.exe' -X utf8 E:/Relay/scripts/relay_capture_watch.py --once
# 查看待批量整理清单，不拉取网络或调用 AI
& 'C:/Program Files/Python313/python.exe' -X utf8 E:/Relay/scripts/relay_capture.py --pending
# 使用现有代理打开 Codex 并附带收信一次
& E:/Relay/scripts/start_codex_relay.ps1
# 可选静默会话入口，不输出模型上下文
& 'C:/Program Files/Python313/python.exe' -X utf8 E:/Relay/scripts/relay_session_start.py --quiet
```

本机日志为 RelayNotes/capture-watch.log，最近一次结果 capture-last-run.json，一次性收信结果 capture-last-run.json。失败类型记录不显示认证值。停用时仅结束命令行明确包含 relay_capture_watch.py 的进程并移除启动调用，不删除笔记。
本次 26 项测试通过，包含新启动/重启、子进程不重复、离线重试、静默输出、分类回退及原有完整性与 Git 竞争保护；实际后台启动检查 PASS，单实例与 Windows 登录入口核对通过；真实手机 PNG 链路已在 2026-10-09 完成。官方 [Hooks 文档](https://learn.chatgpt.com/docs/hooks) 说明 stdout 可进模型上下文且空输出成功，因此此流程不采用输出笔记的 hook。

## 2026-10-08 真实桌面验收

投递包 20261008-capture-desktop-smoke 实际上传 main，接收 note.md 与 99 字节 PNG 到本地 Inbox；图片 SHA256 一致，隔离恢复通过，远端投递包已普通提交清理，仅保留 receipts 回执。原图 32×32 蓝色方块已实际打开，Obsidian 笔记/目录/嵌入核对通过。本地测试笔记和图片随后核对哈希删除，不留测试杂项。手机 ChatGPT 的真实写入/图片字节上传已于 2026-10-09 验收；2026-10-09 已改为 Windows 后台程序，无需原生 hook。

## 2026-10-09 手机真实 PNG 验收

手机提交 3ceb002（笔记/PNG）及 491a152（ready 清单）。桌面入口接收 20261008-235200-relay-mobile-image-test 至本地 Projects，核对 187 字节、128×40 蓝绿紫橙图及 SHA256 c5bc88385b00f8067e642d6b5cef366eb37de10eaf1af09b5d9fd082e70876bf。目录和相对附件路径通过，实际打开 PNG 与 Obsidian 笔记。独立快照 notes-20261009-000400-865523 的 73 文件、14 项设置及隔离恢复 PASS；普通清理提交 f33db9f 保留回执，原知识/附件未删除。手机已连接，Syncthing completion=100，needBytes=0、needItems=0、无错误。保留本地验收记录供用户查看；手机 Obsidian 实际渲染需用户查看，本次不推定任意大文件与不同应用权限均已验证。
