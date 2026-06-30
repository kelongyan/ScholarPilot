# Kairos Development Roadmap

---

## 1. 路线图定位

本文档描述 Kairos 按新产品定位推进的开发阶段。新主线是“可验证的团队知识库问答与知识运营平台”，原有科研论文 Copilot 能力作为垂直场景保留，Multi-Agent 作为后期受控工作流能力保留。

当前代码已经完成核心 RAG 引擎的大部分基础能力。后续路线不从零开始，而是在现有 FastAPI、Next.js、PostgreSQL、Qdrant、Redis/RQ 和 Hybrid RAG 代码上继续演进。

---

## 2. 阶段状态规则

| 状态 | 含义 |
|---|---|
| `Not Started` | 尚未开始 |
| `In Progress` | 正在开发 |
| `Review` | 功能完成，等待运行验证、文档同步、提交或推送 |
| `Done` | 验收通过，测试记录完整，已提交并推送 |
| `Blocked` | 被外部条件或产品决策阻塞 |

阶段标记为 `Done` 必须同时满足：

- 功能实现完成。
- 必要测试通过。
- 关键运行流程已验证。
- 文档与代码一致。
- `doc/04-development-progress.md` 已更新。
- 相关代码已 commit 并 push。

---

## 3. 总体路线

```text
Phase 0  工程基础与运行环境
Phase 1  核心 RAG 闭环
Phase 2  Hybrid RAG 与 Trace 引擎
Phase 3  知识库产品层
Phase 4  知识运营、权限、审计、评测与可观测
Phase 5  Multi-Agent 协作引擎
Phase 6  生产化、统计看板与扩展生态
```

当前优先级：Phase 5 已启动，先落地受控 Agent 工作流的最小可验证切片。

技术采用原则：

- Phase 3 不引入大型新基础设施，优先复用现有 PostgreSQL、Qdrant、Redis/RQ 和 RAG pipeline。
- Phase 4 开始补 trace、评测、权限和审计，但先用自建最小实现。
- Phase 5 才引入 LangGraph 等 Agent 编排工具。
- Phase 6 后再评估 Docling、Langfuse/Phoenix、LiteLLM、OpenSearch、Milvus、MCP、A2A、GraphRAG 等升级项。

---

## 4. Phase 0：工程基础与运行环境

状态：`Done`

目标：

- 建立前后端工程骨架。
- 建立本地运行、测试、lint、配置管理和仓库规范。

已交付：

- FastAPI 后端骨架。
- Next.js 前端骨架。
- `uv`、Ruff、Pytest、pnpm、ESLint 基础配置。
- 项目文档、规则文档和基础 README。

验收标准：

- 后端健康检查可启动。
- 前端页面可启动。
- 后端测试和前端 lint/build 可运行。

---

## 5. Phase 1：核心 RAG 闭环

状态：`Done`

目标：

```text
上传 PDF -> 解析 -> 切片 -> embedding -> 向量索引 -> 检索 -> 问答 -> 引用返回
```

已交付：

- PDF 上传和本地文件保存。
- 文档、chunk、citation 数据模型。
- PyMuPDF 文本解析和页码保留。
- token chunking 和 overlap。
- embedding provider、LLM provider。
- Qdrant 向量索引。
- Redis/RQ 异步处理。
- `/documents` 和 `/chat` API。
- 前端三栏工作区、上传面板、文档列表、Chat、引用面板。

遗留限制：

- 仅支持 PDF。
- 问答范围是单文档 `doc_id`。
- 没有知识库实体、用户、权限和会话。

---

## 6. Phase 2：Hybrid RAG 与 Trace 引擎

状态：`Done`

目标：

把基础向量检索升级为可调试、可评测的 Hybrid RAG。

已实现能力：

- query rewrite seam。
- dense retrieval + BM25 sparse retrieval。
- RRF 融合排序。
- reranker provider 边界和 deterministic fallback reranker。
- Evidence Pack。
- retrieval trace 返回到前端。
- 最小固定评测 fixture。

已完成收尾：

- 真实端到端流程已验证：上传 PDF、等待 indexed、提问、查看 citations 和 trace。
- runtime 验证覆盖 dense、BM25 sparse、RRF、rerank、Evidence Pack 和 citations。
- 修复 BM25 raw score 非正时 sparse 结果被误丢弃的边界问题。
- 文档状态已同步。

验收标准：

- `/chat` 每次回答可查看 trace。
- Evidence Pack 与 citations 对齐。
- 后端相关测试通过。
- 前端 lint/build 通过。

---

## 7. Phase 3：知识库产品层

状态：`Done`

这是已完成阶段。

目标：

从“单文档 RAG”升级为“多知识库、多文档智能知识库”。

主要功能：

- 新增 `KnowledgeBase` 数据模型。
- 文档归属于知识库。
- 支持知识库列表、创建、更新、归档或删除。
- 文档列表按知识库过滤。
- `/chat` 支持 `knowledge_base_id` 范围检索。
- retrieval service 支持多文档候选召回。
- 前端增加知识库选择、知识库文档分组和基础空状态。
- 记录用户问题、答案、引用和证据不足状态。
- 支持最小反馈入口：有用/无用、引用准确/不准确。
- 为后续权限预留 owner、visibility、access policy 字段。

验收标准：

- 用户可以创建知识库并上传文档到指定知识库。
- 用户可以对一个知识库内多份文档提问。
- 引用能标识来源文档、页码和 chunk。
- 不破坏单文档问答兼容路径。
- 用户反馈和无答案问题可以被记录。
- 后端测试覆盖知识库、文档归属和知识库级问答。

---

## 8. Phase 4：知识运营、权限、审计、评测与可观测

状态：`In Progress`

目标：

补齐团队知识库真正可运营所需的安全、反馈、质量管理和可观测能力。

主要功能：

- 用户登录和 JWT 会话。
- RBAC 基础角色：管理员、知识库管理员、普通用户。
- 知识库级访问控制。
- 操作审计：文档上传、删除、重建索引、权限修改。
- Trace 持久化：query、rewrite、检索结果、Evidence Pack、answer、citations、latency、model。
- 评测 API：固定 QA 集、运行记录、结果查看。
- 前端轻量反馈：有用/无用、引用准确/不准确。
- 知识运营清单：高频问题、无答案问题、低质量引用、解析失败文档、索引失败文档。
- 管理员处理状态：待处理、已补充文档、已忽略、已重建索引。

可选工具边界：

- 可引入 Ragas 或 DeepEval 做离线评测，但前提是已有固定评测集和 trace 表。
- 暂不引入 Langfuse 或 Phoenix；先保证自建 trace 数据结构稳定。
- 暂不引入 OpenFGA 或 Casbin；先实现最小 RBAC。

验收标准：

- 未授权用户不能访问受限知识库。
- 每次问答生成可查询 trace。
- 至少一组评测集可重复运行。
- 关键操作写入审计日志。
- 管理员可以看到无答案问题和低质量引用清单。
- 用户反馈能进入后续评测和知识库改进流程。

---

## 9. Phase 5：Multi-Agent 协作引擎

状态：`In Progress`

目标：

在已有知识库、权限、知识运营和 trace 基础上，引入受控 Agent 工作流。

主要功能：

- LangGraph 或等价状态机式编排。
- Planner Agent：任务分类和步骤规划。
- Retrieval Agent：本地知识库检索，后续扩展外部搜索。
- Analyst Agent：证据对比、趋势分析、逻辑归纳。
- Writer Agent：结构化回答或草稿生成。
- Reviewer Agent：引用支撑和幻觉检查。
- Agent trace 可视化基础数据。
- 知识运营 Agent：基于反馈和无答案问题生成 FAQ 草稿、补文档建议或重建索引建议。

工具边界：

- 推荐引入 LangGraph。
- 不使用开放式无限循环 Agent。
- 不引入 MCP 工具市场。
- 不做 A2A 跨系统 Agent 协作。
- 不自动写入、删除或修改外部系统数据。
- 外部搜索工具只作为受控 Retrieval Agent 能力，必须有白名单和 trace。

验收标准：

- 简单问题走短链路，复杂问题走多 Agent 链路。
- 每个 Agent 步骤有输入、输出、耗时和状态。
- 最大迭代次数和失败退出策略生效。
- 最终输出保留 citations。

---

## 10. Phase 6：生产化、统计看板与扩展生态

状态：`Not Started`

目标：

将系统整理为可部署、可运维、可观察的产品形态。

主要功能：

- Docker 化完整部署。
- 生产环境配置和密钥管理。
- 日志、错误追踪、限流和备份。
- 平台统计看板：用户数、知识库数、文档数、问答次数。
- 知识库看板：文档增长、热门问题、质量趋势。
- 运营看板：无答案问题、低质量引用、用户反馈、待处理知识缺口。
- 成本统计：模型、token、Agent 步骤消耗。
- 多格式解析增强：DOCX、Markdown、HTML、TXT、PPTX。
- 长期扩展评估：GraphRAG、MCP、A2A、移动端、企业 IM。

后期升级候选：

| 方向 | 候选工具 | 触发条件 |
|---|---|---|
| 文档解析增强 | Docling、Unstructured、MarkItDown、Tika | 多格式和复杂版面成为明确需求 |
| 检索扩展 | Qdrant sparse vector、OpenSearch、Elasticsearch | Python BM25 或 Qdrant 单库无法满足规模 |
| 向量集群 | Milvus | Qdrant 容量、并发或集群能力不足 |
| 模型网关 | LiteLLM Proxy | 多模型供应商、预算、限流、fallback 复杂化 |
| 观测平台 | Langfuse、Phoenix | 自建 trace 不能满足分析、成本和评测需求 |
| 权限系统 | Casbin、OpenFGA | 简单 RBAC 无法覆盖团队共享和继承权限 |
| 工具生态 | MCP、A2A | 出现稳定外部工具市场或跨 Agent 系统集成需求 |

验收标准：

- 一套命令可启动完整服务。
- 生产配置不包含密钥。
- 关键服务有健康检查。
- 看板能展示核心运营指标。

---

## 11. 当前开发建议

Phase 5 已启动，当前已有受控 Agent 固定工作流、Agent run/step 持久化、前端 run 回看入口、Agent run 过滤和确定性知识运营建议。下一步不要直接扩张到开放式工具市场或跨系统 Agent，而是继续围绕“可回放、可评测、可运营”的受控工作流补齐产品闭环。

推荐拆分顺序：

1. P4 知识运营清单持久化：无答案问题、低质量引用、解析失败文档、索引失败文档和处理状态。
2. 审计日志：文档上传、reindex、反馈、Agent run 查看等关键操作。
3. 评测 API：固定 QA 集、运行记录、结果查看，并复用 chat trace 与 agent trace。
4. 最小 auth/RBAC：先实现管理员、知识库管理员、普通用户的基础边界。
5. LangGraph 评估：仅在当前状态机 API 契约稳定后替换内部 runner，不改变外部 `/agent-runs` 契约。
