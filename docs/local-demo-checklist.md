# Local Demo Checklist

## 1. 启动前 3 分钟确认

- 使用 `Python 3.11` 虚拟环境
- 本地依赖已安装：`pip install -r requirements.txt`
- 如果只做稳定验证，先关闭：
  - `RAG_ENABLE_EMBEDDINGS=0`
  - `RAG_ENABLE_RERANKER=0`
  - `RAG_ENABLE_LLM=0`
- 服务可正常启动：`uvicorn app.main:app --reload`
- 页面可打开：
  - `http://127.0.0.1:8000/`
  - `http://127.0.0.1:8000/docs`

## 2. 示例问题

- `FastAPI 的依赖注入适合解决什么问题？`
- `asyncio.create_task 和直接 await 有什么区别？`
- `Docker 构建缓存是怎么工作的？`

这三个问题覆盖：

- Web 框架
- 并发模型
- 工程工具链

## 3. 运行时可关注的内容

- 系统面向开发者技术文档问答场景
- 回答必须基于命中的文档 chunk，而不是自由生成
- 前端可直接展示 citation、source link、provider health、source registry
- 即使不配置任何 LLM key，也能用 fallback 模式完成稳定运行

## 4. 如果没有 API key

可使用以下说明：

“系统支持两层回答模式。配置了 provider key 时走结构化 LLM 生成；没有 key 时会自动回退到 grounded extractive answer，因此仍然可以验证检索、引用和证据追踪能力。”

## 5. 如果模型下载慢，怎么处理

可先使用本地轻量模式：

```bash
export RAG_ENABLE_EMBEDDINGS=0
export RAG_ENABLE_RERANKER=0
export RAG_ENABLE_LLM=0
```

这样可以减少首次运行时下载 `sentence-transformers` 或其他大模型依赖。

## 6. 简短总结

“该项目将公开技术文档整理为一个可检索、可引用、可验证的问答系统，并提供 API、Web UI、评测与运维能力。”
