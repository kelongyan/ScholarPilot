# ScholarPilot 本地模型部署与云端 API 配置

---

## 1. 部署目的

ScholarPilot RAG 流水线需要两个核心模型：

- **LLM** — 用于答案生成、查询改写、引文验证。
- **Embedding** — 用于文档分块向量化与语义检索。

模型提供方式有两种，可独立选择、混合搭配：

| 方式 | 适用场景 | 优势 |
|---|---|---|
| **本地部署**（Ollama） | 开发测试、离线环境、零 API 成本 | 无网络依赖、无 token 计费、数据不出本地 |
| **云端 API**（Gemini / OpenAI / Qwen 等） | 生产环境、更高模型能力、免维护 | 模型能力强、无需 GPU、开箱即用 |

Backend Provider 层通过统一的 `EmbeddingProvider` / `LLMProvider` 接口访问模型，切换提供方式只需修改 `.env` 配置，业务代码无需改动。

---

## 2. 硬件环境

| 组件 | 规格 |
|---|---|
| GPU | NVIDIA RTX 3090 (24GB VRAM) |
| 存储 | `D:\Ollama\models` (9.72 GB 已用) |
| 系统 | Windows 11 |

**容量评估：**

| 模型 | VRAM 预估 | 说明 |
|---|---|---|
| Qwen3-14B (Q4_K_M) | ~9–10 GB | 14.8B 参数 + KV cache |
| BGE-M3 (F16) | ~1.5 GB | 566M 参数 |
| **合计** | **~11.5 GB** | 可同时加载，剩余 ~12.5 GB 用于 KV cache 和其他进程 |

RTX 3090 24GB 可同时运行两模型，无需卸载切换。

---

## 3. 模型选择依据

依据 `doc/03-technology-stack.md` §10.2 和 §10.3 的推荐：

| 用途 | 模型 | 理由 |
|---|---|---|
| LLM | **Qwen3-14B** | 中英文双强、学术文本支持好、工具调用/思考模式原生支持、14B Q4_K_M 可装入 24GB |
| Embedding | **BGE-M3** | 中英文混合检索强、本地部署便利、1,024 维与 Qdrant 兼容 |

### 替代方案

| 模型 | 优点 | 缺点 |
|---|---|---|
| DeepSeek-V3 / R1 | 推理能力强 | 671B MoE 无法本地运行 |
| Qwen3-32B | 效果更好 | Q4 仍超 24GB，需流式卸载 |
| BGE-EN-ICL / E5 | 英文检索强 | 中文混合场景不如 BGE-M3 |
| Qwen3 Embedding (local) | 生态一致 | 暂不支持 Ollama |

**当云端服务可用时可切换为：** Qwen-Max / DeepSeek-V3 / OpenAI GPT-4o（LLM），OpenAI text-embedding-3-large / Qwen3 Embedding（Embedding）。

---

## 4. 部署架构

### 4.1 三种配置模式

```text
模式 A：全本地（开发测试首选）
────────────────────────────
Windows Host
├── Ollama Server (localhost:11434)
│   ├── qwen3:14b      → LLM 生成
│   └── bge-m3:latest  → Embedding
└── ScholarPilot Backend
    ├── LLMProvider       → base_url = http://localhost:11434/v1
    └── EmbeddingProvider → base_url = http://localhost:11434/v1


模式 B：全云端（生产 / 免 GPU 维护）
──────────────────────────────────
ScholarPilot Backend
├── LLMProvider       → 云端 API（Gemini / DeepSeek / Qwen-Max / OpenAI）
└── EmbeddingProvider → 云端 API（Gemini / OpenAI / Qwen3 Embedding）


模式 C：混合（本地 LLM + 云端 Embedding）← 当前使用
─────────────────────────────────────────────────
Windows Host
├── Ollama Server (localhost:11434)
│   └── qwen3:14b      → LLM 生成
└── 云端 Embedding API（Gemini / OpenAI）
    └── base_url = https://api.futureppo.top/v1
        model = gemini-embedding-001（3072 维）
```

Backend Provider 层通过 OpenAI-compatible API 调用模型，`base_url` 指向对应端点。切换提供方式时只需修改 `.env` 中的 `*_PROVIDER`、`*_BASE_URL`、`*_MODEL`、`*_API_KEY`，业务代码无需改动。

---

## 5. 本地部署：安装与配置

> 如果选择**云端 API 模式**（模式 B 或 C），可跳过本节，直接看 §6。

### 5.1 安装 Ollama

从 [ollama.ai](https://ollama.ai) 下载 Windows 安装包。

安装后版本：

```powershell
ollama --version
# ollama version is 0.30.11
```

### 5.2 配置模型存储路径

Ollama 默认模型存储在 `C:\Users\<user>\.ollama\models`。为节省 C 盘空间，迁移至 D 盘：

```powershell
# 设置用户级环境变量
[System.Environment]::SetEnvironmentVariable(
    "OLLAMA_MODELS", "D:\Ollama\models", "User"
)
```

设置后重启 Ollama 服务。后续所有模型文件下载至 `D:\Ollama\models\blobs\`。

### 5.3 拉取模型

```powershell
# LLM
ollama pull qwen3:14b

# Embedding
ollama pull bge-m3:latest
```

验证：

```powershell
ollama list
```

### 5.4 启动与持久化

Ollama 安装后默认注册为 Windows 用户级服务，开机自启。确认运行状态：

```powershell
# 查看进程
Get-Process ollama

# API 健康检查
curl.exe http://localhost:11434/api/tags
```

---

## 6. 模型详情

### 6.1 Qwen3-14B

| 属性 | 值 |
|---|---|
| 模型名 | `qwen3:14b` |
| 架构 | Qwen3 |
| 参数量 | 14,768,307,200 (14.8B) |
| 量化 | Q4_K_M (file_type 15) |
| 上下文长度 | 40,960 tokens |
| Embedding 维度 | 5,120 |
| 层数 | 40 |
| 注意力头 | 40 (8 KV heads, GQA) |
| FFN 维度 | 17,408 |
| RoPE 频率基数 | 1,000,000 |
| 特殊 Token | BOS=151643, EOS=151645 |
| 能力 | `completion`, `tools`, `thinking` |
| 磁盘占用 | ~9.28 GB |

### 6.2 BGE-M3

| 属性 | 值 |
|---|---|
| 模型名 | `bge-m3:latest` |
| 架构 | BERT |
| 参数量 | 566.70M |
| 量化 | F16 |
| 上下文长度 | 8,192 tokens |
| Embedding 维度 | 1,024 |
| 能力 | `embedding` |
| 磁盘占用 | ~1.16 GB |

---

## 7. API 接口验证

### 7.1 本地 Ollama

#### 7.1.1 LLM 生成 (OpenAI-compatible `/v1/chat/completions`)

```powershell
curl.exe http://localhost:11434/v1/chat/completions `
  -H "Content-Type: application/json" `
  -d '{\"model\":\"qwen3:14b\",\"messages\":[{\"role\":\"user\",\"content\":\"Explain RAG in one sentence\"}]}'
```

#### 7.1.2 Embedding (OpenAI-compatible `/v1/embeddings`)

```powershell
curl.exe http://localhost:11434/v1/embeddings `
  -H "Content-Type: application/json" `
  -d '{\"model\":\"bge-m3:latest\",\"input\":\"RAG is a technique for knowledge-grounded generation\"}'
```

#### 7.1.3 Ollama 原生 API

```powershell
# 生成
curl.exe http://localhost:11434/api/generate `
  -H "Content-Type: application/json" `
  -d '{\"model\":\"qwen3:14b\",\"prompt\":\"Hello\",\"stream\":false}'

# 嵌入
curl.exe http://localhost:11434/api/embed `
  -H "Content-Type: application/json" `
  -d '{\"model\":\"bge-m3:latest\",\"input\":\"Hello world\"}'
```

### 7.2 云端 API

云端 API 直接通过 OpenAI-compatible 端点调用，格式与 §7.1 相同，仅 `base_url` 和 `api_key` 不同。

#### 7.2.1 Embedding（Gemini 示例）

```powershell
curl.exe https://api.futureppo.top/v1/embeddings `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer sk-xxxxx" `
  -d '{\"model\":\"gemini-embedding-001\",\"input\":\"ScholarPilot test\"}'
```

#### 7.2.2 LLM（DeepSeek 示例）

```powershell
curl.exe https://api.deepseek.com/v1/chat/completions `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer sk-xxxxx" `
  -d '{\"model\":\"deepseek-chat\",\"messages\":[{\"role\":\"user\",\"content\":\"Hi\"}]}'
```

#### 7.2.3 LLM（Gemini 示例）

```powershell
curl.exe https://generativelanguage.googleapis.com/v1beta/openai/chat/completions `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer $(gcloud auth print-access-token)" `
  -d '{\"model\":\"gemini-2.5-flash\",\"messages\":[{\"role\":\"user\",\"content\":\"Hi\"}]}'
```

---

## 8. 后端集成配置

在 `.env` 中配置。以下是三种模式的完整示例：

### 8.1 模式 A：全本地（Ollama）

```env
# LLM — Ollama 本地
LLM_PROVIDER=openai
LLM_MODEL=qwen3:14b
LLM_BASE_URL=http://localhost:11434/v1
LLM_API_KEY=ollama  # Ollama 忽略 key，但不能为空

# Embedding — Ollama 本地
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=bge-m3:latest
EMBEDDING_BASE_URL=http://localhost:11434/v1
EMBEDDING_API_KEY=ollama
EMBEDDING_DIM=1024
```

### 8.2 模式 B：全云端

```env
# LLM — 云端（以 DeepSeek 为例）
LLM_PROVIDER=openai
LLM_MODEL=deepseek-chat
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_API_KEY=sk-xxxxx

# Embedding — 云端（以 Gemini 为例）
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=gemini-embedding-001
EMBEDDING_BASE_URL=https://api.futureppo.top/v1
EMBEDDING_API_KEY=sk-xxxxx
EMBEDDING_DIM=3072
```

也可使用 OpenAI 官方：

```env
# LLM — OpenAI
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-xxxxx

# Embedding — OpenAI
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_BASE_URL=https://api.openai.com/v1
EMBEDDING_API_KEY=sk-xxxxx
EMBEDDING_DIM=1536
```

### 8.3 模式 C：混合（本地 LLM + 云端 Embedding）← 当前使用

```env
# LLM — 本地 Ollama（Qwen3-14B）
LLM_PROVIDER=openai
LLM_MODEL=qwen3:14b
LLM_BASE_URL=http://localhost:11434/v1
LLM_API_KEY=ollama

# Embedding — 云端 Gemini（3072 维，中英文混合强）
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=gemini-embedding-001
EMBEDDING_BASE_URL=https://api.futureppo.top/v1
EMBEDDING_API_KEY=sk-xxxxx
EMBEDDING_DIM=3072
```

**切换原则：** LLM 和 Embedding 可独立选择提供方式。只需修改对应 provider 的 `*_PROVIDER`、`*_BASE_URL`、`*_MODEL`、`*_API_KEY` 和 `*_DIM`，业务代码无需改动。

---

## 9. 常用运维命令

```powershell
# 查看模型列表
ollama list

# 查看模型磁盘占用
Get-ChildItem -Path "D:\Ollama\models" -Recurse -File |
  Measure-Object -Property Length -Sum |
  Select-Object Count, @{N="TotalGB";E={[math]::Round($_.Sum/1GB, 2)}}

# 删除模型
ollama rm <model-name>

# 更新模型
ollama pull <model-name>

# 查看 Ollama 日志（Troubleshooting）
# Ollama 日志输出至启动它的终端，或查看 Windows Event Viewer
```

---

## 10. 注意事项

### 10.1 本地模型：内存与显存

- Qwen3-14B (Q4_K_M) 在 24GB 显存下可与 BGE-M3 同时驻留。
- 首次加载模型需约 10–30 秒（加载权重至显存），后续请求延迟在可接受范围内。
- 如需释放显存，可使用 `ollama stop` 或等待模型超时卸载（默认 5 分钟无请求后自动卸载）。

### 10.2 API Key

- **本地 Ollama：** OpenAI-compatible API 不验证 key。配置中 `LLM_API_KEY` 和 `EMBEDDING_API_KEY` 设为任意非空字符串即可。
- **云端 API：** 需填入真实 API key。Gemini 通过第三方代理时 key 格式为 `sk-xxxxx`；Google 官方 API 使用 OAuth 或服务账号。

### 10.3 模型更新

Ollama 模型标签（如 `qwen3:14b`）可能随上游更新。使用 `ollama pull` 拉取最新版本。若需固定版本，使用具体标签（如 `qwen3:14b-q4_K_M`）。当前拉取时间：2026-06-29。

云端模型版本由提供商管理，通常自动更新。需固定版本时在 `.env` 中指定具体模型名（如 `gpt-4o-2024-08-06`）。

### 10.4 网络隔离

- **本地模型：** 运行在 `localhost:11434`，无外部网络依赖。在离线开发环境中仍可正常工作。
- **云端 API：** 需要互联网连接。若网络不通，Embedding/LLM 调用将失败。建议在生产环境配置重试和超时。

### 10.5 维度一致性

切换 Embedding 模型时，必须同步更新 `EMBEDDING_DIM` 以匹配新模型的输出维度。维度不匹配会导致 Qdrant 向量写入或检索失败。

| 模型 | 维度 |
|---|---|
| BGE-M3（本地） | 1,024 |
| Gemini Embedding-001 | 3,072 |
| OpenAI text-embedding-3-small | 1,536 |
| OpenAI text-embedding-3-large | 3,072 |
| Qwen3 Embedding | 1,024 |

### 10.6 端到端验证

```powershell
# 1. 本地 LLM 测试
curl.exe http://localhost:11434/v1/chat/completions `
  -H "Content-Type: application/json" `
  -d '{\"model\":\"qwen3:14b\",\"messages\":[{\"role\":\"user\",\"content\":\"Hi\"}]}'

# 2. 云端 Embedding 测试（以 Gemini 为例）
curl.exe https://api.futureppo.top/v1/embeddings `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer sk-xxxxx" `
  -d '{\"model\":\"gemini-embedding-001\",\"input\":\"test\"}'
```

---

## 11. 未来扩展

| 阶段 | 计划 | 时间 |
|---|---|---|
| Phase 2 | 增加本地 Reranker 模型（BGE Reranker v2 / Qwen3 Reranker），提升检索质量 | 后续阶段 |
| Phase 3+ | 评估 vLLM / llama.cpp server 替换 Ollama（更高吞吐、更细粒度控制） | 后续阶段 |
| Phase 3+ | 评估 Qwen3-32B 是否需要 2×RTX 3090 或流式卸载方案 | 后续阶段 |
| Phase 3+ | 接入 Gemini / OpenAI 官方 SDK（非仅 OpenAI-compatible 代理） | 后续阶段 |
| Phase 5 | 根据成本/效果自动在本地与云端之间切换模型 | 后续阶段 |

---

*文档版本: 2026-06-29*
*部署人: AI Assistant (ScholarPilot)*
