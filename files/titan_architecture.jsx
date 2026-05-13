import { useState } from "react";

const layers = [
  {
    id: "industry",
    label: "LAYER 4",
    title: "Industry Plugin Layer",
    subtitle: "行业插件层 — 可插拔扩展",
    color: "#c084fc",
    bg: "rgba(192,132,252,0.08)",
    border: "rgba(192,132,252,0.3)",
    items: [
      { id: "fintech", label: "Payment Fintech", icon: "💳", status: "live", desc: "支付金融科技获客：Lead搜索→个性化触达→会议转化" },
      { id: "saas", label: "SaaS B2B Growth", icon: "🚀", status: "planned", desc: "SaaS产品增长：PLG策略、试用转化、扩客" },
      { id: "ecomm", label: "E-Commerce Ops", icon: "🛒", status: "planned", desc: "跨境电商运营：选品、供应链、多平台管理" },
      { id: "content", label: "Content Media", icon: "📱", status: "planned", desc: "自媒体矩阵：内容生产、分发、数据分析" },
      { id: "custom", label: "Custom Plugin SDK", icon: "🔧", status: "future", desc: "企业私有插件开发工具包，完全自定义" },
    ],
  },
  {
    id: "evolution",
    label: "LAYER 3",
    title: "Evolution Engine",
    subtitle: "进化引擎层 — 系统核心大脑",
    color: "#f59e0b",
    bg: "rgba(245,158,11,0.08)",
    border: "rgba(245,158,11,0.3)",
    items: [
      { id: "scorer", label: "KPI Scorer", icon: "📊", status: "live", desc: "多维绩效评分：成功率 × 0.5 + 质量分 × 0.3 - Token消耗 × 0.2" },
      { id: "evolver", label: "Prompt Evolver", icon: "🧬", status: "live", desc: "基于失败案例自动重写Prompt，触发A/B测试验证效果" },
      { id: "abtest", label: "A/B Test Engine", icon: "⚖️", status: "live", desc: "新旧Prompt各跑20个任务，统计显著性胜出者晋升" },
      { id: "workflow", label: "Workflow Optimizer", icon: "🔄", status: "live", desc: "分析任务依赖关系，自动优化串/并行执行结构" },
    ],
  },
  {
    id: "memory",
    label: "LAYER 2",
    title: "Memory & Skill Layer",
    subtitle: "记忆技能层 — 经验持久化",
    color: "#34d399",
    bg: "rgba(52,211,153,0.08)",
    border: "rgba(52,211,153,0.3)",
    items: [
      { id: "shortmem", label: "Short-Term Memory", icon: "⚡", status: "live", desc: "Redis — 任务上下文，TTL 24h，支持多轮对话连贯性" },
      { id: "longmem", label: "Long-Term Memory", icon: "🧠", status: "live", desc: "Qdrant向量库 — 历史经验片段，语义检索top-3注入Prompt" },
      { id: "skills", label: "Skill Docs Library", icon: "📚", status: "live", desc: "Markdown SOP文档，成功任务自动提炼，支持全局共享" },
      { id: "distill", label: "Skill Distiller", icon: "⚗️", status: "live", desc: "5个相似技能触发蒸馏，LLM合并为企业级最佳实践SOP" },
    ],
  },
  {
    id: "execution",
    label: "LAYER 1",
    title: "Execution Layer",
    subtitle: "执行层 — 实际干活的数字员工",
    color: "#60a5fa",
    bg: "rgba(96,165,250,0.08)",
    border: "rgba(96,165,250,0.3)",
    items: [
      { id: "hunter", label: "Growth Hunter", icon: "🎯", status: "live", desc: "Apollo搜索ICP公司 → 找联系人 → 质量评分过滤" },
      { id: "researcher", label: "Market Researcher", icon: "🔬", status: "live", desc: "市场机会分析、竞品追踪、行业政策研究" },
      { id: "outreach", label: "Outreach Agent", icon: "✉️", status: "live", desc: "个性化邮件撰写、Resend发送、自动跟进序列" },
      { id: "delivery", label: "Delivery Agent", icon: "📦", status: "live", desc: "Lead名单整理、周报生成、客户交付物输出" },
      { id: "manager", label: "Evolution Manager", icon: "🎮", status: "live", desc: "目标拆解、任务调度、KPI监控、进化决策" },
    ],
  },
];

const statusConfig = {
  live: { label: "已实现", color: "#34d399", dot: "#34d399" },
  planned: { label: "规划中", color: "#f59e0b", dot: "#f59e0b" },
  future: { label: "未来", color: "#94a3b8", dot: "#94a3b8" },
};

const phaseData = [
  { phase: "Phase 0", weeks: "W1-2", title: "基础设施", items: ["Docker环境", "FastAPI骨架", "DB建表", "LiteLLM接入"], color: "#6366f1" },
  { phase: "Phase 1", weeks: "W3-4", title: "执行层", items: ["Hunter Agent", "Outreach Agent", "CRM集成", "任务队列"], color: "#60a5fa" },
  { phase: "Phase 2", weeks: "W5-6", title: "记忆层", items: ["Qdrant集成", "情节记忆", "技能自动生成", "Prompt注入"], color: "#34d399" },
  { phase: "Phase 3", weeks: "W7-8", title: "进化层", items: ["KPI评分", "Prompt进化", "A/B测试", "进化控制台"], color: "#f59e0b" },
  { phase: "Phase 4", weeks: "W9-12", title: "插件化", items: ["多租户", "插件架构", "第二行业", "监控系统"], color: "#c084fc" },
  { phase: "Phase 5", weeks: "W13-16", title: "商业化", items: ["计费系统", "SaaS流程", "Plugin SDK", "企业API"], color: "#f87171" },
];

const techStack = [
  { cat: "后端框架", items: ["FastAPI", "SQLAlchemy", "Celery", "Alembic"] },
  { cat: "数据存储", items: ["PostgreSQL", "Redis", "Qdrant", "S3/R2"] },
  { cat: "AI层", items: ["LiteLLM", "OpenAI", "Claude", "Llama 3"] },
  { cat: "前端", items: ["Next.js 14", "shadcn/ui", "Zustand", "Recharts"] },
  { cat: "基础设施", items: ["Docker", "Kubernetes", "GitHub Actions", "Grafana"] },
];

export default function TitanArchitecture() {
  const [activeLayer, setActiveLayer] = useState(null);
  const [activeItem, setActiveItem] = useState(null);
  const [activeTab, setActiveTab] = useState("arch");

  const selectedItem = layers
    .flatMap((l) => l.items.map((i) => ({ ...i, layerColor: l.color })))
    .find((i) => i.id === activeItem);

  return (
    <div style={{
      minHeight: "100vh",
      background: "#080c14",
      color: "#e2e8f0",
      fontFamily: "'DM Mono', 'Fira Code', monospace",
      padding: "0",
    }}>
      {/* Header */}
      <div style={{
        borderBottom: "1px solid rgba(255,255,255,0.06)",
        padding: "24px 40px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        background: "rgba(255,255,255,0.02)",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <div style={{
            width: 36, height: 36, borderRadius: 8,
            background: "linear-gradient(135deg, #c084fc, #60a5fa)",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 18,
          }}>⚡</div>
          <div>
            <div style={{ fontSize: 18, fontWeight: 700, letterSpacing: "0.08em", color: "#f8fafc" }}>
              TITAN EVOLUTION OS
            </div>
            <div style={{ fontSize: 11, color: "#64748b", letterSpacing: "0.15em", marginTop: 2 }}>
              自进化数字员工操作系统 · 系统架构图 v1.0
            </div>
          </div>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          {["arch", "roadmap", "tech"].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              style={{
                padding: "6px 16px",
                borderRadius: 6,
                border: "1px solid",
                borderColor: activeTab === tab ? "rgba(192,132,252,0.5)" : "rgba(255,255,255,0.08)",
                background: activeTab === tab ? "rgba(192,132,252,0.12)" : "transparent",
                color: activeTab === tab ? "#c084fc" : "#64748b",
                fontSize: 12,
                cursor: "pointer",
                letterSpacing: "0.08em",
                transition: "all 0.2s",
              }}
            >
              {tab === "arch" ? "架构图" : tab === "roadmap" ? "路线图" : "技术栈"}
            </button>
          ))}
        </div>
      </div>

      <div style={{ padding: "32px 40px", maxWidth: 1200, margin: "0 auto" }}>

        {/* Architecture Tab */}
        {activeTab === "arch" && (
          <div style={{ display: "grid", gridTemplateColumns: activeItem ? "1fr 320px" : "1fr", gap: 24 }}>
            <div>
              {/* Score formula banner */}
              <div style={{
                background: "rgba(245,158,11,0.06)",
                border: "1px solid rgba(245,158,11,0.2)",
                borderRadius: 10,
                padding: "12px 20px",
                marginBottom: 24,
                display: "flex",
                alignItems: "center",
                gap: 12,
              }}>
                <span style={{ fontSize: 13, color: "#f59e0b", letterSpacing: "0.05em" }}>⚡ 进化评分公式：</span>
                <code style={{ fontSize: 13, color: "#fbbf24", background: "rgba(0,0,0,0.3)", padding: "4px 12px", borderRadius: 6 }}>
                  Score = 0.5 × 成功率 + 0.3 × 质量分 − 0.2 × Token消耗(归一化)
                </code>
              </div>

              {/* Layers */}
              {layers.map((layer) => (
                <div
                  key={layer.id}
                  onClick={() => setActiveLayer(activeLayer === layer.id ? null : layer.id)}
                  style={{
                    border: "1px solid",
                    borderColor: activeLayer === layer.id ? layer.border : "rgba(255,255,255,0.06)",
                    borderRadius: 12,
                    marginBottom: 12,
                    background: activeLayer === layer.id ? layer.bg : "rgba(255,255,255,0.02)",
                    transition: "all 0.25s",
                    cursor: "pointer",
                    overflow: "hidden",
                  }}
                >
                  {/* Layer Header */}
                  <div style={{
                    padding: "14px 20px",
                    display: "flex",
                    alignItems: "center",
                    gap: 12,
                    borderBottom: activeLayer === layer.id ? `1px solid ${layer.border}` : "1px solid transparent",
                  }}>
                    <span style={{
                      fontSize: 10, fontWeight: 700, letterSpacing: "0.15em",
                      color: layer.color, background: `${layer.color}18`,
                      padding: "3px 8px", borderRadius: 4,
                      border: `1px solid ${layer.color}40`,
                    }}>{layer.label}</span>
                    <div>
                      <span style={{ fontSize: 15, fontWeight: 600, color: "#f1f5f9" }}>{layer.title}</span>
                      <span style={{ fontSize: 12, color: "#64748b", marginLeft: 10 }}>{layer.subtitle}</span>
                    </div>
                    <span style={{ marginLeft: "auto", color: "#64748b", fontSize: 16, transition: "transform 0.2s", transform: activeLayer === layer.id ? "rotate(90deg)" : "none" }}>›</span>
                  </div>

                  {/* Layer Items */}
                  {activeLayer === layer.id && (
                    <div style={{ padding: "16px 20px", display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 10 }}>
                      {layer.items.map((item) => (
                        <div
                          key={item.id}
                          onClick={(e) => { e.stopPropagation(); setActiveItem(activeItem === item.id ? null : item.id); }}
                          style={{
                            padding: "12px 14px",
                            borderRadius: 8,
                            border: "1px solid",
                            borderColor: activeItem === item.id ? layer.color + "80" : "rgba(255,255,255,0.07)",
                            background: activeItem === item.id ? `${layer.color}12` : "rgba(0,0,0,0.2)",
                            cursor: "pointer",
                            transition: "all 0.2s",
                          }}
                        >
                          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                            <span style={{ fontSize: 16 }}>{item.icon}</span>
                            <span style={{ fontSize: 13, color: "#e2e8f0", fontWeight: 500 }}>{item.label}</span>
                          </div>
                          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                            <div style={{
                              width: 6, height: 6, borderRadius: "50%",
                              background: statusConfig[item.status].dot,
                              boxShadow: `0 0 6px ${statusConfig[item.status].dot}`,
                            }} />
                            <span style={{ fontSize: 10, color: statusConfig[item.status].color, letterSpacing: "0.1em" }}>
                              {statusConfig[item.status].label}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}

              {/* Data flow arrows */}
              <div style={{
                marginTop: 20,
                padding: "16px 20px",
                background: "rgba(255,255,255,0.02)",
                border: "1px solid rgba(255,255,255,0.05)",
                borderRadius: 10,
              }}>
                <div style={{ fontSize: 11, color: "#475569", letterSpacing: "0.12em", marginBottom: 12 }}>数据流向</div>
                <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                  {[
                    { from: "执行层", arrow: "→", to: "记忆层", note: "任务结果写入" },
                    { from: "记忆层", arrow: "→", to: "执行层", note: "经验注入Prompt" },
                    { from: "执行层", arrow: "→", to: "进化层", note: "绩效日志上报" },
                    { from: "进化层", arrow: "→", to: "执行层", note: "新Prompt下发" },
                    { from: "行业插件", arrow: "→", to: "所有层", note: "行业配置覆盖" },
                  ].map((flow, i) => (
                    <div key={i} style={{
                      display: "flex", alignItems: "center", gap: 6,
                      padding: "6px 12px",
                      background: "rgba(0,0,0,0.3)",
                      borderRadius: 6,
                      border: "1px solid rgba(255,255,255,0.05)",
                    }}>
                      <span style={{ fontSize: 12, color: "#94a3b8" }}>{flow.from}</span>
                      <span style={{ fontSize: 12, color: "#475569" }}>{flow.arrow}</span>
                      <span style={{ fontSize: 12, color: "#94a3b8" }}>{flow.to}</span>
                      <span style={{ fontSize: 11, color: "#475569", marginLeft: 4 }}>({flow.note})</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Detail Panel */}
            {activeItem && selectedItem && (
              <div style={{
                background: "rgba(255,255,255,0.02)",
                border: `1px solid ${selectedItem.layerColor}40`,
                borderRadius: 12,
                padding: 24,
                height: "fit-content",
                position: "sticky",
                top: 20,
              }}>
                <div style={{ fontSize: 28, marginBottom: 12 }}>{selectedItem.icon}</div>
                <div style={{ fontSize: 16, fontWeight: 600, color: "#f1f5f9", marginBottom: 8 }}>
                  {selectedItem.label}
                </div>
                <div style={{
                  display: "inline-flex", alignItems: "center", gap: 6,
                  padding: "3px 10px", borderRadius: 20,
                  background: `${statusConfig[selectedItem.status].dot}18`,
                  border: `1px solid ${statusConfig[selectedItem.status].dot}40`,
                  marginBottom: 16,
                }}>
                  <div style={{ width: 6, height: 6, borderRadius: "50%", background: statusConfig[selectedItem.status].dot }} />
                  <span style={{ fontSize: 11, color: statusConfig[selectedItem.status].color }}>
                    {statusConfig[selectedItem.status].label}
                  </span>
                </div>
                <p style={{ fontSize: 13, color: "#94a3b8", lineHeight: 1.7 }}>
                  {selectedItem.desc}
                </p>
                <button
                  onClick={() => setActiveItem(null)}
                  style={{
                    marginTop: 20, width: "100%",
                    padding: "8px", borderRadius: 6,
                    border: "1px solid rgba(255,255,255,0.08)",
                    background: "transparent", color: "#64748b",
                    fontSize: 12, cursor: "pointer",
                  }}
                >关闭</button>
              </div>
            )}
          </div>
        )}

        {/* Roadmap Tab */}
        {activeTab === "roadmap" && (
          <div>
            <div style={{ fontSize: 13, color: "#64748b", marginBottom: 24, letterSpacing: "0.05em" }}>
              总计 16 周 · 5 个阶段 · 从 MVP 到商业化
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 16 }}>
              {phaseData.map((phase, i) => (
                <div key={i} style={{
                  padding: 24,
                  borderRadius: 12,
                  border: "1px solid rgba(255,255,255,0.07)",
                  background: "rgba(255,255,255,0.02)",
                  position: "relative",
                  overflow: "hidden",
                }}>
                  <div style={{
                    position: "absolute", top: 0, left: 0, right: 0, height: 3,
                    background: phase.color,
                    borderRadius: "12px 12px 0 0",
                  }} />
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 12 }}>
                    <div>
                      <div style={{ fontSize: 11, color: phase.color, letterSpacing: "0.15em", marginBottom: 4 }}>{phase.phase}</div>
                      <div style={{ fontSize: 16, fontWeight: 600, color: "#f1f5f9" }}>{phase.title}</div>
                    </div>
                    <span style={{
                      fontSize: 11, color: "#475569",
                      background: "rgba(0,0,0,0.3)",
                      padding: "3px 8px", borderRadius: 4,
                      border: "1px solid rgba(255,255,255,0.05)",
                    }}>{phase.weeks}</span>
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                    {phase.items.map((item, j) => (
                      <div key={j} style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        <div style={{
                          width: 5, height: 5, borderRadius: "50%",
                          background: phase.color, flexShrink: 0,
                        }} />
                        <span style={{ fontSize: 13, color: "#94a3b8" }}>{item}</span>
                      </div>
                    ))}
                  </div>
                  <div style={{
                    marginTop: 16, paddingTop: 16,
                    borderTop: "1px solid rgba(255,255,255,0.05)",
                    fontSize: 11, color: "#475569",
                  }}>
                    {i === 0 && "验收：能创建Agent并调用LLM记录日志"}
                    {i === 1 && "验收：端到端跑通一条完整获客流"}
                    {i === 2 && "验收：第二次任务检索到历史经验"}
                    {i === 3 && "验收：完成第一次完整进化循环"}
                    {i === 4 && "验收：两个行业插件并存隔离运行"}
                    {i === 5 && "验收：付费客户可正式使用"}
                  </div>
                </div>
              ))}
            </div>

            {/* Cold start warning */}
            <div style={{
              marginTop: 24,
              padding: "16px 20px",
              background: "rgba(245,158,11,0.06)",
              border: "1px solid rgba(245,158,11,0.2)",
              borderRadius: 10,
            }}>
              <div style={{ fontSize: 13, color: "#f59e0b", marginBottom: 8, fontWeight: 600 }}>⚠️ 冷启动三阶段（关键风险管控）</div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16 }}>
                {[
                  { phase: "阶段一", cond: "前100个任务", mode: "人工驾驶模式", desc: "关闭自动进化，手动配置Prompt，专注跑通执行层，积累训练数据" },
                  { phase: "阶段二", cond: "100-500个任务", mode: "半自动模式", desc: "开启评分系统，进化层只生成建议，每次变更需人工确认" },
                  { phase: "阶段三", cond: "500+个任务", mode: "全自动模式", desc: "开放自动进化，设置分数护栏和最大进化频率，重大变更推送通知" },
                ].map((s, i) => (
                  <div key={i} style={{ padding: "12px 16px", background: "rgba(0,0,0,0.3)", borderRadius: 8 }}>
                    <div style={{ fontSize: 12, color: "#f59e0b", marginBottom: 4 }}>{s.phase} · {s.cond}</div>
                    <div style={{ fontSize: 13, color: "#e2e8f0", marginBottom: 6, fontWeight: 500 }}>{s.mode}</div>
                    <div style={{ fontSize: 12, color: "#64748b", lineHeight: 1.6 }}>{s.desc}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Tech Stack Tab */}
        {activeTab === "tech" && (
          <div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))", gap: 16, marginBottom: 24 }}>
              {techStack.map((cat, i) => (
                <div key={i} style={{
                  padding: 20,
                  borderRadius: 12,
                  border: "1px solid rgba(255,255,255,0.07)",
                  background: "rgba(255,255,255,0.02)",
                }}>
                  <div style={{ fontSize: 11, color: "#64748b", letterSpacing: "0.15em", marginBottom: 14 }}>{cat.cat}</div>
                  {cat.items.map((item, j) => (
                    <div key={j} style={{
                      padding: "8px 12px", marginBottom: 6,
                      background: "rgba(0,0,0,0.3)",
                      borderRadius: 6,
                      border: "1px solid rgba(255,255,255,0.05)",
                      fontSize: 13, color: "#94a3b8",
                    }}>{item}</div>
                  ))}
                </div>
              ))}
            </div>

            {/* Industry extension cost */}
            <div style={{
              padding: "20px 24px",
              background: "rgba(192,132,252,0.06)",
              border: "1px solid rgba(192,132,252,0.2)",
              borderRadius: 12,
            }}>
              <div style={{ fontSize: 14, color: "#c084fc", marginBottom: 16, fontWeight: 600 }}>🔌 新行业接入成本估算</div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
                <div>
                  <div style={{ fontSize: 12, color: "#64748b", marginBottom: 10 }}>✅ 复用核心（无需改动）</div>
                  {["进化引擎 (~0天)", "记忆系统 (~0天)", "数据库表结构 (~0天)", "前端核心页面 (~0天)"].map((i, j) => (
                    <div key={j} style={{ fontSize: 13, color: "#34d399", marginBottom: 6, display: "flex", alignItems: "center", gap: 8 }}>
                      <span style={{ fontSize: 10 }}>▸</span>{i}
                    </div>
                  ))}
                </div>
                <div>
                  <div style={{ fontSize: 12, color: "#64748b", marginBottom: 10 }}>⚙️ 需新开发</div>
                  {["Plugin实现类 (2-3天)", "行业Agent Prompt (2-3天)", "新API工具集成 (3-5天/个)", "行业UI组件 (1-2天)", "预置技能文档 (2-3天)"].map((i, j) => (
                    <div key={j} style={{ fontSize: 13, color: "#f59e0b", marginBottom: 6, display: "flex", alignItems: "center", gap: 8 }}>
                      <span style={{ fontSize: 10 }}>▸</span>{i}
                    </div>
                  ))}
                  <div style={{ marginTop: 12, padding: "8px 12px", background: "rgba(0,0,0,0.3)", borderRadius: 6, fontSize: 12, color: "#c084fc" }}>
                    总计：新行业接入 ≈ 2-3周<br />
                    vs 从零开发 ≈ 2-3个月
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
