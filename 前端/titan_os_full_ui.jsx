import { useState, useEffect, useRef } from "react";

// ─── Design tokens ────────────────────────────────────────────────
const C = {
  bg: "#07090f",
  surface: "#0d1017",
  surfaceHigh: "#13171f",
  border: "rgba(255,255,255,0.06)",
  borderHover: "rgba(255,255,255,0.12)",
  text: "#e8eaf0",
  textMid: "#8892a4",
  textDim: "#3d4557",
  accent: "#5b6ef5",
  accentGlow: "rgba(91,110,245,0.2)",
  green: "#2dd4a0",
  greenDim: "rgba(45,212,160,0.15)",
  amber: "#f5a524",
  amberDim: "rgba(245,165,36,0.15)",
  red: "#f25f5c",
  redDim: "rgba(242,95,92,0.15)",
  purple: "#a78bfa",
  purpleDim: "rgba(167,139,250,0.15)",
};

// ─── Shared micro-components ──────────────────────────────────────
const Badge = ({ color = C.green, bg, children, dot }) => (
  <span style={{
    display: "inline-flex", alignItems: "center", gap: 5,
    padding: "3px 9px", borderRadius: 20,
    background: bg || `${color}18`,
    border: `1px solid ${color}35`,
    fontSize: 11, color, fontWeight: 500, letterSpacing: "0.04em",
  }}>
    {dot && <span style={{ width: 5, height: 5, borderRadius: "50%", background: color, boxShadow: `0 0 6px ${color}` }} />}
    {children}
  </span>
);

const Card = ({ children, style = {}, glow }) => (
  <div style={{
    background: C.surface,
    border: `1px solid ${C.border}`,
    borderRadius: 14,
    padding: 24,
    ...(glow ? { boxShadow: `0 0 40px ${glow}` } : {}),
    ...style,
  }}>{children}</div>
);

const Btn = ({ children, onClick, variant = "primary", size = "md", style = {} }) => {
  const [hov, setHov] = useState(false);
  const base = {
    display: "inline-flex", alignItems: "center", gap: 7,
    borderRadius: 9, cursor: "pointer", fontWeight: 600,
    border: "none", transition: "all 0.18s", letterSpacing: "0.02em",
    padding: size === "sm" ? "7px 14px" : size === "lg" ? "13px 26px" : "10px 20px",
    fontSize: size === "sm" ? 12 : size === "lg" ? 15 : 13,
  };
  const variants = {
    primary: { background: hov ? "#6b7ef7" : C.accent, color: "#fff", boxShadow: hov ? `0 4px 20px ${C.accentGlow}` : "none" },
    ghost: { background: hov ? "rgba(255,255,255,0.05)" : "transparent", color: C.textMid, border: `1px solid ${C.border}` },
    danger: { background: hov ? "#e04744" : C.red, color: "#fff" },
    success: { background: hov ? "#25c090" : C.green, color: "#07150e" },
  };
  return <button onClick={onClick} onMouseEnter={() => setHov(true)} onMouseLeave={() => setHov(false)}
    style={{ ...base, ...variants[variant], ...style }}>{children}</button>;
};

const Input = ({ label, placeholder, value, onChange, type = "text", icon }) => (
  <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
    {label && <label style={{ fontSize: 12, color: C.textMid, letterSpacing: "0.06em", fontWeight: 500 }}>{label}</label>}
    <div style={{ position: "relative" }}>
      {icon && <span style={{ position: "absolute", left: 12, top: "50%", transform: "translateY(-50%)", fontSize: 14, color: C.textDim }}>{icon}</span>}
      <input type={type} placeholder={placeholder} value={value} onChange={e => onChange?.(e.target.value)}
        style={{
          width: "100%", padding: icon ? "11px 14px 11px 36px" : "11px 14px",
          background: C.surfaceHigh, border: `1px solid ${C.border}`,
          borderRadius: 9, color: C.text, fontSize: 14, outline: "none",
          boxSizing: "border-box",
          transition: "border-color 0.2s",
        }}
        onFocus={e => e.target.style.borderColor = C.accent}
        onBlur={e => e.target.style.borderColor = C.border}
      />
    </div>
  </div>
);

const StatCard = ({ label, value, sub, color = C.accent, icon }) => (
  <Card style={{ padding: "20px 24px" }}>
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
      <div>
        <div style={{ fontSize: 11, color: C.textMid, letterSpacing: "0.1em", marginBottom: 8, textTransform: "uppercase" }}>{label}</div>
        <div style={{ fontSize: 32, fontWeight: 700, color, fontVariantNumeric: "tabular-nums" }}>{value}</div>
        {sub && <div style={{ fontSize: 12, color: C.textDim, marginTop: 4 }}>{sub}</div>}
      </div>
      {icon && <div style={{ fontSize: 24, opacity: 0.6 }}>{icon}</div>}
    </div>
  </Card>
);

// ─── Sidebar ──────────────────────────────────────────────────────
const NAV = [
  { id: "dashboard", label: "Dashboard", icon: "⬡" },
  { id: "agents", label: "Digital Team", icon: "◈" },
  { id: "tasks", label: "Task Center", icon: "⊞" },
  { id: "evolution", label: "Evolution", icon: "◎" },
  { id: "skills", label: "Skills Library", icon: "⟐" },
  { id: "billing", label: "Billing", icon: "◇" },
  { id: "settings", label: "Settings", icon: "⊛" },
];

function Sidebar({ active, onNav }) {
  return (
    <div style={{
      width: 220, flexShrink: 0,
      background: C.surface,
      borderRight: `1px solid ${C.border}`,
      display: "flex", flexDirection: "column",
      height: "100vh", position: "sticky", top: 0,
    }}>
      {/* Logo */}
      <div style={{ padding: "24px 20px 20px", borderBottom: `1px solid ${C.border}` }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{
            width: 32, height: 32, borderRadius: 8,
            background: `linear-gradient(135deg, ${C.accent}, ${C.purple})`,
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 16, flexShrink: 0,
          }}>⚡</div>
          <div>
            <div style={{ fontSize: 13, fontWeight: 700, color: C.text, letterSpacing: "0.06em" }}>TITAN</div>
            <div style={{ fontSize: 10, color: C.textDim, letterSpacing: "0.12em" }}>EVOLUTION OS</div>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav style={{ flex: 1, padding: "12px 10px", display: "flex", flexDirection: "column", gap: 2 }}>
        {NAV.map(n => {
          const isActive = active === n.id;
          return (
            <button key={n.id} onClick={() => onNav(n.id)} style={{
              display: "flex", alignItems: "center", gap: 10,
              padding: "9px 12px", borderRadius: 8, border: "none", cursor: "pointer",
              background: isActive ? `${C.accent}18` : "transparent",
              color: isActive ? C.accent : C.textMid,
              fontSize: 13, fontWeight: isActive ? 600 : 400,
              textAlign: "left", transition: "all 0.15s",
              borderLeft: isActive ? `2px solid ${C.accent}` : "2px solid transparent",
            }}>
              <span style={{ fontSize: 15, width: 18, textAlign: "center" }}>{n.icon}</span>
              {n.label}
            </button>
          );
        })}
      </nav>

      {/* User */}
      <div style={{ padding: 16, borderTop: `1px solid ${C.border}` }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{
            width: 32, height: 32, borderRadius: "50%",
            background: `linear-gradient(135deg, ${C.accent}, ${C.purple})`,
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 13, color: "#fff", fontWeight: 700, flexShrink: 0,
          }}>A</div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 13, color: C.text, fontWeight: 500, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>Alex Chen</div>
            <div style={{ fontSize: 11, color: C.textDim }}>Starter plan</div>
          </div>
          <Badge color={C.green}>✓</Badge>
        </div>
      </div>
    </div>
  );
}

// ─── LOGIN PAGE ───────────────────────────────────────────────────
function LoginPage({ onLogin }) {
  const [tab, setTab] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);

  function handleSubmit() {
    setLoading(true);
    setTimeout(() => { setLoading(false); onLogin(); }, 1200);
  }

  return (
    <div style={{
      minHeight: "100vh", background: C.bg,
      display: "flex", alignItems: "center", justifyContent: "center",
      position: "relative", overflow: "hidden",
    }}>
      {/* bg glow */}
      <div style={{ position: "absolute", width: 600, height: 600, borderRadius: "50%", background: `radial-gradient(circle, ${C.accentGlow} 0%, transparent 70%)`, top: "50%", left: "50%", transform: "translate(-50%,-50%)", pointerEvents: "none" }} />

      <div style={{ width: 420, position: "relative", zIndex: 1 }}>
        {/* Logo */}
        <div style={{ textAlign: "center", marginBottom: 40 }}>
          <div style={{
            width: 52, height: 52, borderRadius: 14,
            background: `linear-gradient(135deg, ${C.accent}, ${C.purple})`,
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 26, margin: "0 auto 16px",
            boxShadow: `0 8px 32px ${C.accentGlow}`,
          }}>⚡</div>
          <div style={{ fontSize: 22, fontWeight: 700, color: C.text, letterSpacing: "0.05em" }}>Titan Evolution OS</div>
          <div style={{ fontSize: 13, color: C.textMid, marginTop: 6 }}>自进化数字员工操作系统</div>
        </div>

        <Card style={{ padding: 32 }}>
          {/* Tabs */}
          <div style={{ display: "flex", gap: 0, marginBottom: 28, background: C.surfaceHigh, borderRadius: 9, padding: 3 }}>
            {["login", "register"].map(t => (
              <button key={t} onClick={() => setTab(t)} style={{
                flex: 1, padding: "8px", borderRadius: 7, border: "none", cursor: "pointer",
                background: tab === t ? C.surface : "transparent",
                color: tab === t ? C.text : C.textMid,
                fontSize: 13, fontWeight: tab === t ? 600 : 400,
                boxShadow: tab === t ? `0 1px 4px rgba(0,0,0,0.4)` : "none",
                transition: "all 0.18s",
              }}>{t === "login" ? "登录" : "注册"}</button>
            ))}
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            {tab === "register" && <Input label="姓名" placeholder="你的名字" value={name} onChange={setName} icon="👤" />}
            <Input label="邮箱" placeholder="you@company.com" value={email} onChange={setEmail} type="email" icon="✉" />
            <Input label="密码" placeholder="••••••••" value={password} onChange={setPassword} type="password" icon="🔒" />

            {tab === "login" && (
              <div style={{ textAlign: "right" }}>
                <span style={{ fontSize: 12, color: C.accent, cursor: "pointer" }}>忘记密码？</span>
              </div>
            )}

            <Btn onClick={handleSubmit} size="lg" style={{ width: "100%", justifyContent: "center", marginTop: 4 }}>
              {loading ? "验证中..." : tab === "login" ? "登录" : "创建账号"}
            </Btn>

            <div style={{ display: "flex", alignItems: "center", gap: 12, margin: "4px 0" }}>
              <div style={{ flex: 1, height: 1, background: C.border }} />
              <span style={{ fontSize: 12, color: C.textDim }}>或者</span>
              <div style={{ flex: 1, height: 1, background: C.border }} />
            </div>

            <button onClick={handleSubmit} style={{
              width: "100%", padding: "11px", borderRadius: 9,
              border: `1px solid ${C.border}`,
              background: C.surfaceHigh, color: C.text,
              fontSize: 13, cursor: "pointer", display: "flex",
              alignItems: "center", justifyContent: "center", gap: 10,
              fontWeight: 500,
            }}>
              <span>G</span> 使用 Google 账号{tab === "login" ? "登录" : "注册"}
            </button>
          </div>
        </Card>
        <p style={{ textAlign: "center", marginTop: 20, fontSize: 12, color: C.textDim }}>
          登录即表示你同意我们的服务条款和隐私政策
        </p>
      </div>
    </div>
  );
}

// ─── ONBOARDING ───────────────────────────────────────────────────
function OnboardingPage({ onDone }) {
  const [step, setStep] = useState(0);
  const [industry, setIndustry] = useState(null);
  const [goal, setGoal] = useState("");
  const [provisioning, setProvisioning] = useState(false);

  const industries = [
    { id: "payment_fintech", icon: "💳", label: "Payment & Fintech", desc: "支付、金融科技获客与增长" },
    { id: "saas_b2b", icon: "🚀", label: "SaaS B2B", desc: "SaaS产品增长与用户转化" },
    { id: "ecommerce", icon: "🛒", label: "电商运营", desc: "跨境电商选品与运营" },
    { id: "custom", icon: "🔧", label: "自定义", desc: "我有特定的使用场景" },
  ];

  function handleFinish() {
    setProvisioning(true);
    setTimeout(() => { setProvisioning(false); onDone(); }, 2000);
  }

  const steps = ["选择行业", "设定目标", "初始化团队"];

  return (
    <div style={{ minHeight: "100vh", background: C.bg, display: "flex", alignItems: "center", justifyContent: "center" }}>
      <div style={{ width: 560, position: "relative" }}>
        {/* Progress */}
        <div style={{ display: "flex", gap: 8, marginBottom: 40, justifyContent: "center" }}>
          {steps.map((s, i) => (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <div style={{
                width: 28, height: 28, borderRadius: "50%",
                background: i < step ? C.green : i === step ? C.accent : C.surfaceHigh,
                border: `2px solid ${i < step ? C.green : i === step ? C.accent : C.border}`,
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: 12, fontWeight: 700,
                color: i <= step ? "#fff" : C.textDim,
                transition: "all 0.3s",
              }}>{i < step ? "✓" : i + 1}</div>
              <span style={{ fontSize: 12, color: i === step ? C.text : C.textDim }}>{s}</span>
              {i < steps.length - 1 && <div style={{ width: 32, height: 1, background: i < step ? C.green : C.border, transition: "all 0.3s" }} />}
            </div>
          ))}
        </div>

        <Card style={{ padding: 40 }}>
          {step === 0 && (
            <div>
              <h2 style={{ fontSize: 22, fontWeight: 700, color: C.text, marginBottom: 8 }}>你主要做哪个方向？</h2>
              <p style={{ fontSize: 14, color: C.textMid, marginBottom: 28 }}>我们会自动配置最适合的 Agent 团队和技能库</p>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                {industries.map(ind => (
                  <div key={ind.id} onClick={() => setIndustry(ind.id)} style={{
                    padding: 20, borderRadius: 12, cursor: "pointer",
                    border: `2px solid ${industry === ind.id ? C.accent : C.border}`,
                    background: industry === ind.id ? `${C.accent}10` : C.surfaceHigh,
                    transition: "all 0.2s",
                  }}>
                    <div style={{ fontSize: 24, marginBottom: 8 }}>{ind.icon}</div>
                    <div style={{ fontSize: 14, fontWeight: 600, color: C.text, marginBottom: 4 }}>{ind.label}</div>
                    <div style={{ fontSize: 12, color: C.textMid }}>{ind.desc}</div>
                  </div>
                ))}
              </div>
              <Btn onClick={() => industry && setStep(1)} style={{ marginTop: 28, width: "100%", justifyContent: "center" }} size="lg">
                下一步 →
              </Btn>
            </div>
          )}

          {step === 1 && (
            <div>
              <h2 style={{ fontSize: 22, fontWeight: 700, color: C.text, marginBottom: 8 }}>你的第一个目标是什么？</h2>
              <p style={{ fontSize: 14, color: C.textMid, marginBottom: 28 }}>越具体越好，Agent 会据此制定行动计划</p>
              <div style={{ display: "flex", flexDirection: "column", gap: 10, marginBottom: 24 }}>
                {["找到50家 MENA 地区的支付公司并获得联系方式", "研究东南亚数字支付市场机会报告", "为我们的产品撰写并发送20封个性化开发信"].map(s => (
                  <div key={s} onClick={() => setGoal(s)} style={{
                    padding: "14px 16px", borderRadius: 9, cursor: "pointer",
                    border: `1px solid ${goal === s ? C.accent : C.border}`,
                    background: goal === s ? `${C.accent}10` : C.surfaceHigh,
                    fontSize: 13, color: goal === s ? C.text : C.textMid,
                    transition: "all 0.2s",
                  }}>{s}</div>
                ))}
              </div>
              <Input placeholder="或者输入你自己的目标..." value={goal} onChange={setGoal} />
              <div style={{ display: "flex", gap: 12, marginTop: 24 }}>
                <Btn onClick={() => setStep(0)} variant="ghost" style={{ flex: 1, justifyContent: "center" }}>← 返回</Btn>
                <Btn onClick={() => goal && setStep(2)} style={{ flex: 2, justifyContent: "center" }} size="lg">初始化团队 →</Btn>
              </div>
            </div>
          )}

          {step === 2 && (
            <div style={{ textAlign: "center" }}>
              {!provisioning ? (
                <>
                  <div style={{ fontSize: 40, marginBottom: 16 }}>🤖</div>
                  <h2 style={{ fontSize: 22, fontWeight: 700, color: C.text, marginBottom: 8 }}>准备好了！</h2>
                  <p style={{ fontSize: 14, color: C.textMid, marginBottom: 32 }}>
                    我们将为你自动创建 4 个 Agent 并配置好技能库，整个过程只需几秒
                  </p>
                  <div style={{ display: "flex", flexDirection: "column", gap: 10, marginBottom: 32, textAlign: "left" }}>
                    {[
                      { icon: "🎯", name: "Growth Hunter", desc: "负责搜索目标公司和联系人" },
                      { icon: "🔬", name: "Researcher", desc: "负责行业研究和竞品分析" },
                      { icon: "✉️", name: "Outreach Agent", desc: "负责撰写和发送个性化邮件" },
                      { icon: "📦", name: "Delivery Agent", desc: "负责整理交付物和生成报告" },
                    ].map(a => (
                      <div key={a.name} style={{ display: "flex", alignItems: "center", gap: 14, padding: "12px 16px", background: C.surfaceHigh, borderRadius: 9, border: `1px solid ${C.border}` }}>
                        <span style={{ fontSize: 20 }}>{a.icon}</span>
                        <div>
                          <div style={{ fontSize: 13, fontWeight: 600, color: C.text }}>{a.name}</div>
                          <div style={{ fontSize: 12, color: C.textMid }}>{a.desc}</div>
                        </div>
                        <Badge color={C.green} style={{ marginLeft: "auto" }}>自动配置</Badge>
                      </div>
                    ))}
                  </div>
                  <Btn onClick={handleFinish} size="lg" variant="success" style={{ width: "100%", justifyContent: "center" }}>
                    ⚡ 启动我的团队
                  </Btn>
                </>
              ) : (
                <div>
                  <div style={{ fontSize: 40, marginBottom: 20 }}>⚙️</div>
                  <h2 style={{ fontSize: 20, fontWeight: 700, color: C.text, marginBottom: 16 }}>正在初始化...</h2>
                  {["创建 Demo Workspace ✓", "配置 Payment & Fintech 插件 ✓", "初始化 4 个 Agent...", "注入行业技能文档..."].map((s, i) => (
                    <div key={i} style={{ fontSize: 13, color: i < 2 ? C.green : C.textMid, marginBottom: 8 }}>{s}</div>
                  ))}
                </div>
              )}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}

// ─── DASHBOARD ────────────────────────────────────────────────────
const LOG_ITEMS = [
  { time: "10:34", icon: "✅", msg: "Hunter-1 找到 Paymob (Cairo, EG) — 联系人: Ahmed K.", color: C.green },
  { time: "10:34", icon: "✅", msg: "Hunter-1 找到 Fawry (Cairo, EG) — 联系人: Sara M.", color: C.green },
  { time: "10:33", icon: "⚡", msg: "记忆层检索：注入3条相似历史经验到 Hunter-1", color: C.accent },
  { time: "10:32", icon: "✉️", msg: "Outreach 发送邮件给 Ahmed K. — 主题: Expansion to MENA", color: C.purple },
  { time: "10:31", icon: "🔄", msg: "Evolution Manager 评分触发：Hunter-1 score=0.78 ✓", color: C.amber },
  { time: "10:28", icon: "✅", msg: "Researcher 完成市场报告：Saudi Arabia Fintech 2024", color: C.green },
];

function DashboardPage() {
  const [logIdx, setLogIdx] = useState(3);
  useEffect(() => {
    const t = setInterval(() => setLogIdx(i => (i + 1) % LOG_ITEMS.length), 3000);
    return () => clearInterval(t);
  }, []);

  const agents = [
    { name: "Hunter-1", role: "Growth Hunter", score: 0.82, status: "running", tasks: 47, icon: "🎯" },
    { name: "Researcher", role: "Market Intel", score: 0.75, status: "idle", tasks: 23, icon: "🔬" },
    { name: "Outreach-1", role: "Outreach", score: 0.68, status: "running", tasks: 61, icon: "✉️" },
    { name: "Delivery", role: "Delivery", score: 0.91, status: "idle", tasks: 18, icon: "📦" },
  ];

  return (
    <div>
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, color: C.text, marginBottom: 4 }}>今日概览</h1>
        <p style={{ fontSize: 14, color: C.textMid }}>你的数字团队正在运行中 — 周四, 5月14日</p>
      </div>

      {/* Stats row */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16, marginBottom: 24 }}>
        <StatCard label="今日任务" value="47" sub="+12 较昨日" color={C.accent} icon="⊞" />
        <StatCard label="成功率" value="78%" sub="目标 ≥ 75%" color={C.green} icon="◎" />
        <StatCard label="节省时间" value="12h" sub="本周累计 68h" color={C.purple} icon="⏱" />
        <StatCard label="进化次数" value="3" sub="上次 2h 前" color={C.amber} icon="🧬" />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 340px", gap: 20 }}>
        {/* Live log */}
        <Card>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 18 }}>
            <h3 style={{ fontSize: 15, fontWeight: 600, color: C.text }}>实时任务流</h3>
            <Badge color={C.green} dot>运行中</Badge>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
            {LOG_ITEMS.map((item, i) => (
              <div key={i} style={{
                display: "flex", gap: 12, padding: "10px 0",
                borderBottom: `1px solid ${C.border}`,
                opacity: i > logIdx ? 0.3 : 1,
                transition: "opacity 0.5s",
              }}>
                <span style={{ fontSize: 11, color: C.textDim, flexShrink: 0, marginTop: 1, fontVariantNumeric: "tabular-nums" }}>{item.time}</span>
                <span style={{ fontSize: 14, flexShrink: 0 }}>{item.icon}</span>
                <span style={{ fontSize: 13, color: i === logIdx ? item.color : C.textMid, lineHeight: 1.5 }}>{item.msg}</span>
              </div>
            ))}
          </div>
        </Card>

        {/* Agent status */}
        <Card>
          <h3 style={{ fontSize: 15, fontWeight: 600, color: C.text, marginBottom: 18 }}>Agent 状态</h3>
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {agents.map(a => (
              <div key={a.name} style={{
                padding: "12px 14px", borderRadius: 10,
                background: C.surfaceHigh, border: `1px solid ${C.border}`,
              }}>
                <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
                  <span style={{ fontSize: 18 }}>{a.icon}</span>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 13, fontWeight: 600, color: C.text }}>{a.name}</div>
                    <div style={{ fontSize: 11, color: C.textDim }}>{a.role}</div>
                  </div>
                  <Badge color={a.status === "running" ? C.green : C.textDim} dot>
                    {a.status === "running" ? "运行中" : "空闲"}
                  </Badge>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div style={{ flex: 1, height: 4, background: C.border, borderRadius: 2, overflow: "hidden" }}>
                    <div style={{ width: `${a.score * 100}%`, height: "100%", background: a.score > 0.75 ? C.green : a.score > 0.6 ? C.amber : C.red, borderRadius: 2 }} />
                  </div>
                  <span style={{ fontSize: 11, color: C.textMid, marginLeft: 10, fontVariantNumeric: "tabular-nums" }}>
                    {(a.score * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
          <Btn style={{ width: "100%", justifyContent: "center", marginTop: 14 }} variant="ghost" size="sm">
            管理团队 →
          </Btn>
        </Card>
      </div>
    </div>
  );
}

// ─── AGENTS PAGE ──────────────────────────────────────────────────
function AgentsPage() {
  const [showCreate, setShowCreate] = useState(false);
  const [createStep, setCreateStep] = useState(0);
  const [selectedRole, setSelectedRole] = useState(null);
  const [agentName, setAgentName] = useState("");
  const [style, setStyle_] = useState(null);

  const roles = [
    { id: "hunter", icon: "🎯", label: "Growth Hunter", desc: "搜索目标公司和联系人" },
    { id: "researcher", icon: "🔬", label: "Researcher", desc: "市场研究和竞品分析" },
    { id: "outreach", icon: "✉️", label: "Outreach Agent", desc: "撰写和发送个性化邮件" },
    { id: "delivery", icon: "📦", label: "Delivery Agent", desc: "整理交付物和生成报告" },
  ];

  const agents = [
    { id: 1, name: "Hunter-1", role: "hunter", icon: "🎯", score: 0.82, status: "active", gen: 3, tasks: 47, version: "v3" },
    { id: 2, name: "Researcher", role: "researcher", icon: "🔬", score: 0.75, status: "active", gen: 1, tasks: 23, version: "v1" },
    { id: 3, name: "Outreach-1", role: "outreach", icon: "✉️", score: 0.68, status: "testing", gen: 2, tasks: 61, version: "v2" },
    { id: 4, name: "Delivery", role: "delivery", icon: "📦", score: 0.91, status: "active", gen: 1, tasks: 18, version: "v1" },
  ];

  const statusColor = { active: C.green, testing: C.amber, retired: C.textDim };
  const statusLabel = { active: "活跃", testing: "A/B测试中", retired: "已退休" };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 28 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700, color: C.text, marginBottom: 4 }}>数字员工团队</h1>
          <p style={{ fontSize: 14, color: C.textMid }}>4 个 Agent · 2 个运行中 · 1 个进化测试中</p>
        </div>
        <Btn onClick={() => { setShowCreate(true); setCreateStep(0); }}>+ 雇用新员工</Btn>
      </div>

      {/* Agent Grid */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 16, marginBottom: 24 }}>
        {agents.map(a => (
          <Card key={a.id} style={{ cursor: "pointer", transition: "border-color 0.2s" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 16 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <div style={{ fontSize: 28, width: 44, height: 44, display: "flex", alignItems: "center", justifyContent: "center", background: C.surfaceHigh, borderRadius: 10, border: `1px solid ${C.border}` }}>{a.icon}</div>
                <div>
                  <div style={{ fontSize: 15, fontWeight: 700, color: C.text }}>{a.name}</div>
                  <div style={{ fontSize: 11, color: C.textDim, marginTop: 2 }}>{a.version} · 第{a.gen}代</div>
                </div>
              </div>
              <Badge color={statusColor[a.status]} dot>{statusLabel[a.status]}</Badge>
            </div>

            {/* Score bar */}
            <div style={{ marginBottom: 14 }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 5 }}>
                <span style={{ fontSize: 11, color: C.textDim }}>绩效分</span>
                <span style={{ fontSize: 13, fontWeight: 700, color: a.score > 0.75 ? C.green : a.score > 0.6 ? C.amber : C.red }}>
                  {(a.score * 100).toFixed(0)}
                </span>
              </div>
              <div style={{ height: 5, background: C.border, borderRadius: 3, overflow: "hidden" }}>
                <div style={{ width: `${a.score * 100}%`, height: "100%", background: a.score > 0.75 ? C.green : a.score > 0.6 ? C.amber : C.red, borderRadius: 3, transition: "width 1s ease" }} />
              </div>
            </div>

            <div style={{ display: "flex", gap: 8, fontSize: 12, color: C.textDim }}>
              <span>📋 {a.tasks} 任务</span>
              <span>·</span>
              <span>🧬 进化{a.gen - 1}次</span>
            </div>
          </Card>
        ))}
      </div>

      {/* Create Modal */}
      {showCreate && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.75)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 100 }}>
          <Card style={{ width: 520, padding: 36, position: "relative" }}>
            <button onClick={() => setShowCreate(false)} style={{ position: "absolute", top: 16, right: 16, background: "transparent", border: "none", color: C.textMid, fontSize: 20, cursor: "pointer" }}>✕</button>
            <h2 style={{ fontSize: 19, fontWeight: 700, color: C.text, marginBottom: 24 }}>
              {createStep === 0 ? "选择岗位" : createStep === 1 ? "基本配置" : "工作风格"}
            </h2>

            {createStep === 0 && (
              <div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 24 }}>
                  {roles.map(r => (
                    <div key={r.id} onClick={() => setSelectedRole(r.id)} style={{
                      padding: 16, borderRadius: 10, cursor: "pointer",
                      border: `2px solid ${selectedRole === r.id ? C.accent : C.border}`,
                      background: selectedRole === r.id ? `${C.accent}10` : C.surfaceHigh,
                      transition: "all 0.2s",
                    }}>
                      <div style={{ fontSize: 22, marginBottom: 6 }}>{r.icon}</div>
                      <div style={{ fontSize: 13, fontWeight: 600, color: C.text, marginBottom: 3 }}>{r.label}</div>
                      <div style={{ fontSize: 11, color: C.textMid }}>{r.desc}</div>
                    </div>
                  ))}
                </div>
                <Btn onClick={() => selectedRole && setCreateStep(1)} style={{ width: "100%", justifyContent: "center" }}>下一步 →</Btn>
              </div>
            )}

            {createStep === 1 && (
              <div>
                <div style={{ marginBottom: 20 }}>
                  <Input label="员工名称" placeholder={`${roles.find(r => r.id === selectedRole)?.label}-2`}
                    value={agentName} onChange={setAgentName} />
                </div>
                <div style={{ padding: 14, background: C.surfaceHigh, borderRadius: 9, border: `1px solid ${C.border}`, marginBottom: 24, fontSize: 13, color: C.textMid }}>
                  💡 系统会根据行业插件自动配置默认 Prompt，你也可以在创建后手动调整
                </div>
                <div style={{ display: "flex", gap: 10 }}>
                  <Btn onClick={() => setCreateStep(0)} variant="ghost" style={{ flex: 1, justifyContent: "center" }}>← 返回</Btn>
                  <Btn onClick={() => setCreateStep(2)} style={{ flex: 2, justifyContent: "center" }}>下一步 →</Btn>
                </div>
              </div>
            )}

            {createStep === 2 && (
              <div>
                <p style={{ fontSize: 13, color: C.textMid, marginBottom: 16 }}>选择这位员工的工作风格（会影响 Prompt 策略）</p>
                <div style={{ display: "flex", flexDirection: "column", gap: 10, marginBottom: 24 }}>
                  {[
                    { id: "aggressive", icon: "⚡", label: "激进型", desc: "广撒网，追求数量和速度" },
                    { id: "precise", icon: "🎯", label: "精准型", desc: "深度研究，追求质量和转化率" },
                    { id: "balanced", icon: "⚖️", label: "均衡型", desc: "数量和质量平衡，推荐新手" },
                  ].map(s => (
                    <div key={s.id} onClick={() => setStyle_(s.id)} style={{
                      display: "flex", alignItems: "center", gap: 14,
                      padding: "12px 16px", borderRadius: 9, cursor: "pointer",
                      border: `2px solid ${style === s.id ? C.accent : C.border}`,
                      background: style === s.id ? `${C.accent}10` : C.surfaceHigh,
                      transition: "all 0.2s",
                    }}>
                      <span style={{ fontSize: 20 }}>{s.icon}</span>
                      <div>
                        <div style={{ fontSize: 13, fontWeight: 600, color: C.text }}>{s.label}</div>
                        <div style={{ fontSize: 12, color: C.textMid }}>{s.desc}</div>
                      </div>
                      {style === s.id && <span style={{ marginLeft: "auto", color: C.accent }}>✓</span>}
                    </div>
                  ))}
                </div>
                <div style={{ display: "flex", gap: 10 }}>
                  <Btn onClick={() => setCreateStep(1)} variant="ghost" style={{ flex: 1, justifyContent: "center" }}>← 返回</Btn>
                  <Btn onClick={() => setShowCreate(false)} variant="success" style={{ flex: 2, justifyContent: "center" }}>✓ 雇用上岗</Btn>
                </div>
              </div>
            )}
          </Card>
        </div>
      )}
    </div>
  );
}

// ─── TASKS PAGE ───────────────────────────────────────────────────
function TasksPage() {
  const [goal, setGoal] = useState("找到50家 MENA 地区的支付公司");
  const [running, setRunning] = useState(false);
  const [logs, setLogs] = useState([]);
  const logRef = useRef(null);

  const taskTypes = ["搜索潜在客户", "撰写邮件序列", "市场研究报告", "竞品分析", "数据整理交付"];
  const [taskType, setTaskType] = useState("搜索潜在客户");
  const [agent, setAgent] = useState("Hunter-1");

  const mockLogs = [
    { t: 500, icon: "🔍", msg: "Hunter-1 开始执行任务...", color: C.accent },
    { t: 1200, icon: "⚡", msg: "记忆层：检索到3条相似历史经验，注入Prompt", color: C.purple },
    { t: 2000, icon: "📚", msg: "技能库：加载 MENA Fintech Pitch Guide v2", color: C.purple },
    { t: 2800, icon: "✅", msg: "找到 Paymob (Cairo, EG) — BD: Ahmed K. ahmed@paymob.com", color: C.green },
    { t: 3400, icon: "✅", msg: "找到 Fawry (Cairo, EG) — CEO: Sara M. sara@fawry.com", color: C.green },
    { t: 4100, icon: "✅", msg: "找到 Moyasar (Riyadh, SA) — CTO: Khalid R.", color: C.green },
    { t: 4900, icon: "⚡", msg: "去重检查：发现1条重复记录，已过滤", color: C.amber },
    { t: 5600, icon: "✅", msg: "找到 PayTabs (Bahrain) — Sales: Fatima A.", color: C.green },
    { t: 6200, icon: "📊", msg: "绩效记录：本次任务 score=0.84，写入进化日志", color: C.amber },
    { t: 6800, icon: "🧠", msg: "记忆沉淀：成功案例已写入长期记忆库", color: C.purple },
    { t: 7200, icon: "✅", msg: "任务完成！找到 4 家公司，质量评分 0.84", color: C.green },
  ];

  function startTask() {
    setRunning(true);
    setLogs([]);
    mockLogs.forEach(({ t, icon, msg, color }) => {
      setTimeout(() => {
        setLogs(prev => [...prev, { icon, msg, color, time: new Date().toLocaleTimeString("zh", { hour: "2-digit", minute: "2-digit", second: "2-digit" }) }]);
      }, t);
    });
    setTimeout(() => setRunning(false), 7500);
  }

  const tasks = [
    { id: 1, type: "lead_search", agent: "Hunter-1", status: "done", score: 0.84, time: "10:34", output: "4家公司" },
    { id: 2, type: "email_write", agent: "Outreach-1", status: "done", score: 0.72, time: "09:51", output: "3封邮件" },
    { id: 3, type: "market_research", agent: "Researcher", status: "running", score: null, time: "10:40", output: "进行中..." },
  ];

  const statusStyle = { done: { color: C.green, label: "完成" }, running: { color: C.amber, label: "运行中" }, failed: { color: C.red, label: "失败" } };

  return (
    <div>
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, color: C.text, marginBottom: 4 }}>任务中心</h1>
        <p style={{ fontSize: 14, color: C.textMid }}>一键启动任务 · 实时查看执行日志</p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, marginBottom: 24 }}>
        {/* Launch panel */}
        <Card>
          <h3 style={{ fontSize: 15, fontWeight: 600, color: C.text, marginBottom: 20 }}>⚡ 快速启动</h3>
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <div>
              <label style={{ fontSize: 12, color: C.textMid, display: "block", marginBottom: 6 }}>任务类型</label>
              <select value={taskType} onChange={e => setTaskType(e.target.value)} style={{ width: "100%", padding: "10px 14px", background: C.surfaceHigh, border: `1px solid ${C.border}`, borderRadius: 9, color: C.text, fontSize: 13 }}>
                {taskTypes.map(t => <option key={t}>{t}</option>)}
              </select>
            </div>
            <Input label="目标描述" placeholder="越具体越好" value={goal} onChange={setGoal} />
            <div>
              <label style={{ fontSize: 12, color: C.textMid, display: "block", marginBottom: 6 }}>分配给</label>
              <select value={agent} onChange={e => setAgent(e.target.value)} style={{ width: "100%", padding: "10px 14px", background: C.surfaceHigh, border: `1px solid ${C.border}`, borderRadius: 9, color: C.text, fontSize: 13 }}>
                {["Hunter-1 (推荐)", "Researcher", "Outreach-1"].map(a => <option key={a}>{a}</option>)}
              </select>
            </div>
            <Btn onClick={startTask} size="lg" style={{ width: "100%", justifyContent: "center" }} variant={running ? "ghost" : "primary"}>
              {running ? "⏳ 运行中..." : "🚀 启动任务"}
            </Btn>
          </div>
        </Card>

        {/* Live log */}
        <Card style={{ display: "flex", flexDirection: "column" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
            <h3 style={{ fontSize: 15, fontWeight: 600, color: C.text }}>执行日志</h3>
            {running && <Badge color={C.green} dot>实时</Badge>}
          </div>
          <div ref={logRef} style={{ flex: 1, minHeight: 240, maxHeight: 300, overflowY: "auto", display: "flex", flexDirection: "column", gap: 0 }}>
            {logs.length === 0 && (
              <div style={{ color: C.textDim, fontSize: 13, textAlign: "center", marginTop: 60 }}>
                启动任务后在此查看实时日志...
              </div>
            )}
            {logs.map((l, i) => (
              <div key={i} style={{ display: "flex", gap: 10, padding: "8px 0", borderBottom: `1px solid ${C.border}`, animation: "fadeIn 0.3s" }}>
                <span style={{ fontSize: 10, color: C.textDim, flexShrink: 0, fontVariantNumeric: "tabular-nums", marginTop: 2 }}>{l.time}</span>
                <span style={{ fontSize: 13, flexShrink: 0 }}>{l.icon}</span>
                <span style={{ fontSize: 12, color: l.color, lineHeight: 1.5 }}>{l.msg}</span>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Task history */}
      <Card>
        <h3 style={{ fontSize: 15, fontWeight: 600, color: C.text, marginBottom: 18 }}>任务历史</h3>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ borderBottom: `1px solid ${C.border}` }}>
              {["任务类型", "执行Agent", "时间", "输出", "绩效分", "状态", "操作"].map(h => (
                <th key={h} style={{ padding: "8px 12px", fontSize: 11, color: C.textDim, textAlign: "left", letterSpacing: "0.08em", textTransform: "uppercase" }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {tasks.map(t => (
              <tr key={t.id} style={{ borderBottom: `1px solid ${C.border}` }}>
                <td style={{ padding: "12px", fontSize: 13, color: C.text }}>{t.type}</td>
                <td style={{ padding: "12px", fontSize: 13, color: C.textMid }}>{t.agent}</td>
                <td style={{ padding: "12px", fontSize: 12, color: C.textDim, fontVariantNumeric: "tabular-nums" }}>{t.time}</td>
                <td style={{ padding: "12px", fontSize: 12, color: C.textMid }}>{t.output}</td>
                <td style={{ padding: "12px" }}>
                  {t.score ? <span style={{ fontSize: 13, fontWeight: 700, color: t.score > 0.75 ? C.green : C.amber }}>{(t.score * 100).toFixed(0)}</span> : <span style={{ color: C.textDim, fontSize: 12 }}>—</span>}
                </td>
                <td style={{ padding: "12px" }}><Badge color={statusStyle[t.status].color} dot>{statusStyle[t.status].label}</Badge></td>
                <td style={{ padding: "12px" }}><Btn size="sm" variant="ghost">查看</Btn></td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}

// ─── EVOLUTION PAGE ───────────────────────────────────────────────
function EvolutionPage() {
  const agents = [
    { name: "Hunter-1", score: 0.82, threshold: 0.65, taskCount: 47, status: "healthy", gen: 3, trend: [0.52, 0.61, 0.74, 0.82] },
    { name: "Outreach-1", score: 0.68, threshold: 0.65, taskCount: 61, status: "testing", gen: 2, trend: [0.55, 0.68] },
    { name: "Researcher", score: 0.75, threshold: 0.65, taskCount: 23, status: "healthy", gen: 1, trend: [0.75] },
    { name: "Delivery", score: 0.91, threshold: 0.65, taskCount: 18, status: "healthy", gen: 1, trend: [0.91] },
  ];

  const abTests = [
    { id: 1, agent: "Outreach-1", varA: "v1 (原始)", varB: "v2 (进化)", scoreA: 0.61, scoreB: 0.72, sampleA: 20, sampleB: 18, status: "running" },
  ];

  const history = [
    { time: "2h前", agent: "Hunter-1", from: "v2", to: "v3", scoreBefore: 0.61, scoreAfter: 0.82, reason: "搜索结果质量低" },
    { time: "1d前", agent: "Outreach-1", from: "v1", to: "v2(测试中)", scoreBefore: 0.55, scoreAfter: "测试中", reason: "回复率低于15%" },
  ];

  const coldStartProgress = 47;
  const coldStartTarget = 100;
  const phase = coldStartProgress < 100 ? 0 : coldStartProgress < 500 ? 1 : 2;
  const phaseLabels = ["冷启动（人工审核）", "成长期（半自动）", "成熟期（全自动）"];

  return (
    <div>
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, color: C.text, marginBottom: 4 }}>进化控制台</h1>
        <p style={{ fontSize: 14, color: C.textMid }}>系统自动优化 Agent 的 Prompt 和工作流</p>
      </div>

      {/* Cold start banner */}
      <div style={{ padding: "16px 20px", background: `${C.amber}08`, border: `1px solid ${C.amber}25`, borderRadius: 12, marginBottom: 24 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
          <div>
            <span style={{ fontSize: 13, fontWeight: 600, color: C.amber }}>🔒 当前模式：{phaseLabels[phase]}</span>
            <span style={{ fontSize: 12, color: C.textMid, marginLeft: 12 }}>进化变更需要人工确认</span>
          </div>
          <span style={{ fontSize: 12, color: C.textDim }}>{coldStartProgress}/{coldStartTarget} 任务解锁自动进化</span>
        </div>
        <div style={{ height: 6, background: C.border, borderRadius: 3, overflow: "hidden" }}>
          <div style={{ width: `${(coldStartProgress / coldStartTarget) * 100}%`, height: "100%", background: C.amber, borderRadius: 3, transition: "width 1s" }} />
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16, marginBottom: 24 }}>
        <StatCard label="总 Agent 数" value={agents.length} color={C.accent} icon="◈" />
        <StatCard label="低于阈值" value={agents.filter(a => a.score < a.threshold).length} sub="触发进化条件" color={C.amber} icon="⚠" />
        <StatCard label="A/B 测试中" value={abTests.length} color={C.purple} icon="⚖" />
      </div>

      {/* Agent KPI */}
      <Card style={{ marginBottom: 20 }}>
        <h3 style={{ fontSize: 15, fontWeight: 600, color: C.text, marginBottom: 18 }}>Agent 绩效追踪</h3>
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {agents.map(a => (
            <div key={a.name} style={{ display: "flex", alignItems: "center", gap: 16, padding: "14px 16px", background: C.surfaceHigh, borderRadius: 10, border: `1px solid ${C.border}` }}>
              <div style={{ width: 120 }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: C.text }}>{a.name}</div>
                <div style={{ fontSize: 11, color: C.textDim }}>第{a.gen}代 · {a.taskCount}任务</div>
              </div>

              {/* Score trend dots */}
              <div style={{ display: "flex", alignItems: "center", gap: 4, flex: 1 }}>
                {a.trend.map((s, i) => (
                  <div key={i} style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 3 }}>
                    <div style={{
                      width: i === a.trend.length - 1 ? 12 : 8,
                      height: i === a.trend.length - 1 ? 12 : 8,
                      borderRadius: "50%",
                      background: s > 0.75 ? C.green : s > 0.6 ? C.amber : C.red,
                      boxShadow: i === a.trend.length - 1 ? `0 0 8px ${s > 0.75 ? C.green : C.amber}` : "none",
                    }} />
                    <span style={{ fontSize: 9, color: C.textDim }}>{(s * 100).toFixed(0)}</span>
                    {i < a.trend.length - 1 && <div style={{ position: "absolute" }} />}
                  </div>
                ))}
                <div style={{ flex: 1, height: 2, background: `linear-gradient(90deg, ${C.border}, ${C.border})`, marginLeft: 4 }} />
              </div>

              <div style={{ width: 60, textAlign: "right" }}>
                <span style={{ fontSize: 20, fontWeight: 700, color: a.score > 0.75 ? C.green : a.score > 0.6 ? C.amber : C.red }}>
                  {(a.score * 100).toFixed(0)}
                </span>
              </div>

              <Badge
                color={a.status === "testing" ? C.amber : a.status === "healthy" ? C.green : C.red}
                dot
              >
                {a.status === "testing" ? "A/B测试中" : a.status === "healthy" ? "健康" : "待进化"}
              </Badge>
            </div>
          ))}
        </div>
      </Card>

      {/* A/B Tests */}
      <Card style={{ marginBottom: 20 }}>
        <h3 style={{ fontSize: 15, fontWeight: 600, color: C.text, marginBottom: 18 }}>A/B 测试看板</h3>
        {abTests.map(t => (
          <div key={t.id} style={{ padding: 20, background: C.surfaceHigh, borderRadius: 10, border: `1px solid ${C.border}` }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
              <div>
                <span style={{ fontSize: 14, fontWeight: 600, color: C.text }}>{t.agent} — Prompt 对比测试</span>
                <Badge color={C.amber} dot style={{ marginLeft: 10 }}>进行中</Badge>
              </div>
              <Btn size="sm" variant="ghost">手动结束</Btn>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
              {[
                { label: t.varA, score: t.scoreA, sample: t.sampleA, isWinning: t.scoreB > t.scoreA },
                { label: t.varB, score: t.scoreB, sample: t.sampleB, isWinning: t.scoreB > t.scoreA },
              ].map((v, i) => (
                <div key={i} style={{
                  padding: 16, borderRadius: 9,
                  border: `2px solid ${v.isWinning !== (i === 0) ? C.green : C.border}`,
                  background: v.isWinning !== (i === 0) ? C.greenDim : C.bg,
                }}>
                  <div style={{ fontSize: 12, color: C.textMid, marginBottom: 8 }}>版本 {i === 0 ? "A" : "B"}: {v.label}</div>
                  <div style={{ fontSize: 28, fontWeight: 700, color: v.isWinning !== (i === 0) ? C.green : C.textMid }}>
                    {(v.score * 100).toFixed(0)}
                  </div>
                  <div style={{ fontSize: 11, color: C.textDim }}>{v.sample} 个任务样本</div>
                  {v.isWinning !== (i === 0) && <div style={{ fontSize: 11, color: C.green, marginTop: 6 }}>↑ 领先 {((t.scoreB - t.scoreA) * 100).toFixed(0)} 分</div>}
                </div>
              ))}
            </div>
          </div>
        ))}
      </Card>

      {/* Evolution history */}
      <Card>
        <h3 style={{ fontSize: 15, fontWeight: 600, color: C.text, marginBottom: 18 }}>进化历史</h3>
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {history.map((h, i) => (
            <div key={i} style={{ display: "flex", gap: 14, padding: "12px 0", borderBottom: `1px solid ${C.border}` }}>
              <span style={{ fontSize: 12, color: C.textDim, flexShrink: 0, width: 40 }}>{h.time}</span>
              <div style={{ flex: 1 }}>
                <span style={{ fontSize: 13, color: C.text, fontWeight: 500 }}>{h.agent}</span>
                <span style={{ fontSize: 13, color: C.textMid }}> {h.from} → </span>
                <span style={{ fontSize: 13, color: C.accent }}>{h.to}</span>
                <div style={{ fontSize: 12, color: C.textDim, marginTop: 3 }}>触发原因：{h.reason}</div>
              </div>
              <div style={{ textAlign: "right" }}>
                <span style={{ fontSize: 12, color: C.textDim }}>{typeof h.scoreBefore === "number" ? (h.scoreBefore * 100).toFixed(0) : h.scoreBefore}</span>
                <span style={{ fontSize: 12, color: C.textDim }}> → </span>
                <span style={{ fontSize: 12, color: typeof h.scoreAfter === "number" ? C.green : C.amber }}>{typeof h.scoreAfter === "number" ? (h.scoreAfter * 100).toFixed(0) : h.scoreAfter}</span>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

// ─── SKILLS PAGE ──────────────────────────────────────────────────
function SkillsPage() {
  const [search, setSearch] = useState("");
  const [role, setRole] = useState("all");
  const [expanded, setExpanded] = useState(null);

  const skills = [
    { id: 1, name: "MENA Fintech Pitch Guide", role: "hunter", source: "预置", successRate: 0.84, uses: 23, global: true, preview: "适用于中东北非金融科技公司的开场白策略。核心方法：先提监管痛点，再引出解决方案，最后给出具体案例数据..." },
    { id: 2, name: "Cold Email Framework v3", role: "outreach", source: "Hunter-1", successRate: 0.76, uses: 41, global: true, preview: "高转化率冷邮件结构：主题行用数字和痛点；第一句直接说对方公司名；正文三句话：痛点→方案→CTA..." },
    { id: 3, name: "License Research SOP", role: "researcher", source: "Researcher", successRate: 0.91, uses: 8, global: false, preview: "支付牌照研究标准流程：1. 先查官方央行网站 2. 检索当地法律数据库 3. 对比相邻国家门槛..." },
    { id: 4, name: "Saudi Arabia Market Map", role: "researcher", source: "Researcher", successRate: 0.88, uses: 5, global: false, preview: "沙特金融科技市场地图：主要监管机构SAMA，本地支付玩家STC Pay / Madfu..." },
    { id: 5, name: "Lead Scoring Rules", role: "hunter", source: "预置", successRate: 0.79, uses: 67, global: true, preview: "线索质量评分标准：公司规模>50人 +2分，有融资记录 +3分，官网有支付集成需求 +2分..." },
  ];

  const filtered = skills.filter(s =>
    (role === "all" || s.role === role) &&
    s.name.toLowerCase().includes(search.toLowerCase())
  );

  const roleColors = { hunter: C.accent, outreach: C.purple, researcher: C.green, delivery: C.amber };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 28 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700, color: C.text, marginBottom: 4 }}>技能图书馆</h1>
          <p style={{ fontSize: 14, color: C.textMid }}>{skills.length} 个技能 · {skills.filter(s => s.global).length} 个全局共享</p>
        </div>
        <Btn>+ 手动添加技能</Btn>
      </div>

      {/* Filters */}
      <div style={{ display: "flex", gap: 12, marginBottom: 20 }}>
        <Input placeholder="🔍 搜索技能名称..." value={search} onChange={setSearch} style={{ flex: 1 }} />
        <select value={role} onChange={e => setRole(e.target.value)} style={{ padding: "10px 14px", background: C.surfaceHigh, border: `1px solid ${C.border}`, borderRadius: 9, color: C.text, fontSize: 13 }}>
          <option value="all">全部岗位</option>
          <option value="hunter">Hunter</option>
          <option value="outreach">Outreach</option>
          <option value="researcher">Researcher</option>
          <option value="delivery">Delivery</option>
        </select>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        {filtered.map(s => (
          <Card key={s.id} style={{ padding: 0, overflow: "hidden" }}>
            <div onClick={() => setExpanded(expanded === s.id ? null : s.id)} style={{ padding: "16px 20px", cursor: "pointer", display: "flex", alignItems: "center", gap: 14 }}>
              <div style={{ flex: 1 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
                  <span style={{ fontSize: 14, fontWeight: 600, color: C.text }}>{s.name}</span>
                  {s.global && <Badge color={C.accent}>🌐 全局</Badge>}
                </div>
                <div style={{ display: "flex", gap: 12, fontSize: 12, color: C.textDim }}>
                  <Badge color={roleColors[s.role]}>{s.role}</Badge>
                  <span>来源：{s.source}</span>
                  <span>使用 {s.uses} 次</span>
                </div>
              </div>
              <div style={{ textAlign: "right", flexShrink: 0 }}>
                <div style={{ fontSize: 22, fontWeight: 700, color: s.successRate > 0.8 ? C.green : C.amber }}>{(s.successRate * 100).toFixed(0)}</div>
                <div style={{ fontSize: 10, color: C.textDim }}>成功率</div>
              </div>
              <span style={{ color: C.textDim, fontSize: 18, marginLeft: 8, transition: "transform 0.2s", transform: expanded === s.id ? "rotate(90deg)" : "none" }}>›</span>
            </div>
            {expanded === s.id && (
              <div style={{ borderTop: `1px solid ${C.border}`, padding: "16px 20px", background: C.surfaceHigh }}>
                <pre style={{ fontSize: 13, color: C.textMid, lineHeight: 1.7, whiteSpace: "pre-wrap", fontFamily: "inherit", margin: 0 }}>{s.preview}</pre>
                <div style={{ display: "flex", gap: 10, marginTop: 16 }}>
                  <Btn size="sm" variant="ghost">✏️ 编辑</Btn>
                  {!s.global && <Btn size="sm">🌐 提升为全局</Btn>}
                </div>
              </div>
            )}
          </Card>
        ))}
      </div>
    </div>
  );
}

// ─── BILLING PAGE ─────────────────────────────────────────────────
function BillingPage() {
  const plans = [
    { id: "starter", name: "Starter", price: "免费", agents: 3, tasks: 500, features: ["基础进化功能", "1个行业插件", "社区支持"], current: true, color: C.textMid },
    { id: "growth", name: "Growth", price: "$49", period: "/月", agents: 15, tasks: 5000, features: ["完整进化系统", "2个行业插件", "技能蒸馏", "优先支持"], color: C.accent },
    { id: "enterprise", name: "Enterprise", price: "联系我们", agents: 100, tasks: 50000, features: ["无限进化", "自定义插件", "专属客户成功", "SLA保障", "私有部署"], color: C.purple },
  ];

  const usage = { agents: 2, maxAgents: 3, tasks: 47, maxTasks: 500, tokens: 12400, maxTokens: 100000 };

  return (
    <div>
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, color: C.text, marginBottom: 4 }}>套餐与用量</h1>
        <p style={{ fontSize: 14, color: C.textMid }}>当前：Starter 免费版</p>
      </div>

      {/* Current usage */}
      <Card style={{ marginBottom: 24 }}>
        <h3 style={{ fontSize: 15, fontWeight: 600, color: C.text, marginBottom: 18 }}>本月用量</h3>
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {[
            { label: "Agent 数量", used: usage.agents, max: usage.maxAgents, color: C.accent },
            { label: "任务数", used: usage.tasks, max: usage.maxTasks, color: C.green },
            { label: "Token 消耗", used: usage.tokens, max: usage.maxTokens, color: C.purple },
          ].map(u => (
            <div key={u.label}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                <span style={{ fontSize: 13, color: C.textMid }}>{u.label}</span>
                <span style={{ fontSize: 13, color: C.text, fontVariantNumeric: "tabular-nums" }}>
                  {u.used.toLocaleString()} / {u.max.toLocaleString()}
                </span>
              </div>
              <div style={{ height: 6, background: C.border, borderRadius: 3, overflow: "hidden" }}>
                <div style={{ width: `${(u.used / u.max) * 100}%`, height: "100%", background: u.used / u.max > 0.8 ? C.red : u.color, borderRadius: 3 }} />
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Plans */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16 }}>
        {plans.map(p => (
          <Card key={p.id} style={{
            border: `1px solid ${p.current ? C.accent : p.id === "growth" ? `${C.accent}40` : C.border}`,
            background: p.id === "growth" ? `${C.accent}05` : C.surface,
            position: "relative",
          }}>
            {p.id === "growth" && (
              <div style={{ position: "absolute", top: -11, left: "50%", transform: "translateX(-50%)" }}>
                <Badge color={C.accent}>推荐</Badge>
              </div>
            )}
            <div style={{ marginBottom: 20 }}>
              <div style={{ fontSize: 14, fontWeight: 600, color: p.color, marginBottom: 8 }}>{p.name}</div>
              <div style={{ display: "flex", alignItems: "baseline", gap: 4 }}>
                <span style={{ fontSize: 28, fontWeight: 800, color: C.text }}>{p.price}</span>
                {p.period && <span style={{ fontSize: 13, color: C.textMid }}>{p.period}</span>}
              </div>
            </div>
            <div style={{ marginBottom: 20, fontSize: 12, color: C.textMid }}>
              <div style={{ marginBottom: 4 }}>最多 {p.agents} 个 Agent</div>
              <div>{p.tasks.toLocaleString()} 任务/月</div>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 7, marginBottom: 24 }}>
              {p.features.map(f => (
                <div key={f} style={{ fontSize: 12, color: C.textMid, display: "flex", alignItems: "center", gap: 6 }}>
                  <span style={{ color: p.color, fontSize: 10 }}>✓</span>{f}
                </div>
              ))}
            </div>
            {p.current
              ? <Btn variant="ghost" style={{ width: "100%", justifyContent: "center" }} size="sm">当前套餐</Btn>
              : <Btn style={{ width: "100%", justifyContent: "center", background: p.color }} size="sm">{p.id === "enterprise" ? "联系销售" : "升级"}</Btn>
            }
          </Card>
        ))}
      </div>
    </div>
  );
}

// ─── MAIN APP ─────────────────────────────────────────────────────
export default function App() {
  const [screen, setScreen] = useState("login"); // login | onboarding | app
  const [page, setPage] = useState("dashboard");

  if (screen === "login") return <LoginPage onLogin={() => setScreen("onboarding")} />;
  if (screen === "onboarding") return <OnboardingPage onDone={() => setScreen("app")} />;

  const pages = {
    dashboard: <DashboardPage />,
    agents: <AgentsPage />,
    tasks: <TasksPage />,
    evolution: <EvolutionPage />,
    skills: <SkillsPage />,
    billing: <BillingPage />,
    settings: <div style={{ color: C.textMid, padding: 40 }}>Settings — 即将推出</div>,
  };

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: C.bg, fontFamily: "'DM Sans', 'Helvetica Neue', sans-serif" }}>
      <style>{`
        * { box-sizing: border-box; margin: 0; padding: 0; }
        ::-webkit-scrollbar { width: 4px; } 
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #2a2e3a; border-radius: 2px; }
        select option { background: #13171f; color: #e8eaf0; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: none; } }
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap');
      `}</style>

      <Sidebar active={page} onNav={setPage} />

      <main style={{ flex: 1, padding: "32px 36px", overflowY: "auto", minWidth: 0 }}>
        {pages[page] || pages.dashboard}
      </main>
    </div>
  );
}
