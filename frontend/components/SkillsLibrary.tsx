"use client";

import { useCallback, useEffect, useState } from "react";
import { apiUrl } from "@/lib/api-origin";
import { useAuth } from "@/hooks/useAuth";

export type SkillsLabels = {
  title: string;
  search: string;
  roleFilter: string;
  allRoles: string;
  noSkills: string;
  usageCount: string;
  successRate: string;
  global: string;
  promote: string;
  promoted: string;
  close: string;
  refresh: string;
  tenant: string;
  tenantPlaceholder: string;
};

type Skill = {
  id: string;
  name: string;
  description: string | null;
  content_md: string;
  role_tags: string[];
  industry_tags: string[];
  usage_count: number;
  success_rate: number;
  is_global: boolean;
  version: number;
};

const ROLE_COLOR: Record<string, string> = {
  hunter: "bg-violet-900/50 text-violet-300",
  outreach: "bg-sky-900/50 text-sky-300",
  researcher: "bg-teal-900/50 text-teal-300",
  delivery: "bg-orange-900/50 text-orange-300",
  manager: "bg-pink-900/50 text-pink-300",
};

function MarkdownPreview({ md }: { md: string }) {
  // Simple rendering: headings, bold, lists
  const lines = md.split("\n");
  return (
    <div className="space-y-1 font-mono text-[11px] leading-relaxed text-zinc-300">
      {lines.map((line, i) => {
        if (line.startsWith("## "))
          return <p key={i} className="mt-3 font-semibold text-zinc-100">{line.slice(3)}</p>;
        if (line.startsWith("# "))
          return <p key={i} className="mt-2 text-sm font-bold text-white">{line.slice(2)}</p>;
        if (line.startsWith("- "))
          return <p key={i} className="pl-3 before:content-['•'] before:mr-2 before:text-zinc-500">{line.slice(2)}</p>;
        return <p key={i} className="text-zinc-400">{line || "\u00a0"}</p>;
      })}
    </div>
  );
}

export function SkillsLibrary({ labels }: { labels: SkillsLabels }) {
  const { tenantId } = useAuth();
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState("all");
  const [skills, setSkills] = useState<Skill[]>([]);
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState<Skill | null>(null);
  const [promoting, setPromoting] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!tenantId) return;
    setLoading(true);
    const p = new URLSearchParams({ tenant_id: tenantId });
    if (roleFilter !== "all") p.set("role", roleFilter);
    if (search.trim()) p.set("search", search.trim());
    try {
      const res = await fetch(apiUrl(`/api/v1/memory/skills?${p}`));
      if (res.ok) setSkills(await res.json());
    } finally {
      setLoading(false);
    }
  }, [tenantId, search, roleFilter]);

  useEffect(() => { load(); }, [load]);

  const promote = async (skillId: string) => {
    setPromoting(skillId);
    try {
      await fetch(apiUrl(`/api/v1/memory/skills/${skillId}/promote`), { method: "POST" });
      await load();
      if (selected?.id === skillId) setSelected({ ...selected, is_global: true });
    } finally {
      setPromoting(null);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-white">{labels.title}</h1>

      {/* filters */}
      <div className="flex flex-wrap gap-3">
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder={labels.search}
          className="rounded-md border border-zinc-700 bg-zinc-800 px-3 py-1.5 text-xs text-zinc-300 placeholder-zinc-600 focus:outline-none focus:ring-1 focus:ring-sky-500 sm:w-48"
        />
        <select
          value={roleFilter}
          onChange={(e) => setRoleFilter(e.target.value)}
          className="rounded-md border border-zinc-700 bg-zinc-800 px-3 py-1.5 text-xs text-zinc-300 focus:outline-none focus:ring-1 focus:ring-sky-500"
        >
          {["all", "hunter", "outreach", "researcher", "delivery", "manager"].map((r) => (
            <option key={r} value={r}>{r === "all" ? labels.allRoles : r}</option>
          ))}
        </select>
        <button
          onClick={load}
          disabled={loading}
          className="rounded-md bg-zinc-800 px-3 py-1.5 text-xs text-zinc-300 hover:bg-zinc-700 disabled:opacity-50"
        >
          {loading ? "…" : labels.refresh}
        </button>
      </div>

      {/* skill cards */}
      {skills.length === 0 ? (
        <p className="text-xs text-zinc-500">{labels.noSkills}</p>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {skills.map((s) => (
            <button
              key={s.id}
              onClick={() => setSelected(s)}
              className="group relative rounded-xl border border-zinc-800 bg-zinc-900/50 p-4 text-left transition hover:border-sky-700 hover:bg-zinc-900"
            >
              {s.is_global && (
                <span className="absolute right-3 top-3 rounded bg-amber-800/60 px-1.5 py-0.5 text-[10px] font-medium text-amber-300">
                  {labels.global}
                </span>
              )}
              <div className="mb-2 flex flex-wrap gap-1">
                {s.role_tags.map((r) => (
                  <span key={r} className={`rounded px-1.5 py-0.5 text-[10px] font-medium ${ROLE_COLOR[r] ?? "bg-zinc-800 text-zinc-300"}`}>
                    {r}
                  </span>
                ))}
              </div>
              <p className="mb-1 text-sm font-medium text-zinc-100 leading-snug line-clamp-2">
                {s.name}
              </p>
              <div className="mt-3 flex items-center gap-4 text-[11px] text-zinc-500">
                <span>{labels.successRate}: <b className="text-zinc-300">{(s.success_rate * 100).toFixed(0)}%</b></span>
                <span>{labels.usageCount}: <b className="text-zinc-300">{s.usage_count}</b></span>
              </div>
            </button>
          ))}
        </div>
      )}

      {/* detail modal */}
      {selected && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
          <div className="flex max-h-[85vh] w-full max-w-2xl flex-col rounded-xl border border-zinc-700 bg-zinc-900 shadow-2xl">
            {/* header */}
            <div className="flex items-start justify-between gap-4 border-b border-zinc-800 p-5">
              <div>
                <div className="mb-1 flex flex-wrap gap-1">
                  {selected.role_tags.map((r) => (
                    <span key={r} className={`rounded px-1.5 py-0.5 text-[10px] font-medium ${ROLE_COLOR[r] ?? "bg-zinc-800 text-zinc-300"}`}>{r}</span>
                  ))}
                  {selected.is_global && (
                    <span className="rounded bg-amber-800/60 px-1.5 py-0.5 text-[10px] font-medium text-amber-300">{labels.global}</span>
                  )}
                </div>
                <h2 className="text-base font-semibold text-white">{selected.name}</h2>
                <p className="mt-1 text-xs text-zinc-500">
                  {labels.successRate}: {(selected.success_rate * 100).toFixed(0)}% &nbsp;·&nbsp;
                  {labels.usageCount}: {selected.usage_count}
                </p>
              </div>
              <div className="flex shrink-0 gap-2">
                {!selected.is_global && (
                  <button
                    onClick={() => promote(selected.id)}
                    disabled={promoting === selected.id}
                    className="rounded-md bg-amber-700 px-3 py-1.5 text-xs font-medium text-white hover:bg-amber-600 disabled:opacity-50"
                  >
                    {promoting === selected.id ? "…" : labels.promote}
                  </button>
                )}
                <button
                  onClick={() => setSelected(null)}
                  className="rounded-md bg-zinc-800 px-3 py-1.5 text-xs text-zinc-400 hover:bg-zinc-700"
                >
                  {labels.close}
                </button>
              </div>
            </div>
            {/* content */}
            <div className="flex-1 overflow-y-auto p-5">
              <MarkdownPreview md={selected.content_md} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
