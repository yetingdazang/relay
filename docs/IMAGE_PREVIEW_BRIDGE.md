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
