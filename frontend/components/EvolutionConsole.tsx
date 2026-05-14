"use client";

import { useCallback, useEffect, useState } from "react";
import { apiUrl } from "@/lib/api-origin";
import { useAuth } from "@/hooks/useAuth";

export type EvolutionLabels = {
  title: string;
  overview: string;
  totalAgents: string;
  belowThreshold: string;
  activeTests: string;
  agentKpi: string;
  kpiScore: string;
  samples: string;
  successRate: string;
  status: string;
  abTests: string;
  variantA: string;
  variantB: string;
  winner: string;
  conclude: string;
  forceA: string;
  forceB: string;
  auto: string;
  trigger: string;
  triggering: string;
  refresh: string;
  noAgents: string;
  noTests: string;
  tenant: string;
  tenantPlaceholder: string;
  running: string;
  concluded: string;
  below: string;
  ok: string;
};

type AgentStat = {
  agent_id: string;
  name: string;
  role: string;
  status: string;
  kpi_score: number;
  sample_count: number;
  success_rate: number;
  below_threshold: boolean;
};

type EvolutionStatus = {
  agents: AgentStat[];
  active_ab_tests: number;
  agents_below_threshold: number;
};

type ABTest = {
  id: string;
  agent_id: string;
  variant_a_id: string;
  variant_b_id: string;
  status: string;
  winner_id: string | null;
};

const ROLE_COLOR: Record<string, string> = {
  hunter: "bg-violet-900/50 text-violet-300",
  outreach: "bg-sky-900/50 text-sky-300",
  researcher: "bg-teal-900/50 text-teal-300",
  delivery: "bg-orange-900/50 text-orange-300",
  manager: "bg-pink-900/50 text-pink-300",
};

function KpiBar({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const color = score >= 0.65 ? "bg-emerald-500" : score >= 0.4 ? "bg-amber-500" : "bg-red-500";
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-20 overflow-hidden rounded-full bg-zinc-700">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-mono text-zinc-300">{score.toFixed(2)}</span>
    </div>
  );
}

export function EvolutionConsole({ labels }: { labels: EvolutionLabels }) {
  const { tenantId } = useAuth();
  const [evStatus, setEvStatus] = useState<EvolutionStatus | null>(null);
  const [abTests, setAbTests] = useState<ABTest[]>([]);
  const [loading, setLoading] = useState(false);
  const [triggering, setTriggering] = useState<string | null>(null);
  const [concluding, setConcluding] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!tenantId) return;
    setLoading(true);
    const p = new URLSearchParams({ tenant_id: tenantId });
    try {
      const [sRes, aRes] = await Promise.all([
        fetch(apiUrl(`/api/v1/evolution/status?${p}`)),
        fetch(apiUrl("/api/v1/evolution/ab-tests")),
      ]);
      if (sRes.ok) setEvStatus(await sRes.json());
      if (aRes.ok) setAbTests(await aRes.json());
    } finally {
      setLoading(false);
    }
  }, [tenantId]);

  useEffect(() => { load(); }, [load]);

  const trigger = async (agentId: string) => {
    setTriggering(agentId);
    try {
      await fetch(apiUrl(`/api/v1/evolution/trigger/${agentId}`), { method: "POST" });
      setTimeout(load, 2000);
    } finally {
      setTriggering(null);
    }
  };

  const conclude = async (testId: string, force: string | null) => {
    setConcluding(testId);
    try {
      await fetch(apiUrl(`/api/v1/evolution/ab-tests/${testId}/conclude`), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ force_winner: force }),
      });
      await load();
    } finally {
      setConcluding(null);
    }
  };

  const stat = (label: string, value: string | number) => (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4">
      <p className="text-xs text-zinc-500 uppercase tracking-wide">{label}</p>
      <p className="mt-1 text-2xl font-bold text-white">{value}</p>
    </div>
  );

  const totalSamples = evStatus?.agents.reduce((s, a) => s + a.sample_count, 0) ?? 0;
  const COLD_START_TARGET = 20;
  const coldStartDone = totalSamples >= COLD_START_TARGET;
  const phase = totalSamples < COLD_START_TARGET ? 0 : totalSamples < 500 ? 1 : 2;
  const phaseLabels = ["Cold start (human review required)", "Growth (semi-automatic)", "Mature (fully automatic)"];

  return (
    <div className="space-y-8">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <h1 className="text-xl font-semibold text-white">{labels.title}</h1>
          <p style={{ fontSize: 14, color: "#8892a4", marginTop: 4 }}>System automatically optimises Agent prompts over time</p>
        </div>
        <button onClick={load} disabled={loading} style={{ padding: "8px 14px", borderRadius: 8, border: "1px solid rgba(255,255,255,0.06)", background: "#13171f", color: "#8892a4", fontSize: 12, cursor: "pointer" }}>
          {loading ? "…" : labels.refresh}
        </button>
      </div>

      {/* Cold-start / evolution phase banner */}
      <div style={{ padding: "16px 20px", background: coldStartDone ? "rgba(45,212,160,0.08)" : "rgba(245,165,36,0.08)", border: `1px solid ${coldStartDone ? "rgba(45,212,160,0.25)" : "rgba(245,165,36,0.25)"}`, borderRadius: 12 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
          <div>
            <span style={{ fontSize: 13, fontWeight: 600, color: coldStartDone ? "#2dd4a0" : "#f5a524" }}>
              {coldStartDone ? "🧬" : "🔒"} Current mode: {phaseLabels[phase]}
            </span>
            <span style={{ fontSize: 12, color: "#8892a4", marginLeft: 12 }}>
              {phase === 0 ? "Evolution changes need human confirmation" : "Auto-evolution active"}
            </span>
          </div>
          <span style={{ fontSize: 12, color: "#3d4557" }}>{totalSamples}/{COLD_START_TARGET} tasks to unlock auto-evolution</span>
        </div>
        <div style={{ height: 6, background: "rgba(255,255,255,0.06)", borderRadius: 3, overflow: "hidden" }}>
          <div style={{ width: `${Math.min((totalSamples / COLD_START_TARGET) * 100, 100)}%`, height: "100%", background: coldStartDone ? "#2dd4a0" : "#f5a524", borderRadius: 3, transition: "width 1s" }} />
        </div>
        {!coldStartDone && (
          <p style={{ fontSize: 12, color: "#3d4557", marginTop: 8 }}>
            Complete {COLD_START_TARGET - totalSamples} more task{COLD_START_TARGET - totalSamples !== 1 ? "s" : ""} to unlock automatic prompt evolution.
          </p>
        )}
      </div>

      {/* overview cards */}
      {evStatus && (
        <div className="grid grid-cols-3 gap-3">
          {stat(labels.totalAgents, evStatus.agents.length)}
          {stat(labels.belowThreshold, evStatus.agents_below_threshold)}
          {stat(labels.activeTests, evStatus.active_ab_tests)}
        </div>
      )}

      {/* agent KPI table */}
      <section>
        <h2 className="mb-3 text-sm font-semibold text-zinc-300">{labels.agentKpi}</h2>
        {!evStatus || evStatus.agents.length === 0 ? (
          <p className="text-xs text-zinc-500">{labels.noAgents}</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-zinc-800 text-zinc-500">
                  <th className="pb-2 pr-4 text-left font-medium">Agent</th>
                  <th className="pb-2 pr-4 text-left font-medium">{labels.kpiScore}</th>
                  <th className="pb-2 pr-4 text-right font-medium">{labels.successRate}</th>
                  <th className="pb-2 pr-4 text-right font-medium">{labels.samples}</th>
                  <th className="pb-2 pr-4 text-left font-medium">{labels.status}</th>
                  <th className="pb-2 text-right font-medium">{labels.trigger}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800/60">
                {evStatus.agents.map((a) => (
                  <tr key={a.agent_id} className="hover:bg-zinc-900/30">
                    <td className="py-2 pr-4">
                      <div className="flex items-center gap-2">
                        <span className={`rounded px-1.5 py-0.5 text-[10px] font-medium ${ROLE_COLOR[a.role] ?? "bg-zinc-800 text-zinc-300"}`}>
                          {a.role}
                        </span>
                        <span className="text-zinc-200">{a.name}</span>
                      </div>
                    </td>
                    <td className="py-2 pr-4">
                      <KpiBar score={a.kpi_score} />
                    </td>
                    <td className="py-2 pr-4 text-right text-zinc-400">
                      {(a.success_rate * 100).toFixed(1)}%
                    </td>
                    <td className="py-2 pr-4 text-right text-zinc-400">{a.sample_count}</td>
                    <td className="py-2 pr-4">
                      <span className={`font-medium ${
                        a.below_threshold ? "text-red-400" :
                        a.status === "testing" ? "text-amber-400" : "text-emerald-400"
                      }`}>
                        {a.below_threshold ? labels.below : labels.ok}
                        {a.status === "testing" && " (A/B)"}
                      </span>
                    </td>
                    <td className="py-2 text-right">
                      <button
                        onClick={() => trigger(a.agent_id)}
                        disabled={triggering === a.agent_id}
                        className="rounded bg-violet-700 px-2 py-0.5 text-[10px] font-medium text-white hover:bg-violet-600 disabled:opacity-50"
                      >
                        {triggering === a.agent_id ? "…" : labels.trigger}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* A/B test board */}
      <section>
        <h2 className="mb-3 text-sm font-semibold text-zinc-300">{labels.abTests}</h2>
        {abTests.length === 0 ? (
          <p className="text-xs text-zinc-500">{labels.noTests}</p>
        ) : (
          <ul className="space-y-3">
            {abTests.map((t) => (
              <li
                key={t.id}
                className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-4"
              >
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="space-y-1 text-xs">
                    <div className="flex items-center gap-2">
                      <span className={`rounded px-1.5 py-0.5 text-[10px] font-medium ${
                        t.status === "running" ? "bg-sky-900/50 text-sky-300" : "bg-zinc-800 text-zinc-400"
                      }`}>
                        {t.status === "running" ? labels.running : labels.concluded}
                      </span>
                      <span className="font-mono text-zinc-500">{t.id.slice(0, 8)}…</span>
                    </div>
                    <p className="text-zinc-500">
                      A: <span className="font-mono text-zinc-300">{t.variant_a_id.slice(0, 8)}</span>
                      &nbsp;vs B: <span className="font-mono text-zinc-300">{t.variant_b_id.slice(0, 8)}</span>
                      {t.winner_id && (
                        <span className="ml-2 text-emerald-400">
                          ✓ {labels.winner}: {t.winner_id === t.variant_b_id ? "B" : "A"}
                        </span>
                      )}
                    </p>
                  </div>

                  {t.status === "running" && (
                    <div className="flex gap-2">
                      <button
                        onClick={() => conclude(t.id, "a")}
                        disabled={concluding === t.id}
                        className="rounded bg-zinc-700 px-2 py-1 text-[10px] text-zinc-300 hover:bg-zinc-600 disabled:opacity-50"
                      >
                        {labels.forceA}
                      </button>
                      <button
                        onClick={() => conclude(t.id, "b")}
                        disabled={concluding === t.id}
                        className="rounded bg-zinc-700 px-2 py-1 text-[10px] text-zinc-300 hover:bg-zinc-600 disabled:opacity-50"
                      >
                        {labels.forceB}
                      </button>
                      <button
                        onClick={() => conclude(t.id, null)}
                        disabled={concluding === t.id}
                        className="rounded bg-emerald-700 px-2 py-1 text-[10px] font-medium text-white hover:bg-emerald-600 disabled:opacity-50"
                      >
                        {concluding === t.id ? "…" : labels.auto}
                      </button>
                    </div>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
