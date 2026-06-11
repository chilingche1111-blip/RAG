# 简历描述模板

## 1. 一句话版本

开发了一个面向开发者技术文档场景的 RAG 智能问答系统，基于公开官方文档构建知识库，支持混合检索、结构化回答、证据引用和 API/Web 演示。

## 2. 简历项目描述版本

### 版本 A：偏产品落地

- 构建面向开发者文档场景的 RAG 智能问答系统，基于公开技术文档建立知识库，支持 FastAPI、asyncio、Redis、PostgreSQL、Docker 等主题问答
- 设计 Hybrid Retrieval 链路，融合关键词检索、dense embedding 召回与 cross-encoder rerank，提升文档命中率与答案相关性
- 实现结构化答案输出、citation 引用跳转、来源追踪、自动评测、官方文档抓取与局部索引重建，形成可演示的 API + Web UI 闭环

### 版本 B：偏工程实现

- 基于 FastAPI 搭建开发者文档问答服务，完成文档抓取、标题感知分块、知识库索引、混合检索和结构化回答生成
- 支持多 provider LLM 接入与本地 grounded fallback，未配置模型时仍可返回可验证的引用式答案
- 提供评测脚本、provider health、source registry、recent logs 和 operator console，具备进一步产品化扩展基础

### 版本 C：偏 AI / RAG

- 独立实现一个 developer-facing RAG QA system，围绕公开技术文档构建知识库，支持混合检索、证据引用和结构化问答
- 通过 lexical recall、dense embedding 和 reranker 组合优化检索链路，并输出带 chunk-level citation 的 grounded answer
- 增加自动评测、抓取增量同步、局部重建和多模型接入能力，使系统具备真实演示和迭代优化条件

## 3. 面试口述版本

可以按下面这条线介绍：

1. 我没有做通用聊天机器人，而是做了一个面向开发者技术文档场景的问答系统
2. 知识来源是公开官方文档，先抓取并沉淀成 Markdown，再做分块和索引
3. 检索层采用 Hybrid Retrieval，结合 lexical、dense embedding 和 rerank
4. 回答层优先走 LLM 结构化生成，没有可用模型时会回退到 grounded extractive answer
5. 最终输出不仅有答案，还有 citation、来源链接、相关问题和管理端运维能力

## 4. 可强调的亮点

- 不是单纯聊天 Demo，而是有明确场景边界的 developer docs assistant
- 回答可追溯到证据 chunk，强调 grounded answer 而不是自由生成
- 同时覆盖 crawler、index、retrieval、generation、evaluation、API、UI 全链路
- 支持本地稳定演示，不依赖公网服务也能完成展示

## 5. 如果面试官追问“难点是什么”

你可以重点讲：

- 如何把通用 RAG 缩到开发者文档这个高相关场景
- 如何平衡 lexical recall、dense retrieval 和 rerank 的组合
- 为什么要做结构化输出和 citation，而不是只返回一段自然语言
- 为什么要保留 fallback 机制，保证没有模型 key 也能稳定演示
