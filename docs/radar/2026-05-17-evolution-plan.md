# Titan Evolution OS — 现状评估与未来进化开发计划

> 版本 v1.0 · 2026-05-17  
> 基于：代码库深度扫描（14,446 行 Python） + GitHub 开源生态全面评估（30+ 候选项目）  
> 状态：待核心团队评审

---

## 一、现状评估：我们站在哪里

### 1.1 代码库规模与健康度

| 维度 | 数据 | 评估 |
|------|------|------|
| Python 总行数 | 14,446 | 中型项目，骨架完整 |
| 后端模块数 | 13 个顶层包 | 模块划分清晰，符合 DEV-SPEC-1.0 |
| 前端页面 | 14 个路由 | B2B 控制台基本完整 |
| Alembic 迁移 | 8 个版本（001–008） | 数据模型迭代有序 |
| 文档 | 20 篇 Markdown | 覆盖产品、开发、安全 |

### 1.2 模块完成度矩阵

| 模块 | 代码量 | 完成度 | 说明 |
|------|--------|--------|------|
| **integrations/** | 3,282 行 | 🟢 85% | `execute_capability` 统一入口、OAuth、catalog、metering、grants、审计 —— 核心集成层成熟 |
| **context_sync/** | 1,316 行 | 🟡 50% | fetchers（Gmail/Calendar/GitHub）、pipeline、oauth、rollup 已 stub；beat 调度、端到端验证、prod 部署未完成 |
| **agents/** | 951 行 | 🟢 80% | 8 种 Agent 角色（Manager/Researcher/Hunter/Outreach/Delivery/Generic/Discipline/Hashline）、tool runner —— 角色体系成熟 |
| **memory/** | 707 行 | 🟡 55% | token_compress、context_retrieval、short/long-term、skill_manager、prompt_builder 已 stub；分层加载、多因子排序未实现 |
| **evolution/** | 633 行 | 🟡 45% | scorer、evolver、ab_test、capability_radar 已实现；全自动闭环进化、GSEP 式基因组变异未开始 |
| **computer_use/** | 381 行 | 🟡 30% | orchestrator、runner_client、capability_handlers 已 stub；Runner 镜像未构建、沙箱未部署、Agent-S/UI-TARS 未对接 |
| **mcp/** | 2 文件 | 🟡 40% | stdio host + tool_bridge 已 stub；gateway/registry/security 层未建 |
| **industry_plugins/** | 3 插件 | 🟡 25% | payment_fintech、saas_b2b、sales_outreach（今日新增）已模板化；skill_docs 全为占位 |
| **前端** | 14 页面 | 🟡 55% | 控制台基本完整；evolution/capability-radar、integrations console、computer_use 面板未实现 |

### 1.3 已完成的关键基础设施

- ✅ `execute_capability()` 统一执行入口（强制规则 #1）
- ✅ OAuth 流程：Google YouTube、Google Workspace、GitHub
- ✅ 多租户隔离：tenant_id 贯穿所有数据操作
- ✅ Celery Beat 调度骨架（evolution.scan_all、context_sync.tick 等）
- ✅ Qdrant 向量存储 + Postgres 关系存储
- ✅ TokenCompress（HTML→Markdown、空白折叠、长列表截断）
- ✅ Capability Radar API + 14 个候选项目
- ✅ MCP stdio host + agent tool bridge
- ✅ Agent-S isolated runner（computer_use 基础）
- ✅ 行业插件目录结构（payment_fintech、saas_b2b、sales_outreach）
- ✅ 前端 i18n 架构（`[locale]` 路由）
- ✅ ADR 001–004（Computer Use 云沙箱、Context Sync 三源、OpenHuman GPL 侧车、execute_capability 不变）

---

## 二、开源生态对标：世界走到了哪

### 2.1 GitHub 高星项目格局（2026 年 5 月）

| 领域 | 领军项目 | Stars | Titan 相关性 |
|------|----------|-------|-------------|
| **浏览器自动化** | Browser Use | 90K | ⭐⭐⭐⭐⭐ 直接作为 Computer Use 第二后端 |
| **GUI Agent** | UI-TARS (ByteDance) | 27K | ⭐⭐⭐⭐⭐ 已列入 Titan grounding 候选 |
| **记忆/上下文** | OpenViking (ByteDance) | 21.7K | ⭐⭐⭐⭐⭐ 文件系统分层直接对位 Memory Tree |
| **记忆/上下文** | Mem0 | 48K | ⭐⭐⭐⭐ 通用记忆层参考 |
| **记忆/运行时** | Statewave | v0.7.1 | ⭐⭐⭐⭐ Postgres+pgvector 架构兼容 |
| **Agent 框架** | DeerFlow 2.0 (ByteDance) | 46K | ⭐⭐⭐⭐ 沙箱编排模式参考 |
| **Agent 框架** | CrewAI | 46K | ⭐⭐⭐ Role-based teams 参考 |
| **Agent 模板** | agency-agents | 60K+ | ⭐⭐⭐ 144 个专业 Agent 模板 |
| **销售自动化** | OpenClaw | 150K+ | ⭐⭐⭐⭐⭐ 10 大销售工作流模式 |
| **AI 员工平台** | NocoBase | 21.7K | ⭐⭐⭐ AI 员工嵌入业务流参考 |
| **MCP 安全** | MCPGuard / IronContext | 新兴 | ⭐⭐⭐ MCP 运行时安全参考 |
| **MCP 优化** | Tooltrim | 新兴 | ⭐⭐⭐ Token 节省 70-93% |
| **可观测性** | Opik (Comet) | 12.7K | ⭐⭐⭐⭐ Agent 全链路追踪 |
| **可观测性** | Future AGI | 945 | ⭐⭐⭐ 全功能一体化平台 |
| **自我进化** | GSEP | 新兴 | ⭐⭐⭐⭐⭐ 基因组式 Prompt 进化 |
| **评估基准** | AgencyBench (ACL 2026) | — | ⭐⭐⭐⭐ 1M-token 真实场景评估 |
| **评估基准** | MASEval | 31 | ⭐⭐⭐⭐ 多 Agent 系统级评估 |
| **评估基准** | MemoryAgentBench (ICLR 2026) | 303 | ⭐⭐⭐ 记忆能力专项评估 |

### 2.2 关键趋势信号

1. **纯视觉 GUI Agent 正在成熟**：UI-TARS 27K stars、Browser Use 90K stars —— 2026 是 "Computer Use 可落地年"
2. **记忆不是向量搜索，是分层架构**：OpenViking 的 L0/L1/L2 文件系统范式、Statewave 的多因子排序、GSEP 的基因变异 —— 远超 "加个向量库" 的早期阶段
3. **MCP 已成为 USB-C**：10,000+ 公开 MCP server、Slack/Notion/Salesforce 全有官方支持 —— Titan 的 MCP 层必须从 "可工作" 升级到 "可治理"
4. **Agent 评估从 QA 走向系统级**：AgencyBench、MASEval、ClawForge 都在测 "框架+模型+工具" 的组合效果，而不只是模型本身
5. **自我进化从概念走向代码**：GSEP 的 4 阶段进化循环（转录→变异→仿真→选择）提供了可直接参考的实现模式
6. **销售/CRM AI Agent 已到生产级**：OpenClaw 150K+ stars、NocoBase 的 5 个 AI 员工 —— Titan 的行业插件方向有丰富的参考模板

---

## 三、差距分析：Titan 离「傻瓜式全自动」还差什么

### 3.1 能力差距

| 用户期望 | 当前 Titan | 差距 |
|----------|-----------|------|
| "打开 Gmail 和 GitHub，自动帮我整理今天要做的事" | Context Sync fetcher 已 stub，但 beat 调度和 prompt 注入未端到端验证 | 🔴 Phase 1 未完成 |
| "帮我在浏览器里提交那个报销单" | Computer Use orchestrator 已 stub，但 Runner 镜像未构建、沙箱未部署 | 🔴 Phase 2 未开始 |
| "我上周做过的那个客户分析，再来一遍" | Memory Tree 有基本结构，但分层加载、多因子排序未实现 | 🟡 检索精度不够 |
| "这个 Agent 的回复质量在下降，自动帮我优化" | Evolution scorer + ab_test 已有，但闭环自动优化未实现 | 🟡 需人工干预 |
| "给我的销售团队加一个自动外呼工作流" | 行业插件目录已有 3 个模板，但 skill_docs 全为占位，无可执行能力 | 🟡 模板空壳 |
| "同时连 Salesforce 和 Slack，让 Agent 帮我管 pipeline" | MCP host 已 stub，但 SaaS connector 和 registry 未建 | 🔴 无 SaaS 连接器 |
| "出问题了，帮我看看 Agent 到底做了什么" | 有 capability_audit_logs，但无可视化 Tracing、无 RCA | 🟡 排障靠看日志 |

### 3.2 架构债务

| 债务 | 影响 | 建议处理时机 |
|------|------|-------------|
| `integrations/` 单包 22 文件 3,282 行 | 修改一个能力影响多个文件，新人难以理解 | Phase 1 内重构 |
| `computer_use/` Runner 镜像未构建 | 整个 Computer Use 能力停留在代码层 | Phase 2 起步 |
| 前端未接 capability-radar API | 新能力发现只能在代码/文档层面，用户不可见 | Phase 1 补充 |
| 无 Agent 评估 pipeline | 无法量化 "这次改动是否真的改进了" | Phase 3 建立 |
| 多因子排序在 memory/ 中缺失 | Agent 获得的是 flat top-k，而非按角色/场景排名的上下文 | Phase 2 内实现 |
| MCP 只有 host 没有 gateway | 无法治理多 MCP server 的工具列表膨胀和安全边界 | Phase 3 建立 |

---

## 四、进化开发计划（分四阶段）

### Phase 1：补齐 MVP 闭环（当前 — 2026 年 6 月）

**目标：让 Context Sync 和 Computer Use 从 stub 变成可演示的端到端能力。**

| 优先级 | 任务 | 预计文件影响 | 参考开源项目 |
|--------|------|-------------|-------------|
| P0 | **Context Sync 端到端验证**：beat 20min 调度 → Gmail/Calendar/GitHub 增量拉取 → TokenCompress → Qdrant 写入 → Agent prompt 注入 | `context_sync/tasks.py`、`celery_app.py`、`prompt_builder.py`、Alembic 009 | — |
| P0 | **Computer Use Runner 镜像构建**：Dockerfile + Xvfb + Agent-S/UI-TARS + 录屏存储 → `computer_use_submit` 端到端 | `computer-use-runner/`、`docker-compose.computer-use.yml` | Browser Use CDP 架构、UI-TARS |
| P1 | **OAuth 生产化**：Google Workspace + GitHub OAuth 回调 → token 存储 → 刷新 → sync 状态 UI | `oauth_workspace.py`、`oauth_github.py`、前端 IntegrationsConsole | — |
| P1 | **前端能力雷达**：`/evolution/capability-radar` API 消费 → 候选卡片 + 分类筛选 | `frontend/app/[locale]/evolution/page.tsx` | — |
| P2 | **integrations/ 分包重构**：按领域拆到 `context_sync/`、`computer_use/`、`integrations/` 各 ≤10 文件 | `integrations/` 拆分 | DEV-SPEC-1.0 §2.1 |
| P2 | **前端 Computer Use 面板**：提交任务 → 查看状态 → 下载录屏 | `frontend/app/[locale]/settings/` 扩展 | — |

### Phase 2：智能记忆与多策略检索（2026 年 7–8 月）

**目标：Agent 不再靠 flat top-k 获得上下文，而是分层、分角色、多因子排序的精准记忆注入。**

| 优先级 | 任务 | 预计文件影响 | 参考开源项目 |
|--------|------|-------------|-------------|
| P0 | **Memory Tree 分层加载**：L0（Redis 工作记忆）+ L1（Qdrant 项目摘要）+ L2（长期知识）三层注入 | `memory/memory_hierarchy.py`、`context_retrieval.py`、`base_agent.py` | **OpenViking** AGFS 分层、Letta/MemGPT OS 分页 |
| P0 | **多因子检索排序**：semantic + recency + role_relevance + temporal_validity 加权融合 | `memory/retrieval_ranker.py`、ADR 002 | **Statewave** ranked retrieval、Hindsight 多策略 |
| P1 | **Browser Use 后端集成**：Computer Use Runner 增加 CDP-based 第二后端，通过 `engine` 参数切换 | `computer-use-runner/app/browser_use_backend.py` | **Browser Use** v0.12 CDP 架构 |
| P1 | **Memory Tree rollup 质量评分**：低于阈值自动触发重新总结 | `context_sync/rollup.py` | LongMemEval 评估标准 |
| P2 | **行业插件 skill_docs 填充**：sales_outreach 的 7 个技能文档从占位变为实际内容 | `industry_plugins/sales_outreach/skill_docs/` | OpenClaw 销售工作流、Apify Agent Skills |
| P2 | **UI-TARS grounding 集成**：评估并接入 UI-TARS-1.5-7B 作为 Computer Use 的视觉推理模型 | `computer_use/orchestrator.py` | **UI-TARS Desktop** 视觉 grounding |

### Phase 3：可观测、可评估、可进化（2026 年 9–10 月）

**目标：Agent 的行为可追溯、质量可量化、能力可自动进化。**

| 优先级 | 任务 | 预计文件影响 | 参考开源项目 |
|--------|------|-------------|-------------|
| P0 | **Agent 全链路 Tracing**：OpenTelemetry 集成 → 每个 `execute_capability` 调用生成 trace → 前端可视化 | `integrations/capability_audit_repo.py`（增强）、`services/tracing.py`（新） | **Opik** (Comet)、**Future AGI** |
| P0 | **Agent 评估 Pipeline**：基于 AgencyBench / MemoryAgentBench 模式，建立 Titan 内部回归测试集 | `evolution/eval_pipeline.py`（新）、`tests/evals/`（新） | **AgencyBench**（ACL 2026）、**MASEval** |
| P1 | **自我进化闭环（GSEP 模式）**：4 阶段进化循环 —— 转录交互日志 → 生成 Prompt 变异 → 沙箱仿真测试 → 选择最优部署 | `evolution/genomic_evolver.py`（新）、`evolution/sandbox_simulator.py`（新） | **GSEP** 基因组式进化 |
| P1 | **MCP Gateway + Registry**：统一的 MCP 工具发现、安全扫描、token 预算管理 | `mcp/gateway.py`（新）、`mcp/registry.py`（新） | **agentgateway**（Linux Foundation）、**Tooltrim** |
| P2 | **多 Agent 系统级评估**：测试 Titan 的 Agent 团队（Manager+Researcher+Writer）在不同 workflow 下的端到端质量 | `tests/system/`（新） | **MASEval** 框架无关评估 |
| P2 | **SaaS 连接器第一批**：Slack MCP + Notion MCP + Salesforce MCP → Titan capability catalog | `integrations/saas_connectors/`（新） | **Fastn MCP**（250+ connectors）、**universal-mcp-toolkit** |

### Phase 4：行业深水区与个人线（2026 年 11 月 — 持续）

**目标：行业插件从模板变成可执行闭环；OpenHuman 侧车与 Titan B2B 形成双轨协同。**

| 优先级 | 任务 | 预计文件影响 | 参考开源项目 |
|--------|------|-------------|-------------|
| P0 | **销售外呼插件端到端**：lead_discovery → enrichment → draft → review → CRM sync 全流程可执行 | `industry_plugins/sales_outreach/` 全部 capability 实现 | **OpenClaw** 10 大销售工作流 |
| P1 | **第二个行业插件**：Delivery/Digital Marketing/Recruiting 三选一 | `industry_plugins/` 新目录 | **NocoBase** AI 员工角色设计 |
| P1 | **OpenHuman 侧车构建**：独立仓库/镜像 → `sidecar/memory-push` API → 用户绑定 | `titan-openhuman-sidecar/`、`integrations/sidecar_api.py` | ADR 003 |
| P2 | **个人级「数字团队」一键体验包**：预设 Manager+Researcher+Outreach 三人组 + 3 个行业模板 | `services/smart_launch_planner.py`（增强） | agency-agents 144 模板 |
| P2 | **Firecracker/Kata 沙箱**：从 Docker per task 升级到 microVM 级隔离 | `computer-use-runner/` firecracker 后端 | MCPGuard 沙箱后端 |

---

## 五、Top 10 外部能力引入建议（带优先级）

| # | 项目 | 引入方式 | 引入阶段 | 预期收益 |
|----|------|----------|----------|----------|
| 1 | **Browser Use** (90K★, MIT) | Computer Use Runner 第二后端 | Phase 2 | 浏览器自动化成功率从 ~70% 提升到 ~89% |
| 2 | **OpenViking** (21.7K★, Apache-2.0) | Memory Tree 分层加载架构参考 | Phase 2 | Token 节省 ~80%，检索精度显著提升 |
| 3 | **Statewave** (v0.7.1) | 多因子排序 + durable episodes 模式参考 | Phase 2 | 检索相关性提升，支持客户健康度评分 |
| 4 | **UI-TARS** (27K★, Apache-2.0) | Computer Use grounding 模型 | Phase 2 | 纯视觉 GUI 操作，无 DOM/API 依赖 |
| 5 | **OpenClaw** (150K+★) | 销售行业插件模式提取 | Phase 1（模板）/ Phase 4（执行） | 10 大销售工作流直接转 Titan capability |
| 6 | **Opik / Future AGI** | Agent Tracing 架构参考 | Phase 3 | 全链路可观测，排障时间缩短 80% |
| 7 | **GSEP** | 自我进化闭环模式参考 | Phase 3 | Prompt 自动优化，减少人工调参 |
| 8 | **AgencyBench** (ACL 2026) | Titan 内部评估基准设计参考 | Phase 3 | 量化 Agent 改进效果，指导进化方向 |
| 9 | **agentgateway** (Linux Foundation) | MCP Gateway 架构参考 | Phase 3 | 统一治理多 MCP server 的工具膨胀和安全 |
| 10 | **Fastn MCP / universal-mcp-toolkit** | SaaS connector 实现参考 | Phase 3 | Slack/Notion/Salesforce 等快速接入 |

---

## 六、风险与缓解

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| Browser Use 与 Agent-S 架构冲突 | 中 | 中 | 先做概念验证，通过 `engine` 参数隔离，不同时 merge |
| OpenViking C++/Go 依赖过重 | 中 | 低 | 只参考架构模式，不嵌入运行时；纯 Python 实现分层逻辑 |
| OpenClaw license 不兼容 | 高 | 中 | 在确认 license 前只提取抽象模式，不复制任何代码 |
| Computer Use 沙箱成本失控 | 中 | 高 | 已有 `capability_metering` + `max_steps` + 并发上限；Phase 4 前不开放自助 |
| GSEP 式自动进化引入不可控变更 | 高 | 高 | 始终保留 human approval gate；所有自动变更记录在 ab_test 中可回滚 |

---

## 七、成功度量（Phase 1 验收标准）

- [ ] Context Sync：租户完成 Google + GitHub OAuth 后，20 分钟内 Researcher prompt 含 ≥3 条 Gmail/Calendar/GitHub 摘要
- [ ] Computer Use：提交 "打开浏览器访问 example.com 并截图" → 沙箱内成功 → Titan 可下载 artifact
- [ ] 前端能力雷达：用户可在 Evolution 页面看到 14 个候选能力卡片，按分类筛选
- [ ] 行业插件模板：sales_outreach workflow.yaml 可在 Titan 中注册为 capability pack，`workflow_run` 至少执行到 quality_review 步骤
- [ ] 零安全回归：API 进程内无 pyautogui import；GPL 代码未进入 backend 镜像；所有写操作经过 `execute_capability`

---

## 八、建议的下一步行动（本周内）

1. **评审本文档**：核心团队通读，确认 Phase 1–4 的优先级和范围
2. **P0 任务启动**：从 M02 Context Sync 端到端验证和 M03 Computer Use Runner 镜像构建开始
3. **开源引入决策**：正式评估 Browser Use（MIT）和 OpenViking（Apache-2.0）的引入方式，写入 ADR
4. **前端雷达 UI**：分配前端开发者实现 `/evolution/capability-radar` 的消费端
5. **评估基准建立**：选 1 个基准（推荐 MemoryAgentBench）建立 Titan 内部 Agent 质量回归测试

---

*本文档随生态扫描和开发进度持续更新。下次评审：Phase 1 完成时。*
