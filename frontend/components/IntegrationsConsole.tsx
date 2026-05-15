"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { apiUrl } from "@/lib/api-origin";
import { useAuth } from "@/hooks/useAuth";

export type IntegrationsLabels = {
  title: string;
  subtitle: string;
  backToSettings: string;
  capabilitiesTitle: string;
  connectionsTitle: string;
  refresh: string;
  connect: string;
  connected: string;
  notConnected: string;
  statusReady: string;
  statusBlocked: string;
  statusStub: string;
  noTenant: string;
  webhookUrl: string;
  webhookProvider: string;
  saveWebhook: string;
  saving: string;
  deleteConnection: string;
  oauthHint: string;
  category: string;
  executeBlocked: string;
};

type CapabilityRow = {
  id: string;
  display_name: string;
  category: string;
  description: string;
  status: string;
  can_execute_now: boolean;
  execute_block_reason: string | null;
  user_connection_active: boolean;
  server_env_configured: boolean;
  oauth_app_configured: boolean | null;
  connection_provider_any: string[];
};

type ConnectionRow = {
  provider: string;
  meta: Record<string, unknown>;
  created_at: string | null;
};

const OAUTH_LINKS: { provider: string; path: string; labelKey: string }[] = [
  { provider: "slack", path: "slack", labelKey: "Slack" },
  { provider: "twitter", path: "twitter", labelKey: "X (Twitter)" },
  { provider: "linkedin", path: "linkedin", labelKey: "LinkedIn" },
  { provider: "facebook", path: "facebook", labelKey: "Facebook" },
  { provider: "weibo", path: "weibo", labelKey: "Weibo" },
  { provider: "reddit", path: "reddit", labelKey: "Reddit" },
  { provider: "google_youtube", path: "google-youtube", labelKey: "YouTube" },
];

const WEBHOOK_PROVIDERS = [
  "discord_webhook",
  "slack_incoming_webhook",
  "feishu_webhook",
  "wechat_work_webhook",
] as const;

function healthDot(cap: CapabilityRow): "green" | "yellow" | "red" {
  if (cap.status === "stub") return "yellow";
  if (cap.can_execute_now) return "green";
  if (cap.user_connection_active || cap.server_env_configured) return "yellow";
  return "red";
}

export function IntegrationsConsole({
  labels,
  locale,
}: {
  labels: IntegrationsLabels;
  locale: string;
}) {
  const { tenantId } = useAuth();
  const [capabilities, setCapabilities] = useState<CapabilityRow[]>([]);
  const [connections, setConnections] = useState<ConnectionRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [webhookProvider, setWebhookProvider] = useState<(typeof WEBHOOK_PROVIDERS)[number]>("discord_webhook");
  const [webhookUrl, setWebhookUrl] = useState("");
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  const connectionSet = useMemo(
    () => new Set(connections.map((c) => c.provider)),
    [connections],
  );

  const load = useCallback(async () => {
    if (!tenantId) return;
    setLoading(true);
    setMessage("");
    try {
      const [capRes, connRes] = await Promise.all([
        fetch(apiUrl(`/api/v1/integrations/capabilities?tenant_id=${tenantId}`)),
        fetch(apiUrl(`/api/v1/integrations/tenants/${tenantId}/connections`)),
      ]);
      if (capRes.ok) setCapabilities(await capRes.json());
      if (connRes.ok) setConnections(await connRes.json());
    } catch {
      setMessage("load_failed");
    } finally {
      setLoading(false);
    }
  }, [tenantId]);

  useEffect(() => {
    void load();
  }, [load]);

  const startOAuth = (path: string) => {
    if (!tenantId) return;
    window.open(
      apiUrl(`/api/v1/integrations/oauth/${path}/start?tenant_id=${tenantId}`),
      "_blank",
      "noopener,noreferrer",
    );
  };

  const saveWebhook = async () => {
    if (!tenantId || !webhookUrl.trim()) return;
    setSaving(true);
    setMessage("");
    try {
      const res = await fetch(apiUrl(`/api/v1/integrations/tenants/${tenantId}/connections/webhook`), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ provider: webhookProvider, webhook_url: webhookUrl.trim() }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setMessage(String((err as { detail?: string }).detail || "save_failed"));
        return;
      }
      setWebhookUrl("");
      await load();
    } finally {
      setSaving(false);
    }
  };

  const removeConnection = async (provider: string) => {
    if (!tenantId) return;
    await fetch(apiUrl(`/api/v1/integrations/tenants/${tenantId}/connections/${provider}`), {
      method: "DELETE",
    });
    await load();
  };

  if (!tenantId) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-8 text-sm text-zinc-400">
        {labels.noTenant}
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl space-y-8 px-4 py-8">
      <header className="space-y-2">
        <Link
          href={`/${locale}/settings`}
          className="text-xs text-sky-400 hover:text-sky-300"
        >
          ← {labels.backToSettings}
        </Link>
        <h1 className="text-xl font-semibold text-white">{labels.title}</h1>
        <p className="text-sm text-zinc-400">{labels.subtitle}</p>
        <button
          type="button"
          onClick={() => void load()}
          disabled={loading}
          className="rounded-md border border-zinc-700 px-3 py-1.5 text-xs text-zinc-300 hover:bg-zinc-800"
        >
          {loading ? "…" : labels.refresh}
        </button>
      </header>

      {message ? (
        <p className="rounded-md border border-amber-900/50 bg-amber-950/30 px-3 py-2 text-xs text-amber-200">
          {message}
        </p>
      ) : null}

      <section className="space-y-3">
        <h2 className="text-sm font-medium text-zinc-200">{labels.connectionsTitle}</h2>
        <p className="text-xs text-zinc-500">{labels.oauthHint}</p>
        <div className="flex flex-wrap gap-2">
          {OAUTH_LINKS.map((o) => {
            const provId =
              o.path === "slack"
                ? "slack_oauth"
                : o.path === "twitter"
                  ? "twitter_oauth"
                  : o.path === "linkedin"
                    ? "linkedin_oauth"
                    : o.path === "facebook"
                      ? "facebook_graph_oauth"
                      : o.path === "weibo"
                        ? "weibo_oauth"
                        : o.path === "reddit"
                          ? "reddit_oauth"
                          : "google_youtube_oauth";
            const isConn = connectionSet.has(provId);
            return (
              <button
                key={o.path}
                type="button"
                onClick={() => startOAuth(o.path)}
                className={`rounded-md border px-3 py-1.5 text-xs ${
                  isConn
                    ? "border-emerald-800 bg-emerald-950/40 text-emerald-300"
                    : "border-zinc-700 text-zinc-300 hover:bg-zinc-800"
                }`}
              >
                {o.labelKey} · {isConn ? labels.connected : labels.connect}
              </button>
            );
          })}
        </div>
        <div className="mt-4 space-y-2 rounded-lg border border-zinc-800 bg-zinc-900/50 p-4">
          <p className="text-xs font-medium text-zinc-300">{labels.webhookProvider}</p>
          <div className="flex flex-wrap gap-2">
            <select
              value={webhookProvider}
              onChange={(e) => setWebhookProvider(e.target.value as (typeof WEBHOOK_PROVIDERS)[number])}
              className="rounded border border-zinc-700 bg-zinc-950 px-2 py-1 text-xs text-zinc-200"
            >
              {WEBHOOK_PROVIDERS.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
            <input
              type="url"
              value={webhookUrl}
              onChange={(e) => setWebhookUrl(e.target.value)}
              placeholder={labels.webhookUrl}
              className="min-w-[200px] flex-1 rounded border border-zinc-700 bg-zinc-950 px-2 py-1 text-xs text-zinc-200"
            />
            <button
              type="button"
              disabled={saving}
              onClick={() => void saveWebhook()}
              className="rounded bg-sky-700 px-3 py-1 text-xs text-white hover:bg-sky-600 disabled:opacity-50"
            >
              {saving ? labels.saving : labels.saveWebhook}
            </button>
          </div>
        </div>
        {connections.length > 0 ? (
          <ul className="space-y-1 text-xs text-zinc-400">
            {connections.map((c) => (
              <li key={c.provider} className="flex items-center justify-between gap-2 rounded border border-zinc-800 px-2 py-1">
                <span>{c.provider}</span>
                <button
                  type="button"
                  onClick={() => void removeConnection(c.provider)}
                  className="text-red-400 hover:text-red-300"
                >
                  {labels.deleteConnection}
                </button>
              </li>
            ))}
          </ul>
        ) : null}
      </section>

      <section className="space-y-3">
        <h2 className="text-sm font-medium text-zinc-200">{labels.capabilitiesTitle}</h2>
        <ul className="space-y-2">
          {capabilities.map((cap) => {
            const dot = healthDot(cap);
            const statusLabel =
              dot === "green"
                ? labels.statusReady
                : cap.status === "stub"
                  ? labels.statusStub
                  : labels.statusBlocked;
            return (
              <li
                key={cap.id}
                className="rounded-lg border border-zinc-800 bg-zinc-900/40 px-3 py-2"
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="text-sm font-medium text-zinc-100">{cap.display_name}</p>
                    <p className="text-xs text-zinc-500">
                      {labels.category}: {cap.category} · {cap.id}
                    </p>
                    <p className="mt-1 text-xs text-zinc-400">{cap.description}</p>
                    {!cap.can_execute_now && cap.execute_block_reason ? (
                      <p className="mt-1 text-xs text-amber-500/90">
                        {labels.executeBlocked}: {cap.execute_block_reason}
                      </p>
                    ) : null}
                  </div>
                  <span
                    className={`mt-1 h-2.5 w-2.5 shrink-0 rounded-full ${
                      dot === "green"
                        ? "bg-emerald-500"
                        : dot === "yellow"
                          ? "bg-amber-500"
                          : "bg-red-500"
                    }`}
                    title={statusLabel}
                  />
                </div>
              </li>
            );
          })}
        </ul>
      </section>
    </div>
  );
}
