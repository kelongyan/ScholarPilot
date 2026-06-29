# ScholarPilot 开发环境配置

本文档记录 ScholarPilot 的开发环境状态与配置方法。

---

## 环境总览（当前实际状态）

| 组件 | 状态 | 位置 / 说明 |
|---|---|---|
| Python (Windows) | ✅ 3.13.9 (miniconda) | `D:\miniconda3\python.exe` |
| uv (Windows) | ✅ 0.11.25 | `C:\Users\admin\AppData\Roaming\Python\Python313\Scripts\uv.exe` |
| Node.js | ✅ v24.14.0 | `C:\Program Files\nodejs\` |
| pnpm | ✅ 11.5.2 | 全局（PATH 可用） |
| WSL Ubuntu-22.04 | ✅ 运行中 | 数据在 `D:\WSL\Ubuntu\ext4.vhdx`（164G） |
| Ollama (本地模型) | ✅ 0.30.11 | `localhost:11434`，监听 `0.0.0.0`，模型在 `D:\Ollama\models` |
| LLM (qwen3:14b) | ✅ 已加载 | Q4_K_M，9.28GB，OpenAI 兼容 `/v1/chat/completions` |
| Embedding (bge-m3) | ✅ 已加载 | F16，1024 维，OpenAI 兼容 `/v1/embeddings` |
| uv (WSL) | ✅ 0.11.25 | `~/.local/bin/uv`（WSL 内） |
| Python (WSL) | ✅ 3.12.13 | uv 自动下载，WSL venv `.venv-wsl` |
| Docker Engine | ✅ 29.6.1 + compose 5.2.0 | 装在 WSL Ubuntu 内，数据在 D 盘 |
| PostgreSQL/Qdrant/Redis | ✅ Docker 容器运行中 | 端口 5432/6333/6379 |

**关键：WSL 数据已在 D 盘**（`D:\WSL\Ubuntu\ext4.vhdx`），Docker 数据天然在 D 盘，无需迁移。

---

## 架构：API 在 Windows，Worker 在 WSL

由于 **RQ worker 依赖 `os.fork()`，Windows 不支持**，采用分离部署：

| 服务 | 运行环境 | 原因 |
|---|---|---|
| FastAPI API | Windows (uvicorn) | 无 fork 依赖，热重载方便 |
| RQ Worker | WSL Ubuntu (Linux) | RQ 需要 `os.fork()` |
| PostgreSQL/Qdrant/Redis | WSL Docker | 统一基础设施 |

API 和 Worker 共享同一个 PostgreSQL（Docker），文件路径用 **POSIX 相对路径**（`storage/xxx.pdf`）存储，确保跨平台兼容。

---

## uv 使用说明

### Windows 侧（API）

`uv` 不在 bash PATH，需用完整路径：

```bash
export UV="/c/Users/admin/Appdata/Roaming/Python/Python313/Scripts/uv.exe"
export UV_LINK_MODE=copy   # 避免 hardlink 警告

cd D:/ScholarPilot/backend
"$UV" sync --extra dev
"$UV" run uvicorn app.main:app --reload
```

### WSL 侧（Worker）

```bash
wsl -d Ubuntu-22.04
export PATH="$HOME/.local/bin:$PATH"
cd /mnt/d/ScholarPilot/backend
UV_PROJECT_ENVIRONMENT=.venv-wsl uv sync --extra dev --python 3.12
```

---

## Docker（已安装完成）

Docker Engine 装在 WSL Ubuntu-22.04 内（非 Docker Desktop）。
- 镜像加速器已配置（`/etc/docker/daemon.json`）：`docker.1ms.run`、`docker.xuanyuan.me`、`docker.m.daocloud.io`
- systemd 自启已启用
- 用户 `ykl` 已加入 docker 组

**注意**：docker 命令必须在 WSL 内执行，Windows 侧无 docker CLI。

### 常用命令（WSL 内）

```bash
cd /mnt/d/ScholarPilot
docker compose up -d        # 启动 postgres + qdrant + redis
docker compose ps           # 查看状态
docker compose down         # 停止（保留数据）
docker compose down -v      # 停止并删除数据卷
docker compose logs -f      # 查看日志
```

### 端口冲突处理（已完成）

WSL 内原有的本地 PostgreSQL 14 和 Redis 已停止并禁用自启（`systemctl disable`），避免与 Docker 容器端口冲突。如需恢复，重新 `systemctl enable`。

---

## 启动 ScholarPilot（完整流程）

### 1. 启动基础设施（WSL 内）

```bash
wsl -d Ubuntu-22.04
cd /mnt/d/ScholarPilot
docker compose up -d
docker compose ps    # 等待三个服务 healthy
```

### 2. 配置本地模型（Ollama）

本地已部署 Ollama + qwen3:14b (LLM) + bge-m3 (Embedding)，详见
`doc/06-local-llm-deployment.md`。`.env` 已配置为本地模型：

```env
LLM_PROVIDER=openai
LLM_BASE_URL=http://172.31.240.1:11434/v1
LLM_MODEL=qwen3:14b
LLM_API_KEY=ollama

EMBEDDING_PROVIDER=openai
EMBEDDING_BASE_URL=http://172.31.240.1:11434/v1
EMBEDDING_MODEL=bge-m3:latest
EMBEDDING_API_KEY=ollama
EMBEDDING_DIM=1024
```

**关键：Ollama 网络配置**
- Ollama 必须监听 `0.0.0.0:11434`（设置 `OLLAMA_HOST=0.0.0.0:11434`），否则 WSL worker 连不上。
- 用 `scripts/start_ollama.bat` 启动 Ollama（已设好 `OLLAMA_MODELS=D:\Ollama\models` 和 `OLLAMA_HOST=0.0.0.0:11434`）。
- `.env` 里的 `172.31.240.1` 是 WSL2 网关 IP（Windows 主机），Windows 侧和 WSL 侧都能访问。**不要用 localhost**——WSL worker 用 localhost 连不到 Windows 的 Ollama。
- 需要一条防火墙规则允许 WSL 子网 (172.16.0.0/12) 访问 11434 端口（见 `scripts/add-firewall-rule.ps1`，以管理员运行）。
- WSL2 网关 IP 可能变化，若 worker 报 embedding 连接错误，用 `wsl -d Ubuntu-22.04 -- ip route | grep default` 查最新网关 IP 并更新 `.env`。

### 3. 运行数据库迁移（首次，Windows 侧）

```bash
export UV="/c/Users/admin/Appdata/Roaming/Python/Python313/Scripts/uv.exe"
cd D:/ScholarPilot/backend
"$UV" run alembic upgrade head
```

### 4. 启动 API（Windows 侧）

```bash
"$UV" run uvicorn app.main:app --reload    # :8000
```

### 5. 启动 RQ Worker（WSL 侧，另开终端）

```bash
wsl -d Ubuntu-22.04
export PATH="$HOME/.local/bin:$PATH"
cd /mnt/d/ScholarPilot/backend
UV_PROJECT_ENVIRONMENT=.venv-wsl uv run rq worker --url "redis://localhost:6379/0" default
```

### 6. 启动前端（Windows 侧）

```bash
cd D:/ScholarPilot/frontend
pnpm dev    # :3000
```

### 7. 端到端验证

浏览器打开 http://localhost:3000：
1. 上传 PDF → 等 status=indexed
2. 提问 → 看答案和引用

---

## 已验证的端到端流程

- ✅ Docker 三服务启动（postgres/qdrant/redis healthy）
- ✅ Alembic 迁移建表（documents/chunks/citations）
- ✅ API 启动（/health, /documents, /docs）
- ✅ Ollama 本地模型加载（qwen3:14b + bge-m3，监听 0.0.0.0）
- ✅ WSL worker 通过网关 IP 访问 Ollama（防火墙规则已加）
- ✅ PDF 上传 → 解析 → chunk → embedding → 索引（status: indexed, pages: 4）
- ✅ Qdrant chunks 集合创建（1024 维，匹配 bge-m3）
- ✅ RAG 问答：基于证据生成答案 + 返回引用（page/score/原文片段）
- ✅ 证据不足时明确拒答（"当前资料不足以支持可靠回答"）

**端到端 RAG 闭环已完全跑通。**

---

## 常见问题

### `docker` 命令在 Windows 终端不可用
Docker 装在 WSL 内，**必须在 WSL 终端执行 docker 命令**。

### RQ worker 报 `os.fork` 错误
Worker 必须在 WSL（Linux）跑，不能在 Windows 跑。

### 文件路径错误（worker 找不到 PDF）
文件路径已改为 POSIX 相对路径（`storage/xxx.pdf`）。API 和 worker 都从 backend 目录解析。不要改回绝对路径。

### WSL 重启后 docker 没启动
systemd 已启用，docker 已 `systemctl enable`。若没起来，手动 `sudo systemctl start docker`。

### 端口冲突（5432/6379）
WSL 内本地 PostgreSQL/Redis 已禁用。若仍冲突，检查 `ss -tlnp | grep <port>`。
