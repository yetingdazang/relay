# Relay 手机端真实 PNG 投递验收记录

> [!summary] 提要
> 本笔记用于验收手机 ChatGPT 经 GitHub Relay 投递知识笔记和**真实 PNG 文件字节**的能力，不依赖临时图片链接。本次附图是专门制作的非敏感四色测试图，不含个人资料、凭据或原始聊天记录。GitHub 上传成功不等于桌面导入成功，仍需由 Codex 在本机核验。

## 目录

- [[#测试目的|测试目的]]
- [[#投递流程|投递流程]]
- [[#验证要点|验证要点]]
- [[#限制与下一步|限制与下一步]]
- [[#原始资料与附件|原始资料与附件]]

## 测试目的

- 验证 `capture/items/<唯一ID>/` 可携带 `note.md`、PNG 附件和最后写入的 `ready=true` 清单。
- 验证上传的是 PNG 的原始文件字节，而不是 ChatGPT 临时图片地址、图片说明文字或伪造的 Base64。
- 保持永久 Obsidian Vault 仅在本地；GitHub 仅作临时投递队列。

## 投递流程

1. 手机端 ChatGPT 读取 Relay `main` 的 `AGENTS.md`、`docs/GITHUB_CAPTURE.md` 和 `docs/NOTE_FORMAT.md`。
2. 在 `capture/items/` 创建唯一投递包，先提交笔记与 `attachments/relay-capture-test.png` 的真实字节。
3. 最后写入 `manifest.json`，设置 `version=1`、`ready=true`、`category=projects`，登记附件相对路径。
4. 桌面 Codex 下次启动或恢复会话时运行项目会话入口，按规则导入本地 Vault，验证哈希并生成收据，审阅后标记完成。

## 验证要点

- 测试图尺寸：128 × 40 像素；依次为蓝、绿、紫、橙四色块。
- PNG 文件大小：187 字节。
- PNG SHA-256：`c5bc88385b00f8067e642d6b5cef366eb37de10eaf1af09b5d9fd082e70876bf`。
- 图片应当能被 PNG 解码器正常打开；Codex 导入后应检查实际图片、Obsidian 嵌入路径与 SHA-256。
- **验收边界**：此笔记只记录云端投递；本地接收、备份与清理应以桌面 Codex 的实际运行结果为准。

## 限制与下一步

- 禁止在投递包中放密码、令牌、私钥或完整本地 Vault。
- 不使用临时图片 URL 代替真实文件；上传失败应保持 `ready=false` 并说明原因。
- 桌面端完成核验后，按仓库流程生成 `receipts/<ID>.json` 并安全清理远端临时投递包；Git 历史并非隐私擦除手段。

## 原始资料与附件

- 规则来源：仓库 `AGENTS.md`、`docs/GITHUB_CAPTURE.md` 和 `docs/NOTE_FORMAT.md`（`main`，2026-10-08 读取）。
- 附件说明：非敏感、自行生成的 PNG 四色链路测试图，不是任何个人真实截图。
- ![[attachments/relay-capture-test.png]]
