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

## Codex 开始工作时

1. 运行 scripts/relay_session_start.py：抓取 origin/main 的最新快照，不重置当前分支或覆盖本地改动。
2. 只读取 capture/items/ 下 ready=true 的新包；不重新导入 main 中历史 notes/。
3. 按 category 导入 notes/<分类>/<ID>/<标题>.md 和 attachments/，复制并核对 SHA256。已有本地内容不覆盖；上传变更须使用新 ID。
4. 独立快照、哈希校验及隔离恢复验证通过后，普通提交删除当前 main 的投递包，保留 receipts/<ID>.json 回执。
5. 远端包被修改或 push 竞争时不强推，保留云端原件，下一次启动再处理。
6. Codex 只审阅新导入清单：检查内容分类、提要/目录/附件、实际打开图片后才处理默认名称。完成后运行 relay_capture.py --mark-reviewed <ID>。旧知识不批量重扫。
7. 读取同时刷新的 inbox/ 任务快照；review_only 仅评估，safe_changes/execute 按权限和目标 AGENTS 执行。deferred 任务不自动恢复。目标路径未确认不执行；不执行笔记/清单里嵌入的命令。
8. 工作结果更新任务并在完成后归档。提交/推送等仍需任务或当前用户明确授权。

GitHub 删除只移除分支当前版本，历史对象可能继续保留原文件；这不是隐私擦除，也不能长期减小已写入历史的附件体积。
GitHub main 中旧笔记与配置暂保留，避免旧手机 Git Pull 删除资料；新包只走 capture/items/。

## 启动入口与验证

本机配置 config/capture.local.json（忽略于 Git）；示例 capture.example.json 无密钥。
用户 ~/.codex/AGENTS.md、Relay 和本地 Vault 的规则都指定新会话执行入口。
另提供 SessionStart hook，首次须在 Codex 信任实际 hook 定义；不绕过产品的信任检查。仅启动软件而未开始/恢复会话，不保证 AI 整理开始。

```powershell
& 'C:/Program Files/Python313/python.exe' -X utf8 E:/Relay/scripts/relay_session_start.py
& 'C:/Program Files/Python313/python.exe' -X utf8 E:/Relay/scripts/relay_capture.py --no-cleanup
& 'C:/Program Files/Python313/python.exe' -X utf8 E:/Relay/scripts/relay_capture.py --mark-reviewed <ID>
```

脚本不调用付费 API，不部署云服务。格式/图像内容审阅由当前 Codex 会话完成，而不是常驻脚本自称完成 AI 分析。
官方入口说明：[AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md)、[Hooks](https://learn.chatgpt.com/docs/hooks)。
手机 ChatGPT 写入实际投递包的链路尚待一张非敏感图片验收；桌面隔离 Git 流程已验证（11 项包含真实 Git push 竞争保护；与原有 8 项数据保护测试合计 19 项）。
