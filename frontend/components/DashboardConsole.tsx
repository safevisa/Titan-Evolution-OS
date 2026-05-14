"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { apiUrl } from "@/lib/api-origin";
import { useAuth } from "@/hooks/useAuth";
import Link from "next/link";
import { useParams } from "next/navigation";

const C = {
  bg: "#07090f", surface: "#0d1017", surfaceHigh: "#13171f",
  border: "rgba(255,255,255,0.06)", text: "#e8eaf0", textMid: "#8892a4",
  textDim: "#3d4557", accent: "#5b6ef5", accentGlow: "rgba(91,110,245,0.2)",
  green: "#2dd4a0", amber: "#f5a524", red: "#f25f5c", purple: "#a78bfa",
};

type Summary = {
  total_tasks: number; done_tasks: number; success_rate: number | null;
  total_tokens: number; active_agents: number; total_agents: number;
};
type AgentRow = { id: string; name: string; role: string; status: string; task_count: number; avg_score: number | null };
type TaskRow = { id: string; type: string; status: string; token_used: number; duration_ms: number | null; created_at: string };

const STATUS_COLOR: Record<string, string> = { done: C.green, running: C.accent, failed: C.red, pending: C.amber };
const ROLE_ICON: Record<string, string> = { hunter: "🎯", researcher: "🔬", outreach: "✉️", delivery: "📦", manager: "🧠" };

function StatCard({ label, value, sub, color = C.accent, icon }: { label: string; value: string | number; sub?: string; color?: string; icon?: string }) {
  return (
    <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 14, padding: "20px 24px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <div style={{ fontSize: 11, color: C.textMid, letterSpacing: "0.1em", marginBottom: 8, textTransform: "uppercase" }}>{label}</div>
          <div style={{ fontSize: 32, fontWeight: 700, color, fontVariantNumeric: "tabular-nums" }}>{value}</div>
          {sub && <div style={{ fontSize: 12, color: C.textDim, marginTop: 4 }}>{sub}</div>}
        </div>
        {icon && <div style={{ fontSize: 24, opacity: 0.6 }}>{icon}</div>}
      </div>
    </div>
  );
}

export function DashboardConsole() {
  const { tenantId, user } = useAuth();
  const params = useParams();
  const locale = (params?.locale as string) ?? "en";

  const [summary, setSummary] = useState<Summary | null>(null);
  const [agents, setAgents] = useState<AgentRow[]>([]);
  const [tasks, setTasks] = useState<TaskRow[]>([]);
  const [loading, setLoading] = useState(false);
  const logRef = useRef<HTMLDivElement>(null);

  // auto-scroll log
  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [tasks]);

  const load = useCallback(async () => {
    if (!tenantId) return;
    setLoading(true);
    try {
      const p = new URLSearchParams({ tenant_id: tenantId });
      const [sRes, aRes, tRes] = await Promise.all([
        fetch(apiUrl(`/api/v1/analytics/summary?${p}`)),
        fetch(apiUrl(`/api/v1/analytics/agents?${p}`)),
        fetch(apiUrl(`/api/v1/tasks?${p}`)),
      ]);
      if (sRes.ok) setSummary(await sRes.json());
      if (aRes.ok) setAgents(await aRes.json());
      if (tRes.ok) setTasks((await tRes.json()).slice(0, 10));
    } finally { setLoading(false); }
  }, [tenantId]);

  useEffect(() => { load(); }, [load]);

  // auto-refresh every 10s if running tasks
  useEffect(() => {
    const hasRunning = tasks.some(t => t.status === "running");
    if (!hasRunning) return;
    const id = setInterval(load, 10000);
    return () => clearInterval(id);
  }, [tasks, load]);

  const pct = (n: number | null) => n == null ? "—" : `${(n * 100).toFixed(1)}%`;
  const greeting = user?.name?.split(" ")[0] ?? user?.email?.split("@")[0] ?? "there";

  // Empty state — no agents yet
  if (!loading && summary?.total_agents === 0) {
    return (
      <div>
        <div style={{ marginBottom: 32 }}>
          <h1 style={{ fontSize: 28, fontWeight: 700, color: C.text, marginBottom: 6 }}>
            Welcome, {greeting} 👋
          </h1>
          <p style={{ fontSize: 15, color: C.textMid }}>Your digital workforce is ready to be set up.</p>
        </div>
        <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 18, padding: 48, textAlign: "center", maxWidth: 560 }}>
          <div style={{ fontSize: 56, marginBottom: 20 }}>🤖</div>
          <h2 style={{ fontSize: 20, fontWeight: 700, color: C.text, marginBottom: 10 }}>No agents yet</h2>
          <p style={{ fontSize: 14, color: C.textMid, marginBottom: 32, lineHeight: 1.6 }}>
            Start by creating your first Agent. Each agent has a role, a default prompt,
            and will learn from every task it completes.
          </p>
          <div style={{ display: "flex", gap: 12, justifyContent: "center", flexWrap: "wrap" }}>
            <Link href={`/${locale}/agents`} style={{ padding: "13px 28px", borderRadius: 10, background: C.accent, color: "#fff", textDecoration: "none", fontSize: 14, fontWeight: 600 }}>
              + Create your first Agent
            </Link>
            <Link href={`/${locale}/onboarding`} style={{ padding: "13px 28px", borderRadius: 10, border: `1px solid ${C.border}`, background: C.surfaceHigh, color: C.textMid, textDecoration: "none", fontSize: 14, fontWeight: 600 }}>
              Run setup wizard
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 28 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700, color: C.text, marginBottom: 4 }}>
            {greeting ? `Welcome back, ${greeting}` : "Today's Overview"}
          </h1>
          <p style={{ fontSize: 14, color: C.textMid }}>
            {summary?.active_agents
              ? `${summary.active_agents} agent${summary.active_agents !== 1 ? "s" : ""} active · ${new Date().toLocaleDateString("en", { weekday: "long", month: "long", day: "numeric" })}`
              : new Date().toLocaleDateString("en", { weekday: "long", month: "long", day: "numeric" })}
          </p>
        </div>
        <button onClick={load} disabled={loading} style={{ padding: "8px 16px", borderRadius: 8, border: `1px solid ${C.border}`, background: C.surfaceHigh, color: C.textMid, fontSize: 12, cursor: "pointer" }}>
          {loading ? "…" : "↻ Refresh"}
        </button>
      </div>

      {/* Stats */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16, marginBottom: 24 }}>
        <StatCard label="Today's Tasks" value={summary?.total_tasks ?? "—"} color={C.accent} icon="⊞" />
        <StatCard label="Success Rate" value={pct(summary?.success_rate ?? null)} color={C.green} icon="◎" />
        <StatCard label="Active Agents" value={summary?.active_agents ?? "—"} color={C.purple} icon="◈" />
        <StatCard label="Tokens Used" value={summary ? summary.total_tokens.toLocaleString() : "—"} color={C.amber} icon="⚡" />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 340px", gap: 20 }}>
        {/* Live log */}
        <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 14, padding: 24 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 18 }}>
            <h3 style={{ fontSize: 15, fontWeight: 600, color: C.text }}>Task stream</h3>
            {tasks.some(t => t.status === "running") && (
              <span style={{ fontSize: 11, padding: "3px 9px", borderRadius: 20, background: `${C.green}18`, color: C.green, border: `1px solid ${C.green}35` }}>● Live</span>
            )}
          </div>
          <div ref={logRef} style={{ maxHeight: 300, overflowY: "auto" }}>
            {tasks.length === 0 ? (
              <div style={{ textAlign: "center", padding: "40px 0", color: C.textDim, fontSize: 13 }}>
                No tasks yet &mdash;{" "}
                <Link href={`/${locale}/tasks`} style={{ color: C.accent, textDecoration: "none" }}>create and run one</Link>
              </div>
            ) : tasks.map((t) => (
              <div key={t.id} style={{ display: "flex", gap: 12, padding: "10px 0", borderBottom: `1px solid ${C.border}` }}>
                <span style={{ fontSize: 11, color: C.textDim, flexShrink: 0, marginTop: 1, fontVariantNumeric: "tabular-nums", width: 42 }}>
                  {new Date(t.created_at).toLocaleTimeString("en", { hour: "2-digit", minute: "2-digit" })}
                </span>
                <span style={{ fontSize: 14, flexShrink: 0 }}>
                  {{ done: "✅", running: "⏳", failed: "❌", pending: "⏸" }[t.status] ?? "•"}
                </span>
                <span style={{ fontSize: 13, color: STATUS_COLOR[t.status] ?? C.textMid, lineHeight: 1.5, flex: 1 }}>
                  {t.type}
                  {t.duration_ms != null && <span style={{ color: C.textDim, fontSize: 11, marginLeft: 8 }}>{t.duration_ms}ms</span>}
                </span>
              </div>
            ))}
          </div>
          {tasks.length > 0 && (
            <div style={{ marginTop: 14, textAlign: "right" }}>
              <Link href={`/${locale}/tasks`} style={{ fontSize: 12, color: C.accent, textDecoration: "none" }}>View all tasks →</Link>
            </div>
          )}
        </div>

        {/* Agent status */}
        <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 14, padding: 24 }}>
          <h3 style={{ fontSize: 15, fontWeight: 600, color: C.text, marginBottom: 18 }}>Agent Status</h3>
          {agents.length === 0 ? (
            <div style={{ textAlign: "center", padding: "20px 0" }}>
              <p style={{ fontSize: 13, color: C.textDim, marginBottom: 14 }}>No agents yet</p>
              <Link href={`/${locale}/agents`} style={{ fontSize: 13, color: C.accent, textDecoration: "none", padding: "8px 16px", border: `1px solid ${C.accent}35`, borderRadius: 8 }}>
                + Create Agent
              </Link>
            </div>
          ) : (
            <>
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {agents.slice(0, 4).map(a => (
                  <div key={a.id} style={{ padding: "12px 14px", borderRadius: 10, background: C.surfaceHigh, border: `1px solid ${C.border}` }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
                      <span style={{ fontSize: 18 }}>{ROLE_ICON[a.role] ?? "◈"}</span>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontSize: 13, fontWeight: 600, color: C.text }}>{a.name}</div>
                        <div style={{ fontSize: 11, color: C.textDim }}>{a.role}</div>
                      </div>
                      <span style={{ fontSize: 11, padding: "2px 8px", borderRadius: 20, background: `${a.status === "active" ? C.green : C.textDim}18`, color: a.status === "active" ? C.green : C.textDim, border: `1px solid ${a.status === "active" ? C.green : C.textDim}35` }}>
                        {a.status === "active" ? "active" : a.status}
                      </span>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <div style={{ flex: 1, height: 4, background: C.border, borderRadius: 2, overflow: "hidden" }}>
                        <div style={{ width: `${a.avg_score != null ? a.avg_score * 100 : 0}%`, height: "100%", background: (a.avg_score ?? 0) > 0.75 ? C.green : (a.avg_score ?? 0) > 0.6 ? C.amber : a.task_count > 0 ? C.red : C.border, borderRadius: 2, transition: "width 1s" }} />
                      </div>
                      <span style={{ fontSize: 11, color: C.textMid, fontVariantNumeric: "tabular-nums", width: 28 }}>
                        {a.avg_score != null ? `${(a.avg_score * 100).toFixed(0)}` : "—"}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
              <Link href={`/${locale}/agents`} style={{ display: "block", marginTop: 14, padding: "8px 0", textAlign: "center", borderRadius: 8, border: `1px solid ${C.border}`, background: "transparent", color: C.textMid, textDecoration: "none", fontSize: 13 }}>
                Manage team →
              </Link>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
