"use client";

import { useCallback, useEffect, useState } from "react";
import { apiUrl } from "@/lib/api-origin";
import { useAuth } from "@/hooks/useAuth";

export type BillingLabels = {
  title: string;
  tenantId: string;
  tenantPlaceholder: string;
  load: string;
  planLabel: string;
  limitsLabel: string;
  maxAgents: string;
  maxTasks: string;
  currentMonth: string;
  tasksUsed: string;
  tokensUsed: string;
  agentsPeak: string;
  costUsd: string;
  agentUsage: string;
  taskUsage: string;
  historyLabel: string;
  period: string;
  exportTitle: string;
  exportTasks: string;
  exportContacts: string;
  exportPerformance: string;
  onboardingTitle: string;
  progress: string;
  plans: string;
  noData: string;
};

type BillingSummary = {
  tenant_id: string;
  plan: string;
  limits: { max_agents: number; max_tasks_per_month: number };
  current_month: { tasks_count: number; tokens_used: number; agents_peak: number; cost_usd: number; period?: string };
  active_agents: number;
  task_usage_pct: number;
  agent_usage_pct: number;
  history: Array<{ period: string; tasks_count: number; tokens_used: number; cost_usd: number }>;
};

type OnboardingStep = { step: number; label: string; done: boolean; detail?: string };
type Onboarding = { progress: string; complete: boolean; steps: OnboardingStep[] };

type PlanInfo = { plan: string; max_agents: number; max_tasks_per_month: number };

function UsageBar({ pct, label }: { pct: number; label: string }) {
  const color = pct >= 90 ? "bg-red-500" : pct >= 70 ? "bg-amber-500" : "bg-emerald-500";
  return (
    <div>
      <div className="mb-1 flex justify-between text-xs text-zinc-400">
        <span>{label}</span><span>{pct}%</span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-zinc-700">
        <div className={`h-full rounded-full ${color} transition-all`} style={{ width: `${Math.min(pct, 100)}%` }} />
      </div>
    </div>
  );
}

export function BillingConsole({ labels }: { labels: BillingLabels }) {
  const { tenantId } = useAuth();
  const [summary, setSummary] = useState<BillingSummary | null>(null);
  const [onboarding, setOnboarding] = useState<Onboarding | null>(null);
  const [plans, setPlans] = useState<PlanInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Load plans once
  useEffect(() => {
    fetch(apiUrl("/api/v1/billing/plans"))
      .then((r) => r.ok ? r.json() : [])
      .then(setPlans)
      .catch(() => {});
  }, []);

  const load = useCallback(async () => {
    if (!tenantId) return;
    setLoading(true);
    setError("");
    try {
      const [sRes, oRes] = await Promise.all([
        fetch(apiUrl(`/api/v1/billing/summary/${tenantId.trim()}`)),
        fetch(apiUrl(`/api/v1/billing/onboarding/${tenantId.trim()}`)),
      ]);
      if (sRes.ok) setSummary(await sRes.json());
      else setError(`HTTP ${sRes.status}`);
      if (oRes.ok) setOnboarding(await oRes.json());
    } finally {
      setLoading(false);
    }
  }, [tenantId]);

  const exportCSV = (type: string) => {
    if (!tenantId) return;
    window.open(apiUrl(`/api/v1/billing/export/${type}/${tenantId}`), "_blank");
  };

  return (
    <div className="space-y-10">
      <h1 className="text-xl font-semibold text-white">{labels.title}</h1>

      <div className="flex">
        <button onClick={load} disabled={loading || !tenantId} className="rounded-md bg-sky-600 px-4 py-2 text-xs font-medium text-white hover:bg-sky-500 disabled:opacity-50">
          {loading ? "…" : labels.load}
        </button>
      </div>
      {error && <p className="text-xs text-red-400">{error}</p>}

      {summary && (
        <>
          {/* current month stats */}
          <section className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold text-zinc-300">{labels.currentMonth}</h2>
              <span className={`rounded px-2 py-0.5 text-xs font-semibold ${
                summary.plan === "enterprise" ? "bg-amber-800/60 text-amber-300" :
                summary.plan === "growth" ? "bg-sky-800/60 text-sky-300" :
                "bg-zinc-800 text-zinc-400"
              }`}>{summary.plan}</span>
            </div>

            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              {[
                [labels.tasksUsed, summary.current_month.tasks_count],
                [labels.tokensUsed, summary.current_month.tokens_used.toLocaleString()],
                [labels.agentsPeak, summary.current_month.agents_peak],
                [labels.costUsd, `$${summary.current_month.cost_usd.toFixed(4)}`],
              ].map(([l, v]) => (
                <div key={l as string} className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-3">
                  <p className="text-[10px] text-zinc-500 uppercase tracking-wide">{l}</p>
                  <p className="mt-0.5 text-lg font-bold text-white">{v}</p>
                </div>
              ))}
            </div>

            <div className="space-y-3">
              <UsageBar pct={summary.task_usage_pct} label={`${labels.tasksUsed} (${summary.current_month.tasks_count}/${summary.limits.max_tasks_per_month})`} />
              <UsageBar pct={summary.agent_usage_pct} label={`${labels.agentsPeak} (${summary.active_agents}/${summary.limits.max_agents})`} />
            </div>
          </section>

          {/* usage history */}
          {summary.history.length > 0 && (
            <section>
              <h2 className="mb-3 text-sm font-semibold text-zinc-300">{labels.historyLabel}</h2>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-zinc-800 text-zinc-500">
                      {[labels.period, labels.tasksUsed, labels.tokensUsed, labels.costUsd].map((h) => (
                        <th key={h} className="pb-2 pr-6 text-left font-medium">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-800/60">
                    {summary.history.map((row) => (
                      <tr key={row.period} className="hover:bg-zinc-900/30">
                        <td className="py-2 pr-6 font-mono text-zinc-300">{row.period}</td>
                        <td className="py-2 pr-6 text-zinc-400">{row.tasks_count}</td>
                        <td className="py-2 pr-6 text-zinc-400">{row.tokens_used.toLocaleString()}</td>
                        <td className="py-2 pr-6 text-zinc-400">${row.cost_usd.toFixed(4)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}

          {/* data export */}
          <section className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5 space-y-3">
            <h2 className="text-sm font-semibold text-zinc-300">{labels.exportTitle}</h2>
            <div className="flex flex-wrap gap-3">
              {[
                ["tasks", labels.exportTasks],
                ["contacts", labels.exportContacts],
                ["performance", labels.exportPerformance],
              ].map(([type, lbl]) => (
                <button
                  key={type}
                  onClick={() => exportCSV(type)}
                  className="rounded-md border border-zinc-700 bg-zinc-800 px-3 py-2 text-xs text-zinc-300 hover:bg-zinc-700 hover:text-white"
                >
                  ↓ {lbl}
                </button>
              ))}
            </div>
          </section>
        </>
      )}

      {/* onboarding checklist */}
      {onboarding && (
        <section className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5 space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-zinc-300">{labels.onboardingTitle}</h2>
            <span className={`text-xs font-medium ${onboarding.complete ? "text-emerald-400" : "text-zinc-400"}`}>
              {labels.progress}: {onboarding.progress}
            </span>
          </div>
          <ul className="space-y-2">
            {onboarding.steps.map((s) => (
              <li key={s.step} className="flex items-start gap-3 text-xs">
                <span className={`mt-0.5 text-base leading-none ${s.done ? "text-emerald-400" : "text-zinc-600"}`}>
                  {s.done ? "✓" : "○"}
                </span>
                <div>
                  <span className={s.done ? "text-zinc-200" : "text-zinc-500"}>{s.label}</span>
                  {s.detail && <span className="ml-2 text-zinc-600">— {s.detail}</span>}
                </div>
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* plan comparison */}
      {plans.length > 0 && (
        <section>
          <h2 className="mb-3 text-sm font-semibold text-zinc-300">{labels.plans}</h2>
          <div className="grid gap-3 sm:grid-cols-3">
            {plans.map((p) => (
              <div key={p.plan} className={`rounded-xl border p-4 text-xs ${
                p.plan === "enterprise" ? "border-amber-800/50 bg-amber-900/10" :
                p.plan === "growth" ? "border-sky-800/50 bg-sky-900/10" :
                "border-zinc-800 bg-zinc-900/40"
              }`}>
                <p className="mb-2 text-sm font-semibold capitalize text-white">{p.plan}</p>
                <p className="text-zinc-400">{labels.maxAgents}: <b className="text-zinc-200">{p.max_agents}</b></p>
                <p className="text-zinc-400">{labels.maxTasks}: <b className="text-zinc-200">{p.max_tasks_per_month.toLocaleString()}</b>/mo</p>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
