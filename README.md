# DevDocs QA

一个面向开发者的技术文档智能问答系统，基于公开技术文档构建知识库，支持混合检索、证据引用和 API 问答服务。

当前仓库提供的是一个可运行的 RAG MVP，同时保留了继续扩展到正式产品的结构：

- 文档 ingestion
- 标题感知 chunking
- Hybrid retrieval
- 真实 dense embedding
- cross-encoder rerank
- grounded answer generation
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

问答结果包含：

- `answer`
- `confidence_label`
- `documentation_hint`
- `related_questions`
- `citations`
- `retrieved_chunks`

这样前端不仅能展示答案，还能展示：

- 为什么命中这段内容
- 对应来源是什么
- 用户下一步还可以问什么

## 4. 技术架构

### 4.1 后端

- Python 3.9+
- FastAPI
- Pydantic v2

### 4.2 检索与模型

- `sentence-transformers`
- `torch`
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

不直接调用大模型，而是从命中文档中提取最相关句子，生成 grounded answer。

这种设计的优点是：

- 更容易演示 RAG 的核心价值
- 不依赖外部 LLM API
- 便于后续替换为真实生成模型

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

### 获取索引状态

`GET /api/v1/index/stats`

返回示例字段：

- `document_count`
- `chunk_count`
- `knowledge_base_dir`
- `retrieval_backend`
- `reranker_backend`

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
    "top_k": 3
  }'
```

响应结构示例：

```json
{
  "question": "FastAPI 的依赖注入适合解决什么问题？",
  "answer": "When a request reaches a path operation, FastAPI builds a dependency graph...",
  "topic": "fastapi",
  "confidence_label": "high",
  "documentation_hint": "回答 FastAPI 问题时，优先区分路由层、依赖注入层和 async 运行时语义。",
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

### 8.4 单元测试

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

示例见：[.env.example](/Users/cii/RAG_PROJECT/.env.example)

## 10. 已完成验证

当前仓库已验证：

- `python3 -m unittest discover -s tests`
- `python3 -m compileall app tests scripts`
- 轻量回退检索可运行
- 真实 `sentence-transformers` embedding 可加载
- 真实 `cross-encoder` rerank 可加载
- FastAPI 服务结构完整

说明：

- 首次加载真实模型时会下载 Hugging Face 模型文件，耗时明显更长
- 本机 Python 使用 `LibreSSL` 时，`urllib3` 可能打印告警，但不影响当前功能运行

## 11. 后续扩展建议

最值得继续做的方向：

1. 接入真正的 LLM 生成层，把证据片段变成更自然的中文答案
2. 增加官方文档抓取器和增量索引更新
3. 增加 rerank 前后的评测指标
4. 支持代码片段级检索
5. 增加用户反馈闭环和命中评测集
6. 支持多站点、多团队知识库混合问答

## 12. 相关文档

- [产品说明](docs/developer-docs-product.md)
- [实施计划](docs/rag-system-plan.md)
