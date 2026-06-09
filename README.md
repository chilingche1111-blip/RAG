# DevDocs QA

`DevDocs QA` 是一个面向开发者的技术文档智能问答系统，基于公开技术文档构建知识库，支持混合检索、证据引用和 API 问答服务。

当前知识库示例来自公开官方文档主题：

- FastAPI
- Python asyncio
- Redis
- PostgreSQL
- Docker

## 核心能力

- 基于 Markdown 文档和元数据构建知识库
- 标题感知分块与 overlap
- Hybrid RAG：关键词匹配 + 轻量语义相似度
- 返回 grounded answer、置信度、相关问题和证据引用
- 提供 FastAPI 接口和单页 Web 演示

## 适合的落地场景

- 内部开发者文档问答
- 团队框架使用指南问答
- 公开技术文档聚合问答
- API 平台或门户的文档助手

## 项目结构

```text
RAG/
├── app/
│   ├── api/
│   ├── core/
│   ├── services/
│   ├── static/
│   ├── config.py
│   └── main.py
├── data/
│   └── knowledge_base/
├── docs/
├── scripts/
├── tests/
└── requirements.txt
```

## 本地运行

### 1. 安装依赖

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 启动服务

```bash
uvicorn app.main:app --reload
```

启动后访问：

- Web 页面：`http://127.0.0.1:8000/`
- OpenAPI：`http://127.0.0.1:8000/docs`

### 3. 命令行演示

```bash
python3 scripts/query_demo.py "Redis 的 RDB 和 AOF 应该怎样取舍？" --topic redis
```

### 4. 运行测试

```bash
python3 -m unittest discover -s tests
```

## 主要接口

- `GET /health`
- `GET /api/v1/topics`
- `GET /api/v1/suggestions`
- `GET /api/v1/index/stats`
- `POST /api/v1/index/rebuild`
- `POST /api/v1/query`

示例请求：

```bash
curl -X POST http://127.0.0.1:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "FastAPI 的依赖注入适合解决什么问题？",
    "topic": "fastapi",
    "top_k": 3
  }'
```

## 返回内容

- `answer`：基于命中文档片段生成的回答
- `confidence_label`：粗粒度命中置信度
- `documentation_hint`：针对当前技术主题的阅读提示
- `related_questions`：可继续追问的问题
- `citations / retrieved_chunks`：命中的文档片段与来源链接

## 下一步建议

- 接入真实 embedding 模型
- 增加 rerank 层
- 接入官方文档抓取与增量更新
- 增加代码示例级别的检索
- 增加答案质量评测

## 相关文档

- [产品说明](docs/developer-docs-product.md)
- [实施计划](docs/rag-system-plan.md)
