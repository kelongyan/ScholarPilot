# Kairos Project Overview

---

## 1. 项目定位

Kairos 当前产品定位调整为：

**可验证的团队知识库问答与知识运营平台。**

系统面向企业、团队和知识密集型组织，用于统一管理内部文档，提供精准检索、可溯源问答、用户反馈、知识缺口发现、执行过程追踪和持续评测能力。

原有“论文阅读、文献分析、科研 Copilot”方向不再作为主线，而作为智能知识库的一个垂直场景保留。Multi-Agent 也不作为短期对外主定位，而是后期受控工作流能力。后续产品设计、路线图和验收标准均以“可验证知识问答 + 知识运营闭环”为主。

---

## 2. 核心目标

Kairos 要解决的问题：

- 知识分散在 PDF、Word、Markdown、HTML、TXT、PPT 等不同格式中。
- 用户需要手动搜索大量文档，效率低且容易遗漏。
- 复杂问题的答案往往分散在多份文档中，人工综合成本高。
- 普通 LLM 容易产生幻觉，难以满足企业知识问答的准确性要求。
- 团队缺少对问答质量、检索效果、知识缺口、文档过期和知识使用情况的持续观察。

系统目标：

- 建立多知识库、多文档的统一管理能力。
- 用 Hybrid RAG 提供语义 + 关键词双通道检索。
- 用 Evidence Pack 和 citation grounding 保证答案可追溯。
- 用用户反馈、Trace、评测集和知识运营看板持续改进知识库质量。
- 在基础产品稳定后，用受控 Multi-Agent 工作流处理复杂查询、分析和审核任务。

---

## 3. 设计原则

### 3.1 证据优先

系统先检索、筛选和组织证据，再生成答案。检索内容只能作为 evidence，不允许覆盖系统指令。证据不足时必须明确提示“不足以支持可靠回答”。

### 3.2 知识库优先

问答默认绑定到明确知识库范围。文档、chunk、索引、权限、统计和评测都应围绕知识库组织，而不是只围绕单篇文档。

### 3.3 受控 Agent

Agent 不做短期核心卖点，也不做无限自主循环。Planner、Retrieval、Analyst、Writer、Reviewer 等角色必须有明确输入、输出、工具权限、最大迭代次数和 trace。

### 3.4 渐进产品化

现有代码已经有可运行 RAG 引擎，后续优先补齐知识库产品层、反馈闭环、知识缺口发现、trace 持久化、权限边界和评测闭环，再引入复杂 Agent、GraphRAG、MCP、A2A 等增强能力。

---

## 4. 当前系统基线

当前代码已实现：

- FastAPI 后端和 Next.js 前端骨架。
- PostgreSQL 文档、chunk、citation 数据模型。
- PDF 上传、PyMuPDF 解析、chunk 切分和页码保留。
- Redis/RQ 异步任务处理。
- Qdrant 向量索引和 dense retrieval。
- BM25 sparse retrieval、RRF 融合、rerank provider 边界。
- Evidence Pack 构建。
- 知识库实体、文档归属和知识库级多文档问答。
- `/chat` 返回 answer、citations 和 retrieval trace，并持久化 chat trace。
- 用户问题记录和基础反馈。
- 受控 Agent 工作流：planner、retrieval、analyst、writer、reviewer 固定链路。
- Agent run 和 Agent step 持久化，支持 `/agent-runs` 创建、列表、详情和按知识库、route、status、answer_status、时间范围过滤。
- 确定性知识运营建议：基于证据不足问题、低质量反馈和失败文档生成 FAQ 草稿、引用复核和重建索引建议。
- 前端三栏工作区：知识库、文档列表、知识运营建议、Chat/Agent 模式、引用、retrieval trace、Agent step trace、Agent run 历史回看和过滤。

当前尚未实现：

- 多格式文档解析。
- 用户、登录、RBAC、审计日志。
- SSE 流式输出和多轮会话。
- 评测 API、统计看板。
- 热门问题、无答案问题、低质量引用等持久化知识运营清单和处理状态。
- LangGraph 编排替换、外部搜索工具和 LLM-backed Knowledge Operations Agent。

因此，当前项目应被定义为：

```text
核心 RAG、知识库产品层、trace 持久化和受控 Agent 第一版已跑通；
P4 权限/审计/评测/运营清单与 P5 Agent 增强仍在推进中。
```

---

## 5. 目标架构

```text
Frontend UI
  -> Knowledge Base / Document / Chat / Citation / Feedback / Trace / Dashboard

FastAPI API Layer
  -> Auth / KnowledgeBase / Document / Search / Chat / Agent / Eval

Business Services
  -> Document Service
  -> Retrieval Service
  -> Chat Service
  -> Feedback Service
  -> Knowledge Operations Service
  -> Trace Service
  -> Agent Orchestration Service

AI Capability Layer
  -> LLM Provider
  -> Embedding Provider
  -> Reranker Provider
  -> Parser Provider

Storage Layer
  -> PostgreSQL metadata
  -> Qdrant vectors
  -> Redis queue/cache
  -> local filesystem or object storage
```

---

## 6. 核心模块

### 6.1 知识库管理

负责知识库创建、文档归属、访问范围、统计信息和后续切片策略配置。下一阶段的首要目标是把当前全局文档列表升级为知识库下的文档管理。

### 6.2 文档处理

当前 PDF 链路继续保留。后续扩展 DOCX、Markdown、HTML、TXT、PPTX，并逐步增加语义结构切片、文档版本、替换、删除和重新索引。

### 6.3 Hybrid RAG

当前实现是可复用核心资产。后续重点是从单文档 `doc_id` 检索扩展到知识库级 `knowledge_base_id` 检索，并将 Evidence Pack 与 trace 持久化。

### 6.4 智能问答

从单轮、单文档问答升级为知识库级、多轮、可流式输出的问答。答案必须携带引用来源和证据不足标记。

### 6.5 知识运营

知识运营是系统的产品闭环：记录问题、答案、引用、反馈和失败原因，帮助管理员发现热门问题、无答案问题、低质量引用、过期文档和需要补充的知识内容。

第一版不需要复杂大屏，但应提供最小可用清单：

- 高频问题。
- 无答案或证据不足问题。
- 被用户标记为无用或引用不准的回答。
- 解析失败或索引失败文档。
- 建议补充或更新的文档。

### 6.6 Multi-Agent

Agent 作为后置增强层。优先支持复杂查询分解、跨文档检索、证据归纳、答案撰写和引用审核。第一版 Agent 应走固定工作流，不做开放式自动工具调用。

### 6.7 评测与可观测

每次问答和 Agent 执行都应生成可回放 trace。评测体系先从固定 QA 集、检索命中、引用准确和延迟统计开始。

---

## 7. 风险与取舍

| 风险 | 应对 |
|---|---|
| 产品范围过大 | 下一阶段只做知识库问答和知识运营最小闭环，不立即上完整 Agent |
| 多格式解析质量不稳定 | PDF 保持主链路，其他格式分批接入 |
| 引用不支撑答案 | 强化 Evidence Pack、citation verifier 和评测 |
| Agent 成本和不可控性 | 使用固定工作流、最大迭代次数和工具权限 |
| 权限系统改造成本高 | 数据模型先预留知识库归属和访问边界 |
| 现有代码与新定位不一致 | 保留 RAG 引擎，逐步替换产品概念和 API 范围 |

---

## 8. 当前建议

当前阶段继续推进 P5，并并行收尾 P4。优先完成：

```text
知识运营清单持久化
  -> 审计日志
  -> 评测 API
  -> 最小 auth/RBAC
  -> LangGraph 评估
```

这一步完成后，系统会从“可验证知识库问答”进一步进入“可运营、可回放、可评测的受控 Agent 知识平台”。
