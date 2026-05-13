# Titan Evolution OS — 完整开发方案
> 版本 v1.0 | 自进化数字员工操作系统

---

## 目录

1. [产品定义与核心理念](#1-产品定义)
2. [系统整体架构](#2-系统架构)
3. [数据库设计](#3-数据库设计)
4. [后端开发方案](#4-后端方案)
5. [前端产品功能设计](#5-前端设计)
6. [Agent 模块详细设计](#6-agent-设计)
7. [进化引擎详细设计](#7-进化引擎)
8. [记忆与技能系统](#8-记忆系统)
9. [多行业扩展架构](#9-扩展架构)
10. [开发路线图](#10-roadmap)
11. [技术栈清单](#11-技术栈)
12. [风险与应对](#12-风险)

---

## 1. 产品定义

### 1.1 一句话定义

**Titan Evolution OS** 是一套可以自我进化的数字员工操作系统：
- 每个 Agent = 一名有记忆、有技能、会学习的数字员工
- Evolution Layer = 自动优化岗位配置、淘汰低效 Prompt
- Memory Layer = 沉淀行业经验，换了底层模型也不会"失忆"
- Multi-Industry Core = 同一套引擎，插件化切换行业场景

### 1.2 核心差异化

| 普通 AI 工具 | Titan Evolution OS |
|---|---|
| 每次对话从零开始 | 长期记忆持续积累 |
| Prompt 手动优化 | 基于绩效自动进化 |
| 单一任务执行 | 多岗位协作流水线 |
| 绑定特定 LLM | 模型无关，技能可迁移 |
| 单一场景 | 插件化多行业扩展 |

### 1.3 用户价值

- **创业公司**：用 5 个 Agent 替代早期销售/研究/运营团队
- **中小企业**：让现有团队 10 倍产能，AI 负责重复性工作
- **服务商**：将这套系统作为产品交付给客户（SaaS 模式）

---

## 2. 系统架构

### 2.1 四层架构总览

```
┌─────────────────────────────────────────────────────────────────┐
│                    TITAN EVOLUTION OS                           │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 4: Industry Plugin Layer  (行业插件层)                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ Payment  │ │ SaaS B2B │ │ E-Comm   │ │ [Custom] │ ...       │
│  │ Fintech  │ │ Growth   │ │ Ops      │ │ Plugin   │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 3: Evolution Engine  (进化引擎层)                         │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────┐   │
│  │ KPI Scorer  │  │ Prompt Evolver│  │ Workflow Optimizer  │   │
│  │ 绩效评分    │  │ Prompt自动进化│  │ 流程结构优化        │   │
│  └─────────────┘  └──────────────┘  └─────────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 2: Memory & Skill Layer  (记忆技能层)                     │
│  ┌────────────┐  ┌─────────────┐  ┌────────────────────────┐  │
│  │ Short-Term │  │  Long-Term  │  │     Skill Docs         │  │
│  │   Redis    │  │   Qdrant    │  │  Markdown + JSON       │  │
│  └────────────┘  └─────────────┘  └────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 1: Execution Layer  (执行层)                              │
│  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐  │
│  │ Hunter  │ │Researcher│ │ Outreach │ │ Delivery         │  │
│  │ Agent   │ │ Agent    │ │ Agent    │ │ Agent            │  │
│  └────┬────┘ └────┬─────┘ └────┬─────┘ └────────┬─────────┘  │
│       └───────────┴────────────┴────────────────┘             │
│  Tools: Apollo | Resend | Airtable | Search | Webhook          │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 请求流转图

```
用户下达目标
    │
    ▼
Evolution Manager 解析目标
    │
    ├─► 拆分子任务
    │       │
    │       ▼
    │   任务队列 (Redis Queue)
    │       │
    │       ▼
    │   分配给对应 Agent
    │       │
    │       ├─► 读取 Memory Layer（相关经验 + 技能文档）
    │       │
    │       ├─► 组装增强 Prompt
    │       │
    │       ├─► 调用 LLM API 执行
    │       │
    │       └─► 输出结果 + 记录绩效日志
    │
    ├─► 汇总结果 → 交付输出
    │
    └─► 触发进化评估（异步）
            │
            ├─► 评分是否达标？
            │       ├─ 是 → 继续当前 Prompt
            │       └─ 否 → 触发 Prompt 进化流程
            │
            └─► 技能沉淀（写入 Skill Docs）
```

---

## 3. 数据库设计

### 3.1 关系型数据库（PostgreSQL）

```sql
-- ================================================
-- 核心业务表
-- ================================================

-- 租户表（多行业 SaaS 基础）
CREATE TABLE tenants (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(255) NOT NULL,
    industry_plugin VARCHAR(100) NOT NULL,  -- 'payment_fintech' | 'saas_b2b' | 'ecommerce'
    plan            VARCHAR(50)  NOT NULL,  -- 'starter' | 'growth' | 'enterprise'
    config          JSONB        DEFAULT '{}',  -- 行业特定配置
    created_at      TIMESTAMPTZ  DEFAULT NOW()
);

-- Agent 档案表
CREATE TABLE agents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID REFERENCES tenants(id),
    name            VARCHAR(255) NOT NULL,
    role            VARCHAR(100) NOT NULL,  -- 'hunter' | 'researcher' | 'outreach' | 'delivery' | 'manager'
    prompt_version  INTEGER      DEFAULT 1,
    current_prompt  TEXT         NOT NULL,
    status          VARCHAR(50)  DEFAULT 'active',  -- 'active' | 'testing' | 'retired'
    generation      INTEGER      DEFAULT 1,  -- 第几代进化
    parent_agent_id UUID REFERENCES agents(id),  -- 从哪个Agent进化而来
    meta            JSONB        DEFAULT '{}',
    created_at      TIMESTAMPTZ  DEFAULT NOW()
);

-- 任务表
CREATE TABLE tasks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID REFERENCES tenants(id),
    agent_id        UUID REFERENCES agents(id),
    type            VARCHAR(100) NOT NULL,  -- 'lead_search' | 'email_write' | 'send_email' | 'research'
    input           JSONB        NOT NULL,
    output          JSONB,
    status          VARCHAR(50)  DEFAULT 'pending',  -- 'pending'|'running'|'done'|'failed'
    token_used      INTEGER      DEFAULT 0,
    duration_ms     INTEGER,
    created_at      TIMESTAMPTZ  DEFAULT NOW(),
    completed_at    TIMESTAMPTZ
);

-- 绩效日志表（进化的燃料）
CREATE TABLE performance_logs (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id            UUID REFERENCES tenants(id),
    agent_id             UUID REFERENCES agents(id),
    task_id              UUID REFERENCES tasks(id),
    success_flag         BOOLEAN      NOT NULL,
    quality_score        FLOAT,       -- 0.0 - 1.0，人工评分或自动评估
    token_cost           INTEGER      DEFAULT 0,
    latency_ms           INTEGER,
    human_feedback       TEXT,        -- 人工反馈文本
    auto_eval_reason     TEXT,        -- 自动评估原因
    created_at           TIMESTAMPTZ  DEFAULT NOW()
);

-- Prompt 版本历史表
CREATE TABLE prompt_versions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id        UUID REFERENCES agents(id),
    version         INTEGER      NOT NULL,
    content         TEXT         NOT NULL,
    avg_score       FLOAT        DEFAULT 0,
    task_count      INTEGER      DEFAULT 0,
    status          VARCHAR(50)  DEFAULT 'active',  -- 'active' | 'archived' | 'testing'
    evolved_reason  TEXT,        -- 为什么产生这个版本
    created_at      TIMESTAMPTZ  DEFAULT NOW()
);

-- A/B 测试表
CREATE TABLE ab_tests (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id        UUID REFERENCES agents(id),
    variant_a_id    UUID REFERENCES prompt_versions(id),
    variant_b_id    UUID REFERENCES prompt_versions(id),
    status          VARCHAR(50)  DEFAULT 'running',
    winner_id       UUID REFERENCES prompt_versions(id),
    started_at      TIMESTAMPTZ  DEFAULT NOW(),
    ended_at        TIMESTAMPTZ
);

-- 技能文档表
CREATE TABLE skill_docs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID REFERENCES tenants(id),
    name            VARCHAR(255) NOT NULL,
    description     TEXT,
    content_md      TEXT         NOT NULL,
    role_tags       TEXT[]       DEFAULT '{}',  -- 适用岗位
    industry_tags   TEXT[]       DEFAULT '{}',  -- 适用行业
    usage_count     INTEGER      DEFAULT 0,
    success_rate    FLOAT        DEFAULT 0,
    is_global       BOOLEAN      DEFAULT FALSE,
    source_agent_id UUID REFERENCES agents(id),
    version         INTEGER      DEFAULT 1,
    created_at      TIMESTAMPTZ  DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  DEFAULT NOW()
);

-- 工作流模板表
CREATE TABLE workflow_templates (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID REFERENCES tenants(id),
    name            VARCHAR(255) NOT NULL,
    industry        VARCHAR(100),
    dag_config      JSONB        NOT NULL,  -- 有向无环图：节点+边
    avg_score       FLOAT        DEFAULT 0,
    run_count       INTEGER      DEFAULT 0,
    is_active       BOOLEAN      DEFAULT TRUE,
    created_at      TIMESTAMPTZ  DEFAULT NOW()
);

-- CRM 联系人表（Payment Fintech 插件默认）
CREATE TABLE contacts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID REFERENCES tenants(id),
    company_name    VARCHAR(255),
    contact_name    VARCHAR(255),
    email           VARCHAR(255),
    linkedin_url    TEXT,
    industry        VARCHAR(100),
    country         VARCHAR(100),
    company_size    VARCHAR(50),
    status          VARCHAR(100) DEFAULT 'new',  -- 'new'|'contacted'|'replied'|'meeting'|'won'|'lost'
    score           FLOAT        DEFAULT 0,
    assigned_agent  UUID REFERENCES agents(id),
    notes           TEXT,
    meta            JSONB        DEFAULT '{}',
    created_at      TIMESTAMPTZ  DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  DEFAULT NOW()
);

-- 邮件记录表
CREATE TABLE emails (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID REFERENCES tenants(id),
    contact_id      UUID REFERENCES contacts(id),
    agent_id        UUID REFERENCES agents(id),
    subject         TEXT         NOT NULL,
    body            TEXT         NOT NULL,
    status          VARCHAR(50)  DEFAULT 'sent',  -- 'draft'|'sent'|'opened'|'replied'|'bounced'
    sent_at         TIMESTAMPTZ,
    opened_at       TIMESTAMPTZ,
    replied_at      TIMESTAMPTZ,
    thread_id       VARCHAR(255),  -- 邮件线程ID
    created_at      TIMESTAMPTZ  DEFAULT NOW()
);
```

### 3.2 向量数据库（Qdrant）集合设计

```
Collections:

1. agent_memories_{tenant_id}
   向量维度: 1536 (text-embedding-3-small)
   Payload: {
     agent_id, task_type, summary,
     success_flag, quality_score,
     timestamp, tags[]
   }

2. skill_embeddings_{tenant_id}
   向量维度: 1536
   Payload: {
     skill_id, skill_name, role_tags[],
     industry_tags[], success_rate
   }

3. contact_profiles_{tenant_id}
   向量维度: 1536
   Payload: {
     contact_id, company_profile_text,
     industry, country, status
   }
```

### 3.3 Redis 键设计

```
# 短期记忆（任务上下文，TTL 24h）
task:context:{task_id}            → JSON

# Agent 工作队列
queue:agent:{agent_id}            → List

# 实时绩效缓存（触发进化用）
perf:agent:{agent_id}:recent      → Sorted Set（最近50条score）

# 进化锁（防止同一Agent并发进化）
lock:evolve:{agent_id}            → String (TTL 10min)

# 限流
ratelimit:llm:{tenant_id}         → Counter (TTL 1min)
```

---

## 4. 后端方案

### 4.1 技术选型

```
框架:        FastAPI (Python) — 异步友好，AI 生态丰富
数据库:      PostgreSQL 15 + SQLAlchemy ORM
向量库:      Qdrant (自托管 Docker)
缓存队列:    Redis 7
任务调度:    Celery + Redis Broker
LLM 调用:   LiteLLM (统一接口，支持 GPT/Claude/Llama 切换)
部署:        Docker Compose (开发) → Kubernetes (生产)
监控:        Prometheus + Grafana
日志:        Structlog + Loki
```

### 4.2 目录结构

```
titan-evolution-os/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI 入口
│   │   ├── core/
│   │   │   ├── config.py              # 环境配置
│   │   │   ├── database.py            # DB 连接
│   │   │   ├── redis_client.py
│   │   │   └── qdrant_client.py
│   │   │
│   │   ├── agents/
│   │   │   ├── base_agent.py          # Agent 基类
│   │   │   ├── hunter_agent.py
│   │   │   ├── researcher_agent.py
│   │   │   ├── outreach_agent.py
│   │   │   ├── delivery_agent.py
│   │   │   └── manager_agent.py
│   │   │
│   │   ├── evolution/
│   │   │   ├── scorer.py              # KPI 评分引擎
│   │   │   ├── evolver.py             # Prompt 进化器
│   │   │   ├── ab_test.py             # A/B 测试管理
│   │   │   └── workflow_optimizer.py  # 流程优化
│   │   │
│   │   ├── memory/
│   │   │   ├── short_term.py          # Redis 短期记忆
│   │   │   ├── long_term.py           # Qdrant 长期记忆
│   │   │   └── skill_manager.py       # 技能库管理
│   │   │
│   │   ├── tools/
│   │   │   ├── apollo_tool.py         # Apollo API
│   │   │   ├── resend_tool.py         # Resend 邮件
│   │   │   ├── airtable_tool.py       # Airtable CRM
│   │   │   ├── search_tool.py         # 搜索
│   │   │   └── tool_registry.py       # 工具注册中心
│   │   │
│   │   ├── industry_plugins/          # 行业插件（核心扩展点）
│   │   │   ├── base_plugin.py         # 插件基类（接口定义）
│   │   │   ├── payment_fintech/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── agents.py          # 行业特定 Agent 配置
│   │   │   │   ├── workflows.py       # 行业工作流模板
│   │   │   │   ├── skills/            # 行业技能文档
│   │   │   │   │   ├── mena_pitch.md
│   │   │   │   │   └── license_research.md
│   │   │   │   └── tools.py           # 行业特定工具
│   │   │   │
│   │   │   ├── saas_b2b/              # 未来扩展
│   │   │   └── ecommerce/             # 未来扩展
│   │   │
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── agents.py          # Agent CRUD
│   │   │   │   ├── tasks.py           # 任务管理
│   │   │   │   ├── evolution.py       # 进化控制
│   │   │   │   ├── memory.py          # 记忆查询
│   │   │   │   ├── crm.py             # CRM 接口
│   │   │   │   └── analytics.py       # 数据分析
│   │   │   └── websocket.py           # 实时推送
│   │   │
│   │   └── workers/
│   │       ├── task_worker.py         # Celery 任务执行
│   │       ├── evolution_worker.py    # 进化调度（定时）
│   │       └── memory_worker.py       # 记忆沉淀（异步）
│   │
│   ├── tests/
│   ├── alembic/                       # 数据库迁移
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/                          # 见前端章节
├── docker-compose.yml
└── k8s/                               # Kubernetes 配置
```

### 4.3 核心模块代码设计

#### Agent 基类

```python
# agents/base_agent.py
class BaseAgent:
    def __init__(self, agent_id: str, tenant_id: str):
        self.agent_id = agent_id
        self.tenant_id = tenant_id
        self.memory = MemoryManager(agent_id, tenant_id)
        self.tools = ToolRegistry.get_tools_for_role(self.role)

    async def run(self, task: Task) -> TaskResult:
        # 1. 从记忆层构建增强 Prompt
        enhanced_prompt = await self._build_prompt(task)

        # 2. 执行 LLM 调用
        result = await self._call_llm(enhanced_prompt)

        # 3. 解析并执行工具调用
        if result.requires_tool:
            result = await self._execute_tools(result)

        # 4. 异步写入绩效日志
        asyncio.create_task(self._log_performance(task, result))

        # 5. 异步写入记忆
        asyncio.create_task(self.memory.save(task, result))

        return result

    async def _build_prompt(self, task: Task) -> str:
        # 并行获取记忆和技能
        memories, skills = await asyncio.gather(
            self.memory.retrieve_relevant(task.context, top_k=3),
            self.memory.get_relevant_skills(task.type, top_k=5)
        )
        return PromptBuilder.build(
            base=self.current_prompt,
            memories=memories,
            skills=skills,
            task=task
        )
```

#### 进化引擎

```python
# evolution/evolver.py
class PromptEvolver:
    EVOLUTION_THRESHOLD = 0.65   # 低于此分数触发进化
    MIN_SAMPLES = 20             # 最少样本数才进化

    async def maybe_evolve(self, agent_id: str):
        # 防止并发进化
        if not await redis.set(f"lock:evolve:{agent_id}", 1, nx=True, ex=600):
            return

        try:
            stats = await self._get_recent_stats(agent_id)
            if stats.sample_count < self.MIN_SAMPLES:
                return
            if stats.avg_score >= self.EVOLUTION_THRESHOLD:
                return

            # 收集失败案例
            failures = await self._get_failure_cases(agent_id, limit=10)
            current_prompt = await self._get_current_prompt(agent_id)

            # 用 LLM 生成新 Prompt
            new_prompt = await self._generate_evolved_prompt(
                current_prompt, failures, stats
            )

            # 创建 A/B 测试
            await self._create_ab_test(agent_id, current_prompt, new_prompt)

        finally:
            await redis.delete(f"lock:evolve:{agent_id}")

    async def _generate_evolved_prompt(
        self, current: str, failures: list, stats: Stats
    ) -> str:
        meta_prompt = f"""
你是一个 Prompt 工程师。请分析以下失败案例，改进 Agent 的系统提示词。

当前 Prompt:
{current}

失败案例（最近10条）:
{format_failures(failures)}

当前平均分: {stats.avg_score:.2f}
主要失败原因: {stats.top_failure_reasons}

要求：
1. 保留原 Prompt 的核心角色定义
2. 针对失败原因添加具体指导
3. 不超过原 Prompt 长度的 1.3 倍
4. 只输出新 Prompt，不要解释

新 Prompt:
"""
        return await llm.complete(meta_prompt, model="gpt-4o")
```

#### 技能沉淀

```python
# memory/skill_manager.py
class SkillManager:
    async def maybe_create_skill(self, task: Task, result: TaskResult):
        """当任务成功时，判断是否值得沉淀为技能文档"""
        if not result.success:
            return
        if result.quality_score < 0.8:  # 只沉淀高质量结果
            return

        # 检查是否已有类似技能（避免重复）
        similar = await self._find_similar_skill(task.type, result.summary)
        if similar and similar.success_rate > 0.85:
            # 已有更好的技能，只更新使用计数
            await self._increment_usage(similar.id)
            return

        # 生成技能文档（Markdown）
        skill_doc = await self._generate_skill_doc(task, result)
        await self._save_skill(skill_doc)

    async def _generate_skill_doc(self, task, result) -> SkillDoc:
        prompt = f"""
将以下成功的任务执行过程，提炼为一份可复用的 SOP 技能文档（Markdown格式）。

任务类型: {task.type}
输入: {task.input}
执行步骤: {result.steps}
最终输出: {result.output}

要求：
- 标题：简洁描述技能名称
- 适用场景：什么时候用这个技能
- 前置条件：需要哪些输入
- 执行步骤：清晰的步骤列表
- 注意事项：常见坑和解决方法
- 输出示例：期望的输出格式

只输出 Markdown 文档：
"""
        content = await llm.complete(prompt)
        return SkillDoc(
            name=extract_title(content),
            content_md=content,
            role_tags=[task.agent_role],
            industry_tags=[task.industry],
            source_agent_id=task.agent_id
        )
```

### 4.4 API 接口清单

```
# Agent 管理
POST   /api/v1/agents                    创建 Agent
GET    /api/v1/agents                    获取 Agent 列表
GET    /api/v1/agents/{id}               Agent 详情
PUT    /api/v1/agents/{id}/prompt        手动更新 Prompt
POST   /api/v1/agents/{id}/retire        退休 Agent

# 任务管理
POST   /api/v1/tasks                     创建任务
GET    /api/v1/tasks                     任务列表
GET    /api/v1/tasks/{id}                任务详情
POST   /api/v1/tasks/{id}/feedback       人工反馈评分

# 进化管理
GET    /api/v1/evolution/status          当前进化状态
POST   /api/v1/evolution/trigger         手动触发进化
GET    /api/v1/evolution/ab-tests        A/B 测试列表
POST   /api/v1/evolution/ab-tests/{id}/conclude  结束A/B测试

# 记忆管理
GET    /api/v1/memory/skills             技能库列表
GET    /api/v1/memory/skills/{id}        技能文档详情
PUT    /api/v1/memory/skills/{id}        编辑技能文档
POST   /api/v1/memory/skills/{id}/promote 提升为全局技能

# CRM（Payment Fintech 插件）
POST   /api/v1/crm/contacts              添加联系人
GET    /api/v1/crm/contacts              联系人列表
PUT    /api/v1/crm/contacts/{id}/status  更新状态
GET    /api/v1/crm/pipeline              漏斗视图

# 分析
GET    /api/v1/analytics/dashboard       总览数据
GET    /api/v1/analytics/agents          Agent 绩效对比
GET    /api/v1/analytics/evolution       进化历史曲线

# WebSocket
WS     /ws/tasks/{task_id}               任务实时进度
WS     /ws/dashboard                     实时仪表盘更新
```

---

## 5. 前端产品功能设计

### 5.1 页面架构

```
titan-frontend/
├── 登录/注册
├── 主控台 (Dashboard)          ← 每日概览、实时任务流
├── 数字员工管理 (Agents)
│   ├── 员工列表
│   ├── 员工详情/绩效
│   └── Prompt 编辑器
├── 任务中心 (Tasks)
│   ├── 任务队列
│   ├── 执行日志
│   └── 人工反馈
├── 进化控制台 (Evolution)
│   ├── 进化状态总览
│   ├── A/B 测试管理
│   └── 进化历史时间线
├── 技能图书馆 (Skills)
│   ├── 技能卡片浏览
│   ├── 技能详情/编辑
│   └── 全局 vs 私有
├── CRM 面板 (仅 Fintech 插件)
│   ├── 线索看板（Kanban）
│   └── 邮件追踪
└── 设置
    ├── 行业插件选择
    ├── API 密钥管理
    └── 模型配置
```

### 5.2 核心页面详细设计

#### Dashboard（主控台）
```
布局：
┌─────────────────────────────────────────────────────┐
│ 今日概览卡片                                          │
│ [任务完成 47]  [成功率 78%]  [节省时间 12h]  [进化次数 2]│
├────────────────────────┬────────────────────────────┤
│ 实时任务流（左）         │ Agent 状态板（右）           │
│ ● Hunter 正在搜索...    │ 🟢 Hunter A  (score 0.82)   │
│ ● Outreach 发送邮件...  │ 🟡 Researcher (score 0.71)  │
│ ✅ Delivery 完成报告    │ 🔴 Outreach B (进化中...)   │
├────────────────────────┴────────────────────────────┤
│ 本周绩效趋势图（折线图）                               │
│ 进化事件时间线                                        │
└─────────────────────────────────────────────────────┘
```

#### Evolution Console（进化控制台）
```
这是产品最核心、最差异化的页面：

顶部：系统进化状态
  - 总进化次数
  - 最近进化时间
  - 平均分提升幅度

中部：Agent 进化对比
  Prompt v1 → v2 → v3 的 Score 折线图
  每次进化的触发原因标注

底部：A/B 测试看板
  当前进行中的对比实验
  实时胜率统计
  手动结束按钮（人工介入）
```

#### Skills Library（技能图书馆）
```
卡片式布局，类似 Notion：
- 搜索 + 行业/岗位标签筛选
- 每张卡片显示：技能名、成功率、使用次数、来源 Agent
- 点击展开：完整 Markdown 内容 + 编辑按钮
- "提升为全局" 开关（优质技能共享给所有 Agent）
```

---

## 6. Agent 模块详细设计

### 6.1 各岗位 Agent 规格

#### Growth Hunter Agent
```yaml
role: hunter
职责:
  - 根据 ICP (Ideal Customer Profile) 搜索目标公司
  - 找到关键联系人（CEO/BD/Sales）
  - 初步打分和过滤

默认工具:
  - apollo_search(filters)     # 公司+联系人搜索
  - web_search(query)          # 补充研究
  - contact_enrich(company)    # 联系人丰富

KPI 指标:
  - lead_quality_score         # 线索质量（后续由转化率反推）
  - leads_per_hour             # 效率
  - dedup_rate                 # 重复率（越低越好）

进化信号:
  - 线索最终转化为会议 → 正向
  - 线索质量评分 < 0.6 → 负向
```

#### Outreach Agent
```yaml
role: outreach
职责:
  - 撰写个性化邮件/LinkedIn消息
  - 安排发送时间
  - 跟进未回复名单

默认工具:
  - email_send(to, subject, body)
  - email_schedule(send_at)
  - crm_update(contact_id, status)

KPI 指标:
  - open_rate                  # 打开率
  - reply_rate                 # 回复率
  - meeting_booked_rate        # 会议转化率

进化信号:
  - 邮件被回复 → 正向
  - 邮件被标记垃圾 → 强负向
  - 会议被预约 → 强正向
```

### 6.2 Agent 状态机

```
           创建
            │
            ▼
         [active] ←──────────────────┐
            │                        │
            │ score < 阈值 × 20次     │
            ▼                        │
         [testing]                   │ A/B 测试胜出
            │                        │
       ┌────┴────┐                   │
       │         │                   │
    胜出        败北 ──────────────► [retired]
       │
       └──────────────────────────► [active] (新版本)
```

---

## 7. 进化引擎详细设计

### 7.1 评分公式

```
基础分 = 0.50 × 成功率
       + 0.30 × 质量评分（0-1）
       - 0.20 × Token消耗归一化值

归一化Token消耗 = agent_token_cost / baseline_token_cost

特殊加成/惩罚:
  × 1.3  如果任务带来了直接收入事件（成交/会议）
  × 0.7  如果输出被人工明确标记为差
  × 0.5  如果触发了垃圾邮件投诉
```

### 7.2 进化触发策略

```
阶段一（冷启动，前100任务）:
  - 关闭自动进化
  - 只记录，不行动
  - 人工每周复盘一次

阶段二（成长期，100-500任务）:
  - 自动评分 + 生成建议
  - 每次进化需人工确认
  - A/B 测试窗口：各跑20个任务

阶段三（成熟期，500+任务）:
  - 全自动进化
  - 人工设置护栏（最低分阈值、最大进化频率）
  - 重大变更仍推送通知
```

### 7.3 技能蒸馏（进阶功能）

```
触发条件：
  同一行业内，5个以上Agent产生了相似技能文档

执行流程：
  1. 聚类算法找到相似技能组
  2. 用 LLM 阅读所有版本
  3. 生成一份"最佳实践合并版"
  4. 标记为 Enterprise SOP
  5. 自动分发给该行业所有新 Agent
```

---

## 8. 记忆系统

### 8.1 三层记忆架构

```
Layer 1: Working Memory (工作记忆)
  存储: Redis
  内容: 当前任务上下文
  TTL: 24小时
  用途: 多轮对话、任务继续

Layer 2: Episodic Memory (情节记忆)
  存储: Qdrant 向量数据库
  内容: 历史任务执行片段（成功+失败）
  用途: 相似任务时检索参考经验
  检索: 余弦相似度，top-3

Layer 3: Semantic Memory (语义记忆)
  存储: PostgreSQL + Qdrant
  内容: 提炼后的技能文档（SOP）
  用途: 新任务前注入稳定知识
  检索: 按 role_tags + industry_tags + 语义相似度
```

### 8.2 Prompt 组装模板

```
[系统角色定义]
你是 Titan 系统中的 {role_name}，负责 {role_description}。

[行业上下文]
当前行业：{industry}
客户档案：{customer_profile}

[相关经验]（从情节记忆注入）
以下是你过去处理类似任务的经验：
{relevant_memories_formatted}

[可用技能]（从语义记忆注入）
以下是适用于此类任务的 SOP：
{relevant_skills_formatted}

[当前任务]
{task_description}

[执行要求]
{role_specific_constraints}

[输出格式]
{output_schema}
```

---

## 9. 多行业扩展架构

### 9.1 插件接口定义（IndustryPlugin 基类）

```python
# industry_plugins/base_plugin.py
from abc import ABC, abstractmethod

class IndustryPlugin(ABC):
    """
    所有行业插件必须实现这个接口
    新行业只需继承此类，无需修改核心代码
    """

    @property
    @abstractmethod
    def plugin_id(self) -> str:
        """唯一标识，如 'payment_fintech'"""

    @property
    @abstractmethod
    def display_name(self) -> str:
        """显示名称，如 'Payment & Fintech'"""

    @abstractmethod
    def get_agent_configs(self) -> list[AgentConfig]:
        """返回该行业默认的 Agent 角色配置"""

    @abstractmethod
    def get_workflow_templates(self) -> list[WorkflowTemplate]:
        """返回该行业的工作流模板"""

    @abstractmethod
    def get_default_skills(self) -> list[SkillDoc]:
        """返回预置的行业技能文档"""

    @abstractmethod
    def get_kpi_definition(self) -> KPIDefinition:
        """定义该行业的 KPI 评分规则（覆盖默认公式）"""

    @abstractmethod
    def get_required_tools(self) -> list[str]:
        """该行业需要启用的工具列表"""

    def get_custom_ui_config(self) -> dict:
        """可选：自定义前端 UI 配置（表单、看板字段等）"""
        return {}
```

### 9.2 当前与规划中的插件

```
已实现:
  ✅ payment_fintech
     - 支付/金融科技获客
     - 工具: Apollo, Resend, Airtable
     - 特殊Agent: License Researcher

规划中（复用核心，配置不同）:
  🔲 saas_b2b_growth
     - SaaS 产品 PLG 增长
     - 新增工具: Product Hunt API, G2 Reviews
     - 特殊Agent: Trial Converter

  🔲 ecommerce_ops
     - 跨境电商运营
     - 新增工具: Shopify API, 1688 API
     - 特殊Agent: Supplier Hunter

  🔲 content_media
     - 自媒体矩阵管理
     - 新增工具: Twitter API, YouTube API
     - 特殊Agent: Content Repurposer

  🔲 code_audit
     - 自动化代码安全审计
     - 新增工具: GitHub API, SAST tools
     - 特殊Agent: Vulnerability Researcher

  🔲 [Custom Plugin SDK]
     - 提供给企业客户的私有插件开发能力
```

### 9.3 新行业接入成本估算

```
复用核心框架（无需改动）:
  ✅ 进化引擎（~0 天）
  ✅ 记忆系统（~0 天）
  ✅ 数据库表结构（~0 天）
  ✅ 前端核心页面（~0 天）

需要新开发:
  ⚙️ IndustryPlugin 实现类（2-3 天）
  ⚙️ 行业专属 Agent Prompt（2-3 天）
  ⚙️ 新增 API 工具集成（3-5 天/个工具）
  ⚙️ 行业专属 UI 组件（1-2 天）
  ⚙️ 预置技能文档撰写（2-3 天）

总计: 新行业接入约 2-3 周（vs 从零开发约 2-3 个月）
```

---

## 10. 开发路线图

### Phase 0：基础设施（第 1-2 周）

```
目标：让系统能跑起来

任务:
  □ Docker Compose 环境搭建
    - PostgreSQL + Redis + Qdrant
  □ FastAPI 项目骨架
  □ 数据库表创建 + Alembic 迁移
  □ LiteLLM 集成（先只接 OpenAI）
  □ 基础 API 框架（CRUD）

验收标准: 能创建一个 Agent，能调用 LLM，能记录日志
```

### Phase 1：执行层（第 3-4 周）

```
目标：让 Agent 能真正干活

任务:
  □ Hunter Agent 实现
    - Apollo API 集成
    - 基础搜索+过滤逻辑
  □ Outreach Agent 实现
    - Resend 邮件发送
    - 个性化邮件生成
  □ CRM Agent 实现
    - Airtable 集成
    - 状态流转管理
  □ 任务队列 (Celery)
  □ 基础前端：Dashboard + Task List

验收标准: 能端到端完成一条获客流（搜索→写信→发送→记录）
冷启动模式: 手动配置 Prompt，人工触发任务
```

### Phase 2：记忆层（第 5-6 周）

```
目标：让 Agent 有记忆

任务:
  □ Qdrant 集成 + 向量写入/查询
  □ Redis 短期记忆
  □ 情节记忆写入（任务完成后自动保存）
  □ Prompt 组装器（记忆注入）
  □ 技能文档自动生成
  □ 前端：Skills Library 页面

验收标准: 第二次执行同类任务时，能检索到上次经验并提升质量
```

### Phase 3：进化层（第 7-8 周）

```
目标：让系统开始进化

任务:
  □ KPI 评分引擎
  □ 人工反馈接口（前端评分 UI）
  □ Prompt 进化器（基于失败案例重写）
  □ A/B 测试框架
  □ 前端：Evolution Console 页面
  □ 进化事件通知（邮件/Webhook）

验收标准: 至少完成一次完整进化循环（检测低分→生成新Prompt→A/B测试→确定胜者）
```

### Phase 4：多租户 + 插件化（第 9-12 周）

```
目标：为商业化和扩展做准备

任务:
  □ 多租户隔离（数据、配额、计费）
  □ IndustryPlugin 基类 + payment_fintech 插件封装
  □ 第二个行业插件（SaaS B2B）验证插件架构
  □ 前端：插件市场/选择页面
  □ 用户权限系统（RBAC）
  □ 监控 + 告警（Prometheus + Grafana）

验收标准: 两个行业插件并存运行，相互隔离
```

### Phase 5：商业化（第 13-16 周）

```
目标：可以给付费客户使用

任务:
  □ 计费系统（按任务数/Agent数/Token数）
  □ SaaS 注册/支付流程
  □ 客户 Onboarding 流程自动化
  □ API 文档（供企业客户集成）
  □ Custom Plugin SDK（给企业客户）
  □ 数据导出（客户自己的数据）
```

---

## 11. 技术栈清单

### 后端

```
核心框架:    FastAPI 0.110+
ORM:         SQLAlchemy 2.0 (async)
数据库:      PostgreSQL 15
向量库:      Qdrant 1.9
缓存:        Redis 7
任务队列:    Celery 5 + Redis
LLM 统一:   LiteLLM（支持 GPT/Claude/Gemini/Llama）
嵌入向量:   text-embedding-3-small (OpenAI)
认证:        JWT + FastAPI-Users
配置管理:    Pydantic Settings
迁移:        Alembic
测试:        pytest + httpx
```

### 前端

```
框架:        Next.js 14 (App Router)
UI 库:       shadcn/ui + Tailwind CSS
状态管理:    Zustand + React Query
图表:        Recharts
实时:        Socket.io Client
富文本:      TipTap（技能文档编辑）
拖拽:        dnd-kit（Kanban）
```

### 基础设施

```
容器:        Docker + Docker Compose
编排:        Kubernetes（生产）
CI/CD:       GitHub Actions
监控:        Prometheus + Grafana
日志:        Loki + Grafana
对象存储:    S3 / Cloudflare R2（技能文档附件）
CDN:         Cloudflare
```

---

## 12. 风险与应对

| 风险 | 概率 | 影响 | 应对措施 |
|------|------|------|--------|
| LLM API 成本超预期 | 高 | 高 | 任务级 Token 预算限制；优先用本地模型执行 |
| 进化方向跑偏 | 中 | 高 | 人工护栏设置；进化变更必须通过人工审核（Phase1-2）|
| 冷启动数据不足 | 高 | 中 | Phase 0 预置 50+ 条人工标注样本作为种子数据 |
| 邮件被标记垃圾 | 中 | 高 | 发送频率限制；域名预热；邮件内容合规检测 |
| 行业插件架构耦合 | 低 | 高 | 严格遵守插件接口，禁止核心代码引用插件 |
| 向量检索不准确 | 中 | 中 | 定期重建索引；引入用户反馈修正嵌入 |

---

*文档版本: v1.0 | 最后更新: 2025*
*下一步: 基于此文档生成 Cursor 开发指令集*
