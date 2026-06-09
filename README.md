# DevDocs QA

一个面向开发者的技术文档智能问答系统，基于公开技术文档构建知识库，支持混合检索、证据引用和 API 问答服务。

当前仓库提供的是一个可运行的 RAG MVP，同时保留了继续扩展到正式产品的结构：

- 文档 ingestion
- 标题感知 chunking
- Hybrid retrieval
- 真实 dense embedding
- cross-encoder rerank
- multi-provider LLM answer generation
- grounded fallback generation
- 引用与原始文档链接返回
- FastAPI API
- Web 演示页面

## 1. 项目定位

这个项目不是泛聊天机器人，而是一个更适合真实落地的开发者文档问答系统。

目标场景：

- 团队内部技术文档问答
- 公开官方文档聚合问答
- API 门户 / 开发者中心问答助手
- IDE 插件或内部工具的文档检索服务

核心价值：

- 把分散的文档内容收敛成统一问答入口
- 回答必须基于命中文档片段，不依赖自由发挥
- 返回引用片段和原始来源链接，方便继续深挖
- 通过 API 对外服务，便于二次集成

## 2. 当前知识库主题

示例知识库基于公开技术文档主题整理：

- `FastAPI`
- `Python asyncio`
- `Redis`
- `PostgreSQL`
- `Docker`

每份知识文件都带有元数据，例如：

- `topic`
- `source_name`
- `source_url`

这样可以在问答结果中返回来源说明和跳转链接。

## 3. 系统能力

### 3.1 文档处理

- 支持 Markdown / txt 文档导入
- 支持 frontmatter 元数据解析
- 支持标题感知分块
- 支持 chunk overlap

### 3.2 检索能力

当前检索链路分成三层：

1. 关键词匹配
2. dense embedding 相似度召回
3. cross-encoder rerank 重排

实现策略：

- lexical score：基于词项重叠与余弦相似度
- semantic score：优先使用真实 embedding，相依赖缺失时自动退回轻量语义特征
- rerank score：使用 cross-encoder 对候选 chunk 重新排序

默认模型：

- Embedding：`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- Reranker：`BAAI/bge-reranker-base`

这套配置适合当前“中文提问 + 技术文档知识库”的演示场景。

### 3.3 问答输出

当前生成链路分成两层：

1. 优先调用配置好的 LLM provider 生成结构化答案
2. 如果没有配置对应 provider 的 API Key 或调用失败，则自动回退到本地 extractive grounded answer

当前内置 provider：

- `OpenAI`：Responses API
- `Claude`：Anthropic Messages API
- `DeepSeek`：OpenAI-compatible API
- `Groq`：OpenAI-compatible API
- `OpenRouter`：OpenAI-compatible API
- `Together`：OpenAI-compatible API
- `Moonshot Kimi`：OpenAI-compatible API
- `SiliconFlow`：OpenAI-compatible API
- `DashScope Qwen`：compatible-mode API
- `Mistral`：chat completions API
- `Perplexity`：chat completions API

同时支持通过 `RAG_EXTRA_LLM_PROVIDERS_JSON` 增加更多 OpenAI-compatible provider。

默认 LLM 配置：

- Provider：`openai`
- Model：`gpt-5.4-mini`

生成约束：

- 只允许使用命中的文档证据回答
- 不允许编造 API、参数或默认行为
- 生成层先输出结构化答案对象
- 关键结论和要点必须附带内联 `chunk_id` citation

问答结果包含：

- `answer`
- `summary`
- `key_points`
- `caveats`
- `used_chunk_ids`
- `confidence_label`
- `documentation_hint`
- `related_questions`
- `answer_backend`
- `citations`
- `retrieved_chunks`

这样前端不仅能展示答案，还能展示：

- 为什么命中这段内容
- 对应来源是什么
- 用户下一步还可以问什么
- 点击 citation 后可以直接跳转并高亮对应证据卡

## 4. 技术架构

### 4.1 后端

- Python 3.9+
- FastAPI
- Pydantic v2

### 4.2 检索与模型

- `sentence-transformers`
- `torch`
- `openai`
- `anthropic`
- Hybrid RAG 自定义检索器

### 4.3 前端

- 原生 HTML / CSS / JavaScript
- 单页演示 UI

## 5. 目录结构

```text
RAG/
├── app/
│   ├── api/               # FastAPI 路由与接口 schema
│   ├── core/              # chunking / retrieval / generation / model adapters
│   ├── services/          # RAG orchestration
│   ├── static/            # Web 演示页面
│   ├── config.py          # 运行配置
│   └── main.py            # FastAPI 入口
├── data/
│   └── knowledge_base/    # 示例知识库
├── docs/
│   ├── developer-docs-product.md
│   └── rag-system-plan.md
├── scripts/
│   └── query_demo.py      # 命令行问答示例
├── tests/
└── requirements.txt
```

## 6. 核心模块说明

### `app/core/chunking.py`

负责 Markdown 文档切分，避免生成只有标题没有正文的无效 chunk。

### `app/core/dense_models.py`

负责接入真实 embedding 和 reranker。

主要能力：

- `SentenceTransformerEncoder`
- `CrossEncoderReranker`
- 依赖不可用时自动回退

### `app/core/retrieval.py`

负责混合检索。

流程：

1. 计算 lexical score
2. 计算 dense semantic score
3. 合并初始召回分数
4. 对候选集进行 rerank
5. 返回最终 Top-K

### `app/core/generation.py`

负责生成层编排。

当前策略：

- 有可用 provider key 时：调用真实 LLM 生成结构化答案
- 无可用 provider key 时：回退到 extractive grounded answer

这种设计的优点是：

- 本地无 Key 也能跑通
- 接入 Key 后能直接升级成真实生成式问答
- 保持答案仍然受证据约束

### `app/core/llm_generation.py`

负责多 provider LLM 接入。

主要能力：

- 读取不同 provider 的 API Key
- 调用 OpenAI / Claude / OpenAI-compatible provider
- 将 top-k 证据块拼接进 prompt
- 将 LLM 输出约束为结构化 JSON
- 在失败时自动交回本地 fallback

### `app/services/rag_service.py`

负责全链路编排：

- 加载知识库
- 构建 chunk
- 建立索引
- 接收 query
- 检索并生成答案

## 7. API 设计

### 健康检查

`GET /health`

### 获取主题

`GET /api/v1/topics`

### 获取推荐问题

`GET /api/v1/suggestions`

### 获取 LLM Provider 选项

`GET /api/v1/llm/options`

这个接口会返回：

- `provider_id`
- `provider_type`
- `default_model`
- `api_key_env`
- `base_url`
- `description`

### 获取索引状态

`GET /api/v1/index/stats`

返回示例字段：

- `document_count`
- `chunk_count`
- `knowledge_base_dir`
- `retrieval_backend`
- `reranker_backend`
- `generation_backend`

### 重建索引

`POST /api/v1/index/rebuild`

### 查询问答

`POST /api/v1/query`

请求示例：

```bash
curl -X POST http://127.0.0.1:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "FastAPI 的依赖注入适合解决什么问题？",
    "topic": "fastapi",
    "llm_provider": "openrouter",
    "llm_model": "anthropic/claude-3.7-sonnet",
    "top_k": 3
  }'
```

响应结构示例：

```json
{
  "question": "FastAPI 的依赖注入适合解决什么问题？",
  "answer": "结论：FastAPI dependencies let you declare shared logic once and reuse it across path operations. [dependencies-0001]\n\n关键点：\n- FastAPI dependencies are useful for shared request-time logic. [dependencies-0001]",
  "summary": "FastAPI dependencies let you declare shared logic once and reuse it across path operations. [dependencies-0001]",
  "key_points": [
    "FastAPI dependencies are useful for shared request-time logic. [dependencies-0001]"
  ],
  "caveats": [
    "Middleware is better for request-wide wrapping behavior. [dependencies-0003]"
  ],
  "used_chunk_ids": ["dependencies-0001", "dependencies-0003"],
  "topic": "fastapi",
  "confidence_label": "high",
  "documentation_hint": "回答 FastAPI 问题时，优先区分路由层、依赖注入层和 async 运行时语义。",
  "answer_backend": "openai:gpt-5.4-mini",
  "related_questions": [
    "FastAPI 依赖注入和中间件分别适合什么场景？"
  ],
  "citations": [
    {
      "chunk_id": "dependencies-0002",
      "source_name": "FastAPI Dependencies",
      "source_url": "https://fastapi.tiangolo.com/tutorial/dependencies/",
      "score": 0.80
    }
  ]
}
```

## 8. 本地运行

### 8.1 安装依赖

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

如果你想启用真实 LLM 生成，还需要配置：

```bash
export OPENAI_API_KEY=your_openai_api_key
```

如果切换其他 provider，还需要配置对应 key，例如：

```bash
export ANTHROPIC_API_KEY=your_anthropic_api_key
export DEEPSEEK_API_KEY=your_deepseek_api_key
export GROQ_API_KEY=your_groq_api_key
export OPENROUTER_API_KEY=your_openrouter_api_key
export TOGETHER_API_KEY=your_together_api_key
export MOONSHOT_API_KEY=your_moonshot_api_key
export SILICONFLOW_API_KEY=your_siliconflow_api_key
export DASHSCOPE_API_KEY=your_dashscope_api_key
export MISTRAL_API_KEY=your_mistral_api_key
export PERPLEXITY_API_KEY=your_perplexity_api_key
```

### 8.2 启动服务

```bash
uvicorn app.main:app --reload
```

启动后访问：

- Web 页面：`http://127.0.0.1:8000/`
- OpenAPI 文档：`http://127.0.0.1:8000/docs`

### 8.3 命令行测试

```bash
python3 scripts/query_demo.py "Redis 的 RDB 和 AOF 应该怎样取舍？" --topic redis
```

指定 provider 和模型：

```bash
python3 scripts/query_demo.py "FastAPI 的依赖注入适合解决什么问题？" \
  --topic fastapi \
  --llm-provider deepseek \
  --llm-model deepseek-chat
```

### 8.4 Web 使用

1. 启动 `uvicorn app.main:app --reload`
2. 打开 `http://127.0.0.1:8000/`
3. 输入问题
4. 选择技术主题
5. 选择 LLM provider，必要时覆盖模型名
6. 提交查询
7. 点击答案里的 `[chunk-id]` 跳到并高亮对应证据卡

### 8.5 单元测试

```bash
python3 -m unittest discover -s tests
```

## 9. 环境变量配置

常用配置项：

- `RAG_KB_DIR`
- `RAG_CHUNK_SIZE`
- `RAG_CHUNK_OVERLAP`
- `RAG_TOP_K`
- `RAG_MIN_SCORE`
- `RAG_LEXICAL_WEIGHT`
- `RAG_SEMANTIC_WEIGHT`
- `RAG_ENABLE_EMBEDDINGS`
- `RAG_EMBEDDING_MODEL`
- `RAG_ENABLE_RERANKER`
- `RAG_RERANKER_MODEL`
- `RAG_RERANK_CANDIDATES`
- `RAG_RERANK_WEIGHT`
- `RAG_ENABLE_LLM`
- `RAG_LLM_PROVIDER`
- `RAG_LLM_MODEL`
- `RAG_LLM_REASONING_EFFORT`
- `RAG_LLM_MAX_OUTPUT_TOKENS`
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `DEEPSEEK_API_KEY`
- `GROQ_API_KEY`
- `OPENROUTER_API_KEY`
- `TOGETHER_API_KEY`
- `MOONSHOT_API_KEY`
- `SILICONFLOW_API_KEY`
- `DASHSCOPE_API_KEY`
- `MISTRAL_API_KEY`
- `PERPLEXITY_API_KEY`
- `RAG_EXTRA_LLM_PROVIDERS_JSON`

示例见：[.env.example](/Users/cii/RAG_PROJECT/.env.example)

## 10. 已完成验证

当前仓库已验证：

- `python3 -m unittest discover -s tests`
- `python3 -m compileall app tests scripts`
- 轻量回退检索可运行
- 真实 `sentence-transformers` embedding 可加载
- 真实 `cross-encoder` rerank 可加载
- 未配置可用 provider key 时可自动回退到 extractive 生成
- FastAPI 服务结构完整

说明：

- 首次加载真实模型时会下载 Hugging Face 模型文件，耗时明显更长
- 本机 Python 使用 `LibreSSL` 时，`urllib3` 可能打印告警，但不影响当前功能运行
- 真实 LLM 生成层需要你提供对应 provider 的有效 API Key 才能完成联网调用

## 11. 后续扩展建议

最值得继续做的方向：

1. 增加更多预置 provider，例如 Together、Moonshot、企业自建兼容网关
2. 增加官方文档抓取器和增量索引更新
3. 增加 rerank 前后的评测指标
4. 支持代码片段级检索
5. 增加用户反馈闭环和命中评测集
6. 支持多站点、多团队知识库混合问答

## 12. 相关文档

- [产品说明](docs/developer-docs-product.md)
- [实施计划](docs/rag-system-plan.md)
