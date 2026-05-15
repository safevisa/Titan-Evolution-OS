"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { apiUrl } from "@/lib/api-origin";
import { useAuth } from "@/hooks/useAuth";

export type ContextSyncLabels = {
  title: string;
  googleWorkspace: string;
  github: string;
  overview: string;
  lastSync: string;
  never: string;
  trigger: string;
  syncing: string;
  statusOk: string;
  statusError: string;
  statusPending: string;
  statusNotConnected: string;
  gmail: string;
  gcal: string;
  lastError: string;
};

export type CapabilityPackLabels = {
  title: string;
  contextSync: string;
  desktopAutomation: string;
  apply: string;
  applying: string;
  applied: string;
};

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
  contextSync: ContextSyncLabels;
  capabilityPacks: CapabilityPackLabels;
  errors: Record<string, string>;
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

type SyncSourceStatus = {
  connected: boolean;
  status: string;
  last_success_at: string | null;
  last_error: string | null;
};

type SyncStatusResponse = {
  enabled: boolean;
  sources: {
    gmail: SyncSourceStatus;
    gcal: SyncSourceStatus;
    github: SyncSourceStatus;
  };
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

const CONTEXT_OAUTH: { path: string; provId: string; labelKey: "googleWorkspace" | "github" }[] = [
  { path: "google-workspace", provId: "google_workspace_oauth", labelKey: "googleWorkspace" },
  { path: "github", provId: "github_oauth", labelKey: "github" },
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

function formatSyncTime(iso: string | null): string {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

function sourceStatusLabel(src: SyncSourceStatus, cs: ContextSyncLabels): string {
  if (!src.connected) return cs.statusNotConnected;
  if (src.status === "ok") return cs.statusOk;
  if (src.status === "error") return cs.statusError;
  return cs.statusPending;
}

export function IntegrationsConsole({
  labels,
  locale,
}: {
  labels: IntegrationsLabels;
  locale: string;
}) {
  const { tenantId } = useAuth();
  const cs = labels.contextSync;
  const packs = labels.capabilityPacks;
  const [capabilities, setCapabilities] = useState<CapabilityRow[]>([]);
  const [connections, setConnections] = useState<ConnectionRow[]>([]);
  const [syncStatus, setSyncStatus] = useState<SyncStatusResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [applyingPack, setApplyingPack] = useState<string | null>(null);
  const [webhookProvider, setWebhookProvider] = useState<(typeof WEBHOOK_PROVIDERS)[number]>("discord_webhook");
  const [webhookUrl, setWebhookUrl] = useState("");
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const connectionSet = useMemo(
    () => new Set(connections.map((c) => c.provider)),
    [connections],
  );

  const loadSyncStatus = useCallback(async () => {
    if (!tenantId) return;
    const res = await fetch(apiUrl(`/api/v1/integrations/tenants/${tenantId}/sync-status`));
    if (res.ok) setSyncStatus(await res.json());
  }, [tenantId]);

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
      await loadSyncStatus();
    } catch {
      setMessage("load_failed");
    } finally {
      setLoading(false);
    }
  }, [tenantId, loadSyncStatus]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (!syncing) {
      if (pollRef.current) clearInterval(pollRef.current);
      pollRef.current = null;
      return;
    }
    pollRef.current = setInterval(() => void loadSyncStatus(), 30_000);
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [syncing, loadSyncStatus]);

  const startOAuth = (path: string) => {
    if (!tenantId) return;
    window.open(
      apiUrl(`/api/v1/integrations/oauth/${path}/start?tenant_id=${tenantId}`),
      "_blank",
      "noopener,noreferrer",
    );
  };

  const triggerSync = async () => {
    if (!tenantId) return;
    setSyncing(true);
    setMessage("");
    try {
      const res = await fetch(apiUrl(`/api/v1/integrations/tenants/${tenantId}/sync/trigger`), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      if (!res.ok) {
        await res.json().catch(() => ({}));
        setMessage("sync_failed");
        return;
      }
      setMessage("sync_triggered");
      await loadSyncStatus();
    } finally {
      setSyncing(false);
    }
  };

  const applyPack = async (packId: string) => {
    if (!tenantId) return;
    setApplyingPack(packId);
    setMessage("");
    try {
      const res = await fetch(apiUrl(`/api/v1/integrations/tenants/${tenantId}/grants/apply-pack`), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pack_id: packId, merge: true }),
      });
      if (!res.ok) {
        setMessage("pack_failed");
        return;
      }
      setMessage("pack_applied");
      await load();
    } finally {
      setApplyingPack(null);
    }
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
        setMessage("save_failed");
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

  const errText = message ? (labels.errors[message] ?? message) : "";

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
        <Link href={`/${locale}/settings`} className="text-xs text-sky-400 hover:text-sky-300">
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

      {errText ? (
        <p className="rounded-md border border-amber-900/50 bg-amber-950/30 px-3 py-2 text-xs text-amber-200">
          {errText}
        </p>
      ) : null}

      <section className="space-y-3 rounded-lg border border-zinc-800 bg-zinc-900/40 p-4">
        <h2 className="text-sm font-medium text-zinc-200">{cs.title}</h2>
        <div className="flex flex-wrap gap-2">
          {CONTEXT_OAUTH.map((o) => {
            const isConn = connectionSet.has(o.provId);
            const label = cs[o.labelKey];
            return (
              <button
                key={o.path}
                type="button"
                aria-label={label}
                onClick={() => startOAuth(o.path)}
                className={`rounded-md border px-3 py-1.5 text-xs ${
                  isConn
                    ? "border-emerald-800 bg-emerald-950/40 text-emerald-300"
                    : "border-zinc-700 text-zinc-300 hover:bg-zinc-800"
                }`}
              >
                {label} · {isConn ? labels.connected : labels.connect}
              </button>
            );
          })}
        </div>
        {syncStatus ? (
          <div className="mt-3 space-y-2 text-xs text-zinc-400">
            <p className="font-medium text-zinc-300">{cs.overview}</p>
            {(["gmail", "gcal", "github"] as const).map((key) => {
              const src = syncStatus.sources[key];
              const name = key === "gmail" ? cs.gmail : key === "gcal" ? cs.gcal : cs.github;
              return (
                <div
                  key={key}
                  className="flex flex-wrap items-center justify-between gap-2 rounded border border-zinc-800 px-2 py-1.5"
                >
                  <span className="text-zinc-300">{name}</span>
                  <span>{sourceStatusLabel(src, cs)}</span>
                  <span className="text-zinc-500">
                    {cs.lastSync}: {formatSyncTime(src.last_success_at) || cs.never}
                  </span>
                  {src.last_error ? (
                    <span className="w-full text-amber-500/90">
                      {cs.lastError}: {src.last_error}
                    </span>
                  ) : null}
                </div>
              );
            })}
          </div>
        ) : null}
        <button
          type="button"
          aria-label={cs.trigger}
          disabled={syncing}
          onClick={() => void triggerSync()}
          className="rounded bg-sky-700 px-3 py-1.5 text-xs text-white hover:bg-sky-600 disabled:opacity-50"
        >
          {syncing ? cs.syncing : cs.trigger}
        </button>
      </section>

      <section className="space-y-3 rounded-lg border border-zinc-800 bg-zinc-900/40 p-4">
        <h2 className="text-sm font-medium text-zinc-200">{packs.title}</h2>
        <div className="flex flex-wrap gap-2">
          {[
            { id: "context_sync", label: packs.contextSync },
            { id: "desktop_automation", label: packs.desktopAutomation },
          ].map((p) => (
            <button
              key={p.id}
              type="button"
              disabled={applyingPack !== null}
              onClick={() => void applyPack(p.id)}
              className="rounded-md border border-zinc-700 px-3 py-1.5 text-xs text-zinc-300 hover:bg-zinc-800 disabled:opacity-50"
            >
              {applyingPack === p.id ? packs.applying : `${packs.apply}: ${p.label}`}
            </button>
          ))}
        </div>
      </section>

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
              title={labels.webhookProvider}
              aria-label={labels.webhookProvider}
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
              <li
                key={c.provider}
                className="flex items-center justify-between gap-2 rounded border border-zinc-800 px-2 py-1"
              >
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
              <li key={cap.id} className="rounded-lg border border-zinc-800 bg-zinc-900/40 px-3 py-2">
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
