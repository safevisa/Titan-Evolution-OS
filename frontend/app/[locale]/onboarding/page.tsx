"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { apiUrl } from "@/lib/api-origin";

const C = {
  bg: "#07090f", surface: "#0d1017", surfaceHigh: "#13171f",
  border: "rgba(255,255,255,0.06)", text: "#e8eaf0", textMid: "#8892a4",
  textDim: "#3d4557", accent: "#5b6ef5", accentGlow: "rgba(91,110,245,0.2)",
  green: "#2dd4a0", greenDim: "rgba(45,212,160,0.15)", purple: "#a78bfa",
};

type PluginRow = {
  plugin_id: string;
  display_name: string;
  name_zh?: string;
  icon?: string;
  catalog?: boolean;
  agent_roles?: string[];
};

const COPY: Record<string, Record<string, string>> = {
  en: {
    stepIndustry: "Choose your industry",
    stepIndustrySub: "Pick one sector — we provision agents and skills from the catalog.",
    search: "Search industries…",
    featured: "Featured",
    global: "All industries",
    next: "Next →",
    stepGoal: "Your first goal",
    stepGoalSub: "Be specific — agents will plan against it.",
    ownGoal: "Or type your own goal…",
    back: "← Back",
    launchTeam: "Launch team →",
    readyTitle: "Ready to launch",
    readySub: "We will align your workspace to the selected industry and reprovision agents.",
    launchBtn: "⚡ Launch my team",
    initTitle: "Initialising…",
    stepLabels: "Industry · Goal · Launch",
  },
  zh: {
    stepIndustry: "选择你的行业",
    stepIndustrySub: "选择一个细分行业 — 我们将按目录开通数字员工与技能库。",
    search: "搜索行业…",
    featured: "精选模板",
    global: "全球行业",
    next: "下一步 →",
    stepGoal: "你的第一个目标",
    stepGoalSub: "越具体越好 — Agent 会据此拆解行动。",
    ownGoal: "或输入自定义目标…",
    back: "← 返回",
    launchTeam: "启动团队 →",
    readyTitle: "准备就绪",
    readySub: "将把租户切换到所选行业，并重新开通岗位与技能（旧 Agent 将归档）。",
    launchBtn: "⚡ 启动我的团队",
    initTitle: "正在初始化…",
    stepLabels: "行业 · 目标 · 启动",
  },
};

function goalsFor(locale: string, pluginId: string): string[] {
  const zh = locale === "zh";
  const enSpecific: Record<string, [string, string, string]> = {
    payment_fintech: [
      "Find 50 payment / acquiring targets in MENA with contacts",
      "Research SEA digital wallet regulatory landscape",
      "Draft 20 personalised partner outreach emails",
    ],
    saas_b2b: [
      "Find 30 SaaS companies (50–200 FTE) in our ICP",
      "Competitive pricing & packaging intel for top 5 rivals",
      "Invite 25 qualified prospects to a live demo",
    ],
  };
  const zhSpecific: Record<string, [string, string, string]> = {
    payment_fintech: [
      "在中东寻找 50 家支付/收单相关目标公司及联系人",
      "调研东南亚数字钱包监管与牌照路径",
      "撰写 20 封个性化合作伙伴触达邮件",
    ],
    saas_b2b: [
      "寻找 30 家 50–200 人规模的 SaaS 公司（符合 ICP）",
      "调研前 5 名竞品的定价与打包策略",
      "邀请 25 名合格潜在客户参加产品演示",
    ],
  };
  if (zh && zhSpecific[pluginId]) return [...zhSpecific[pluginId]];
  if (!zh && enSpecific[pluginId]) return [...enSpecific[pluginId]];
  if (zh) {
    return [
      "为所选行业制定季度增长假设与关键指标",
      "梳理主要监管与合规关注点清单",
      "输出跨部门协同的里程碑计划（含负责人）",
    ];
  }
  return [
    "Draft quarterly growth hypotheses and KPIs for this industry",
    "Map top regulatory and compliance watch-points",
    "Produce a cross-functional milestone plan with owners",
  ];
}

export default function OnboardingPage({ params }: { params: { locale: string } }) {
  const router = useRouter();
  const { tenantId } = useAuth();
  const locale = params.locale === "zh" ? "zh" : "en";
  const L = COPY[locale];

  const [step, setStep] = useState(0);
  const [industry, setIndustry] = useState<string | null>(null);
  const [goal, setGoal] = useState("");
  const [provisioning, setProvisioning] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const [plugins, setPlugins] = useState<PluginRow[]>([]);
  const [loadErr, setLoadErr] = useState<string | null>(null);
  const [q, setQ] = useState("");

  const loadPlugins = useCallback(async () => {
    try {
      const res = await fetch(apiUrl("/api/v1/tenants/plugins/list"));
      if (!res.ok) throw new Error(String(res.status));
      const data = (await res.json()) as PluginRow[];
      setPlugins(Array.isArray(data) ? data : []);
    } catch {
      setLoadErr(locale === "zh" ? "无法加载行业目录" : "Could not load industry catalog");
    }
  }, [locale]);

  useEffect(() => {
    void loadPlugins();
  }, [loadPlugins]);

  const filtered = useMemo(() => {
    const s = q.trim().toLowerCase();
    if (!s) return plugins;
    return plugins.filter((p) => {
      const en = p.display_name.toLowerCase();
      const zh = (p.name_zh ?? "").toLowerCase();
      const id = p.plugin_id.toLowerCase();
      return en.includes(s) || zh.includes(s) || id.includes(s);
    });
  }, [plugins, q]);

  const featured = useMemo(
    () => plugins.filter((p) => !p.catalog && ["payment_fintech", "saas_b2b"].includes(p.plugin_id)),
    [plugins],
  );
  const catalog = useMemo(() => filtered.filter((p) => p.catalog), [filtered]);

  const selected = useMemo(
    () => plugins.find((p) => p.plugin_id === industry) ?? null,
    [plugins, industry],
  );

  const label = (p: PluginRow) => (locale === "zh" ? (p.name_zh || p.display_name) : p.display_name);

  async function handleFinish() {
    if (!tenantId || !industry) return;
    setProvisioning(true);
    const n = selected?.agent_roles?.length ?? 0;
    const lines = [
      locale === "zh" ? `正在切换行业插件：${industry}` : `Switching industry plugin: ${industry}`,
      locale === "zh" ? "正在归档旧 Agent 并写入新岗位…" : "Archiving old agents, provisioning new roles…",
      locale === "zh" ? `注入技能与行业上下文（约 ${n} 个岗位）` : `Seeding skills + sector context (~${n} roles)`,
      locale === "zh" ? "✅ 完成" : "✅ Done",
    ];
    for (let i = 0; i < lines.length; i++) {
      await new Promise((r) => setTimeout(r, 500));
      setLogs((prev) => [...prev, lines[i]]);
    }

    try {
      const res = await fetch(apiUrl(`/api/v1/tenants/${tenantId}`), {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          industry_plugin: industry,
          reprovision_agents: true,
        }),
      });
      if (!res.ok) {
        const t = await res.text();
        setLogs((prev) => [...prev, `PATCH failed: ${res.status} ${t.slice(0, 200)}`]);
      }
    } catch (e) {
      setLogs((prev) => [...prev, String(e)]);
    }

    await new Promise((r) => setTimeout(r, 400));
    router.push(`/${params.locale}/dashboard`);
  }

  const steps = L.stepLabels.split(" · ");

  return (
    <div style={{ minHeight: "100vh", background: C.bg, display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "'DM Sans','Helvetica Neue',sans-serif" }}>
      <style>{`* { box-sizing: border-box; } @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap');`}</style>
      <div style={{ width: 620, maxWidth: "96vw" }}>

        <div style={{ display: "flex", gap: 8, marginBottom: 40, justifyContent: "center", alignItems: "center", flexWrap: "wrap" }}>
          {steps.map((s, i) => (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <div style={{ width: 28, height: 28, borderRadius: "50%", background: i < step ? C.green : i === step ? C.accent : C.surfaceHigh, border: `2px solid ${i < step ? C.green : i === step ? C.accent : C.border}`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 12, fontWeight: 700, color: i <= step ? "#fff" : C.textDim, transition: "all 0.3s" }}>
                {i < step ? "✓" : i + 1}
              </div>
              <span style={{ fontSize: 12, color: i === step ? C.text : C.textDim }}>{s}</span>
              {i < steps.length - 1 && <div style={{ width: 32, height: 1, background: i < step ? C.green : C.border, transition: "all 0.3s" }} />}
            </div>
          ))}
        </div>

        <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 14, padding: 36 }}>
          {step === 0 && (
            <div>
              <h2 style={{ fontSize: 22, fontWeight: 700, color: C.text, marginBottom: 8 }}>{L.stepIndustry}</h2>
              <p style={{ fontSize: 14, color: C.textMid, marginBottom: 16 }}>{L.stepIndustrySub}</p>
              {loadErr && <p style={{ color: "#f87171", fontSize: 13, marginBottom: 12 }}>{loadErr}</p>}
              <input
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder={L.search}
                style={{ width: "100%", marginBottom: 14, padding: "10px 12px", background: C.surfaceHigh, border: `1px solid ${C.border}`, borderRadius: 9, color: C.text, fontSize: 14, outline: "none" }}
              />
              <div style={{ maxHeight: 340, overflowY: "auto", paddingRight: 4 }}>
                {featured.length > 0 && (
                  <>
                    <div style={{ fontSize: 11, fontWeight: 700, color: C.textDim, marginBottom: 8, letterSpacing: "0.06em" }}>{L.featured.toUpperCase()}</div>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 18 }}>
                      {featured.map((ind) => (
                        <div key={ind.plugin_id} onClick={() => setIndustry(ind.plugin_id)} style={{ padding: 16, borderRadius: 12, cursor: "pointer", border: `2px solid ${industry === ind.plugin_id ? C.accent : C.border}`, background: industry === ind.plugin_id ? `${C.accent}10` : C.surfaceHigh, transition: "all 0.2s" }}>
                          <div style={{ fontSize: 22, marginBottom: 6 }}>{ind.icon || "⭐"}</div>
                          <div style={{ fontSize: 14, fontWeight: 600, color: C.text, marginBottom: 4 }}>{label(ind)}</div>
                          <div style={{ fontSize: 11, color: C.textDim }}>{ind.plugin_id}</div>
                        </div>
                      ))}
                    </div>
                  </>
                )}
                <div style={{ fontSize: 11, fontWeight: 700, color: C.textDim, marginBottom: 8, letterSpacing: "0.06em" }}>{L.global.toUpperCase()} ({catalog.length})</div>
                <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                  {catalog.map((ind) => (
                    <div key={ind.plugin_id} onClick={() => setIndustry(ind.plugin_id)} style={{ padding: "12px 14px", borderRadius: 10, cursor: "pointer", border: `1px solid ${industry === ind.plugin_id ? C.accent : C.border}`, background: industry === ind.plugin_id ? `${C.accent}12` : "transparent", display: "flex", alignItems: "center", gap: 12 }}>
                      <span style={{ fontSize: 18 }}>{ind.icon || "🏢"}</span>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontSize: 13, fontWeight: 600, color: C.text }}>{label(ind)}</div>
                        <div style={{ fontSize: 11, color: C.textDim }}>{ind.plugin_id} · {(ind.agent_roles?.length ?? 0)} roles</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              <button type="button" onClick={() => industry && setStep(1)} disabled={!industry} style={{ marginTop: 22, width: "100%", padding: "13px", borderRadius: 9, border: "none", cursor: industry ? "pointer" : "not-allowed", fontWeight: 600, fontSize: 15, background: industry ? C.accent : "#2a2e3a", color: "#fff", transition: "all 0.18s" }}>
                {L.next}
              </button>
            </div>
          )}

          {step === 1 && (
            <div>
              <h2 style={{ fontSize: 22, fontWeight: 700, color: C.text, marginBottom: 8 }}>{L.stepGoal}</h2>
              <p style={{ fontSize: 14, color: C.textMid, marginBottom: 22 }}>{L.stepGoalSub}</p>
              <div style={{ display: "flex", flexDirection: "column", gap: 10, marginBottom: 18 }}>
                {goalsFor(locale, industry ?? "payment_fintech").map((s) => (
                  <div key={s} onClick={() => setGoal(s)} style={{ padding: "14px 16px", borderRadius: 9, cursor: "pointer", border: `1px solid ${goal === s ? C.accent : C.border}`, background: goal === s ? `${C.accent}10` : C.surfaceHigh, fontSize: 13, color: goal === s ? C.text : C.textMid, transition: "all 0.2s" }}>
                    {s}
                  </div>
                ))}
              </div>
              <input placeholder={L.ownGoal} value={goal} onChange={(e) => setGoal(e.target.value)} style={{ width: "100%", padding: "11px 14px", background: C.surfaceHigh, border: `1px solid ${C.border}`, borderRadius: 9, color: C.text, fontSize: 14, outline: "none" }} />
              <div style={{ display: "flex", gap: 12, marginTop: 22 }}>
                <button type="button" onClick={() => setStep(0)} style={{ flex: 1, padding: "10px", borderRadius: 9, border: `1px solid ${C.border}`, background: "transparent", color: C.textMid, fontSize: 13, cursor: "pointer" }}>{L.back}</button>
                <button type="button" onClick={() => goal && setStep(2)} disabled={!goal} style={{ flex: 2, padding: "13px", borderRadius: 9, border: "none", cursor: goal ? "pointer" : "not-allowed", fontWeight: 600, fontSize: 15, background: goal ? C.accent : "#2a2e3a", color: "#fff" }}>
                  {L.launchTeam}
                </button>
              </div>
            </div>
          )}

          {step === 2 && (
            <div style={{ textAlign: "center" }}>
              {!provisioning ? (
                <>
                  <div style={{ fontSize: 40, marginBottom: 16 }}>🤖</div>
                  <h2 style={{ fontSize: 22, fontWeight: 700, color: C.text, marginBottom: 8 }}>{L.readyTitle}</h2>
                  <p style={{ fontSize: 14, color: C.textMid, marginBottom: 14 }}>{L.readySub}</p>
                  <p style={{ fontSize: 12, color: C.purple, marginBottom: 22 }}>
                    {selected ? `${label(selected)} · ${selected.agent_roles?.length ?? 0} ${locale === "zh" ? "个岗位" : "roles"}` : industry}
                  </p>
                  <button type="button" onClick={handleFinish} style={{ width: "100%", padding: "13px", borderRadius: 9, border: "none", cursor: "pointer", fontWeight: 600, fontSize: 15, background: C.green, color: "#07150e" }}>
                    {L.launchBtn}
                  </button>
                </>
              ) : (
                <div>
                  <div style={{ fontSize: 40, marginBottom: 20 }}>⚙️</div>
                  <h2 style={{ fontSize: 20, fontWeight: 700, color: C.text, marginBottom: 16 }}>{L.initTitle}</h2>
                  {logs.map((line, i) => (
                    <div key={i} style={{ fontSize: 13, color: i === logs.length - 1 && line.startsWith("✅") ? C.green : i < logs.length - 1 ? C.green : C.textMid, marginBottom: 8 }}>{line}</div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
