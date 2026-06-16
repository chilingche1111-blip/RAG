# 使用说明书

这份说明书面向第一次接手仓库的人，按“安装、启动、提问、抓取文档、重建索引、运行评测、排查问题”的顺序组织。

## 1. 运行要求

- Python：`3.11`
- 包管理：`pip`
- 可选：`Docker`、`Docker Compose`
- 可选：任一已配置的 LLM Provider API Key

默认开发环境以 `Python 3.11 + OpenSSL` 为主。

## 2. 安装依赖

在仓库根目录执行：

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

如果只想先验证检索链路、引用和前端页面，可以先关闭模型层：

```bash
export RAG_ENABLE_EMBEDDINGS=0
export RAG_ENABLE_RERANKER=0
export RAG_ENABLE_LLM=0
```

## 3. 启动服务

### 3.1 本地启动

```bash
uvicorn app.main:app --reload
```

启动后访问：

- Web UI：`http://127.0.0.1:8000/`
- OpenAPI：`http://127.0.0.1:8000/docs`
- 健康检查：`http://127.0.0.1:8000/health`

### 3.2 Docker 启动

轻量模式：

```bash
docker compose up --build
```

完整模式：

```bash
docker compose -f docker-compose.yml -f docker-compose.full.yml up --build
```

后台运行：

```bash
docker compose up -d --build
```

停止服务：

```bash
docker compose down
```

如果是本地 `uvicorn` 启动，可在终端按 `Ctrl+C` 停止。

## 4. 环境变量

仓库提供了 [`.env.example`](../.env.example) 可作为模板。

常用变量：

- `RAG_KB_DIR`：知识库目录
- `RAG_DOC_SOURCES_PATH`：文档抓取源配置
- `RAG_EVAL_CASES_PATH`：评测集路径
- `RAG_TOP_K`：默认召回数量
- `RAG_ENABLE_EMBEDDINGS`：是否启用 dense embedding
- `RAG_ENABLE_RERANKER`：是否启用 reranker
- `RAG_ENABLE_LLM`：是否启用 LLM 生成
- `RAG_LLM_PROVIDER`：默认 provider
- `RAG_LLM_MODEL`：默认模型名

启用某个 Provider 时，需要设置对应 API Key，例如：

```bash
export OPENAI_API_KEY=your_openai_api_key
export ANTHROPIC_API_KEY=your_anthropic_api_key
export DEEPSEEK_API_KEY=your_deepseek_api_key
```

## 5. 使用方式

### 5.1 Web UI

1. 打开 `http://127.0.0.1:8000/`
2. 输入问题
3. 可选选择 `topic`
4. 可选覆盖 `LLM provider` 和模型名
5. 查看答案、citation、命中文档片段和来源链接

Web 页面同时会展示：

- provider 配置状态
- source registry
- 最近抓取与评测入口
- citation 跳转结果

### 5.2 命令行查询

```bash
python3 scripts/query_demo.py "asyncio.create_task 和直接 await 有什么区别？"
```

按 topic 查询：

```bash
python3 scripts/query_demo.py "Redis 为什么同时启用 RDB 和 AOF？" --topic redis
```

指定 provider 和模型：

```bash
python3 scripts/query_demo.py "FastAPI 的依赖注入适合解决什么问题？" \
  --topic fastapi \
  --llm-provider deepseek \
  --llm-model deepseek-chat
```

### 5.3 API 查询

```bash
curl -X POST http://127.0.0.1:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Docker 构建缓存是怎么工作的？",
    "topic": "docker",
    "top_k": 4
  }'
```

返回结果包含：

- `answer`
- `summary`
- `key_points`
- `caveats`
- `used_chunk_ids`
- `citations`
- `retrieved_chunks`

## 6. 知识库维护

### 6.1 查看 topic

```bash
curl http://127.0.0.1:8000/api/v1/topics
```

### 6.2 查看抓取源

```bash
curl http://127.0.0.1:8000/api/v1/docs/sources
```

### 6.3 抓取官方文档

抓取单个来源：

```bash
python3 scripts/fetch_docs.py --source fastapi
```

批量抓取所有来源，并限制每个来源最多抓取 3 页：

```bash
python3 scripts/fetch_docs.py --source all --limit 3
```

强制重抓并覆盖：

```bash
python3 scripts/fetch_docs.py --source fastapi --no-incremental
```

也可以通过 API 触发抓取：

```bash
curl -X POST http://127.0.0.1:8000/api/v1/docs/crawl \
  -H "Content-Type: application/json" \
  -d '{
    "source_id": "fastapi",
    "limit": 3,
    "incremental": true,
    "rebuild_after": true
  }'
```

### 6.4 重建索引

重建全部索引：

```bash
curl -X POST http://127.0.0.1:8000/api/v1/index/rebuild
```

只重建指定 topic：

```bash
curl -X POST http://127.0.0.1:8000/api/v1/index/rebuild \
  -H "Content-Type: application/json" \
  -d '{"topics":["fastapi","docker"]}'
```

### 6.5 查看索引状态

```bash
curl http://127.0.0.1:8000/api/v1/index/stats
```

## 7. 模型层管理

### 7.1 查看可用 Provider

```bash
curl http://127.0.0.1:8000/api/v1/llm/options
```

### 7.2 查看 Provider 状态

```bash
curl http://127.0.0.1:8000/api/v1/llm/health
```

如果未配置任何可用 API Key，系统会自动回退到 grounded extractive answer，仍然可以验证检索、引用和证据链路。

### 7.3 增加兼容 Provider

可以通过 `RAG_EXTRA_LLM_PROVIDERS_JSON` 增加 OpenAI-compatible provider，例如：

```bash
export RAG_EXTRA_LLM_PROVIDERS_JSON='[
  {
    "provider_id": "custom-gateway",
    "label": "Custom Gateway",
    "provider_type": "openai_compatible_chat",
    "api_key_env": "CUSTOM_GATEWAY_API_KEY",
    "default_model": "gpt-4o-mini",
    "base_url": "https://your-gateway.example.com/v1",
    "description": "Custom OpenAI-compatible gateway."
  }
]'
```

## 8. 评测与运维

### 8.1 运行评测脚本

```bash
python3 scripts/evaluate_rag.py
```

只评测单个 topic：

```bash
python3 scripts/evaluate_rag.py --topic fastapi
```

限制评测数量并导出结果：

```bash
python3 scripts/evaluate_rag.py --limit 5 --output-json tmp/eval-report.json
```

### 8.2 通过 API 运行评测

```bash
curl -X POST http://127.0.0.1:8000/api/v1/evaluation/run \
  -H "Content-Type: application/json" \
  -d '{
    "top_k": 4,
    "topic": "fastapi"
  }'
```

### 8.3 查看最近查询日志

```bash
curl "http://127.0.0.1:8000/api/v1/admin/logs?limit=20"
```

## 9. 推荐使用顺序

第一次接触仓库时，建议按下面顺序验证：

1. 用轻量模式启动服务
2. 打开 Web UI，直接提问
3. 查看 `/api/v1/index/stats` 和 `/api/v1/topics`
4. 跑一次 `scripts/query_demo.py`
5. 跑一次 `scripts/evaluate_rag.py`
6. 再决定是否启用 embeddings、reranker 和外部 LLM

## 10. 常见问题

### 10.1 页面能打开，但回答比较短

通常是以下几种情况：

- 当前运行在 fallback 模式
- 未配置可用 Provider API Key
- `RAG_ENABLE_LLM=0`

可先检查：

```bash
curl http://127.0.0.1:8000/api/v1/llm/health
```

### 10.2 第一次启动很慢

如果开启了 embeddings 或 reranker，首次加载会下载 Hugging Face 模型文件。只想先验证主链路时，可以关闭：

```bash
export RAG_ENABLE_EMBEDDINGS=0
export RAG_ENABLE_RERANKER=0
export RAG_ENABLE_LLM=0
```

### 10.3 抓取后没有出现在问答结果里

通常需要重建索引。可执行：

```bash
curl -X POST http://127.0.0.1:8000/api/v1/index/rebuild
```

### 10.4 Docker 启动成功，但效果和本地不一致

默认 Docker 配置走轻量模式，会关闭 dense embeddings 和 reranker。如需完整检索路径，使用：

```bash
docker compose -f docker-compose.yml -f docker-compose.full.yml up --build
```
