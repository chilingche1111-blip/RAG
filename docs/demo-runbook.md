# 5 分钟 Demo 流程

这份文档用于现场演示，目标是在 5 分钟内把系统的核心能力讲清楚，同时尽量降低演示过程中的变量。

## 1. 演示前准备

建议使用轻量模式启动，避免现场等待模型下载或外部接口超时：

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export RAG_ENABLE_EMBEDDINGS=0
export RAG_ENABLE_RERANKER=0
export RAG_ENABLE_LLM=0
uvicorn app.main:app --reload
```

确认以下页面可以打开：

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/docs`

如果你已经配置了可用的 Provider Key，也可以保留 `RAG_ENABLE_LLM=1`，但现场演示时仍建议优先准备 fallback 方案。

## 2. 演示目标

这一轮演示建议只强调四件事：

1. 系统基于公开技术文档构建知识库
2. 问答不是自由生成，而是基于命中文档证据
3. 输出里有 citation、来源链接和命中文档片段
4. 系统除了问答，还覆盖抓取、重建、评测和 Provider 管理

## 3. 推荐演示顺序

### 第一步：30 秒介绍项目

可以直接这样说：

“这是一个面向开发者技术文档场景的 RAG 问答系统。它把公开官方文档整理成知识库，通过混合检索和证据引用返回可追溯的答案，同时提供 API、Web UI、文档抓取和评测能力。”

### 第二步：打开 Web UI

进入 `http://127.0.0.1:8000/`，说明页面包含三类信息：

- 问答输入区
- 答案和 citation 展示区
- provider / source registry / operator console

这里的说明重点不是界面视觉，而是“一个页面能把问答、证据和运维入口串起来”。

### 第三步：提一个稳定问题

建议优先使用下面三个问题之一：

- `FastAPI 的依赖注入适合解决什么问题？`
- `asyncio.create_task 和直接 await 有什么区别？`
- `Docker 构建缓存是怎么工作的？`

演示时重点指向以下结果：

- 答案先给结论
- 关键点带引用标记
- citation 可定位到 chunk
- 每条证据带来源名称和原始链接

### 第四步：展开 retrieved chunks

这一步要明确说明：

- 系统不仅返回答案，也返回检索命中的证据块
- 每个 chunk 都包含 `score`、`title`、`topic` 和原始文本
- 如果答案有争议，可以直接回看证据，而不是只相信模型输出

### 第五步：展示 Provider 状态

如果没有配置任何模型 Key，可以直接说明：

“当前运行在 fallback 模式，没有依赖外部模型调用，但检索、引用和证据追踪链路仍然完整。”

如果已经配置了模型 Key，可以额外演示：

- provider 列表
- configured / missing key 状态
- 切换不同 provider 或模型

### 第六步：展示运维接口

建议再点到两项即可，不要全部展开：

- `GET /api/v1/llm/health`
- `POST /api/v1/evaluation/run`

如果时间够，再补一句：

“仓库里还提供了文档抓取和局部重建能力，可以把新的公开文档增量纳入知识库。”

## 4. 推荐演示话术

### 版本 A：偏产品视角

“这个系统解决的是开发者查文档效率问题。和普通聊天问答不同，它要求答案必须能回到文档证据，因此更适合做内部知识检索、开发者门户助手或技术支持场景。”

### 版本 B：偏工程视角

“底层链路包括文档抓取、Markdown 化、分块、混合检索、重排和结构化回答。即使没有配置外部模型，也能先通过 grounded fallback 验证检索和 citation 这条主链路。”

### 版本 C：偏交付视角

“这个仓库不只是问答接口，还包含评测脚本、Provider 健康检查、抓取源管理和局部重建能力，便于继续往可维护的服务形态扩展。”

## 5. 现场兜底方案

### 情况 1：外部模型不可用

处理方式：

- 关闭 `RAG_ENABLE_LLM`
- 明确说明当前演示的是 grounded fallback 路径

这样不会影响核心展示目标。

### 情况 2：首次加载太慢

处理方式：

- 提前用轻量模式启动
- 不在现场开启 embeddings / reranker 下载

### 情况 3：回答不够长

处理方式：

- 把重点转回 citation 和 retrieved chunks
- 强调系统关注的是“可验证性”，不是单纯生成更长文本

### 情况 4：想展示 API 能力

可以直接打开 `http://127.0.0.1:8000/docs`，再补一条查询请求：

```bash
curl -X POST http://127.0.0.1:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "FastAPI 的依赖注入适合解决什么问题？",
    "topic": "fastapi",
    "top_k": 4
  }'
```

## 6. 5 分钟时间分配

- 第 1 分钟：项目定位和页面结构
- 第 2 分钟：输入问题并展示答案
- 第 3 分钟：展开 citation 和 retrieved chunks
- 第 4 分钟：展示 Provider 状态或 API 文档
- 第 5 分钟：补充抓取、重建、评测能力

## 7. 一句话收尾

可以用这句结束：

“这个项目的重点不只是回答问题，而是把开发者技术文档整理成一个可检索、可引用、可追溯、可继续扩展的问答服务。”
