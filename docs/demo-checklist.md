# Demo Checklist

## 1. 演示前 3 分钟确认

- 使用 `Python 3.11` 虚拟环境
- 本地依赖已安装：`pip install -r requirements.txt`
- 如果只做稳定演示，先关闭：
  - `RAG_ENABLE_EMBEDDINGS=0`
  - `RAG_ENABLE_RERANKER=0`
  - `RAG_ENABLE_LLM=0`
- 服务可正常启动：`uvicorn app.main:app --reload`
- 页面可打开：
  - `http://127.0.0.1:8000/`
  - `http://127.0.0.1:8000/docs`

## 2. 最推荐的 3 个演示问题

- `FastAPI 的依赖注入适合解决什么问题？`
- `asyncio.create_task 和直接 await 有什么区别？`
- `Docker 构建缓存是怎么工作的？`

这三个问题覆盖：

- Web 框架
- 并发模型
- 工程工具链

## 3. 演示时要强调什么

- 这不是通用聊天机器人，而是开发者技术文档问答系统
- 回答必须基于命中的文档 chunk，而不是自由生成
- 前端可直接展示 citation、source link、provider health、source registry
- 即使不配置任何 LLM key，也能用 fallback 模式完成稳定演示

## 4. 如果没有 API key，怎么讲

推荐这样表达：

“这个 Demo 默认支持两层回答模式。配置了 provider key 时走结构化 LLM 生成；没有 key 时会自动回退到 grounded extractive answer，所以演示时仍然可以稳定展示检索、引用和证据追踪能力。”

## 5. 如果模型下载慢，怎么处理

优先使用本地轻量模式：

```bash
export RAG_ENABLE_EMBEDDINGS=0
export RAG_ENABLE_RERANKER=0
export RAG_ENABLE_LLM=0
```

这样可以避免首次演示时下载 `sentence-transformers` 或其他大模型依赖。

## 6. 演示结束时一句话总结

“这个项目重点不是做一个聊天壳子，而是把公开技术文档整理成一个可检索、可引用、可验证的开发者问答系统，并且已经具备 API、Web UI、评测和运维闭环。” 
