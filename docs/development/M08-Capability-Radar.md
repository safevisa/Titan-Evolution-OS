# M08 - Capability Radar 与每日进化接入

> 版本：2026-05-17
> 目标：把每天从 GitHub / MCP / agent 技能市场发现的高价值能力，变成 Titan 可审计、可筛选、可逐步落地的产品输入。

---

## 1. 为什么要做

Titan 的长期目标是让普通用户用「傻瓜式」方式调用数字员工完成工作。要做到这一点，系统不能只依赖一次性手写集成，而要每天吸收外部开源生态中的成熟能力，并经过统一筛选后进入：

- `SkillDoc`：转成可复用 SOP / 技能；
- `ToolCapability`：转成能力 catalog 或 stub；
- `industry_plugins`：转成行业工作流模板；
- `context_sync` / `computer_use` / `memory`：转成平台级基础能力；
- `docs/development`：沉淀为 Cursor / Codex 可执行的开发说明。

---

## 2. 市场发现（截至 2026-05-17）

### 首次扫描（2026-05-17 上午）

| 候选 | stars | license | Titan 价值 | 建议动作 |
|------|-------|---------|------------|----------|
| GitHub MCP Server | 29.9k | MIT | 官方 GitHub MCP，可强化代码、Issue、PR、CI/CD 自动化 | 优先作为工程 agent 工具包候选 |
| Context7 | 55.4k | MIT | 给 coding / delivery agent 注入最新库文档，降低幻觉 | 先作为文档新鲜度 skill/sidecar |
| Conductor OSS | 31.8k | Apache-2.0 | durable workflow、重试、回放、人审，适合参考 Titan DAG 进化 | 作为架构参考，不直接嵌入 |
| ToolHive | 1.8k | Apache-2.0 | MCP registry、gateway、隔离运行、审计、OTel | 评估作为 MCP 安全运行时参考 |
| Apify Agent Skills | 2k | Apache-2.0 | web data、lead gen、竞品监控等技能模式成熟 | 转成行业 SkillDoc / capability stub |
| IBM MCP Context Forge | 3.7k | Apache-2.0 + unknown policy file | MCP/A2A/REST 统一网关、插件、guardrails | 只学习架构，复制代码前需法务审查 |

### 第二次扫描（2026-05-17 下午 — 深度扫描）

| 候选 | stars | license | Titan 价值 | 建议动作 |
|------|-------|---------|------------|----------|
| **Browser Use** | ~90k | MIT | CDP 直连浏览器，速度 2x、token 减半，WebVoyager 89.1% | 评估作为 `computer_use` Runner 第二后端 |
| **UI-TARS Desktop** | 27k | Apache-2.0 | 纯视觉 GUI Agent，已列入 Titan grounding 候选 | 集成作为 Computer Use grounding 模型 |
| **OpenViking** | 21.7k | Apache-2.0 | 文件系统范式上下文 DB，L0/L1/L2 分层，83% token 节省 | 融入 Memory Tree 分层加载设计 |
| **OpenClaw** | 150k+ | 待确认 | 10 大销售工作流模式，模型无关 + Cron 调度 | 转为 Titan 销售行业插件模板 |
| **Statewave** | v0.7.1 | 待确认 | Postgres+pgvector durable episodes + ranked retrieval | 参考 episodes 和多因子排序模式 |
| **DeerFlow 2.0** | 46k+ | Apache-2.0 | 沙箱执行 runtime + 子代理编排 + MCP 集成 | 参考沙箱编排架构 |
| **Tooltrim** | 新兴 | 待确认 | MCP proxy，token 节省 70-93%，~3.7ms 延迟 | 评估用于 MCP 工具列表优化 |
| **NocoBase** | 21.7k | Apache-2.0 | AI 员工嵌入业务流程（Scout/Viz/Ellis/Dex/Lexi） | 参考 AI 员工 UX 和角色设计 |
| **Stagehand** | ~20.8k | MIT | AI+代码混合控制 + 自愈 + 操作缓存 | 参考混合自动化模式 |
| **CrewAI** | 46k | Apache-2.0 | Role-based agent teams, MCP + A2A 支持 | 参考 Agent 角色团队设计 |
| **agency-agents** | 60k+ | MIT | 144 预定义专业代理模板 | 参考 Agent 模板化方法 |
| **agentgateway** | ~2k | Apache-2.0 | Linux Foundation 统一 MCP/A2A 网关 v1.0 | 参考 MCP registry 架构 |
| **Mem0** | 48k+ | Apache-2.0 | 最大独立记忆层社区，SOC 2 | 参考通用记忆层设计 |
| **LongMemEval** | 学术基准 | — | 6 维度 agent memory 评估标准 | 用于 Memory Tree 质量回归测试 |

---

## 3. 产品更新范围

### 首次更新（2026-05-17 上午）

低风险基础设施，不引入第三方依赖、不复制第三方代码：

1. 新增 `backend/app/evolution/capability_radar.py`。
2. 新增 API：`GET /api/v1/evolution/capability-radar`。
3. 支持 `category` 查询参数，例如 `?category=mcp`。
4. 增加单元测试，保证候选项可排序、可过滤、有落地动作。

### 第二次更新（2026-05-17 下午 — 深度扫描与模板落地）

1. **capability_radar.py 扩展**：添加 8 个新候选项目（Browser Use、OpenViking、OpenClaw、Statewave、UI-TARS Desktop、DeerFlow 2.0、Tooltrim、NocoBase）。
2. **行业插件模板**：新增 `backend/app/industry_plugins/sales_outreach/` 目录，含 `workflow.yaml`（7 步销售外呼 DAG）、`agent_roles.yaml`（3 个销售角色定义）、`skill_docs/README.md`（7 个技能文档占位）。
3. **ADR 草案**：新增 `docs/adr/002-memory-tiered-loading.md`，将 OpenViking 的 L0/L1/L2 分层思想、Statewave 的多因子排序融入 Titan Memory Tree 设计。
4. **日报存档**：`docs/radar/2026-05-17-daily-radar.md` 含完整评估、优先级和建议集成路径。

---

## 4. 后续 Cursor 开发任务说明

Cursor 接力开发时按以下顺序执行：

1. 在前端 `frontend/app/[locale]/evolution/page.tsx` 增加「Capability Radar」区域。
2. 调用 `/api/v1/evolution/capability-radar` 展示候选能力卡片。
3. 每张卡展示：名称、类别、stars、license、Titan fit score、建议动作、风险说明。
4. 增加筛选：`mcp`、`workflow`、`skills`、`docs`、`security-runtime`。
5. 增加「转成开发任务」按钮的前端占位，按钮保持 disabled，后端下一阶段再接入 Issue / Task 创建。
6. 不要自动安装候选项目，不要要求用户输入第三方密钥，不要把候选能力标记为 live。

---

## 5. 验收标准

- 后端测试：`pytest backend/tests/test_capability_radar.py` 通过。
- API 返回结构包含 `summary` 与 `items`。
- 候选项按 `titan_fit_score` 降序排列。
- 对有许可证风险的项目明确标记风险。
- 前端只展示「候选/建议」，不误导用户认为能力已经接入完成。

---

## 6. 安全边界

- GPL / AGPL 项目只能作为独立侧车或架构参考。
- Apache/MIT 项目也不得直接复制大段代码，先转模式、接口、测试清单。
- MCP server 默认视为不可信执行体，必须经过沙箱、权限、审计、网络隔离。
- 写能力必须比读能力更严格：OAuth scope、tenant grant、quota、audit log 缺一不可。
