# ADR 002: Memory Tree 分层加载 (Tiered Memory Loading)

> 状态：Draft（提议阶段，未批准）  
> 日期：2026-05-17  
> 决策者：待定  
> 影响模块：`backend/app/memory/`、`backend/app/context_sync/`、`backend/app/agents/base_agent.py`

---

## 背景与动机

当前 Titan Memory Tree 的设计为 level=0（chunk）、level=1（rollup）、level=2（agent summary），所有层级平等存储在 Qdrant 中，Agent prompt 注入时使用 flat top-k 检索。这导致两个问题：

1. **token 浪费**：Agent 获得过多细粒度 chunk 而非压缩后的高层摘要，上下文窗口利用率低。
2. **检索精度不足**：没有根据 task type / agent role / urgency 调整检索深度，每次都做全深度检索。

参考开源生态中的最佳实践（OpenViking 的 L0/L1/L2 文件系统分层、Letta/MemGPT 的 OS 风格内存分页、Hindsight 的多策略检索），建议引入分层加载机制。

---

## 建议方案

### 分层模型

| 层级 | 名称 | 存储位置 | 内容 | 典型 token | 加载条件 |
|------|------|----------|------|-----------|----------|
| L0 | Working Memory | 会话内 Redis | 当前对话消息、最近任务结果 | 4k-8k | 总是加载 |
| L1 | Project Context | Qdrant (level=1 rollup) | 项目内最近摘要、活跃 PR/Issue 概要 | 2k-4k | task.context 命中时加载 |
| L2 | Long-term Knowledge | Qdrant (level=2) + Postgres | 跨项目知识、技能文档、行业模板 | 1k-2k | 语义匹配阈值触发 |

### Agent Prompt 注入策略

```
prompt_injection = L0 (always) 
                 + L1 (if task.source_project or task.tags match)
                 + L2 (top-k semantic search, max 3 results)
                 = total ≤ configurable MAX_CONTEXT_TOKENS (default 8k)
```

### 检索优先级（参考 Statewave 的 ranked retrieval）

```python
score = semantic_similarity * w_sem 
      + recency_boost(days_since_update) * w_rec 
      + role_relevance(agent_role, memory_tags) * w_rel
      + temporal_validity(memory.created_at, memory.expires_at) * w_tmp
```

---

## 与开源参考的对齐

| 参考项目 | 借鉴点 | Titan 落地方式 |
|----------|--------|---------------|
| OpenViking | AGFS 文件系统分层、L0/L1/L2、可视化检索轨迹 | `memory_hierarchy.py` 分层加载器 |
| Statewave | Durable episodes、ranked retrieval、token budget | `context_retrieval.py` 多因子排序 |
| Hindsight | Multi-strategy retrieval（semantic + BM25 + graph + temporal） | 多因子融合评分函数 |
| Letta/MemGPT | OS 风格内存分页、core/archival/recall 三级 | 分层模型对齐 |

---

## 文件变更预估

```
新增:
  backend/app/memory/memory_hierarchy.py   # L0/L1/L2 分层加载器
  backend/app/memory/retrieval_ranker.py   # 多因子排序评分
  backend/tests/test_memory_hierarchy.py
  backend/tests/test_retrieval_ranker.py

修改:
  backend/app/memory/context_retrieval.py  # 接入分层 + 排序
  backend/app/agents/base_agent.py         # prompt 注入改为分层
  backend/app/context_sync/rollup.py       # L2 rollup 增加标签
  docs/development/M02-Context-Sync.md     # 更新检索说明
  docs/development/附录-接口与数据字典.md   # 新增 memory_hierarchy 表/字段
```

---

## 风险与缓解

| 风险 | 缓解 |
|------|------|
| 分层加载增加检索延迟 | L0 从 Redis 取，延迟 <5ms；L1/L2 并行检索 |
| rollup 质量不足导致 L1 信息密度低 | rollup 任务增加质量评分，低于阈值触发重新总结 |
| 租户间跨层检索泄露 | Qdrant 的 `tenant_id` filter 在所有层级强制应用 |

---

## 未决问题（讨论中）

1. L2 rollup 触发时机：当前设计是每 6h 定时批量 rollup，是否需要事件驱动（例如项目 milestone 关闭时立即 rollup）？
2. Token budget 配置粒度：租户级 vs 角色级 vs 任务级？建议租户级默认 + 角色级覆盖。
3. 检索轨迹 (retrieval trace) 的可视化：前端如何展示"为什么 Agent 获得了这段 memory"？参考 OpenViking 的可视化模式。

---

## 参考资料

- [OpenViking — Filesystem Context Database](https://github.com/volcengine/OpenViking)
- [Statewave — Memory Runtime](https://github.com/smaramwbc/statewave)
- [Hindsight vs Cognee — AI Agent Memory Comparison (2026)](https://vectorize.io/articles/hindsight-vs-cognee)
- [Best AI Agent Memory Frameworks in 2026](https://atlan.com/know/best-ai-agent-memory-frameworks-2026/)
- [Titan 产品开发说明 — Memory Tree](../Titan_双轨进化_ContextSync_ComputerUse_OpenHuman_产品开发说明.md#33-数据管道)
