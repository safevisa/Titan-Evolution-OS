"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { apiUrl } from "@/lib/api-origin";
import { useAuth } from "@/hooks/useAuth";

export type SettingsLabels = {
  title: string;
  newTenantTitle: string;
  tenantName: string;
  selectPlugin: string;
  selectPlan: string;
  autoProvision: string;
  autoProvisionHint: string;
  create: string;
  creating: string;
  existingTitle: string;
  yourWorkspace: string;
  noTenants: string;
  plugin: string;
  plan: string;
  refresh: string;
  pluginsTitle: string;
  requiredTools: string;
  agentRoles: string;
  quotaTitle: string;
  tokenUsage: string;
  checkUsage: string;
  tenantId: string;
  copy: string;
  copied: string;
  searchPlugins: string;
  openIntegrations: string;
};

type TenantDetail = {
  id: string;
  name: string;
  industry_plugin: string;
  plan: string;
  agents_created?: number;
  skills_seeded?: number;
};

type PluginInfo = {
  plugin_id: string;
  display_name: string;
  name_zh?: string;
  icon?: string;
  catalog?: boolean;
  required_tools: string[];
  agent_roles: string[];
};

const PLANS = ["starter", "growth", "enterprise"];

const PLAN_COLOR: Record<string, string> = {
  starter: "text-zinc-400",
  growth: "text-sky-400",
  enterprise: "text-amber-400",
};

export function SettingsConsole({
  labels,
  locale = "en",
}: {
  labels: SettingsLabels;
  locale?: string;
}) {
  const { tenantId: currentTenantId, isPlatformAdmin } = useAuth();
  const [tenants, setTenants] = useState<TenantDetail[]>([]);
  const [plugins, setPlugins] = useState<PluginInfo[]>([]);
  const [loading, setLoading] = useState(false);

  // create form
  const [name, setName] = useState("");
  const [pluginId, setPluginId] = useState("payment_fintech");
  const [plan, setPlan] = useState("starter");
  const [autoProvision, setAutoProvision] = useState(true);
  const [creating, setCreating] = useState(false);
  const [createResult, setCreateResult] = useState<TenantDetail | null>(null);
  const [error, setError] = useState("");

  // quota
  const [quotaTenantId, setQuotaTenantId] = useState(currentTenantId ?? "");
  const [quotaUsage, setQuotaUsage] = useState<number | null>(null);
  const [checkingQuota, setCheckingQuota] = useState(false);

  // clipboard
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const [pluginQ, setPluginQ] = useState("");

  const filteredPlugins = useMemo(() => {
    const s = pluginQ.trim().toLowerCase();
    if (!s) return plugins;
    return plugins.filter(
      (p) =>
        p.display_name.toLowerCase().includes(s) ||
        (p.name_zh ?? "").toLowerCase().includes(s) ||
        p.plugin_id.toLowerCase().includes(s),
    );
  }, [plugins, pluginQ]);

  const rolePreview = (roles: string[]) => {
    if (!roles?.length) return "—";
    if (roles.length <= 8) return roles.join(", ");
    return `${roles.slice(0, 8).join(", ")}… (+${roles.length - 8})`;
  };

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const tenantRequest = isPlatformAdmin
        ? fetch(apiUrl("/api/v1/tenants"))
        : currentTenantId
          ? fetch(apiUrl(`/api/v1/tenants/${currentTenantId}`))
          : Promise.resolve(null);
      const [tRes, pRes] = await Promise.all([
        tenantRequest,
        fetch(apiUrl("/api/v1/tenants/plugins/list")),
      ]);
      if (tRes?.ok) {
        const tenantData = await tRes.json();
        setTenants(Array.isArray(tenantData) ? tenantData : [tenantData]);
      }
      if (pRes.ok) {
        const pData: PluginInfo[] = await pRes.json();
        setPlugins(pData);
        if (pData.length > 0) setPluginId(prev => prev || pData[0].plugin_id);
      }
    } finally {
      setLoading(false);
    }
  }, [currentTenantId, isPlatformAdmin]);

  useEffect(() => { load(); }, [load]);

  const handleCreate = async () => {
    if (!name.trim()) return;
    setCreating(true);
    setError("");
    setCreateResult(null);
    try {
      const res = await fetch(apiUrl("/api/v1/tenants"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: name.trim(),
          industry_plugin: pluginId,
          plan,
          auto_provision: autoProvision,
        }),
      });
      if (!res.ok) {
        const d = await res.json().catch(() => ({}));
        setError(d.detail ?? `HTTP ${res.status}`);
      } else {
        const data = await res.json();
        setCreateResult(data);
        setName("");
        await load();
      }
    } finally {
      setCreating(false);
    }
  };

  const copy = (id: string) => {
    navigator.clipboard.writeText(id).catch(() => {});
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const checkQuota = async () => {
    if (!quotaTenantId.trim()) return;
    setCheckingQuota(true);
    try {
      const res = await fetch(apiUrl(`/api/v1/tenants/${quotaTenantId.trim()}/quota`));
      if (res.ok) {
        const d = await res.json();
        setQuotaUsage(d.tokens_used_this_minute ?? 0);
      }
    } finally {
      setCheckingQuota(false);
    }
  };

  const selectedPlugin = plugins.find((p) => p.plugin_id === pluginId);

  return (
    <div className="space-y-10">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-xl font-semibold text-white">{labels.title}</h1>
        <Link
          href={`/${locale}/settings/integrations`}
          className="rounded-md border border-zinc-700 px-3 py-1.5 text-xs text-sky-400 hover:bg-zinc-800"
        >
          {labels.openIntegrations}
        </Link>
      </div>

      {/* create tenant */}
      {isPlatformAdmin && (
      <section className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5 space-y-4">
        <h2 className="text-sm font-semibold text-zinc-300">{labels.newTenantTitle}</h2>

        <div className="grid gap-3 sm:grid-cols-3">
          <div>
            <label className="mb-1 block text-xs text-zinc-500">{labels.tenantName}</label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder={labels.tenantName}
              className="w-full rounded-md border border-zinc-700 bg-zinc-800 px-3 py-2 text-xs text-zinc-200 placeholder-zinc-600 focus:outline-none focus:ring-1 focus:ring-sky-500"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs text-zinc-500">{labels.selectPlugin}</label>
            <input
              value={pluginQ}
              onChange={(e) => setPluginQ(e.target.value)}
              placeholder={labels.searchPlugins}
              className="mb-2 w-full rounded-md border border-zinc-700 bg-zinc-800 px-3 py-1.5 text-xs text-zinc-200 placeholder-zinc-600 focus:outline-none focus:ring-1 focus:ring-sky-500"
            />
            <select
              value={pluginId}
              onChange={(e) => setPluginId(e.target.value)}
              title={labels.selectPlugin}
              className="w-full rounded-md border border-zinc-700 bg-zinc-800 px-3 py-2 text-xs text-zinc-200 focus:outline-none focus:ring-1 focus:ring-sky-500"
            >
              {filteredPlugins.map((p) => (
                <option key={p.plugin_id} value={p.plugin_id}>
                  {(p.icon ? `${p.icon} ` : "") + p.display_name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-xs text-zinc-500">{labels.selectPlan}</label>
            <select
              value={plan}
              onChange={(e) => setPlan(e.target.value)}
              title={labels.selectPlan}
              className="w-full rounded-md border border-zinc-700 bg-zinc-800 px-3 py-2 text-xs text-zinc-200 focus:outline-none focus:ring-1 focus:ring-sky-500"
            >
              {PLANS.map((p) => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>
        </div>

        {/* plugin preview */}
        {selectedPlugin && (
          <div className="rounded-lg border border-zinc-800 bg-zinc-900/40 p-3 text-xs text-zinc-500">
            <span className="text-zinc-300 font-medium">{selectedPlugin.display_name}</span>
            {" · "}{labels.agentRoles}: <span className="text-zinc-300">{rolePreview(selectedPlugin.agent_roles)}</span>
            {" · "}{labels.requiredTools}: <span className="text-zinc-300">{(selectedPlugin.required_tools ?? []).join(", ") || "—"}</span>
          </div>
        )}

        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={autoProvision}
            onChange={(e) => setAutoProvision(e.target.checked)}
            className="h-3.5 w-3.5 rounded border-zinc-600 bg-zinc-800 accent-sky-500"
          />
          <span className="text-xs text-zinc-400">{labels.autoProvision}</span>
          <span className="text-xs text-zinc-600">— {labels.autoProvisionHint}</span>
        </label>

        {error && <p className="text-xs text-red-400">{error}</p>}

        {createResult && (
          <div className="rounded-lg border border-emerald-800/50 bg-emerald-900/20 p-3 text-xs text-emerald-300">
            ✓ Created: <b>{createResult.name}</b> — ID:{" "}
            <span className="font-mono">{createResult.id}</span>
            {createResult.agents_created !== undefined && (
              <> · {createResult.agents_created} agents, {createResult.skills_seeded} skills seeded</>
            )}
          </div>
        )}

        <button
          onClick={handleCreate}
          disabled={creating || !name.trim()}
          className="rounded-md bg-sky-600 px-4 py-2 text-xs font-medium text-white hover:bg-sky-500 disabled:opacity-50"
        >
          {creating ? labels.creating : labels.create}
        </button>
      </section>
      )}

      {/* tenant list */}
      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-zinc-300">
            {isPlatformAdmin ? labels.existingTitle : labels.yourWorkspace}
          </h2>
          <button
            onClick={load}
            disabled={loading}
            className="rounded-md bg-zinc-800 px-3 py-1.5 text-xs text-zinc-300 hover:bg-zinc-700 disabled:opacity-50"
          >
            {loading ? "…" : labels.refresh}
          </button>
        </div>
        {tenants.length === 0 ? (
          <p className="text-xs text-zinc-500">{labels.noTenants}</p>
        ) : (
          <ul className="space-y-2">
            {tenants.map((t) => (
              <li
                key={t.id}
                className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-zinc-800 bg-zinc-900/40 px-4 py-3 text-xs"
              >
                <div>
                  <p className="font-medium text-zinc-100">{t.name}</p>
                  <p className="mt-0.5 font-mono text-[10px] text-zinc-600">{t.id}</p>
                </div>
                <div className="flex items-center gap-4 text-zinc-500">
                  <span>{labels.plugin}: <b className="text-zinc-300">{t.industry_plugin}</b></span>
                  <span className={`font-medium ${PLAN_COLOR[t.plan] ?? "text-zinc-400"}`}>{t.plan}</span>
                  <button
                    onClick={() => copy(t.id)}
                    className="rounded bg-zinc-800 px-2 py-0.5 text-[10px] text-zinc-400 hover:bg-zinc-700"
                  >
                    {copiedId === t.id ? labels.copied : labels.copy}
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* available plugins */}
      <section>
        <h2 className="mb-3 text-sm font-semibold text-zinc-300">{labels.pluginsTitle}</h2>
        <div className="max-h-96 overflow-y-auto grid gap-3 sm:grid-cols-2">
          {filteredPlugins.map((p) => (
            <div key={p.plugin_id} className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-4 text-xs">
              <p className="font-semibold text-zinc-100">{(p.icon ? `${p.icon} ` : "") + p.display_name}</p>
              <p className="mt-1 text-zinc-500">{labels.agentRoles}: <span className="text-zinc-300">{rolePreview(p.agent_roles)}</span></p>
              <p className="text-zinc-500">{labels.requiredTools}: <span className="text-zinc-300">{(p.required_tools ?? []).join(", ") || "—"}</span></p>
            </div>
          ))}
        </div>
      </section>

      {/* quota checker */}
      <section className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5 space-y-3">
        <h2 className="text-sm font-semibold text-zinc-300">{labels.quotaTitle}</h2>
        <div className="flex gap-3">
          <input
            value={quotaTenantId}
            onChange={(e) => setQuotaTenantId(e.target.value)}
            placeholder={labels.tenantId}
            className="flex-1 rounded-md border border-zinc-700 bg-zinc-800 px-3 py-1.5 text-xs text-zinc-300 placeholder-zinc-600 focus:outline-none focus:ring-1 focus:ring-sky-500"
          />
          <button
            onClick={checkQuota}
            disabled={checkingQuota || !quotaTenantId.trim()}
            className="rounded-md bg-zinc-700 px-3 py-1.5 text-xs text-zinc-300 hover:bg-zinc-600 disabled:opacity-50"
          >
            {checkingQuota ? "…" : labels.checkUsage}
          </button>
        </div>
        {quotaUsage !== null && (
          <p className="text-xs text-zinc-400">
            {labels.tokenUsage}: <b className="text-white">{quotaUsage.toLocaleString()}</b> tokens (last 60s)
          </p>
        )}
      </section>
    </div>
  );
}
