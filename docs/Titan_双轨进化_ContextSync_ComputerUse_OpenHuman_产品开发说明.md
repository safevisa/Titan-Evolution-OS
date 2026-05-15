# Titan Evolution OS — 双轨进化产品开发说明（产品层摘要）

> 版本 v1.0 · 2026-05-15  
> 决策基线：Computer Use **云沙箱优先并部署到服务器**；Context Sync 第一期 **Gmail + Google Calendar + GitHub 全接**；OpenHuman 以 **GPL 合规独立侧车** 与 Titan B2B **并行**；在有利于产品进化时可做 **架构重构**。

---

## ⚠️ 开发实施请以完整开发框架为准

**所有编码、PR、排障必须遵循：**

### [docs/development/README.md](./development/README.md)（索引 · DEV-SPEC-1.0）

| 文档 | 用途 |
|------|------|
| [00-开发总则与决策记录](./development/00-开发总则与决策记录.md) | ADR、术语、冻结决策 |
| [01-模块依赖与实施顺序](./development/01-模块依赖与实施顺序.md) | 依赖图、甘特、PR 顺序 |
| [M00](./development/M00-仓库准备与分支策略.md) … [M06](./development/M06-部署与运维.md) | **按模块开发**的完整规格 |
| [07-可观测性与排障手册](./development/07-可观测性与排障手册.md) | 出问题先查 |
| [附录-接口与数据字典](./development/附录-接口与数据字典.md) | 表、API、任务名、capability |

本文档保留产品愿景与架构总览；**字段级/文件级/任务名** 以 `docs/development/` 为准。

---

## 1. 产品定位与双轨战略

### 1.1 一句话

**Titan B2B**：多租户、可审计、可进化的「团队数字员工操作系统」。  
**OpenHuman 侧车（Titan Personal Line）**：GPL 合规的独立个人助理运行时，通过标准 API 向 Titan 提供「上下文同步 + 个人桌面体验」，不污染 B2B 核心许可与部署边界。

### 1.2 为什么双轨而不是硬合并

| 维度 | Titan B2B 核心 | OpenHuman 侧车 |
|------|------------------|----------------|
| 许可证 | 自有 / 可闭源 SaaS | **GPL-3.0**（必须隔离进程与仓库边界） |
| 用户 | 租户 / 团队 / 行业插件 | 个人、桌面、本地优先 |
| 数据主权 | 租户隔离、Postgres/Qdrant、审计 | 设备本地 SQLite + 可选同步到 Titan |
| 集成方式 | `execute_capability`、计量、grants | HTTP/gRPC 侧车 API，Titan 只消费「已脱敏摘要」 |

聚合的是 **能力模式**（auto-fetch、memory tree、token 压缩、GUI 自动化），不是把 OpenHuman Rust 核心链进 backend wheel。

### 1.3 新增两大能力模块（B2B 内）

1. **Context Sync（上下文同步）** — OpenHuman 启发，Titan 自研实现  
   - 定时/手动拉取 Gmail、Google Calendar、GitHub → 分块 → 压缩 → Qdrant + Memory Tree rollup → Agent prompt 注入。

2. **Computer Use（计算机使用）** — Agent-S（Apache-2.0）云沙箱  
   - 无 API 的遗留系统、桌面软件、网页后台操作；任务在 **隔离 VM** 内执行，结果与录屏回传 Titan。

---

## 2. 目标架构（允许重构后的目标态）

```
                         ┌─────────────────────────────────────┐
                         │           用户 / 租户管理员            │
                         └──────────────┬──────────────────────┘
                                        │
          ┌─────────────────────────────┼─────────────────────────────┐
          │                             │                             │
          ▼                             ▼                             ▼
   ┌──────────────┐            ┌──────────────┐            ┌──────────────────┐
   │ Next.js 前端  │            │ Titan API     │            │ OpenHuman 侧车    │
   │ B2B 控制台    │◄──────────►│ FastAPI       │◄──REST────►│ (GPL, 独立容器)   │
   └──────────────┘            │ execute_cap…  │            │ 个人助理 / 可选   │
                               └───────┬──────┘            └──────────────────┘
                                       │
         ┌─────────────────────────────┼─────────────────────────────┐
         │                             │                             │
         ▼                             ▼                             ▼
  ┌─────────────┐              ┌─────────────┐              ┌─────────────────┐
  │ Celery      │              │ Postgres     │              │ Qdrant           │
  │ worker+beat │              │ 租户/任务/审计 │              │ 向量 + tree 元数据 │
  └──────┬──────┘              └─────────────┘              └─────────────────┘
         │
         ├── context_sync.* (Gmail/Calendar/GitHub)
         ├── agent tasks (现有)
         └── computer_use orchestrator
                    │
                    ▼
         ┌──────────────────────────────────────┐
         │  Computer Use Runner 集群（云沙箱）      │
         │  - 每任务 ephemeral VM / Firecracker    │
         │  - gui-agents (Agent-S3) + UI-TARS     │
         │  - 录屏、步骤日志、只读回传 Titan         │
         └──────────────────────────────────────┘
```

### 2.1 建议的重构（收益大于成本时执行）

当前集成层（`execute_capability`、审计、幂等、计量）**保留**，在其上增加 **领域子包**，避免 `integrations/` 无限膨胀：

```
backend/app/
  integrations/          # 现有：catalog, executor, transport, oauth…
  context_sync/          # 新：fetchers, chunker, rollup, beat tasks
  computer_use/          # 新：orchestrator, runner client, sandbox policy
  memory/                # 扩展：memory_tree.py, token_compress.py
```

**统一仍走 `execute_capability`**：Context Sync 的「手动同步」、Computer Use 的「提交任务」都注册为 catalog 能力，便于 grants、审计、计费一致。

**Celery Beat** 扩展（`celery_app.py`）：

| 任务名 | 周期 | 说明 |
|--------|------|------|
| `titan.context_sync.tick` | 20 min | 对所有「已连接且开启 sync」的租户×数据源拉增量 |
| `titan.context_sync.rollup` | 6 h | Memory Tree 父节点摘要 |
| `titan.evolution.scan_all` | 1 h | 现有 |
| `titan.computer_use.reaper` | 15 min | 清理超时 VM、归档录屏 |

---

## 3. Context Sync — 第一期（Gmail / Google Calendar / GitHub）

### 3.1 产品目标

- 租户 OAuth 连接后，**无需用户每次对话前粘贴上下文**，Agent 自动拥有近 7–30 天的压缩上下文。
- 与 OpenHuman 对齐的体验指标：**首次全量同步完成后，Researcher/Manager 类 Agent 的首次有效回复质量明显提升**。

### 3.2 OAuth 与 Provider 设计

在 `providers.py` 新增（与现有 `google_youtube_oauth` **拆分 scope**，避免混用）：

| Provider ID | 用途 | Google / GitHub 范围（示例） |
|-------------|------|------------------------------|
| `google_workspace_oauth` | Gmail + Calendar | `gmail.readonly`, `calendar.readonly` |
| `github_oauth` | 仓库/PR/Issue | `repo`, `read:user`（按最小权限可再收） |

**实现注意**：现有 `GOOGLE_OAUTH_CLIENT_*` 可复用同一 Google Cloud 项目，但 **redirect path 与 token 存储分 provider**，刷新逻辑进 `oauth_token_refresh.py`。

### 3.3 数据管道（单条记录生命周期）

```
OAuth 连接 ─► sync_state 表（cursor / historyId / last_sync_at）
      │
      ▼
Fetcher（per source）─► 原始 payload（短期 Redis 可选）
      │
      ▼
Normalizer ─► CanonicalDocument { source, external_id, title, body_text, occurred_at, url }
      │
      ▼
Chunker ─► ≤3000 token 块（对齐 OpenHuman）
      │
      ▼
TokenCompress（TokenJuice 等价）─► 进 LLM / 进向量前统一压缩
      │
      ├──► Qdrant upsert（payload: tenant_id, source, level, parent_id, external_id）
      └──► 可选 skill_doc / markdown 快照（租户配置）
      │
      ▼
Rollup Job ─► level=1 摘要节点，再 embed
```

### 3.4 各数据源 Fetch 范围（MVP）

| 源 | MVP 拉取 | 增量键 |
|----|----------|--------|
| **Gmail** | INBOX + SENT，最近 30 天，单封上限 256KB | `historyId` |
| **Google Calendar** | 主日历，前后各 14 天事件 | `syncToken` |
| **GitHub** | 用户有权限仓库：Issues + PR + 评论，最近 50 条/库 | `since` / ETag |

### 3.5 新增 Capability（catalog）

| capability_id | 说明 |
|---------------|------|
| `context_sync_run` | params: `sources[]` optional，默认全启 |
| `gmail_send` | 第二期；第一期只读 sync |
| `github_create_pr` | 已有 stub，第二期与 sync 联动 |

**能力包** `context_sync`：`context_sync_run` + 只读查询类（可选 `memory_search_context`）。

### 3.6 数据库（Alembic 建议）

```sql
-- 同步游标与开关
CREATE TABLE integration_sync_states (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  provider VARCHAR(64) NOT NULL,  -- google_workspace | github
  cursor_json JSONB NOT NULL DEFAULT '{}',
  last_success_at TIMESTAMPTZ,
  last_error TEXT,
  enabled BOOLEAN DEFAULT true,
  UNIQUE (tenant_id, provider)
);

-- Memory Tree 节点（与 Qdrant point id 对应）
CREATE TABLE memory_tree_nodes (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  source VARCHAR(32) NOT NULL,     -- gmail | gcal | github
  level SMALLINT NOT NULL,         -- 0=chunk, 1=rollup, 2=...
  parent_id UUID REFERENCES memory_tree_nodes(id),
  external_key VARCHAR(512),
  title TEXT,
  summary TEXT,
  qdrant_point_id VARCHAR(128),
  token_estimate INT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 3.7 API（B2B）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/integrations/oauth/google-workspace/start` | Gmail+Calendar 一次授权 |
| GET | `/integrations/oauth/github/start` | GitHub 授权 |
| GET | `/integrations/tenants/{id}/sync-status` | 三源状态、上次同步、错误 |
| POST | `/integrations/tenants/{id}/sync/trigger` | 立即同步（内部调 `context_sync_run`） |
| GET | `/memory/context-preview` | 管理员预览将注入 Agent 的摘要（脱敏） |

### 3.8 Agent 消费方式

在 `prompt_builder.get_enhanced_prompt` / `BaseAgent` 增加：

1. 按 `task.type` + `agent.role` 检索 Qdrant：`source in (gmail,gcal,github)`，top-k。
2. 注入 system 附录：`## Synced context (compressed)`，总 token 上限可配置（默认 4k）。
3. 与现有 `save_memory` 任务结果共存：任务记忆偏「行为」，Sync 偏「世界状态」。

### 3.9 合规与安全

- 租户级 **opt-in**：`Tenant.config.context_sync.enabled` + 每源开关。
- 日志与审计：同步条数、失败原因；**不**把完整邮件正文写入 `capability_audit_logs`。
- 删除权：断开 OAuth 时触发 `sync_state` 删除 + Qdrant 按 `tenant_id+source` 过滤删除（异步任务）。

---

## 4. Computer Use — 云沙箱（Agent-S）

### 4.1 产品目标

- 为 **Delivery / Operations / Researcher** 提供「像人一样操作浏览器/桌面」的能力，弥补 API 集成空白。
- **默认不在 Titan API 进程内执行 pyautogui**；一律下发到 Runner 沙箱。

### 4.2 技术选型

| 组件 | 选型 | 许可 |
|------|------|------|
| Agent 框架 | `gui-agents` AgentS3 | Apache-2.0 |
| Grounding | UI-TARS-1.5-7B（HF Endpoint 或自托管） | 按模型许可 |
| 沙箱 | Phase1: Docker per task + Xvfb；Phase2: Firecracker/Kata | — |
| 编排 | Titan `computer_use` 服务（Python FastAPI 或 Celery 子队列） | — |

### 4.3 Capability 设计

| capability_id | 说明 |
|---------------|------|
| `computer_use_submit` | `instruction`, `max_steps`(默认30), `viewport` |
| `computer_use_status` | `run_id` |
| `computer_use_cancel` | `run_id` |
| `computer_use_get_artifact` | 录屏 URL / 步骤 JSON（鉴权） |

**能力包** `desktop_automation`：上述四项；默认仅 `enterprise` plan 或显式 grant。

### 4.4 运行流程

```
execute_capability(computer_use_submit)
  → 写入 computer_use_runs (status=queued)
  → Celery: computer_use.dispatch
  → Runner API: POST /runs { instruction, secrets?, network_policy }
  → VM 启动 → AgentS3 loop → 每步截图存对象存储
  → 完成 → status=success|failed, artifact_urls, step_log
  → Webhook/轮询 → Agent 继续后续 LLM 步骤
```

**网络策略（默认）**：沙箱 **无租户内网**；仅 HTTPS 出站；禁止访问 `169.254.0.0/16`、云元数据 IP。

### 4.5 数据库

```sql
CREATE TABLE computer_use_runs (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  task_id UUID REFERENCES tasks(id),
  capability_ref VARCHAR(128),
  instruction TEXT NOT NULL,
  status VARCHAR(32) NOT NULL,  -- queued|running|success|failed|cancelled
  sandbox_id VARCHAR(128),
  step_count INT DEFAULT 0,
  artifact_json JSONB,
  error TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  finished_at TIMESTAMPTZ
);
```

### 4.6 服务器部署（与现有生产一致）

在 `43.128.80.35` 的 compose 中 **新增服务**（建议独立 compose 文件 `docker-compose.computer-use.yml`）：

| 服务 | 镜像/构建 | 端口 |
|------|-----------|------|
| `computer-use-runner` | `backend/runner/Dockerfile` + gui-agents | 内网 8090 |
| `computer-use-gpu`（可选） | UI-TARS vLLM | 内网 8080 |

Titan `backend` / `celery_worker` 环境变量：

- `COMPUTER_USE_RUNNER_URL=http://computer-use-runner:8090`
- `COMPUTER_USE_GROUND_URL=...`
- `COMPUTER_USE_MAX_CONCURRENT=2`（按机器规格调）

**资源**：建议单独 GPU 机型或 CPU 机型 + 远程 HF Endpoint；4C8G 单机并发建议 ≤2 runs。

### 4.7 风险与缓解

| 风险 | 缓解 |
|------|------|
| 任意代码执行 | 仅 Runner 内；`--enable_local_env` 默认 false |
| 凭据泄露 | 沙箱内临时注入、单次任务、结束销毁 |
| 成本失控 | `capability_metering` + 每租户并发上限 + max_steps |
| 恶意指令 | 可选「需 Manager 审批」策略（`Tenant.config.computer_use.require_approval`） |

---

## 5. OpenHuman 侧车 — GPL 合规并行线

### 5.1 边界

- **独立仓库或独立子模块**：`titan-openhuman-sidecar/`（fork 上游或 git submodule，保持 GPL）。
- **独立容器**：`openhuman-sidecar`，**不** link 进 Titan backend 二进制。
- **通信**：仅通过 **HTTPS + 服务账号 JWT**（Titan 签发短期 token）。

### 5.2 Titan 与侧车的分工

| 能力 | 侧车 (OpenHuman) | Titan B2B |
|------|------------------|-----------|
| 桌面吉祥物 / 语音 / Meet | ✅ | ❌ |
| 118+ 个人集成 UI | ✅ | 逐步用 context_sync 覆盖 B2B 高频源 |
| Memory Tree 本地 SQLite | ✅ 主存 | 接收 **摘要同步**（可选） |
| 团队工作流 / 进化 / 多租户 | ❌ | ✅ |
| Computer Use 云沙箱 | 可调用 Titan API | ✅ 拥有 |

### 5.3 侧车 → Titan API（可选同步）

```
POST /api/v1/integrations/sidecar/memory-push
Authorization: Bearer <sidecar_service_jwt>
{
  "tenant_id": "...",
  "user_binding_id": "...",
  "chunks": [{ "source": "openhuman", "title", "compressed_body", "occurred_at" }]
}
```

Titan 侧校验 binding 表，写入 Qdrant，**不**存储 GPL 衍生代码。

### 5.4 产品包装

- **Titan Teams**：现有 SaaS + Context Sync + Computer Use。
- **Titan Personal**（或白标）：安装包 = OpenHuman 侧车 + 配置指向租户 `TITAN_API_PUBLIC_BASE_URL`。
- 同一账号体系：NextAuth / 租户成员绑定 `user_id ↔ sidecar_device_id`。

---

## 6. 共享横切能力

### 6.1 TokenCompress（TokenJuice 等价）

`backend/app/memory/token_compress.py`：

- HTML → Markdown（nh3 + markdownify 或等价）
- 折叠连续空白、剥离 tracking query
- 长列表保留头尾 + `…[N items omitted]…`
- 在 `agent_tool_runner` 工具结果回灌与 context_sync chunk 入库前调用

### 6.2 模型路由（第二期）

`llm.py` 增加 `route_model(task_kind)`：`reasoning | fast | vision`，与 OpenHuman 对齐；Computer Use 的 Worker 模型与 Titan 主模型可分离配置。

---

## 7. 前端（i18n）

| 页面 | 新增 |
|------|------|
| 设置 → 集成 | Google Workspace、GitHub 连接卡片；同步状态、上次时间、「立即同步」 |
| 设置 → 自动化 | Computer Use：开关、并发说明、最近 runs 列表 |
| 任务详情 | 显示 `computer_use_run` 状态与录屏链接 |
| 个人线（可选） | 下载侧车 / 绑定设备 QR |

所有文案进 `frontend` i18n 键，禁止硬编码。

---

## 8. 里程碑与排期（建议）

### Phase 0 — 文档与脚手架（1 周）

- [x] 本文档评审
- [ ] ADR：`docs/adr/001-dual-track-openhuman.md`
- [ ] `context_sync/`、`computer_use/` 空包 + catalog stub

### Phase 1 — Context Sync MVP（3–4 周）

- [ ] OAuth：`google_workspace_oauth`、`github_oauth`
- [ ] Fetchers + sync_state 表 + beat 20min
- [ ] TokenCompress + Qdrant 写入 + prompt 注入
- [ ] API + IntegrationsConsole UI
- [ ] 生产部署 + 单租户试点

### Phase 2 — Computer Use 云沙箱（4–5 周）

- [ ] Runner Dockerfile + `computer_use_submit/status`
- [ ] Celery dispatch + 录屏存储（本地卷或 S3 兼容）
- [ ] grants / metering / 审批策略
- [ ] 生产 compose 扩展 + 压测 2 并发

### Phase 3 — OpenHuman 侧车（4 周，可与 P2 并行）

- [ ] 独立仓库/镜像构建流水线
- [ ] `sidecar/memory-push` + 用户绑定
- [ ] 安装包或脚本指向生产 API

### Phase 4 — 深化（持续）

- [ ] Gmail 发送、GitHub PR 与 sync 联动
- [ ] Memory Tree 多级 rollup
- [ ] Firecracker 沙箱、GPU 本地化
- [ ] 侧车与 B2B 统一计费仪表盘

---

## 9. 验收标准（第一期）

### Context Sync

- [ ] 租户完成 Google + GitHub OAuth 后，20 分钟内自动出现 sync 成功状态
- [ ] Researcher 任务 prompt 中含至少 3 条相关 Gmail/Calendar/GitHub 摘要（可配置）
- [ ] 断开连接后 24h 内相关 Qdrant 点删除
- [ ] 全链路经 `execute_capability` 的手动 `context_sync_run` 有审计记录

### Computer Use

- [ ] 提交「打开浏览器访问 example.com 并截图标题」类任务，沙箱内成功，Titan 可下载 artifact
- [ ] API 进程内无 pyautogui import
- [ ] 失败任务不影响其他租户；并发受 `COMPUTER_USE_MAX_CONCURRENT` 限制

### OpenHuman 侧车

- [ ] 侧车容器独立启动，Titan backend 镜像不含 OpenHuman 源码
- [ ] 法务审查：GPL 边界说明已归档

---

## 10. 环境变量清单（新增摘录）

```bash
# Context Sync
GOOGLE_WORKSPACE_OAUTH_CLIENT_ID=
GOOGLE_WORKSPACE_OAUTH_CLIENT_SECRET=
GITHUB_OAUTH_CLIENT_ID=
GITHUB_OAUTH_CLIENT_SECRET=
CONTEXT_SYNC_INTERVAL_SEC=1200
CONTEXT_SYNC_GMAIL_LOOKBACK_DAYS=30

# Computer Use
COMPUTER_USE_RUNNER_URL=http://computer-use-runner:8090
COMPUTER_USE_GROUND_URL=
COMPUTER_USE_GROUND_MODEL=ui-tars-1.5-7b
COMPUTER_USE_MAX_CONCURRENT=2
COMPUTER_USE_ARTIFACT_DIR=/var/titan/cu-artifacts

# OpenHuman sidecar (Titan API)
TITAN_SIDECAR_JWT_SECRET=
TITAN_SIDECAR_ALLOWED_AUDIENCES=openhuman
```

---

## 11. 与现有文档关系

- 集成细节继续维护：`docs/外部工具与集成.md`（Phase 1 完成后增补 Context Sync / Computer Use 章节）
- 愿景对齐：`docs/愿景与路线图.md` 增加「双轨 + 云沙箱」条目

---

## 12. 决策记录（已确认）

| 项 | 决策 |
|----|------|
| Computer Use 部署 | **云沙箱优先**，Runner 与 Titan 同机或同 VPC 部署到生产服务器 |
| Context Sync 第一期 | **Gmail + Google Calendar + GitHub 全接** |
| OpenHuman | **GPL 合规独立侧车**，与 Titan B2B 并行 |
| 重构 | 允许；以 `context_sync/`、`computer_use/` 分包 + 统一 `execute_capability` 为目标态 |

---

*产品摘要维护：架构评审后更新。实现细节变更请改 `docs/development/` 对应 Mxx 与附录，并更新附录 §11 修订记录。*
