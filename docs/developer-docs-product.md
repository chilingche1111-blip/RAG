# 开发者技术文档智能问答系统

## 1. 产品定义

这是一个面向开发者的技术文档智能问答系统，基于公开技术文档构建知识库，支持混合检索、证据引用和 API 问答服务。

当前版本聚焦：

- FastAPI
- Python asyncio
- Redis
- PostgreSQL
- Docker

## 2. 用户价值

这个产品面向开发者查文档与追溯证据的使用场景。

典型价值：

- 把分散的官方文档组织成统一检索与问答接口
- 给出基于证据的答案，而不是脱离文档自由生成
- 返回引用片段和原始文档链接，方便继续深挖
- 适合作为 API 服务集成到内部工具、IDE 插件或文档门户

## 3. 当前能力

- 运行时：Python 3.11
- 导入 Markdown 形式的文档摘要知识库
- 抓取公开官方文档并沉淀为 Markdown 知识文件
- 使用 `topic` 元数据管理知识源
- 混合检索：关键词 + 真实 dense embedding + cross-encoder rerank
- 生成层：多 provider LLM + 本地 grounded fallback
- 返回结构化答案、内联 citation、相关问题、引用片段和原始来源链接
- 暴露 provider registry 与 provider health，支持前端直观展示配置状态
- 支持增量抓取、topic 局部重建、自动评测和最近查询日志
- 提供 REST API 与单页前端

## 4. 典型问题

- “FastAPI 的依赖注入适合解决什么问题？”
- “asyncio.create_task 和 await 有什么区别？”
- “Redis 为什么同时启用 RDB 和 AOF？”
- “为什么 Docker 某一层变了后面也要重建？”
- “PostgreSQL 的 B-Tree 为什么适合范围查询？”

内置 provider 示例：

- OpenAI
- Claude
- DeepSeek
- Groq
- OpenRouter
- Together
- Moonshot Kimi
- SiliconFlow
- DashScope Qwen
- Mistral
- Perplexity

当前已覆盖的主要功能：

- `data/doc_sources.json` 维护官方文档来源
- `scripts/fetch_docs.py` 执行公开文档抓取
- `POST /api/v1/index/rebuild` 支持按 topic 局部重建
- `POST /api/v1/docs/crawl` 执行增量抓取并回写知识库
- `POST /api/v1/evaluation/run` 运行内置评测集
- `GET /api/v1/llm/health` 查看模型层配置状态
- `GET /api/v1/admin/logs` 查看最近查询日志
- Web UI 直接展示 provider 状态、抓取命令、评测摘要、source registry 和 citation 跳转

## 5. 后续扩展

- 直接采集官方文档站点并建立增量索引
- 增加代码片段检索与答案高亮
- 支持多文档站点联合问答
- 增加用户反馈和答案质量评测
- 增加多 provider 生成答案的评测与 prompt 版本管理
