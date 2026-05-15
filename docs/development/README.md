# Titan 双轨进化 — 开发文档索引（唯一实施依据）

> **所有 Agent / 开发者在改代码前必须先读本文档索引，并按模块顺序实施。**  
> 产品决策已冻结，见 [00-开发总则与决策记录.md](./00-开发总则与决策记录.md)。  
> 出问题先查 [07-可观测性与排障手册.md](./07-可观测性与排障手册.md)。

---

## 文档版本

| 字段 | 值 |
|------|-----|
| 规范版本 | **DEV-SPEC-1.0** |
| 冻结日期 | 2026-05-15 |
| 关联产品说明 | [../Titan_双轨进化_ContextSync_ComputerUse_OpenHuman_产品开发说明.md](../Titan_双轨进化_ContextSync_ComputerUse_OpenHuman_产品开发说明.md) |
| 集成现状说明 | [../外部工具与集成.md](../外部工具与集成.md) |

---

## 强制规则（违反即视为 Bug）

1. **唯一执行入口**：所有对外部世界的作用（发信、发帖、同步、GUI 操作）必须经 `execute_capability()`，禁止 Agent 直接 `httpx` / `pyautogui`。
2. **禁止 GPL 污染**：OpenHuman 源码不得进入 `backend/` 主镜像；仅独立容器 + HTTP API。
3. **禁止 Computer Use 进 API 进程**：`pyautogui` / `gui_agents` 仅存在于 `computer-use-runner` 镜像。
4. **多租户**：任意读写带 `tenant_id`；Qdrant collection 命名保持 `agent_memories_{tenant}` 现有规则。
5. **前端文案**：新增 UI 必须 i18n 键，禁止硬编码中文/英文在 TSX。
6. **迁移编号**：下一 Alembic 为 `009_`，依次递增，禁止改已发布迁移。

---

## 模块实施顺序（必须遵守）

```
M00 准备 → M01 共享基础 → M02 Context Sync → M03 Computer Use → M04 OpenHuman 侧车 → M05 前端 → M06 部署 → M07 贯穿
```

| 顺序 | 模块文档 | 可并行 | 产出物摘要 |
|------|----------|--------|------------|
| M00 | [M00-仓库准备与分支策略.md](./M00-仓库准备与分支策略.md) | — | 目录骨架、feature flag、空包 |
| M01 | [M01-共享基础设施.md](./M01-共享基础设施.md) | — | `token_compress`、`Tenant.config` 约定、009 迁移 |
| M02 | [M02-Context-Sync.md](./M02-Context-Sync.md) | M01 完成后 | Gmail/Calendar/GitHub 全管道 |
| M03 | [M03-Computer-Use.md](./M03-Computer-Use.md) | 与 M02 后端可并行 | Runner + 沙箱 capability |
| M04 | [M04-OpenHuman-侧车.md](./M04-OpenHuman-侧车.md) | M02 有 `memory-push` 后 | GPL 侧车 + 绑定 API |
| M05 | [M05-前端与-i18n.md](./M05-前端与-i18n.md) | 各模块 API 就绪后 | Integrations 扩展 UI |
| M06 | [M06-部署与运维.md](./M06-部署与运维.md) | M02+M03 镜像就绪 | compose、env、生产清单 |
| — | [附录-接口与数据字典.md](./附录-接口与数据字典.md) | 随模块更新 | 表、API、capability、任务名 |
| — | [07-可观测性与排障手册.md](./07-可观测性与排障手册.md) | 全程 | 日志位置、错误码、检查命令 |

---

## 目标目录树（完成后端）

```
backend/app/
  context_sync/           # M02
    __init__.py
    models.py             # CanonicalDocument, SyncCursor（逻辑模型，表在 domain）
    fetchers/
      gmail.py
      google_calendar.py
      github.py
    pipeline.py           # normalize → chunk → compress → store
    rollup.py             # memory tree 父摘要
    tasks.py              # Celery 任务入口
    oauth.py              # workspace + github 授权 URL/回调
  computer_use/           # M03
    __init__.py
    orchestrator.py       # submit/status/cancel
    runner_client.py      # HTTP 调 Runner
    tasks.py
  memory/
    token_compress.py     # M01
    context_retrieval.py  # M02：注入 prompt 的检索
  integrations/
    ...                   # 仅注册 catalog + executor 分支，业务在子包

computer-use-runner/      # M03 独立构建上下文
  Dockerfile
  app/main.py
  requirements.txt

deploy/
  docker-compose.computer-use.yml
  nginx/                  # 如需 Runner 仅内网

titan-openhuman-sidecar/  # M04 独立仓库或 submodule（GPL）
  README.md               # 仅指针，源码不提交到主 repo 可选
```

---

## 实施进度（代码库）

| 模块 | 状态 |
|------|------|
| M00 骨架 + catalog stub | ✅ 已落地 |
| M01 009 迁移 + token_compress + executor 委托 | ✅ 已落地 |
| M02 Context Sync | ⬜ 待开发 |
| M03 Computer Use | ⬜ 待开发 |
| M04 OpenHuman 侧车 | ⬜ 待开发 |

---

## 完成定义（整体验收）

- [ ] 三份 OAuth（Google Workspace、GitHub）可连接，sync 状态 API 正确
- [ ] Beat 每 20 分钟同步，Researcher prompt 含 synced context 块
- [ ] `computer_use_submit` 在 Runner 沙箱完成并回传 artifact
- [ ] OpenHuman 侧车独立容器可 `memory-push` 到 Titan
- [ ] 生产 `43.128.80.35` compose 含 backend + celery + beat + runner（可选侧车）
- [ ] [07-可观测性与排障手册.md](./07-可观测性与排障手册.md) 中每条检查命令在 CI 或 runbook 验证过

---

## 变更流程

1. 若要偏离本文档：先更新对应 `Mxx` 文档 + [00-开发总则](./00-开发总则与决策记录.md) 的「决策变更日志」。
2. PR 描述必须写：`Implements: M02 §3.4` 或 `Fixes: DEV-SPEC-1.0 M03 run status`。
3. 新 capability 必须同时改：`catalog.py`、`builtins_dispatch` 或 `capability_invoke`、`附录-接口与数据字典.md`。
