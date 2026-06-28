# ScholarPilot

ScholarPilot 是一个面向论文阅读、证据检索与研究分析的 AI Research Copilot。项目目标是构建一个以 **Evidence-first RAG** 为核心的科研工作台，帮助用户完成论文解析、可信问答、多文档对比、研究脉络梳理和趋势追踪。

当前仓库处于规划与基础建设阶段，已完成项目方案、分阶段开发方案和项目规则文档。后续开发将按照阶段路线逐步推进。

---

## 1. 项目定位

ScholarPilot 不是普通的“上传 PDF 后聊天”的知识库系统，而是一个强调证据链、引用来源和可验证输出的科研辅助系统。

核心原则：

- **证据优先**：先检索和组织证据，再生成答案。
- **引用可追溯**：答案中的关键结论应能追溯到文档、章节、页码和 chunk。
- **科研任务导向**：围绕论文阅读、文献理解、多论文对比和研究分析设计能力。
- **分阶段落地**：先完成稳定 MVP，再扩展 Hybrid RAG、Agentic Workflow 和 GraphRAG。
- **可评测迭代**：通过检索指标、引用质量和人工反馈持续优化系统。

---

## 2. 核心能力规划

### 2.1 文档接入

计划支持：

- 本地 PDF 上传
- arXiv 论文导入
- Semantic Scholar 论文搜索
- Web 页面解析
- GitHub README / 技术报告解析

文档进入系统后，会经过解析、清洗、切分、向量化和索引构建，形成可检索知识库。

### 2.2 Evidence-first RAG

基础链路：

```text
用户问题
  -> Query Rewrite
  -> Hybrid Retrieval
  -> Rerank
  -> Evidence Pack
  -> LLM Answer
  -> Citation Verification
  -> 答案 + 引用来源
```

系统不会只返回自然语言答案，还需要返回：

- 文档 ID
- chunk ID
- 文档标题
- 章节
- 页码
- 原文片段
- 检索分数

### 2.3 Hybrid Retrieval

计划采用稀疏检索与稠密检索结合：

- BM25 / sparse vector：适合术语、缩写、模型名和数据集名精确匹配。
- embedding retrieval：适合语义召回。
- RRF / weighted fusion：融合多路召回结果。
- reranker：对 Top-K 上下文做二阶段重排。

### 2.4 Agentic Research Workflow

复杂研究任务将通过受控 Agent 工作流完成：

```text
Planner Agent
  -> Retriever Agent
  -> Evidence Synthesizer
  -> Reviewer Agent
  -> Final Output
```

Agent 不做无限自主循环，每一步都应有明确输入、输出、工具权限和 trace。

### 2.5 科研任务

计划支持：

- 单篇论文精读总结
- 多论文结构化对比
- Related Work 草稿
- 研究主题阅读路径推荐
- 研究趋势追踪
- 论文关系与主题聚类

---

## 3. 系统架构规划

```text
Frontend UI
  Next.js / React
  文档库 / 阅读器 / Chat / 引用面板 / 研究任务工作台

API Layer
  FastAPI
  Document API / Search API / Chat API / Agent API / Eval API

RAG Service
  Query Rewrite / Hybrid Retrieval / Rerank / Evidence Pack / Citation Grounding

Agent Service
  Planner / Retriever / Evidence Synthesizer / Reviewer

Knowledge Services
  Parser / Chunker / Embedding Pipeline / Graph Builder

Tool Services
  arXiv / Semantic Scholar / Web Fetcher / PDF Parser

Storage Layer
  PostgreSQL / Vector DB / Object Storage / Redis

Model Layer
  LLM / Embedding / Reranker / Layout Parser
```

---

## 4. 技术栈规划

### 4.1 后端

- Python 3.10+
- FastAPI
- Pydantic
- PostgreSQL
- Redis
- Celery / RQ / Dramatiq
- Pytest

### 4.2 前端

- Next.js
- React
- TypeScript
- Tailwind CSS
- shadcn/ui
- TanStack Query
- PDF.js / react-pdf

### 4.3 AI 与检索

- LLM：Qwen、DeepSeek、OpenAI、Llama
- Embedding：Qwen3 Embedding、BGE-M3、E5
- Reranker：Qwen3 Reranker、BGE Reranker
- Vector Store：FAISS、Qdrant、Milvus
- Sparse Search：BM25、Elasticsearch、OpenSearch
- Agent Workflow：LangGraph
- RAG Evaluation：RAGAS 或自建评测集

### 4.4 文档解析

- PyMuPDF
- pdfplumber
- GROBID
- Docling
- BeautifulSoup / trafilatura

---

## 5. 阶段路线

详细阶段方案见：[doc/分阶段开发方案.md](doc/分阶段开发方案.md)

### Phase 0：项目基础建设

目标：

- 初始化仓库结构。
- 建立前后端工程骨架。
- 建立配置、测试和开发规范。
- 准备基础样例数据。

### Phase 1：单篇论文 RAG MVP

目标：

```text
上传 PDF -> 解析 -> chunk -> embedding -> 检索 -> 问答 -> 引用返回
```

这是当前最高优先级。

### Phase 2：高质量 Hybrid RAG

目标：

- Query rewrite
- BM25 + embedding hybrid retrieval
- RRF 融合
- reranker
- Evidence Pack
- RAG 评测集

### Phase 3：科研任务工作流

目标：

- 单篇论文总结
- 多论文对比
- Related Work 草稿
- 阅读路径推荐
- Agentic RAG 工作流

### Phase 4：趋势追踪与知识增强

目标：

- arXiv / Semantic Scholar 定期检索
- 研究主题聚类
- 趋势报告
- GraphRAG 原型
- 表格、图注、公式增强解析

### Phase 5：产品化与部署

目标：

- Docker 部署
- 日志与监控
- 基础权限
- API 限流
- 成本统计
- 数据备份

---

## 6. 当前仓库结构

```text
ScholarPilot/
├─ README.md
├─ RULE.md
├─ ai-research-copilot-proposal.md
└─ doc/
   └─ 分阶段开发方案.md
```

当前仓库主要包含项目规划文档。代码目录将在 Phase 0 中创建。

---

## 7. 重要文档

| 文件 | 说明 |
|---|---|
| [ai-research-copilot-proposal.md](ai-research-copilot-proposal.md) | 项目总体规划方案 |
| [doc/分阶段开发方案.md](doc/分阶段开发方案.md) | 分阶段开发路线、验收标准和阶段状态 |
| [RULE.md](RULE.md) | 项目开发规则、Git 规则、低耦合规范、测试规范 |

---

## 8. 开发规范摘要

完整规则见：[RULE.md](RULE.md)

### 8.1 阶段推进

每个阶段必须有：

- 阶段状态
- 开发任务
- 验收标准
- 测试结果
- Git commit
- GitHub push

### 8.2 代码质量

必须遵守：

- 模块职责单一。
- 服务之间低耦合。
- 外部能力通过接口封装。
- API 层不写复杂业务逻辑。
- Repository 层不调用 LLM 或外部 API。
- 新功能必须有验证方式。
- 删除无用导入、无用变量和临时代码。

### 8.3 RAG 质量

RAG 输出必须尽量包含证据链：

- 文档
- 章节
- 页码
- chunk
- 原文片段
- 检索分数

证据不足时，系统必须明确提示资料不足，不能编造结论。

---

## 9. 本地开发状态

当前阶段尚未创建后端和前端工程，因此暂无可运行应用命令。

Phase 0 完成后，README 将补充：

- 后端启动命令
- 前端启动命令
- 环境变量说明
- 数据库初始化方式
- 测试命令
- 常见问题

---

## 10. GitHub

仓库地址：

```text
https://github.com/kelongyan/ScholarPilot.git
```

首次推送流程：

```powershell
git init
git add README.md RULE.md ai-research-copilot-proposal.md doc/分阶段开发方案.md
git commit -m "docs: initialize ScholarPilot planning docs"
git branch -M main
git remote add origin https://github.com/kelongyan/ScholarPilot.git
git push -u origin main
```

---

## 11. 当前最高优先级

下一步建议进入 Phase 0：

```text
初始化项目骨架
  -> 后端 FastAPI 健康检查
  -> 前端 Next.js 基础页面
  -> 基础测试框架
  -> 本地开发命令
  -> 阶段进度记录
```

Phase 0 完成后，再进入 Phase 1 的 PDF RAG MVP。

