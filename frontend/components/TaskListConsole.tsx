"use client";

import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";

export type TaskListLabels = {
  title: string;
  tenantFilter: string;
  refresh: string;
  empty: string;
  type: string;
  status: string;
};

function apiBase() {
  return (process.env.NEXT_PUBLIC_API_URL ?? "").replace(/\/$/, "");
}

type TaskRow = { id: string; type: string; status: string };

export function TaskListConsole({ labels }: { labels: TaskListLabels }) {
  const [tenantId, setTenantId] = useState("");

  const url = useMemo(() => {
    const b = apiBase();
    if (!b) return null;
    const q = tenantId ? `?tenant_id=${encodeURIComponent(tenantId)}` : "";
    return `${b}/api/v1/tasks${q}`;
  }, [tenantId]);

  const query = useQuery({
    queryKey: ["tasks", tenantId],
    enabled: Boolean(url),
    queryFn: async (): Promise<TaskRow[]> => {
      const r = await fetch(url!);
      if (!r.ok) throw new Error(await r.text());
      const data = (await r.json()) as { id: string; type: string; status: string }[];
      return data;
    },
  });

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold text-white">{labels.title}</h1>
      <div className="flex flex-wrap items-end gap-3">
        <div>
          <label className="block text-xs text-zinc-500">{labels.tenantFilter}</label>
          <input
            className="mt-1 w-72 rounded border border-zinc-700 bg-zinc-950 px-3 py-2 font-mono text-sm text-zinc-100"
            placeholder="UUID"
            value={tenantId}
            onChange={(e) => setTenantId(e.target.value)}
          />
        </div>
        <button
          type="button"
          className="rounded border border-zinc-600 px-3 py-2 text-sm text-zinc-200 hover:bg-zinc-800"
          onClick={() => query.refetch()}
        >
          {labels.refresh}
        </button>
      </div>
      {!apiBase() && <p className="text-sm text-amber-400">NEXT_PUBLIC_API_URL is not set.</p>}
      {query.isLoading && <p className="text-sm text-zinc-500">{labels.refresh}…</p>}
      {query.error && <p className="text-sm text-red-400">{(query.error as Error).message}</p>}
      {query.data && query.data.length === 0 && <p className="text-sm text-zinc-500">{labels.empty}</p>}
      {query.data && query.data.length > 0 && (
        <div className="overflow-x-auto rounded border border-zinc-800">
          <table className="min-w-full text-left text-sm text-zinc-200">
            <thead className="border-b border-zinc-800 bg-zinc-900/80 text-xs uppercase text-zinc-500">
              <tr>
                <th className="px-3 py-2">id</th>
                <th className="px-3 py-2">{labels.type}</th>
                <th className="px-3 py-2">{labels.status}</th>
              </tr>
            </thead>
            <tbody>
              {query.data.map((row) => (
                <tr key={row.id} className="border-b border-zinc-800/80">
                  <td className="px-3 py-2 font-mono text-xs">{row.id}</td>
                  <td className="px-3 py-2">{row.type}</td>
                  <td className="px-3 py-2">{row.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
