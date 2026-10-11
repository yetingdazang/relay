# 知识处理流程

> [!summary] 提要
> 新资料先接收，再消化，最后形成可复用知识。网页剪藏与手机 ChatGPT 共用这条流程；专业资料独立保存。原文与提炼结果用链接关联，保留附件。

## 每天怎么用
1. 先收集：Edge 剪藏选择“Relay · 网页沉淀”；手机说“按 Relay 最新投递协议，把这份资料发到沉淀池”。
2. 在首页打开“沉淀池”。读资料时只需改状态为“阅读中”，写下“为什么留下 / 想解决什么”。标签可暂时留空。
3. 攒一些后，指定几篇或说“整理这批新投递”：提取有用结论、适用条件、关键词与未解问题。正式知识另存提炼池，链接回原文；原文改“已提炼”。没价值的资料可保留待定，不强行提炼。
4. 开发前从“主题导航”找相关知识与专业资料；项目页负责串联，不复制整篇资料。

## 目录与状态
| 首页入口 | 实际目录 | 放什么 |
| --- | --- | --- |
| 收件箱 | notes/00-Inbox | 临时手记、未知分类、需要确认的收信 |
| 沉淀池 | notes/00-Settling | 新网页和手机资料，原文与阅读标注 |
| 提炼池 | notes/01-Knowledge | 可复用的概念、方法、结论；原长期知识保留 |
| 专业资料 | notes/04-Professional | 官方文档、论文、标准、专业参考；注明版本 |
| 主题与开发 | notes/02-Projects | 主题索引、开发资料入口、项目笔记 |
| 工具与设置 | notes/03-Resources | 模板、Codex 记忆、同步说明及旧参考资料 |
| 归档 | notes/99-Archive | 不常用资料 |

沉淀状态用“待消化 / 阅读中 / 已提炼 / 暂存”。只维护状态与少量标签即可，来源和渠道由模板填写。历史 Clippings 原位保留，在沉淀池的“旧剪藏”视图中浏览；不会因此自动加入 AI 整理队列。旧长期知识和旧参考资料也不重新判断或搬迁。

## 网页剪藏
导入 [Web Clipper 模板 JSON](../config/obsidian-clipper-settling.json)：Edge 的 Obsidian Web Clipper → 设置 → 任一模板 → Import / 导入 → 选择该文件，再把“Relay · 网页沉淀”放到模板列表顶部。保存目录为 `notes/00-Settling`，新建而非覆盖笔记。

模板只使用 title、url、description、content、date 等普通变量，不使用 Interpreter 提示变量或付费 API。网页 description 不是 AI 验证过的摘要；原文中的图片可能仍是网页远程链接，剪藏成功不等于已离线保存附件。需要离线留存时单独保存原始附件并核对。模板文件可导入；实际扩展配置和离线附件能力须在 Edge 中验收。

## 手机 ChatGPT 与 GitHub
手机先读 GitHub Relay 的 `AGENTS.md`、`docs/GITHUB_CAPTURE.md`、`docs/KNOWLEDGE_WORKFLOW.md` 最新版本。新资料默认 manifest `category: settling`；我已明确要求正式知识时用 `refined`，明确的专业原始参考用 `professional`。拿不准用 `inbox`。旧分类仍兼容。

投递保持 `capture/items/<唯一ID>/note.md + attachments/ + manifest.json`；附件和正文上传完毕才置 ready。正文可带 `status: 待消化`、`channel: 手机ChatGPT`、source、tags；不要捏造来源或已经提炼的结论。图片必须是真实字节或可验证 Base64。

桌面“ChatGPT(走代理)”入口一次性接收：原始字节校验 → 本地保存 → 独立备份与隔离恢复 → 普通提交清理当前远端包并留回执。接收和明确分类不调用模型。永久知识库不上传 GitHub，Git 历史可能仍保留投递附件。

知识笔记不写 `E:/Relay/inbox/`，该目录只存 Codex 任务。任务按 execution_policy 和目标项目规则单独执行；收信程序不会执行笔记里的指令。

## 提炼与开发
新建笔记可使用“沉淀资料 / 提炼知识 / 专业资料 / 开发专题”模板。提炼结果要能回答：是什么、什么时候有用、怎么用、限制是什么、来源在哪里。可从同一原文提炼多条知识，保留双向链接；附件只留一份原件。

AI 批处理只在你提出要求时进行。GitHub 导入只读取 `relay_capture.py --pending` 中你选定的这批；网页只读取你选定的条目或新流程中明确限定的批次，不扫全部历史剪藏。完成审阅后逐个 mark-reviewed，同时更新原文状态；“收信成功”不等于“已提炼”。

开发前或过程中，Codex 可以推荐有用资料，先给出标题、用途、来源、保存位置，经你同意再收录。新资料默认先沉淀；可信专业原文可进专业资料。系统说明和 Codex 记忆放工具区，不混进知识提炼列表。

## 同步与恢复
全库双向同步沿用现有 Syncthing：编辑与删除会传播；独立备份继续保留。首页、Bases、模板文件会随库同步；`.obsidian` 被排除，所以桌面 CSS、插件与模板目录设置不会自动改手机设置。

手机如未显示 Bases，先确认其 Obsidian 支持且启用“数据库 / Bases”；所有实际笔记仍可从文件目录打开。文件夹英文路径保持稳定，桌面左侧用 CSS 显示中文别名，关闭样式即可看到原名。

恢复先还原到新目录并核对哈希，再选择恢复目标，避免直接覆盖正在双向同步的库。整理前快照：`C:/Users/Administrator/RelayNotesBackups/notes-20261011-084237-504127`，独立恢复通过。现有图片、原文和同步协议保持原位。

## 来源
- 当前会话用户确认的知识结构与 GitHub 协同要求（2026-10-11）。
- [Web Clipper 模板文档](https://obsidian.md/help/web-clipper/templates)。
- [Bases 语法文档](https://obsidian.md/help/bases/syntax)。
