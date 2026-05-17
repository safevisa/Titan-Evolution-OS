# Titan 每日能力进化雷达日报

> 日期：2026-05-17  
> 扫描范围：GitHub AI Agent 生态 — agent framework、MCP/tools、browser/computer use、workflow、memory/RAG、observability、SaaS/CRM 行业自动化  
> 评估标准：stars 高、30-90 天活跃、license MIT/Apache-2.0 兼容、可服务 Titan 普通用户自动化体验

---

## 一、按类别评估候选

### 1. Agent Framework（多智能体框架）

| 候选 | Stars | License | 活跃度 | Titan 价值 | 风险 | 优先级 |
|------|-------|---------|--------|------------|------|--------|
| **DeerFlow 2.0** (ByteDance) | 46K+ | Apache-2.0 | 2026-03 活跃 | 沙箱执行 + MCP 集成 + 子代理编排的完整 runtime 模式，直接对齐 Titan 的 `computer_use` Runner 和 Celery 任务编排 | LangChain 依赖较重；ByteDance 维护持续性问题 | ⭐⭐⭐ High |
| **CrewAI** | 46K | Apache-2.0 | 2026-03 活跃 | Role-based agent teams 的设计模式值得 Titan 的 Agent 角色系统参考；v1.10 加入 MCP 和 A2A 协议 | 抽象层可能限制精细控制 | ⭐⭐ Medium |
| **agency-agents** | 60K+ | MIT | 活跃 | 144 个预定义专业代理模板，可直接转换为 Titan 的 Agent 模板和行业技能文档 | 代理定义较简单，需加深到 Titan 的任务流水线 | ⭐⭐ Medium |

### 2. Browser / Computer Use（浏览器与桌面自动化）

| 候选 | Stars | License | 活跃度 | Titan 价值 | 风险 | 优先级 |
|------|-------|---------|--------|------------|------|--------|
| **Browser Use** | ~90K | MIT | 2026-05 活跃 v0.12 | CDP 直连浏览器替代 Playwright，速度 2x、token 减半，可直接作为 Titan `computer_use` Runner 的第二后端（当前 Agent-S 之外） | 依赖 Chrome；需评估与 Agent-S/UI-TARS 的互补性 | ⭐⭐⭐ High |
| **UI-TARS** (ByteDance) | 27K | Apache-2.0 | 2026-05 活跃 | 纯视觉 GUI Agent，已是 Titan 产品说明中的 grounding 候选；桌面版 + CLI 版双形态，本地可离线运行 | 视觉模型推理成本较高；需要 GPU 或 HF Endpoint | ⭐⭐⭐ High |
| **Stagehand** (Browserbase) | ~20.8K | MIT | 活跃 | AI+代码混合控制 + 自愈机制 + 操作缓存，适合 Titan 的 "半自动/可审计" 定位 | 依赖 Playwright；与 CDP 路线有冲突可能 | ⭐⭐ Medium |
| **Agent Browser** (Vercel Labs) | ~25K | — | 活跃 | Snapshot+Refs 语义地图系统，将网页翻译为 AI 可理解的界面；<10ms 热启动 | 协议生态较新 | ⭐ Low |

### 3. Memory / RAG（记忆与上下文管理）

| 候选 | Stars | License | 活跃度 | Titan 价值 | 风险 | 优先级 |
|------|-------|---------|--------|------------|------|--------|
| **OpenViking** (火山引擎) | 21.7K+ | Apache-2.0 | 2026-04 高速增长 | 文件系统范式的上下文数据库（AGFS + L0/L1/L2 分层加载），直接映射到 Titan 的 Memory Tree + Context Sync 架构；83% token 节省 | 依赖 C++/Go 组件；集成复杂度中等 | ⭐⭐⭐ High |
| **Statewave** | v0.7.1 | 待确认 | 2026-05 活跃 | Postgres+pgvector 自托管、durable episodes + ranked retrieval + token budget，架构与技术栈与 Titan 高度兼容 | 项目较新（v0.7.1）；社区规模小 | ⭐⭐⭐ High |
| **Mem0** | 48K+ | Apache-2.0 | 活跃 | 最大独立记忆层社区，SOC 2 合规，可作为 Titan Memory Tree 的架构参考 | 已有商业化方向；直接嵌入增加依赖 | ⭐⭐ Medium |
| **OpenDB** | 新兴 | — | 2026 上升 | SQLite FTS5 纯文本搜索获 93.6% LongMemEval，零嵌入 API，极致轻量 | 功能面窄；不如多策略检索架构适配 Titan | ⭐ Low |

### 4. MCP / Tools / Security（工具与安全）

| 候选 | Stars | License | 活跃度 | Titan 价值 | 风险 | 优先级 |
|------|-------|---------|--------|------------|------|--------|
| **Tooltrim** | 新兴 | — | 2026 活跃 | MCP 代理层，过滤/压缩/追踪工具列表，token 节省 70-93%，延迟仅 3.7ms，直接优化 Titan 的 MCP 集成层 | 项目较小；需评估与现有 execute_capability 的关系 | ⭐⭐ Medium |
| **agentgateway** | ~2K | Apache-2.0 | 2026-03 v1.0 | Linux Foundation 托管的统一 MCP/A2A 网关，OpenTelemetry 原生，可作为 Titan MCP registry 的架构参考 | 仍在快速迭代 | ⭐⭐ Medium |
| **MCPGuard** | 新兴 | — | 2026 活跃 | MCP 运行时安全网关，支持 Docker/Firecracker/WASM 沙箱，对齐 Titan 的安全边界要求 | 与 Titan 已有沙箱策略可能重叠 | ⭐ Low |

### 5. SaaS / CRM / 行业自动化

| 候选 | Stars | License | 活跃度 | Titan 价值 | 风险 | 优先级 |
|------|-------|---------|--------|------------|------|--------|
| **OpenClaw** | 150K+ | — | 2026 活跃 | 10 大销售工作流（潜客研究、管道报告、竞争情报等），模型无关、自托管、Cron 调度，是 Titan 行业插件的最佳参考模板 | 确切 license 待确认；已商业化 | ⭐⭐⭐ High |
| **NocoBase** | 21.7K | Apache-2.0 | 活跃 | AI 数字员工深度嵌入业务流（Scout 销售情报、Viz 洞察、Ellis 邮件协作），为 Titan 的 "数字员工" 概念提供落地参考 | 无代码平台重心不同；Titan 是开发者 OS 定位 | ⭐⭐ Medium |
| **Dittofeed** | 高评分 | MIT | 活跃 | 开源客户互动平台，ClickHouse 实时分群 + Git 驱动工作流，营销自动化模式成熟 | 偏营销自动化；Titan 偏通用编排 | ⭐ Low |

### 6. Observability / Evals（可观测与评估）

| 候选 | Stars | License | 活跃度 | Titan 价值 | 风险 | 优先级 |
|------|-------|---------|--------|------------|------|--------|
| **LongMemEval** (ICLR 2025) | 学术基准 | — | 标准 | 6 维度 agent memory 评估基准，Titan 可直接用于 Memory Tree 质量回归测试 | 需自建评估 pipeline | ⭐⭐ Medium |
| **AegisGate** | 新兴 | Apache-2.0 | 活跃 | 144+ 检测模式、8 安全护栏、11K RPS、MITRE ATLAS 覆盖，Titan 可参考其安全护栏模式 | 偏安全网关；与 Titan 核型不同层 | ⭐ Low |

---

## 二、Top 3 强烈推荐（立即可行动）

### 🥇 Browser Use（90K stars, MIT）
**为什么适合 Titan：** Browser Use v0.12 转向 CDP 直连，速度提升 2x、token 用量减半，WebVoyager 基准 89.1% 成功率（开源最高）。Titan 的 Computer Use Runner 当前基于 Agent-S/UI-TARS，增加 Browser Use 作为第二后端可大幅提升浏览器自动化场景的可靠性和效率。
**建议集成方式：** 在 `computer-use-runner/` 中新增 `browser_use_backend.py`，作为 `runner_client.py` 的可选 executor，通过 capability 参数切换（`computer_use_submit` 增加 `engine: "agents3" | "browseruse"`）。不引入到 Titan API 主进程。
**预计文件影响：** `computer-use-runner/app/browser_use_backend.py`（新）、`computer-use-runner/requirements.txt`（增 `browser-use`）、`backend/app/computer_use/orchestrator.py`（增 engine 选择逻辑）、`docs/development/M03-Computer-Use.md`（更新）
**风险：** 需要 Chrome/Chromium 在沙箱内可用；需单开 Dockerfile 或合并到现有 Runner 镜像；验证与 Agent-S 的路由逻辑

### 🥈 OpenViking（21.7K stars, Apache-2.0）
**为什么适合 Titan：** 文件系统范式的上下文管理（`viking://resources/`、`viking://user/`、`viking://agent/`）与 Titan 的 Memory Tree（level=chunk/rollup/summary）设计完全对齐。L0/L1/L2 分层加载可节省 83% token，可视化检索轨迹可直接提升 Titan 的审计能力。Apache-2.0 兼容，不污染核心许可。
**建议集成方式：** 作为 Titan Memory Tree 的架构参考，不直接嵌入代码。将 OpenViking 的 AGFS 分层思想融入 `backend/app/memory/` 的设计迭代：增加 `memory_hierarchy.py`（L0 工作记忆 / L1 项目记忆 / L2 长期知识），在 `context_retrieval.py` 中实现目录递归检索。后续可选通过 HTTP sidecar 对接 OpenViking 实例。
**预计文件影响：** `backend/app/memory/memory_hierarchy.py`（新）、`backend/app/memory/context_retrieval.py`（增强）、`docs/development/M02-Context-Sync.md`（更新）、`docs/adr/002-memory-tiered-loading.md`（新 ADR）
**风险：** OpenViking 依赖 C++/Go 组件，建议先学习模式再决定是否对接运行时

### 🥉 OpenClaw（150K+ stars, 待确认 license）
**为什么适合 Titan：** 10 大销售工作流覆盖潜客研究、管道报告、竞争情报、会议准备等，是 Titan 行业插件模板化的最佳参考。模型无关、自托管、Cron 调度的设计哲学与 Titan B2B 一致。
**建议集成方式：** 将 OpenClaw 的销售工作流模式抽象为 Titan 的行业插件模板：在 `backend/app/industry_plugins/` 下新增 `sales_outreach/` 模板目录（`workflow.yaml` + `agent_roles.yaml` + `skill_docs/`），不复制 OpenClaw 代码，只沉淀模式和评估清单。
**预计文件影响：** `backend/app/industry_plugins/sales_outreach/`（新目录 + 模板文件）、`docs/industry-playbooks/sales-automation.md`（新）、`README.md`（更新行业插件列表）
**风险：** 需确认 OpenClaw 确切 license；若为 GPL，只作架构参考不复制代码

---

## 三、能力雷达更新（新增候选）

以下候选建议加入 `capability_radar.py` 的 `RADAR_ITEMS`：

1. **Browser Use** — `id=browser_use`, category=`browser-automation`, titan_fit_score=0.94, action=`evaluate_as_computer_use_backend`
2. **OpenViking** — `id=openviking`, category=`memory/context`, titan_fit_score=0.91, action=`study_for_memory_tree_architecture`
3. **OpenClaw** — `id=openclaw`, category=`industry/sales`, titan_fit_score=0.89, action=`convert_to_sales_plugin_template`
4. **Statewave** — `id=statewave`, category=`memory/runtime`, titan_fit_score=0.86, action=`study_episodes_and_scoring`
5. **UI-TARS** — `id=ui_tars_desktop`, category=`computer-use/grounding`, titan_fit_score=0.92, action=`integrate_as_grounding_model`
6. **DeerFlow 2.0** — `id=deerflow`, category=`agent-framework`, titan_fit_score=0.87, action=`study_sandbox_orchestration`
7. **Tooltrim** — `id=tooltrim`, category=`mcp/optimization`, titan_fit_score=0.84, action=`evaluate_for_mcp_layer`
8. **NocoBase** — `id=nocobase`, category=`platform/ai-employees`, titan_fit_score=0.83, action=`study_ai_employee_ux`

---

## 四、低风险可立即执行的改进

以下改进不引入第三方依赖、不复制第三方代码、符合现有架构边界，可立即执行：

1. ✅ **更新 `capability_radar.py`**：添加 8 个新候选项目到雷达清单
2. ✅ **创建行业插件模板目录**：`backend/app/industry_plugins/sales_outreach/` 含 `workflow.yaml`、`agent_roles.yaml`、`skill_docs/README.md`
3. ✅ **更新 README.md**：补充行业插件列表和最近的生态发现
4. ✅ **创建 Memory Tree 分层设计 ADR 草案**：`docs/adr/002-memory-tiered-loading.md`
5. ✅ **更新 M08-Capability-Radar.md**：补充今日市场发现

---

## 五、安全与许可提醒

- **GPL/AGPL 项目**（如 Twenty CRM，GPL）：只能作为独立侧车或架构参考，代码不得进入 MIT 核心
- **OpenClaw**：license 待确认，在确认前只提取模式，不复制任何代码
- **Browser Use (MIT)**：可以引入 Runner 镜像，但需在独立的 `computer-use-runner` 容器内，不进 Titan API 进程
- **OpenViking (Apache-2.0)**：兼容，但建议先学模式再考虑 embedding；当前只参考架构
- **所有 MCP 工具**：默认视为不可信执行体，必须经过沙箱、权限、审计、网络隔离

---

*下期建议：重点关注 Browser Use 的 CDP 架构在 Runner 沙箱中的可行性验证，以及 OpenViking 的 AGFS 分层思想在 Titan Memory Tree 中的落地设计。*
