# 项目描述模板

## 1. 一句话版本

这是一个面向开发者技术文档场景的问答系统，基于公开官方文档构建知识库，支持混合检索、结构化回答、证据引用和 API / Web 交互。

## 2. 项目介绍版本

### 版本 A：偏产品实现

- 构建开发者文档问答系统，基于公开技术文档建立知识库，支持 FastAPI、asyncio、Redis、PostgreSQL、Docker 等主题问答
- 设计 Hybrid Retrieval 链路，融合关键词检索、dense embedding 召回与 cross-encoder rerank，提升文档命中率与答案相关性
- 实现结构化答案输出、citation 引用跳转、来源追踪、自动评测、官方文档抓取与局部索引重建，形成 API + Web UI 的完整使用链路

### 版本 B：偏工程实现

- 基于 FastAPI 搭建技术文档问答服务，完成文档抓取、标题感知分块、知识库索引、混合检索和结构化回答生成
- 支持多 provider LLM 接入与本地 grounded fallback，未配置模型时仍可返回可验证的引用式答案
- 提供评测脚本、provider health、source registry、recent logs 和 operator console，具备进一步扩展基础

### 版本 C：偏系统设计

- 实现一个围绕公开技术文档构建知识库的问答系统，支持混合检索、证据引用和结构化问答
- 通过 lexical recall、dense embedding 和 reranker 组合优化检索链路，并输出带 chunk-level citation 的 grounded answer
- 增加自动评测、抓取增量同步、局部重建和多模型接入能力，使系统具备持续迭代条件

## 3. 项目介绍思路

可以按下面这条线介绍：

1. 这是一个面向开发者技术文档场景的问答系统
2. 知识来源是公开官方文档，先抓取并沉淀成 Markdown，再做分块和索引
3. 检索层采用 Hybrid Retrieval，结合 lexical、dense embedding 和 rerank
4. 回答层优先走 LLM 结构化生成，没有可用模型时会回退到 grounded extractive answer
5. 最终输出不仅有答案，还有 citation、来源链接、相关问题和管理端运维能力

## 4. 可强调的特点

- 面向开发者技术文档场景，问题边界清晰
- 回答可追溯到证据 chunk，强调 grounded answer 而不是自由生成
- 同时覆盖 crawler、index、retrieval、generation、evaluation、API、UI 全链路
- 支持本地稳定运行，不依赖公网服务也能完成验证

## 5. 设计难点

- 如何把通用 RAG 缩到开发者文档这个高相关场景
- 如何平衡 lexical recall、dense retrieval 和 rerank 的组合
- 为什么要做结构化输出和 citation，而不是只返回一段自然语言
- 为什么要保留 fallback 机制，保证没有模型 key 也能稳定运行
