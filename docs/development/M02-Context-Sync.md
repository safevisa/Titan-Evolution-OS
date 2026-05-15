# M02 — Context Sync（Gmail / Google Calendar / GitHub）

**前置**：M01  
**后置**：M04（侧车 push）、M05 前端  
**预估**：3–4 周（可分 PR：OAuth → Fetch → Pipeline → Prompt）  

---

## 1. 模块边界

| 负责 | 不负责 |
|------|--------|
| 拉取三源数据、入库、rollup、prompt 注入 | Gmail 发送、GitHub 合并 PR（第二期） |
| OAuth 与 token 刷新 | 替换 Qdrant 为 SQLite |
| `context_sync_run` capability | 118 其他集成 |

---

## 2. Provider 与 OAuth

### 2.1 `providers.py` 新增

```python
PROVIDER_GOOGLE_WORKSPACE_OAUTH = "google_workspace_oauth"
PROVIDER_GITHUB_OAUTH = "github_oauth"
```

加入 `OAUTH_PROVIDERS`。与 `PROVIDER_GOOGLE_YOUTUBE_OAUTH` **并存**。

### 2.2 Google Workspace Scopes

```
https://www.googleapis.com/auth/gmail.readonly
https://www.googleapis.com/auth/calendar.readonly
openid email profile
```

Redirect URI：`{TITAN_API_PUBLIC_BASE_URL}/api/v1/integrations/oauth/google-workspace/callback`

Token 存 `integration_connections` provider=`google_workspace_oauth`，secret JSON：

```json
{
  "access_token": "...",
  "refresh_token": "...",
  "expires_at": 1234567890,
  "scopes": ["..."]
}
```

刷新：`oauth_token_refresh.py` 新增分支，复用 `google_refresh_access_token`。

### 2.3 GitHub OAuth Scopes

```
read:user repo
```

（最小化评审后可改为 `public_repo` 若仅公有库）

Redirect：`.../oauth/github/callback`  
Provider：`github_oauth`

### 2.4 API 路由（`api/v1/integrations.py`）

复制现有 slack/twitter 模式：

- `GET /oauth/google-workspace/start?tenant_id=`
- `GET /oauth/google-workspace/callback`
- `GET /oauth/github/start`
- `GET /oauth/github/callback`
- `GET /tenants/{tenant_id}/sync-status`
- `POST /tenants/{tenant_id}/sync/trigger` → 内部 `execute_capability("context_sync_run", ...)`

State cookie：现有 oauth state 机制，`st["p"] == "google_workspace"` / `"github"`。

---

## 3. Fetchers

路径：`context_sync/fetchers/{gmail,google_calendar,github}.py`

### 3.1 统一返回

```python
@dataclass
class FetchedItem:
    external_id: str          # 稳定 ID
    source: Literal["gmail","gcal","github"]
    title: str
    body_text: str
    occurred_at: datetime
    url: str | None
    raw_meta: dict[str, Any]  # 不进向量，仅调试
```

### 3.2 Gmail（`gmail.py`）

- API：`users.messages.list` + `users.messages.get(format=full)`
- 标签：`INBOX`, `SENT`
- 窗口：`Tenant.config.context_sync.gmail_lookback_days` 默认 30
- 增量：`historyId` 存 `cursor_json.gmail_history_id`
- 解析：提取 Subject/From/Date/body plain；单封 body 上限 256KB，超出截断
- HTTP：`integration_request(..., provider="google_workspace")`

### 3.3 Google Calendar（`google_calendar.py`）

- API：`events.list` 主日历，`timeMin`/`timeMax` 各 14 天
- 增量：`syncToken` → `cursor_json.gcal_sync_token`
- body_text 模板：`{summary}\n{description}\n{start}-{end}\n{location}`

### 3.4 GitHub（`github.py`）

- 对每个可见 repo（分页，上限 30 repo）：`issues` + `pulls` 各取 updated_since
- `cursor_json.github_since` ISO 时间
- body：title + body 前 8k 字符

### 3.5 错误处理

- 401 → 标记 `last_error=token_expired`，触发 refresh 一次
- 429 → `integration_request` 已有重试；仍失败写 `last_error`
- 不抛异常出 Celery 任务；返回 `{ok: false, error}` 结构

---

## 4. Pipeline（`context_sync/pipeline.py`）

```python
async def ingest_items(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    items: list[FetchedItem],
) -> IngestStats: ...
```

步骤：

1. **Dedup**：`memory_tree_nodes (tenant_id, source, external_key)` 已存在且 `occurred_at` 未变 → skip
2. **Chunk**：按 3000 token 估算（chars/4）切分，每块 `level=0`
3. **Compress**：`compress_for_llm`
4. **Embed + Qdrant**：复用 `long_term._embed`，payload 增加字段：

```python
{
  "tenant_id": str,
  "agent_id": "",  # sync 无 agent
  "task_type": "context_sync",
  "source": "gmail|gcal|github",
  "memory_tree_node_id": str,
  "title": str,
  "summary": str,  # 压缩后
  "occurred_at": iso,
}
```

5. **Insert** `memory_tree_nodes` + 更新 `integration_sync_states.last_success_at`

---

## 5. Rollup（`context_sync/rollup.py`）

Celery：`titan.context_sync.rollup`

- 按 tenant+source 聚合同日 chunk（`occurred_at` date）
- LLM 摘要（`complete_chat`，max 800 tokens output）→ `level=1` 父节点
- 父节点同样 embed 入 Qdrant，`parent_id` 指向子节点组

配置：`rollup` 仅 enterprise 或 `context_sync.rollup_enabled=true`

---

## 6. Celery 任务（`context_sync/tasks.py`）

| 任务名 | 函数 | 说明 |
|--------|------|------|
| `titan.context_sync.tick` | `tick_all_tenants` | 查 `integration_sync_states.enabled` + 有连接 |
| `titan.context_sync.tenant` | `sync_tenant(tenant_id)` | 单租户三源 |
| `titan.context_sync.rollup` | `rollup_all` | 6h |

`tick` 逻辑：

```python
for row in enabled_sync_states:
    if not tenant.config.context_sync.enabled:
        continue
    sync_tenant.delay(str(row.tenant_id))
```

`sync_tenant`：顺序 gmail → gcal → github（避免并发刷新 token）。

---

## 7. Capability `context_sync_run`

`context_sync/capability_handlers.py`：

参数：

```json
{
  "sources": ["gmail", "gcal", "github"]  // optional, default all enabled
}
```

返回：

```json
{
  "ok": true,
  "data": {
    "gmail": {"ingested": 12, "skipped": 3},
    "gcal": {...},
    "github": {...}
  }
}
```

catalog：`status="live"`，`category="context"`，`roles_hint` 含 manager/operations。

---

## 8. Prompt 注入（`memory/context_retrieval.py`）

```python
async def fetch_sync_context_block(
    *,
    tenant_id: str,
    query: str,
    max_tokens: int = 4096,
) -> str: ...
```

- Qdrant filter：`task_type == "context_sync"` 或 payload.source in (...)
- `build_enhanced_prompt` 追加块标题：`## Synced context (auto-fetched)\n`

**禁止**注入未压缩原文。

---

## 9. 删除与断开

`connections_repo.delete_connection` 后 hook（或 API 内）：

- Celery：`titan.context_sync.purge_tenant_source(tenant_id, source)`
- 删 Qdrant points（scroll filter）+ `memory_tree_nodes`

---

## 10. 分 PR 计划

| PR | 内容 |
|----|------|
| M02-a | providers + OAuth 四路由 + 连接写入 |
| M02-b | gmail fetcher + pipeline + sync_state |
| M02-c | gcal + github fetchers |
| M02-d | Celery beat + context_sync_run |
| M02-e | context_retrieval + prompt_builder |
| M02-f | rollup（可选） |

---

## 11. 验收

- [ ] 测试租户 OAuth 后 `sync-status` 三源 green
- [ ] 手动 trigger 后 Qdrant 有 `source=gmail` points
- [ ] Researcher 任务日志可见 injected sync block（脱敏）
- [ ] 断开 GitHub 后 24h 内 purge 完成
- [ ] 审计表有 `context_sync_run` 记录

---

## 12. 测试数据

`tests/context_sync/`（若无可先脚本）：

- `scripts/dev_sync_once.py --tenant-id=...` 本地跑一次
