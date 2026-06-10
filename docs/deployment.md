# 部署说明

## 1. 本地 Docker 部署

```bash
docker compose up --build
```

当前 Docker 默认是轻量运行模式：

- `RAG_ENABLE_EMBEDDINGS=0`
- `RAG_ENABLE_RERANKER=0`

这样容器不需要安装 `torch` 和 `sentence-transformers`，更适合本地演示、快速启动和简历项目展示。

如果你要启用完整 dense retrieval，建议在本机 Python 环境使用完整 `requirements.txt`，或者自行扩展 Docker 镜像。

启动后访问：

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/docs`

停止服务：

```bash
docker compose down
```

## 2. 环境变量

至少建议配置：

- `RAG_LLM_PROVIDER`
- `RAG_LLM_MODEL`
- `OPENAI_API_KEY` 或其他 provider key

如果只想跑本地 extractive fallback，可以不配置任何 LLM Key。

## 3. 容器内数据目录

容器默认挂载：

- 本地 `./data`
- 容器 `/app/data`

这样抓取的文档、评测集和知识库文件会保留在宿主机。

## 4. 常见操作

抓取官方文档：

```bash
docker compose exec devdocs-qa python scripts/fetch_docs.py --source fastapi
```

局部重建索引：

```bash
curl -X POST http://127.0.0.1:8000/api/v1/index/rebuild \
  -H "Content-Type: application/json" \
  -d '{"topics":["fastapi"]}'
```

运行评测：

```bash
docker compose exec devdocs-qa python scripts/evaluate_rag.py --limit 5
```

## 5. 云端部署建议

如果要把这个项目作为简历展示项目，建议优先部署到支持 Docker 的平台：

- Railway
- Render
- Fly.io
- 一台最小规格云服务器

推荐做法：

1. 使用 `Dockerfile` 统一运行时
2. 使用平台环境变量配置 LLM Key
3. 首次启动后在管理页执行 crawl / rebuild / evaluation
