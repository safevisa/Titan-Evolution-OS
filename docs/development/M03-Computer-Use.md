# M03 — Computer Use（云沙箱 / Agent-S）

**前置**：M01（`computer_use_runs` 表）  
**后置**：M06 部署  
**可与 M02 并行**（不同开发者）  
**预估**：4–5 周  

---

## 1. 模块边界

| 负责 | 不负责 |
|------|--------|
| 提交/查询/取消 GUI 任务 | 在 backend 容器安装 gui-agents |
| Runner HTTP API + 沙箱生命周期 | 替代 Browser MCP 给开发者本地用 |
| 录屏与步骤 JSON 存储 | OSWorld 评测 harness |

---

## 2. 数据模型（009 已建）

### `computer_use_runs`

| 列 | 类型 | 说明 |
|----|------|------|
| id | UUID PK | 对外 run_id |
| tenant_id | UUID | |
| task_id | UUID nullable | 关联 Agent 任务 |
| instruction | TEXT | 用户自然语言 |
| status | VARCHAR(32) | queued \| running \| success \| failed \| cancelled |
| sandbox_id | VARCHAR(128) | Runner 侧 ID |
| step_count | INT | |
| artifact_json | JSONB | `{screenshot_urls[], recording_url, step_log[]}` |
| error | TEXT | |
| created_at | TIMESTAMPTZ | |
| finished_at | TIMESTAMPTZ | |

索引：`(tenant_id, status, created_at desc)`

---

## 3. 目录 `computer-use-runner/`

```
computer-use-runner/
  Dockerfile              # python:3.12 + xvfb + tesseract + gui-agents
  requirements.txt        # gui-agents, fastapi, uvicorn, pydantic
  app/
    main.py               # FastAPI
    sandbox.py            # 启动/销毁隔离环境（Phase1: subprocess+docker-outside）
    agent_loop.py         # AgentS3 + OSWorldACI 封装
    settings.py
```

### 3.1 Runner API 契约（内网 only）

| 方法 | 路径 | Body | Response |
|------|------|------|----------|
| POST | `/v1/runs` | `{instruction, max_steps, width, height, enable_local_env}` | `{run_id, status}` |
| GET | `/v1/runs/{run_id}` | — | `{status, step_count, artifact, error}` |
| POST | `/v1/runs/{run_id}/cancel` | — | `{status: cancelled}` |
| GET | `/health` | — | 200 |

认证：Header `X-Runner-Token` = env `COMPUTER_USE_RUNNER_TOKEN`（Titan 与 Runner 共享）。

### 3.2 Agent 循环（`agent_loop.py`）

与 Agent-S README 一致：

- `AgentS3` + `OSWorldACI` + `platform` from env
- 每步：`pyautogui.screenshot()` → `predict` → `exec(action[0])`
- `max_steps` 默认 30，硬上限 50
- **`enable_local_env` 默认 False**（ADR）

Grounding env：

- `COMPUTER_USE_GROUND_URL`
- `COMPUTER_USE_GROUND_MODEL=ui-tars-1.5-7b`
- `grounding_width=1920`, `grounding_height=1080`

### 3.3 沙箱 Phase 1

- 单 Runner 进程 **串行** 执行任务（`asyncio.Lock`）
- 每任务：Xvfb `:99` 1920x1080；任务结束 kill 子进程
- 录屏：可选 `ffmpeg` x11grab → mp4 存 `COMPUTER_USE_ARTIFACT_DIR/{run_id}.mp4`

Phase 2（文档记录，不阻塞 MVP）：每任务 `docker run --rm` 隔离桌面镜像。

---

## 4. Titan 侧 `computer_use/`

### 4.1 `orchestrator.py`

```python
async def submit_run(session, tenant_id, instruction, *, task_id=None, max_steps=30) -> UUID: ...
async def get_run(session, tenant_id, run_id) -> dict: ...
async def cancel_run(session, tenant_id, run_id) -> dict: ...
```

提交时：

1. 检查 `Tenant.config.computer_use.enabled` + plan enterprise
2. 检查并发：`count(status in queued,running) < max_concurrent`
3. Insert `computer_use_runs` status=queued
4. `celery`: `titan.computer_use.dispatch(run_id)`

### 4.2 `runner_client.py`

httpx async 调 Runner；超时 connect 5s, read 600s。

### 4.3 Celery

| 任务 | 说明 |
|------|------|
| `titan.computer_use.dispatch` | POST Runner，轮询至完成 |
| `titan.computer_use.reaper` | 超时 30min → failed + cancel Runner |

### 4.4 Capabilities（`capability_handlers.py`）

| id | params | 行为 |
|----|--------|------|
| `computer_use_submit` | instruction, max_steps? | → submit_run |
| `computer_use_status` | run_id | → get_run |
| `computer_use_cancel` | run_id | → cancel_run |

catalog：`category="desktop"`, `status="live"`, enterprise only。

### 4.5 Agent 集成

- `list_agent_capabilities`：delivery/operations 角色可见
- 工作流 DAG 节点 `capability_id: computer_use_submit`（行业插件后续 PR）
- 任务 input 可含 `computer_use_instruction`，Manager 拆任务时填入

---

## 5. 安全

- Runner **不**暴露公网；仅 docker network `titan-internal`
- Titan API 返回 artifact URL 为 **signed 短期链接** 或需 admin session
- 审计：`append_audit_log` 记录 instruction 前 500 字符 + run_id
- `require_approval`：status 初始 `pending_approval`，Manager API approve 后变 queued（M03-b PR）

---

## 6. `deploy/docker-compose.computer-use.yml`

```yaml
services:
  computer-use-runner:
    build: ../computer-use-runner
    environment:
      COMPUTER_USE_RUNNER_TOKEN: ${COMPUTER_USE_RUNNER_TOKEN}
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      COMPUTER_USE_GROUND_URL: ${COMPUTER_USE_GROUND_URL}
      ...
    volumes:
      - cu_artifacts:/var/titan/cu-artifacts
    networks:
      - titan-internal
    # 不 publish 端口到 0.0.0.0
```

`docker-compose.yml` 的 backend/celery 加入：

```yaml
COMPUTER_USE_RUNNER_URL: http://computer-use-runner:8090
```

---

## 7. 分 PR 计划

| PR | 内容 |
|----|------|
| M03-a | Runner skeleton + health + mock run |
| M03-b | AgentS3 真循环 + artifact |
| M03-c | Titan orchestrator + celery dispatch |
| M03-d | capabilities live + grants pack |
| M03-e | compose 生产 + 审批流（可选） |

---

## 8. 验收

- [ ] instruction「打开浏览器访问 https://example.com 并返回页面 title」success
- [ ] backend 镜像无 `gui_agents` import
- [ ] 并发 2 任务第 3 个返回 `concurrency_limit`
- [ ] failed run 有 error + 审计

---

## 9. 依赖版本（锁定）

```
gui-agents>=0.3.2,<0.4
pyautogui>=0.9.54
```

记录于 `computer-use-runner/requirements.txt`，升级需改 DEV-SPEC 变更日志。
