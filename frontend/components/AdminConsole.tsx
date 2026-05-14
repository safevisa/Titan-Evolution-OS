"use client";

import { useCallback, useEffect, useState } from "react";
import { apiUrl } from "@/lib/api-origin";

const C = {
  bg: "#07090f",
  surface: "#0d1017",
  border: "rgba(255,255,255,0.06)",
  text: "#e8eaf0",
  textMid: "#8892a4",
  accent: "#5b6ef5",
  green: "#2dd4a0",
  red: "#f25f5c",
};

export type AdminLabels = {
  title: string;
  subtitle: string;
  syncAll: string;
  syncing: string;
  tenants: string;
  catalog: string;
  agentCount: string;
  skillCount: string;
  lastResult: string;
  noResult: string;
  openApiDocs: string;
};

type TenantRow = { id: string; name: string; plan: string; industry_plugin: string };

export function AdminConsole({ labels }: { labels: AdminLabels }) {
  const [tenants, setTenants] = useState<TenantRow[]>([]);
  const [catalog, setCatalog] = useState<{ agent_count?: number; skill_count?: number } | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [syncJson, setSyncJson] = useState<string>("");
  const [err, setErr] = useState("");

  const load = useCallback(async () => {
    setErr("");
    try {
      const [tRes, cRes] = await Promise.all([
        fetch("/api/admin/tenants-overview"),
        fetch(apiUrl("/api/v1/agents/enterprise-catalog")),
      ]);
      if (tRes.ok) setTenants(await tRes.json());
      else setErr(`Tenants: HTTP ${tRes.status}`);
      if (cRes.ok) setCatalog(await cRes.json());
    } catch {
      setErr("Network error");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const syncAll = async () => {
    setSyncing(true);
    setErr("");
    setSyncJson("");
    try {
      const res = await fetch("/api/admin/sync-all-rosters", { method: "POST" });
      const j = await res.json().catch(() => ({}));
      setSyncJson(JSON.stringify(j, null, 2));
      if (!res.ok) setErr(typeof j.error === "string" ? j.error : `HTTP ${res.status}`);
      await load();
    } catch {
      setErr("Network error");
    } finally {
      setSyncing(false);
    }
  };

  return (
    <div>
      <h1 style={{ fontSize: 24, fontWeight: 700, color: C.text, marginBottom: 6 }}>{labels.title}</h1>
      <p style={{ fontSize: 14, color: C.textMid, marginBottom: 24 }}>{labels.subtitle}</p>

      {err ? <p style={{ color: C.red, fontSize: 13, marginBottom: 16 }}>{err}</p> : null}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))", gap: 16, marginBottom: 24 }}>
        <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 12, padding: 18 }}>
          <div style={{ fontSize: 12, color: C.textMid, marginBottom: 6 }}>{labels.catalog}</div>
          <div style={{ fontSize: 20, fontWeight: 700, color: C.text }}>
            {catalog ? `${catalog.agent_count ?? "—"} ${labels.agentCount} · ${catalog.skill_count ?? "—"} ${labels.skillCount}` : "—"}
          </div>
        </div>
        <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 12, padding: 18 }}>
          <div style={{ fontSize: 12, color: C.textMid, marginBottom: 6 }}>{labels.tenants}</div>
          <div style={{ fontSize: 20, fontWeight: 700, color: C.text }}>{tenants.length}</div>
        </div>
      </div>

      <div style={{ display: "flex", flexWrap: "wrap", gap: 12, marginBottom: 24 }}>
        <button
          type="button"
          onClick={() => void syncAll()}
          disabled={syncing}
          style={{
            padding: "12px 22px",
            borderRadius: 9,
            border: "none",
            cursor: syncing ? "not-allowed" : "pointer",
            fontWeight: 600,
            fontSize: 14,
            background: syncing ? "#2a2e3a" : C.accent,
            color: "#fff",
          }}
        >
          {syncing ? labels.syncing : labels.syncAll}
        </button>
        <a
          href="/api/docs"
          target="_blank"
          rel="noopener noreferrer"
          style={{
            padding: "12px 18px",
            borderRadius: 9,
            border: `1px solid ${C.border}`,
            color: C.textMid,
            textDecoration: "none",
            fontSize: 14,
            alignSelf: "center",
          }}
        >
          {labels.openApiDocs}
        </a>
      </div>

      <h2 style={{ fontSize: 15, fontWeight: 600, color: C.text, marginBottom: 10 }}>{labels.tenants}</h2>
      <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 12, overflow: "hidden", marginBottom: 24 }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
          <thead>
            <tr style={{ borderBottom: `1px solid ${C.border}`, color: C.textMid, textAlign: "left" }}>
              <th style={{ padding: "10px 14px" }}>Name</th>
              <th style={{ padding: "10px 14px" }}>Plan</th>
              <th style={{ padding: "10px 14px" }}>Plugin</th>
            </tr>
          </thead>
          <tbody>
            {tenants.map((t) => (
              <tr key={t.id} style={{ borderBottom: `1px solid ${C.border}`, color: C.text }}>
                <td style={{ padding: "10px 14px" }}>{t.name}</td>
                <td style={{ padding: "10px 14px" }}>{t.plan}</td>
                <td style={{ padding: "10px 14px" }}>{t.industry_plugin}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <h2 style={{ fontSize: 15, fontWeight: 600, color: C.text, marginBottom: 10 }}>{labels.lastResult}</h2>
      <pre
        style={{
          background: "#05070c",
          border: `1px solid ${C.border}`,
          borderRadius: 10,
          padding: 16,
          fontSize: 12,
          color: C.green,
          overflow: "auto",
          maxHeight: 360,
          margin: 0,
        }}
      >
        {syncJson || labels.noResult}
      </pre>
    </div>
  );
}
