# Relay GitHub 图片预览桥（已启用）

## 解决的问题

手机 Obsidian 可以通过 Git 把完整图片上传到私有仓库，但部分 GitHub 文本连接工具无法返回体积较大的 JPG/PNG 二进制内容。这个工作流让 ChatGPT 可以在不重新上传图片的前提下，通过小型 UTF-8 Base64 文件读取图片内容。

### 数据路径

`notes/` 下**新添加**的图片 → GitHub Actions → 按阅读顺序生成较小 JPEG 分段 → `config/image-bridge/<路径哈希>/manifest.json` 与 `tile-xxx.b64.txt` → ChatGPT 按需读取。

- 原图不修改、不删除、不改变画质。
- 预览保存在**同一个私有仓库**；不会发往第三方识图、OCR 或 AI API。
- 处理的是 Git **新增（added）** 图片，**不是**每次修改或每次对话扫描全部历史文件。
- 首次安装已经针对以前上传的那张小黑盒长截图执行了**一次定向回填**。
- 不会自动把截图全文转写成笔记，也不会自动给旧文件改名；命名遵循 `docs/KNOWLEDGE_FILE_NAMING.md` 的增量规则。

## 工作流与脚本

- 工作流：`.github/workflows/relay-image-preview.yml`
- 生产脚本：`scripts/relay_image_preview.py`
- 输出目录：`config/image-bridge/`
- 手工运行：GitHub 仓库 → Actions → Relay image previews → Run workflow。可填 `image_path` 为想补处理的 **一张** `notes/` 下图片路径；不填则不扫描旧图片。

GitHub Actions 需要仓库启用 Actions，并允许它使用具有 `contents: write` 权限的 `GITHUB_TOKEN`。若自动运行失败，查看仓库 Actions 执行记录。

## 给 ChatGPT / Agent 的读取方法

1. 根据图片在 `notes/` 下的相对路径计算 SHA-256，取前 20 位十六进制，定位 `config/image-bridge/<hash>/manifest.json`；如果不知道哈希，可以列出 **缓存目录索引** 来找到 manifest，而不是扫描旧原图。
2. 从 manifest 中读取 `source`、`tile_count`、`truncated` 以及 `tiles` 列表。
3. 按需读取小文件 `tile-001.b64.txt` 等。每个文件是一条 Base64 JPEG 文本，可解码成 `image/jpeg` 展示给视觉模型。
4. 对于长图，按 tile 顺序处理；**不要只阅读第一页就声称已读完整图**。
5. 原始图片依然以 Obsidian 笔记中的 `![[原图.jpg]]` 链接为准，预览文件只是机器读取缓存。

> 这条桥接路径也可供其他只能读取 UTF-8 文本的连接工具使用。对于本来能直接读取二进制图片的桌面 Codex，优先读取原图，避免不必要的额外预览处理。

## 资源与限制

- 最宽 960 像素；分段高度 1024 像素；每片约不超过 240 KiB JPEG（对应 Base64 文本约 320 KiB），以避免 GitHub 内容 API 的大文件响应限制。
- 单张图片最多 96 段；manifest 的 `truncated=true` 表示因上限而未生成全部内容，不能假装已经读取完整文件。
- 超过 40 MiB、无法解码或不受支持的图片将跳过；此时不产生 manifest。
- 生成的预览也会随 Git 下载到手机，因此缓存会增加仓库体积；**只有需要查看时才读取图片分片，避免浪费 Token**。
- 不要把私人密钥、密码或敏感截图放在不适合保存它们的仓库里；私有 GitHub 仓库不是端到端加密存储。
- 若手机端显示 non-fast-forward，执行 Pull 合并后再 Push；**不要强制推送**。

## 技术说明

在 `push` 事件中读取 push 的 `before/after` 提交差异，只选 `--diff-filter=A` 文件。脚本保留每个源路径对应的 manifest，用于避免重复预览。推送缓存时，工作流自动处理正常的并发 Git 更新，但不强制覆盖主分支。

旧的 `scripts/image_preview_bridge.py` 试验脚本已删除；请统一使用上述正式脚本。


## 生命周期与自动清理（已启用）

**这些 Base64 分片是临时缓存，不是需要永久同步到手机的知识资料。**

- 完成图片分析、将有效知识写入 `notes/` 并验证后，**立即删除该图片对应的 `config/image-bridge/<路径哈希>/` 预览目录**，原始图片仍保留。
- 为防用户没有再次回来要求分析，额外设置 **7 天过期兜底**。GitHub Actions 每日运行 `.github/workflows/relay-preview-cleanup.yml`，只扫描预览缓存的 manifest，按 Git 历史中的生成时间判断是否过期。超过 7 天的缓存删除，未过期且未确认分析完成的缓存保留。
- 可在 GitHub Actions → Relay preview cleanup → Run workflow 的 `completed_source` 中输入已处理的某张 `notes/` 下图片路径，立即清理对应分片。也可在仓库完整克隆后运行 `python scripts/cleanup_image_previews.py --completed-source 'notes/路径/图片.jpg'`。
- 自动清理不涉及 `notes/` 的原图，也不会清理新笔记、索引或其他业务文件。
- 完成清理会产生一个正常 Git 提交；手机 Obsidian Pull 后这些临时文件不会再占用当前工作目录空间。
- **重要：Git 删除只减少当前版本与后续克隆的文件量，不会自动抹去历史提交内的二进制分片。** 对于真正长期增长的附件，后续应把原图与预览放在独立的对象存储或有 TTL 的临时对象存储，GitHub 仅留图片引用/索引。历史压缩/重写涉及所有设备同步和密钥泄露处理，不在日常清理工作流内自动执行。

### GitHub 和独立存储的长期分工

- GitHub：Markdown、Agent 规则、项目任务、索引和小型配置。
- 独立附件存储（待选型）：图片、PDF、视频与大二进制；有持久化原图及临时预览的不同生命周期策略。
- Obsidian：笔记体验、与外部附件的可靠链接；迁移时需要先验证离线访问和链接可用性。
- ChatGPT/Codex：只按任务读取必要资料，整理成果后及时清理临时缓存。

