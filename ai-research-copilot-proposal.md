# ScholarPilot：AI Research Copilot 智能科研助理系统规划方案

---

## 1. 项目定位

### 1.1 项目名称

**ScholarPilot：面向论文阅读、证据检索与研究分析的 AI Research Copilot**

### 1.2 核心目标

ScholarPilot 不是普通的“上传 PDF 后问答”的知识库系统，而是一个以 **证据优先（Evidence-first）** 为核心原则的科研工作台。系统需要帮助用户完成论文阅读、文献追踪、概念理解、多论文对比、研究脉络梳理和初步综述整理。

系统目标包括：

- 接入多源科研资料：PDF、arXiv、Semantic Scholar、Web 页面、GitHub README。
- 建立可追溯的论文知识库：文档、章节、chunk、表格、图片说明、引用位置统一管理。
- 提供高质量检索增强生成：Hybrid RAG、reranker、引用定位、答案可溯源。
- 支持 Agentic RAG：让系统能够规划检索步骤、拆解复杂问题、调用工具并审查答案。
- 支持研究分析任务：论文总结、多论文对比、related work 草稿、研究趋势梳理。
- 建立评测闭环：用指标持续衡量检索质量、答案可信度、引用准确性和响应效率。

### 1.3 设计原则

1. **证据先于生成**
   - 系统先检索和组织证据，再生成答案。
   - 每个关键结论必须能回到原文 chunk、页码、章节或外部来源。

2. **科研任务优先**
   - 不追求泛聊天能力，优先服务论文阅读和研究分析。
   - 问答、总结、对比、综述都围绕“文献证据”展开。

3. **可落地优先**
   - MVP 先做稳定的文档解析、检索、引用问答。
   - GraphRAG、多模态解析、多 Agent 协作作为增强层逐步加入。

4. **可评测、可观察、可迭代**
   - 不能只凭主观感觉判断 RAG 效果。
   - 从第一阶段开始记录检索结果、引用命中、生成答案和用户反馈。

---

## 2. 当前技术趋势与项目吸收方向

### 2.1 从传统 RAG 到 Agentic RAG

传统 RAG 通常是固定链路：

```
用户问题 -> 向量检索 -> 拼接上下文 -> LLM 生成答案
```

这个流程适合简单问答，但面对科研任务会遇到问题：

- 用户问题经常不完整，需要 query rewrite 或 query decomposition。
- 多论文对比需要多轮检索和结构化汇总。
- 综述生成需要先找方向、再找代表论文、再组织证据。
- 检索结果可能质量不够，需要自动反思和二次检索。

因此 ScholarPilot 采用 **Agentic RAG** 作为中长期架构：Agent 不直接“自由发挥”，而是在受控工作流中完成规划、检索、证据筛选、答案审查和工具调用。

### 2.2 从纯向量检索到 Hybrid Retrieval

科研文本中包含大量术语、缩写、模型名、数据集名和公式符号。只使用 embedding 检索容易漏掉精确关键词，只使用 BM25 又难以理解语义相似问题。

系统采用 Hybrid Retrieval：

- 稀疏检索：BM25 / SPLADE / sparse vector，用于精确术语匹配。
- 稠密检索：embedding，用于语义召回。
- 融合排序：Reciprocal Rank Fusion（RRF）或 weighted fusion。
- 二阶段重排：cross-encoder reranker 提升 Top-K 上下文质量。

### 2.3 从纯文本 PDF 到 Layout-aware / Multimodal Document AI

论文 PDF 不只是正文，还包含：

- 标题层级
- 摘要、方法、实验、结论等章节结构
- 表格
- 公式
- 图片和图注
- 页码、列布局、参考文献

MVP 阶段先保证文本和章节结构稳定解析；增强阶段引入 Docling 等工具处理版面、表格、公式、图注，必要时扩展到视觉文档检索。

### 2.4 从“答案生成”到“答案评测”

RAG 系统必须有评测闭环，否则很难判断优化是否有效。ScholarPilot 将在规划中加入：

- 检索质量：Recall@K、MRR、context precision、context recall。
- 答案质量：faithfulness、answer relevance、citation coverage。
- 引用质量：引用是否支持答案中的关键 claim。
- 工程指标：延迟、成本、失败率、缓存命中率。

### 2.5 从工具堆叠到受控 Agent 工作流

Agent 能力越强，越需要边界。系统不设计“完全自主研究员”，而是设计可控的科研工作流：

- 明确每个 Agent 的职责。
- 明确工具权限。
- 记录每次检索、工具调用和生成结果。
- 高风险动作需要用户确认。
- 对外部网页和上传文档中的 prompt injection 做隔离和清洗。

---

## 3. 系统总体架构

### 3.1 架构总览

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend UI                           │
│  Next.js / React                                             │
│  文档库 / Chat / 阅读器 / 引用面板 / 研究任务工作台             │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                         API Layer                            │
│  FastAPI                                                     │
│  Auth / Project / Document / Chat / Search / Agent / Eval    │
└───────────────┬───────────────────────┬─────────────────────┘
                │                       │
                ▼                       ▼
┌──────────────────────────┐   ┌──────────────────────────────┐
│      RAG Service          │   │        Agent Service          │
│  Query Rewrite            │   │  Planner                      │
│  Hybrid Retrieval         │   │  Retriever                    │
│  Rerank                   │   │  Evidence Synthesizer         │
│  Citation Grounding       │   │  Reviewer                     │
└──────────────┬───────────┘   └──────────────┬───────────────┘
               │                              │
               ▼                              ▼
┌──────────────────────────┐   ┌──────────────────────────────┐
│    Knowledge Services     │   │        Tool Services          │
│  Document Parser          │   │  arXiv API                    │
│  Chunker                  │   │  Semantic Scholar API         │
│  Embedding Pipeline       │   │  Web Fetcher                  │
│  Graph Builder            │   │  PDF / HTML Parser            │
└──────────────┬───────────┘   └──────────────┬───────────────┘
               │                              │
               ▼                              ▼
┌─────────────────────────────────────────────────────────────┐
│                         Storage Layer                        │
│  PostgreSQL: metadata / projects / tasks / citations          │
│  Vector DB: Qdrant / Milvus / FAISS                           │
│  Object Storage: raw PDF / parsed markdown / figures          │
│  Cache: Redis                                                 │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                         Model Layer                          │
│  LLM: Qwen / OpenAI / DeepSeek / Llama                       │
│  Embedding: Qwen3 Embedding / BGE-M3 / E5                    │
│  Reranker: Qwen3 Reranker / BGE Reranker                     │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 核心分层说明

| 层级 | 职责 |
|---|---|
| Frontend UI | 论文库、阅读器、对话、引用面板、研究任务入口 |
| API Layer | 对外接口、任务管理、权限、状态查询 |
| RAG Service | 查询改写、混合检索、重排、引用绑定、答案生成 |
| Agent Service | 复杂任务规划、多步检索、证据汇总、答案审查 |
| Knowledge Services | 文档解析、chunk 切分、embedding、图谱构建 |
| Tool Services | arXiv、Semantic Scholar、网页抓取、PDF/HTML 处理 |
| Storage Layer | 元数据、向量索引、原始文件、解析结果、缓存 |
| Model Layer | LLM、embedding、reranker、本地或云端推理 |

---

## 4. 核心功能模块

### 4.1 文档接入与解析模块

#### 支持数据源

- 本地 PDF 上传
- arXiv 论文链接或 ID
- Semantic Scholar 论文搜索结果
- Web 论文页面
- GitHub README / 技术报告
- 后续可扩展：DOCX、PPTX、HTML、Markdown

#### 处理流程

```
原始文档
  ↓
文件识别与去重
  ↓
文本 / 版面 / 表格 / 图注解析
  ↓
章节结构识别
  ↓
清洗与规范化
  ↓
语义 chunk 切分
  ↓
metadata 绑定
  ↓
embedding 与索引构建
  ↓
可检索知识库
```

#### 解析策略

MVP 阶段：

- PyMuPDF / pdfplumber：提取正文、页码、基础结构。
- GROBID 可选：解析标题、作者、摘要、参考文献等学术元数据。
- BeautifulSoup / trafilatura：解析网页正文。

增强阶段：

- Docling：处理复杂 PDF 版面、表格、阅读顺序、公式和图注。
- 表格单独入库：表格内容既保留 markdown，也保留结构化 JSON。
- 图片和图注建立关联：用于回答“图 3 说明了什么”一类问题。

#### 文档状态

每篇文档需要有清晰状态：

- `uploaded`
- `parsing`
- `parsed`
- `indexing`
- `indexed`
- `failed`

失败时记录原因，支持重新解析和重新索引。

---

### 4.2 知识库与数据模型

#### 核心对象

```json
{
  "document": {
    "doc_id": "paper_xxx",
    "title": "论文标题",
    "authors": ["作者 A", "作者 B"],
    "source": "pdf | arxiv | semantic_scholar | web",
    "published_at": "2026-01-01",
    "metadata": {
      "doi": "...",
      "arxiv_id": "...",
      "venue": "...",
      "url": "..."
    }
  },
  "chunk": {
    "chunk_id": "chunk_xxx",
    "doc_id": "paper_xxx",
    "section": "Method",
    "page_start": 3,
    "page_end": 4,
    "text": "chunk text",
    "chunk_type": "paragraph | table | figure_caption | reference",
    "token_count": 512
  },
  "citation": {
    "citation_id": "cite_xxx",
    "chunk_id": "chunk_xxx",
    "quote": "原文片段",
    "page": 3,
    "confidence": 0.92
  }
}
```

#### 存储建议

- PostgreSQL：项目、文档、chunk 元数据、任务状态、引用记录。
- Qdrant / Milvus：向量检索，适合服务化部署。
- FAISS：适合本地 MVP 和快速实验。
- Redis：缓存 query rewrite、embedding、检索结果和任务状态。
- 本地文件系统或对象存储：保存原始 PDF、解析 markdown、图片文件。

---

### 4.3 Hybrid RAG 检索系统

#### 检索流程

```
用户问题
  ↓
问题分类
  ↓
Query Rewrite / Query Decomposition
  ↓
Dense Retrieval + Sparse Retrieval
  ↓
RRF 融合排序
  ↓
Reranker 重排
  ↓
Evidence Pack 构建
  ↓
LLM 基于证据生成答案
  ↓
Citation Verifier 校验引用
  ↓
返回答案 + 引用 + 原文位置
```

#### Query 类型

| 类型 | 示例 | 策略 |
|---|---|---|
| 单篇理解 | “这篇论文的方法是什么？” | 限定 doc_id 检索，优先 Method / Experiment |
| 跨论文对比 | “A 和 B 的区别？” | 分别检索两组证据，再结构化对齐 |
| 开放检索 | “最近有哪些 RAG 评测方法？” | 外部论文 API + 本地库联合检索 |
| 概念解释 | “什么是 reranker？” | 本地证据优先，不足时 Web / Semantic Scholar |
| 综述生成 | “帮我整理这个方向” | 多轮检索、聚类、代表论文选择、证据 synthesis |

#### Evidence Pack

检索结果不直接塞给模型，而是先整理成 Evidence Pack：

```json
{
  "question": "...",
  "evidence": [
    {
      "doc_id": "...",
      "title": "...",
      "section": "Method",
      "page": 4,
      "text": "...",
      "score": 0.87,
      "source_type": "dense+bm25+rerank"
    }
  ],
  "missing_info": [],
  "retrieval_trace": {
    "rewritten_query": "...",
    "dense_top_k": 30,
    "sparse_top_k": 30,
    "rerank_top_k": 8
  }
}
```

这样后续评测、调试、引用校验都更清楚。

---

### 4.4 Agentic Research Workflow

#### Agent 角色设计

```
┌──────────────────┐
│   Planner Agent   │
│  任务拆解 / 路由   │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Retriever Agent  │
│  多源检索 / 重查   │
└────────┬─────────┘
         │
         ▼
┌────────────────────────┐
│ Evidence Synthesizer    │
│  证据整理 / 结构化归纳   │
└────────┬───────────────┘
         │
         ▼
┌──────────────────┐
│   Reviewer Agent  │
│  引用检查 / 漏洞检查 │
└────────┬─────────┘
         │
         ▼
       答案
```

#### Agent 职责

| Agent | 职责 | 不能做什么 |
|---|---|---|
| Planner Agent | 判断任务类型，拆解步骤，选择工具 | 不直接生成最终答案 |
| Retriever Agent | 调用本地检索、arXiv、Semantic Scholar、Web | 不绕过权限访问外部数据 |
| Evidence Synthesizer | 将证据整理成表格、要点、对比结构 | 不编造没有证据的结论 |
| Reviewer Agent | 检查引用是否支撑结论，标记不确定内容 | 不擅自删除关键分歧 |

#### 受控工作流

Agent 采用 LangGraph 等状态机式编排，而不是完全开放的自动循环。每个任务需要有：

- 输入
- 当前状态
- 已调用工具
- 检索证据
- 生成草稿
- 审查结果
- 最终输出

复杂任务支持中断、继续、人工确认和失败重试。

---

### 4.5 科研任务能力

#### 1. 单篇论文精读

输出内容：

- 研究问题
- 核心贡献
- 方法流程
- 实验设置
- 主要结论
- 局限性
- 可追溯引用

#### 2. 多论文对比

对比维度：

- 问题定义
- 方法路线
- 模型结构
- 数据集
- 评价指标
- 实验结果
- 优势与不足

输出形式：

- 对比表格
- 差异总结
- 引用证据
- 适用场景建议

#### 3. Related Work 草稿生成

流程：

```
研究主题
  ↓
关键词扩展
  ↓
本地库 + 外部论文检索
  ↓
论文聚类
  ↓
代表论文选择
  ↓
按研究路线组织
  ↓
生成草稿 + 引用列表
```

要求：

- 标注每个观点来自哪些论文。
- 明确哪些内容是系统归纳，哪些是原文证据。
- 不自动冒充最终学术写作，只生成可编辑草稿。

#### 4. 研究趋势分析

能力：

- 按关键词追踪近期论文。
- 聚类研究方向。
- 统计高频方法、数据集、任务和指标。
- 生成“本周/本月研究动态”。

#### 5. 阅读路径推荐

输入一个主题后，系统推荐：

- 入门论文
- 经典论文
- 最新代表论文
- 需要先理解的概念
- 推荐阅读顺序

---

### 4.6 前端产品形态

#### 页面结构

```
┌─────────────────────────────────────────────────────────────┐
│ 顶部：项目切换 / 搜索 / 模型状态 / 任务状态                  │
├───────────────┬──────────────────────────┬──────────────────┤
│ 左侧文档库     │ 中间阅读与对话区           │ 右侧证据与引用面板 │
│ 上传 / 分组    │ PDF 阅读器 / Chat          │ chunk / 页码 / 分数 │
│ 标签 / 状态    │ 研究任务工作台             │ 检索轨迹 / 原文定位 │
└───────────────┴──────────────────────────┴──────────────────┘
```

#### 核心视图

- 文档库视图：上传、导入、解析状态、标签、来源。
- 阅读器视图：PDF/Markdown 阅读、选中文本提问、章节导航。
- Chat 视图：基于当前论文或项目知识库对话。
- 引用面板：展示答案依据的 chunk、页码、原文片段、检索分数。
- 研究任务视图：总结、对比、综述、趋势分析任务。
- 评测视图：展示检索质量、引用命中率、用户反馈。

#### 交互原则

- 用户始终能看到答案依据。
- 引用可以点击跳回原文位置。
- 对不确定结论明确标记“证据不足”。
- 对长任务展示进度：检索中、分析中、审查中、完成。

---

## 5. 技术栈规划

### 5.1 后端

| 模块 | 推荐选型 | 说明 |
|---|---|---|
| API 服务 | FastAPI | Python AI 生态友好，开发效率高 |
| 异步任务 | Celery / RQ / Dramatiq | 文档解析、embedding、批量检索 |
| 数据库 | PostgreSQL | 存项目、文档、chunk、任务、引用 |
| 缓存 | Redis | 任务状态、检索缓存、限流 |
| 对象存储 | 本地文件系统 / MinIO / S3 | 保存 PDF、图片、解析结果 |

### 5.2 检索与知识库

| 模块 | MVP | 增强阶段 |
|---|---|---|
| 向量库 | FAISS / Qdrant | Milvus / Qdrant 集群 |
| 稀疏检索 | rank-bm25 | Elasticsearch / OpenSearch / sparse vector |
| 融合排序 | RRF | 可学习权重融合 |
| Reranker | BGE Reranker / Qwen3 Reranker | 按领域微调 reranker |
| 图谱层 | 暂不强依赖 | GraphRAG / Neo4j / NetworkX |

### 5.3 模型层

| 类型 | 可选模型 |
|---|---|
| LLM | Qwen、DeepSeek、OpenAI、Llama |
| Embedding | Qwen3 Embedding、BGE-M3、E5 |
| Reranker | Qwen3 Reranker、BGE Reranker |
| OCR / Layout | Docling、PyMuPDF、pdfplumber、GROBID |

模型策略：

- MVP 支持一种稳定云端 LLM + 一种本地 embedding。
- 后续通过 provider abstraction 支持多模型切换。
- 对成本敏感任务使用小模型，对综述和复杂推理使用强模型。

### 5.4 Agent 编排

| 需求 | 推荐 |
|---|---|
| 状态机式 Agent | LangGraph |
| 简单工具调用 | 函数调用 / tool calling |
| 外部工具协议 | MCP 可作为后续扩展 |
| 可观察性 | LangSmith / OpenTelemetry / 自建 tracing |

### 5.5 前端

| 模块 | 推荐 |
|---|---|
| 框架 | Next.js / React |
| UI | Tailwind CSS + shadcn/ui |
| PDF 阅读 | react-pdf / PDF.js |
| 状态管理 | Zustand / TanStack Query |
| 图表 | ECharts / Recharts |

---

## 6. API 初步设计

### 6.1 文档 API

| 方法 | 路径 | 说明 |
|---|---|---|
| `POST` | `/documents/upload` | 上传 PDF |
| `POST` | `/documents/import/arxiv` | 从 arXiv 导入 |
| `GET` | `/documents` | 获取文档列表 |
| `GET` | `/documents/{doc_id}` | 获取文档详情 |
| `POST` | `/documents/{doc_id}/reindex` | 重新索引 |

### 6.2 检索与问答 API

| 方法 | 路径 | 说明 |
|---|---|---|
| `POST` | `/search` | 返回检索结果和证据包 |
| `POST` | `/chat` | 基于证据回答问题 |
| `GET` | `/citations/{citation_id}` | 获取引用原文位置 |

### 6.3 研究任务 API

| 方法 | 路径 | 说明 |
|---|---|---|
| `POST` | `/tasks/summarize` | 单篇论文总结 |
| `POST` | `/tasks/compare` | 多论文对比 |
| `POST` | `/tasks/related-work` | related work 草稿 |
| `POST` | `/tasks/trends` | 研究趋势分析 |
| `GET` | `/tasks/{task_id}` | 查询任务状态与结果 |

### 6.4 评测 API

| 方法 | 路径 | 说明 |
|---|---|---|
| `POST` | `/eval/dataset` | 创建评测集 |
| `POST` | `/eval/run` | 运行评测 |
| `GET` | `/eval/runs/{run_id}` | 查看评测结果 |

---

## 7. 评测与质量控制

### 7.1 检索评测

指标：

- Recall@K
- MRR
- nDCG
- Context Precision
- Context Recall
- Rerank 后 Top-K 命中率

评测集来源：

- 手工标注的论文问题。
- 论文摘要、章节标题自动生成的问题。
- 用户真实问题脱敏后沉淀。

### 7.2 答案评测

指标：

- Faithfulness：答案是否被检索证据支持。
- Answer Relevance：答案是否回答了用户问题。
- Citation Coverage：关键 claim 是否有引用。
- Citation Accuracy：引用是否真的支持对应 claim。
- Abstention Quality：证据不足时是否能拒答或提示不确定。

### 7.3 工程评测

指标：

- 文档解析成功率。
- 平均索引耗时。
- 平均问答延迟。
- 单次问答 token 成本。
- Agent 任务成功率。
- 外部 API 失败率。

### 7.4 人工反馈

前端保留轻量反馈入口：

- 答案有用 / 无用
- 引用准确 / 不准确
- 缺少关键论文
- 生成内容过长 / 过短

反馈进入评测集和后续优化流程。

---

## 8. 安全与可靠性设计

### 8.1 Prompt Injection 防护

论文 PDF、网页和 README 都可能包含恶意指令。系统需要：

- 将文档内容明确标记为 untrusted content。
- 检索内容只能作为证据，不允许覆盖系统指令。
- 对“忽略之前指令”“泄露密钥”等文本做检测和降权。
- 工具调用由后端策略控制，不能由文档内容直接触发。

### 8.2 工具权限控制

- arXiv、Semantic Scholar、Web fetcher 只允许访问白名单能力。
- 写文件、删除数据、批量外发请求等动作需要明确授权。
- Agent 每一步工具调用都记录 trace。

### 8.3 数据可靠性

- 原始文件和解析结果分开保存。
- chunk 与文档版本绑定，重新解析后生成新版本索引。
- 引用需要保存页码、章节和原文片段，避免答案脱离来源。

### 8.4 失败处理

- 文档解析失败：返回具体原因，允许重试。
- 检索证据不足：提示用户补充文档或扩大搜索范围。
- 外部 API 失败：降级到本地知识库。
- Agent 循环过多：强制停止并返回当前已完成结果。

---

## 9. 阶段路线图

### Phase 0：项目基础规划

目标：

- 明确产品边界、核心数据模型和技术栈。
- 建立仓库结构、开发规范和配置管理。
- 准备少量测试论文作为样例数据。

交付物：

- 后端和前端基础骨架。
- 文档、chunk、citation 的数据库模型。
- 基础配置和本地启动方式。

### Phase 1：可运行 MVP

目标：

- 用户可以上传 PDF。
- 系统可以解析、切分、embedding、入库。
- 用户可以围绕单篇论文提问。
- 答案带引用来源。

核心功能：

- PDF 上传与解析。
- 基础 chunking。
- FAISS / Qdrant 向量检索。
- 单篇论文 Chat。
- 引用面板。

成功标准：

- 10 篇论文可稳定解析和索引。
- 常见论文理解问题可以返回可追溯答案。
- 每个答案至少展示 Top 引用来源。

### Phase 2：高质量 RAG

目标：

- 提升检索质量和答案可信度。
- 支持项目级多文档问答。

核心功能：

- Query rewrite。
- BM25 + embedding hybrid retrieval。
- RRF 融合排序。
- Reranker。
- Evidence Pack。
- 基础 RAG 评测集。

成功标准：

- 相比纯向量检索，Top-K 命中率明显提升。
- 答案 hallucination 明显减少。
- 可查看检索轨迹和评测结果。

### Phase 3：科研任务工作流

目标：

- 从问答升级到研究任务辅助。

核心功能：

- 单篇论文总结。
- 多论文对比。
- Related Work 草稿。
- 阅读路径推荐。
- LangGraph Agent 工作流。

成功标准：

- 多论文对比结果结构稳定。
- Related Work 草稿能按主题聚类并附引用。
- Agent 任务可中断、可恢复、可追踪。

### Phase 4：趋势分析与增强知识层

目标：

- 支持长期研究主题跟踪和知识组织。

核心功能：

- arXiv / Semantic Scholar 定期检索。
- 研究方向聚类。
- 趋势报告。
- GraphRAG 原型。
- 表格、图注、公式增强解析。

成功标准：

- 用户可以订阅主题并获得周期性研究动态。
- 系统能展示论文之间的主题、方法、引用或相似关系。
- 对复杂综述类问题提供更完整的证据组织。

---

## 10. 风险与取舍

### 10.1 主要风险

| 风险 | 表现 | 应对 |
|---|---|---|
| PDF 解析质量不稳定 | chunk 错乱、表格丢失、页码错误 | MVP 先限制支持范围，后续引入 Docling/GROBID |
| RAG 答案看似合理但引用不支撑 | 用户难以信任结果 | Citation Verifier + faithfulness 评测 |
| Agent 过度复杂 | 难调试、成本高、结果不稳定 | 先做固定工作流，再逐步开放工具 |
| 外部 API 不稳定 | 导入失败、搜索慢 | 本地缓存、失败重试、降级策略 |
| 模型成本过高 | 长任务费用不可控 | 小模型处理检索和总结，大模型处理复杂 synthesis |
| 多源数据权限复杂 | 用户私有文档与公开资料混杂 | 项目级隔离、权限校验、trace 记录 |

### 10.2 技术取舍

- MVP 不优先做 GraphRAG，先把 Hybrid RAG 和引用做好。
- MVP 不追求所有 PDF 完美解析，先支持常规论文 PDF。
- Agent 不直接自由访问所有工具，必须走受控 workflow。
- 先做项目内知识库，再做跨项目全局推荐。
- 先用通用 embedding/reranker，后续再考虑领域微调。

---

## 11. 现阶段建议

当前阶段最重要的是避免一开始铺太大。建议先从 Phase 1 开始，做出一个稳定的闭环：

```
上传论文 -> 解析 -> 切分 -> 向量化 -> 检索 -> 回答 -> 引用跳转
```

只要这个闭环稳定，后面的 Hybrid RAG、Agent、趋势分析和 GraphRAG 都有基础。反过来，如果底层文档解析和引用链路不稳，越早上 Agent，系统越容易变成“说得漂亮但不可验证”。

### 第一阶段最小功能清单

- 后端 FastAPI 项目骨架。
- PostgreSQL 文档与 chunk 数据模型。
- PDF 上传与解析。
- 基础 chunking。
- embedding 生成。
- FAISS 或 Qdrant 检索。
- Chat API。
- 答案引用返回。
- Next.js 三栏界面原型。

### 第一阶段不做的内容

- 完整 GraphRAG。
- 自动写长篇综述。
- 复杂多 Agent 协作。
- 全量多模态 PDF 理解。
- 多用户权限系统。
- 复杂部署和分布式扩展。

---

## 12. 参考趋势来源

- Agentic RAG：传统 RAG 正在向具备规划、工具调用、反思和多 Agent 协作的 Agentic RAG 演进。
- GraphRAG：通过知识图谱和社区摘要增强跨文档、多跳问题理解。
- Hybrid Search：主流向量数据库和检索系统均支持 dense + sparse / BM25 融合检索。
- RAG Evaluation：RAGAS 等评测框架强调 context precision、context recall、faithfulness 等指标。
- Document AI：Docling 等工具开始将 PDF 解析从纯文本提取推进到版面、表格、公式和图注理解。
- LLM Security：OWASP LLM Top 10 将 prompt injection、excessive agency、vector/embedding weaknesses 等列为重要风险。
