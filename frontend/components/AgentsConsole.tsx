"use client";

import { useCallback, useEffect, useState } from "react";
import { apiUrl } from "@/lib/api-origin";
import { useAuth } from "@/hooks/useAuth";

const C = {
  bg: "#07090f", surface: "#0d1017", surfaceHigh: "#13171f",
  border: "rgba(255,255,255,0.06)", text: "#e8eaf0", textMid: "#8892a4",
  textDim: "#3d4557", accent: "#5b6ef5", green: "#2dd4a0",
  amber: "#f5a524", red: "#f25f5c", purple: "#a78bfa",
};

const ROLES = ["hunter", "outreach", "researcher", "delivery", "manager"];
const ROLE_COLOR: Record<string, string> = { hunter: C.purple, outreach: C.accent, researcher: C.green, delivery: C.amber, manager: "#f472b6" };
type AgentRow = { id: string; name: string; role: string; status: string; task_count: number; avg_score: number | null };

function rosterAutosyncKey(tenantId: string) {
  return `titan_roster_autosync_v2_${tenantId}`;
}

export function AgentsConsole() {
  const { tenantId } = useAuth();
  const [agents, setAgents] = useState<AgentRow[]>([]);
  const [rosterTarget, setRosterTarget] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [showCreate, setShowCreate] = useState(false);
  const [createStep, setCreateStep] = useState(0);
  const [selectedRole, setSelectedRole] = useState<string | null>(null);
  const [agentName, setAgentName] = useState("");
  const [workStyle, setWorkStyle] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");
  const [loadError, setLoadError] = useState("");

  const load = useCallback(async () => {
    if (!tenantId) return;
    setLoading(true);
    setLoadError("");
    try {
      const catRes = await fetch(apiUrl("/api/v1/agents/enterprise-catalog"));
      let expected = 54;
      if (catRes.ok) {
        const cat = (await catRes.json()) as { agent_count?: number };
        if (typeof cat.agent_count === "number") {
          expected = cat.agent_count;
          setRosterTarget(expected);
        }
      }

      const fetchAgentsRows = async (): Promise<AgentRow[]> => {
        const res2 = await fetch(apiUrl(`/api/v1/agents?tenant_id=${tenantId}`));
        if (!res2.ok) {
          setLoadError(`Agents list HTTP ${res2.status}`);
          return [];
        }
        const raw = (await res2.json()) as {
          id: string;
          name: string;
          role: string;
          status: string;
        }[];
        const base = raw.map((a) => ({
          id: String(a.id),
          name: a.name,
          role: a.role,
          status: a.status,
          task_count: 0,
          avg_score: null as number | null,
        }));
        const st = await fetch(apiUrl(`/api/v1/analytics/agents?tenant_id=${tenantId}`));
        if (!st.ok) return base;
        const stats: unknown = await st.json();
        if (!Array.isArray(stats)) return base;
        const byId = new Map(
          (stats as { id: string; task_count?: number; avg_score?: number | null }[]).map((s) => [
            s.id,
            { task_count: s.task_count ?? 0, avg_score: s.avg_score ?? null },
          ])
        );
        return base.map((a) => {
          const x = byId.get(a.id);
          return x ? { ...a, task_count: x.task_count, avg_score: x.avg_score } : a;
        });
      };

      let rows = await fetchAgentsRows();
      if (rows.length < expected && typeof window !== "undefined") {
        const k = rosterAutosyncKey(tenantId);
        if (!sessionStorage.getItem(k)) {
          const syn = await fetch(apiUrl(`/api/v1/tenants/${tenantId}/sync-enterprise-roster`), {
            method: "POST",
          });
          const synBody = (await syn.json().catch(() => ({}))) as { ok?: boolean; detail?: string };
          if (syn.ok && synBody.ok !== false) {
            sessionStorage.setItem(k, "1");
            rows = await fetchAgentsRows();
          } else {
            setLoadError(
              typeof synBody.detail === "string" ? synBody.detail : `Roster sync HTTP ${syn.status}`
            );
          }
        }
      }
      setAgents(rows);
    } catch {
      setLoadError("Network error");
      setAgents([]);
    } finally {
      setLoading(false);
    }
  }, [tenantId]);

  useEffect(() => { load(); }, [load]);

  const handleCreate = async () => {
    if (!tenantId || !selectedRole || !agentName) return;
    setCreating(true); setError("");
    try {
      const stylePromptMap: Record<string, string> = {
        aggressive: " Be aggressive: prioritise volume and speed.",
        precise: " Be precise: prioritise quality over quantity.",
        balanced: "",
      };
      const basePrompt = `You are a ${selectedRole} agent.${stylePromptMap[workStyle ?? "balanced"] ?? ""}`;
      const res = await fetch(apiUrl("/api/v1/agents"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tenant_id: tenantId, name: agentName, role: selectedRole, current_prompt: basePrompt }),
      });
      if (!res.ok) { const d = await res.json().catch(() => ({})); setError(d.detail ?? `HTTP ${res.status}`); }
      else { setShowCreate(false); setAgentName(""); setSelectedRole(null); setWorkStyle(null); setCreateStep(0); await load(); }
    } finally { setCreating(false); }
  };

  const statusColor: Record<string, string> = { active: C.green, testing: C.amber, retired: C.textDim };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 28 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700, color: C.text, marginBottom: 4 }}>Digital Team</h1>
          <p translate="no" style={{ fontSize: 14, color: C.textMid }}>
            {loading ? "…" : `${agents.length} agent${agents.length !== 1 ? "s" : ""}`}
            {rosterTarget != null && !loading ? ` · roster ${rosterTarget}` : ""}
          </p>
        </div>
        <button onClick={() => { setShowCreate(true); setCreateStep(0); setError(""); }} style={{ padding: "10px 20px", borderRadius: 9, border: "none", cursor: "pointer", fontWeight: 600, fontSize: 13, background: C.accent, color: "#fff" }}>
          + Hire Agent
        </button>
      </div>

      {loadError ? (
        <p style={{ color: C.red, fontSize: 13, marginBottom: 12 }}>{loadError}</p>
      ) : null}

      {loading ? <p style={{ color: C.textDim, fontSize: 13 }}>Loading...</p> : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 16 }}>
          {agents.map(a => (
            <div key={a.id} style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 14, padding: 24 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 16 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                  <div style={{ fontSize: 22, width: 44, height: 44, display: "flex", alignItems: "center", justifyContent: "center", background: `${ROLE_COLOR[a.role] ?? C.accent}18`, borderRadius: 10, border: `1px solid ${ROLE_COLOR[a.role] ?? C.accent}35` }}>
                    {{hunter:"🎯",researcher:"🔬",outreach:"✉️",delivery:"📦",manager:"🧠"}[a.role] ?? "◈"}
                  </div>
                  <div>
                    <div style={{ fontSize: 15, fontWeight: 700, color: C.text }}>{a.name}</div>
                    <div style={{ fontSize: 11, color: C.textDim, marginTop: 2 }}>{a.role}</div>
                  </div>
                </div>
                <span style={{ fontSize: 11, padding: "3px 9px", borderRadius: 20, background: `${statusColor[a.status] ?? C.textDim}18`, color: statusColor[a.status] ?? C.textDim, border: `1px solid ${statusColor[a.status] ?? C.textDim}35` }}>
                  {a.status}
                </span>
              </div>
              <div style={{ marginBottom: 10 }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 5 }}>
                  <span style={{ fontSize: 11, color: C.textDim }}>KPI score</span>
                  <span style={{ fontSize: 13, fontWeight: 700, color: (a.avg_score ?? 0) > 0.75 ? C.green : (a.avg_score ?? 0) > 0.6 ? C.amber : C.red }}>
                    {a.avg_score != null ? (a.avg_score * 100).toFixed(0) : "—"}
                  </span>
                </div>
                <div style={{ height: 5, background: C.border, borderRadius: 3, overflow: "hidden" }}>
                  <div style={{ width: `${a.avg_score != null ? a.avg_score * 100 : 0}%`, height: "100%", background: (a.avg_score ?? 0) > 0.75 ? C.green : (a.avg_score ?? 0) > 0.6 ? C.amber : C.red, borderRadius: 3 }} />
                </div>
              </div>
              <div style={{ fontSize: 12, color: C.textDim }}>📋 {a.task_count} tasks</div>
            </div>
          ))}
        </div>
      )}

      {/* Create modal */}
      {showCreate && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.75)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 100 }}>
          <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 14, padding: 36, width: 520, position: "relative" }}>
            <button onClick={() => setShowCreate(false)} style={{ position: "absolute", top: 16, right: 16, background: "transparent", border: "none", color: C.textMid, fontSize: 20, cursor: "pointer" }}>✕</button>
            <h2 style={{ fontSize: 19, fontWeight: 700, color: C.text, marginBottom: 24 }}>
              {createStep === 0 ? "Choose Role" : createStep === 1 ? "Configure" : "Work Style"}
            </h2>

            {createStep === 0 && (
              <div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 24 }}>
                  {ROLES.map(r => (
                    <div key={r} onClick={() => setSelectedRole(r)} style={{ padding: 16, borderRadius: 10, cursor: "pointer", border: `2px solid ${selectedRole === r ? C.accent : C.border}`, background: selectedRole === r ? `${C.accent}10` : C.surfaceHigh, transition: "all 0.2s" }}>
                      <div style={{ fontSize: 22, marginBottom: 6 }}>{{hunter:"🎯",outreach:"✉️",researcher:"🔬",delivery:"📦",manager:"🧠"}[r]}</div>
                      <div style={{ fontSize: 13, fontWeight: 600, color: C.text, textTransform: "capitalize" }}>{r}</div>
                    </div>
                  ))}
                </div>
                <button onClick={() => selectedRole && setCreateStep(1)} disabled={!selectedRole} style={{ width: "100%", padding: "11px", borderRadius: 9, border: "none", cursor: selectedRole ? "pointer" : "not-allowed", fontWeight: 600, fontSize: 13, background: selectedRole ? C.accent : "#2a2e3a", color: "#fff" }}>Next →</button>
              </div>
            )}

            {createStep === 1 && (
              <div>
                <div style={{ marginBottom: 16 }}>
                  <label style={{ display: "block", fontSize: 12, color: C.textMid, marginBottom: 6 }}>Agent name</label>
                  <input value={agentName} onChange={e => setAgentName(e.target.value)} placeholder={`${selectedRole}-2`} style={{ width: "100%", padding: "11px 14px", background: C.surfaceHigh, border: `1px solid ${C.border}`, borderRadius: 9, color: C.text, fontSize: 14, outline: "none" }} onFocus={e => e.target.style.borderColor = C.accent} onBlur={e => e.target.style.borderColor = C.border} />
                </div>
                <div style={{ padding: 14, background: C.surfaceHigh, borderRadius: 9, border: `1px solid ${C.border}`, marginBottom: 20, fontSize: 13, color: C.textMid }}>
                  💡 System auto-configures the default prompt for the selected role. You can edit it after creation.
                </div>
                <div style={{ display: "flex", gap: 10 }}>
                  <button onClick={() => setCreateStep(0)} style={{ flex: 1, padding: "10px", borderRadius: 9, border: `1px solid ${C.border}`, background: "transparent", color: C.textMid, fontSize: 13, cursor: "pointer" }}>← Back</button>
                  <button onClick={() => setCreateStep(2)} disabled={!agentName.trim()} style={{ flex: 2, padding: "11px", borderRadius: 9, border: "none", cursor: agentName.trim() ? "pointer" : "not-allowed", fontWeight: 600, fontSize: 13, background: agentName.trim() ? C.accent : "#2a2e3a", color: "#fff" }}>Next →</button>
                </div>
              </div>
            )}

            {createStep === 2 && (
              <div>
                <div style={{ display: "flex", flexDirection: "column", gap: 10, marginBottom: 20 }}>
                  {[
                    { id: "aggressive", icon: "⚡", label: "Aggressive", desc: "Cast wide net, prioritise volume and speed" },
                    { id: "precise", icon: "🎯", label: "Precise", desc: "Deep research, prioritise quality and conversion" },
                    { id: "balanced", icon: "⚖️", label: "Balanced", desc: "Balance quantity and quality (recommended)" },
                  ].map(s => (
                    <div key={s.id} onClick={() => setWorkStyle(s.id)} style={{ display: "flex", alignItems: "center", gap: 14, padding: "12px 16px", borderRadius: 9, cursor: "pointer", border: `2px solid ${workStyle === s.id ? C.accent : C.border}`, background: workStyle === s.id ? `${C.accent}10` : C.surfaceHigh, transition: "all 0.2s" }}>
                      <span style={{ fontSize: 20 }}>{s.icon}</span>
                      <div><div style={{ fontSize: 13, fontWeight: 600, color: C.text }}>{s.label}</div><div style={{ fontSize: 12, color: C.textMid }}>{s.desc}</div></div>
                      {workStyle === s.id && <span style={{ marginLeft: "auto", color: C.accent }}>✓</span>}
                    </div>
                  ))}
                </div>
                {error && <p style={{ fontSize: 13, color: "#f25f5c", marginBottom: 12 }}>{error}</p>}
                <div style={{ display: "flex", gap: 10 }}>
                  <button onClick={() => setCreateStep(1)} style={{ flex: 1, padding: "10px", borderRadius: 9, border: `1px solid ${C.border}`, background: "transparent", color: C.textMid, fontSize: 13, cursor: "pointer" }}>← Back</button>
                  <button onClick={handleCreate} disabled={creating || !workStyle} style={{ flex: 2, padding: "11px", borderRadius: 9, border: "none", cursor: workStyle ? "pointer" : "not-allowed", fontWeight: 600, fontSize: 13, background: C.green, color: "#07150e" }}>
                    {creating ? "…" : "✓ Hire Agent"}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
