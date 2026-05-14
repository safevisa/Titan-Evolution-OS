"use client";

import { useCallback, useEffect, useState } from "react";

import { apiUrl } from "@/lib/api-origin";
import { useAuth } from "@/hooks/useAuth";

export type QuickStartLabels = {
  title: string;
  tenantName: string;
  createTenant: string;
  agentName: string;
  role: string;
  prompt: string;
  createAgent: string;
  taskType: string;
  createTask: string;
  enqueue: string;
  llmTitle: string;
  llmMessage: string;
  llmSend: string;
  log: string;
  apiTitle: string;
  apiChecking: string;
  apiOk: string;
  apiFail: string;
};

export function QuickStartConsole({ labels, locale }: { labels: QuickStartLabels; locale: string }) {
  const { tenantId: sessionTenantId } = useAuth();
  const [tenantName, setTenantName] = useState("Demo Tenant");
  const [tenantId, setTenantId] = useState(sessionTenantId ?? "");
  const [agentName, setAgentName] = useState("Hunter 1");
  const [role, setRole] = useState("hunter");
  const [prompt, setPrompt] = useState("You are a growth hunter focused on MENA fintech.");
  const [agentId, setAgentId] = useState("");
  const [taskType, setTaskType] = useState("lead_search");
  const [taskId, setTaskId] = useState("");
  const [llmMessage, setLlmMessage] = useState("Reply with one word: OK");
  const [log, setLog] = useState<string[]>([]);
  const [apiLoop, setApiLoop] = useState<"checking" | "ok" | "fail">("checking");

  useEffect(() => {
    fetch(apiUrl("/api/v1/bootstrap"))
      .then((r) => (r.ok ? setApiLoop("ok") : setApiLoop("fail")))
      .catch(() => setApiLoop("fail"));
  }, []);

  const pushLog = useCallback((line: string) => {
    setLog((prev) => [...prev.slice(-40), line]);
  }, []);

  const postJson = async (path: string, body: unknown) => {
    const r = await fetch(apiUrl(path), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const text = await r.text();
    if (!r.ok) throw new Error(`${r.status} ${text}`);
    return text ? JSON.parse(text) : {};
  };

  const onTenant = async () => {
    const data = await postJson("/api/v1/tenants", {
      name: tenantName,
      industry_plugin: "payment_fintech",
      plan: "starter",
    });
    setTenantId(data.id);
    pushLog(`tenant ${data.id}`);
  };

  const onAgent = async () => {
    if (!tenantId) {
      pushLog("create tenant first");
      return;
    }
    const data = await postJson("/api/v1/agents", {
      tenant_id: tenantId,
      name: agentName,
      role,
      current_prompt: prompt,
    });
    setAgentId(data.id);
    pushLog(`agent ${data.id}`);
  };

  const onTask = async () => {
    if (!tenantId || !agentId) {
      pushLog("need tenant + agent");
      return;
    }
    const data = await postJson("/api/v1/tasks", {
      tenant_id: tenantId,
      agent_id: agentId,
      type: taskType,
      input: { locale },
    });
    setTaskId(data.id);
    pushLog(`task ${data.id}`);
  };

  const onEnqueue = async () => {
    if (!taskId) {
      pushLog("create task first");
      return;
    }
    const r = await fetch(apiUrl(`/api/v1/tasks/${taskId}/enqueue`), { method: "POST" });
    const text = await r.text();
    if (!r.ok) throw new Error(`${r.status} ${text}`);
    pushLog(`enqueue ${text}`);
  };

  const onLlm = async () => {
    const r = await fetch(apiUrl("/api/v1/llm/complete"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: llmMessage }),
    });
    const text = await r.text();
    if (!r.ok) {
      pushLog(`llm error ${r.status} ${text}`);
      return;
    }
    const data = JSON.parse(text);
    pushLog(`llm: ${data.reply} (tokens ${data.tokens})`);
  };

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-5">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2 border-b border-zinc-800 pb-3">
        <span className="text-sm font-medium text-zinc-300">{labels.apiTitle}</span>
        <span
          className={
            apiLoop === "ok"
              ? "text-xs font-medium text-emerald-400"
              : apiLoop === "fail"
                ? "text-xs font-medium text-red-400"
                : "text-xs text-zinc-500"
          }
        >
          {apiLoop === "checking" ? labels.apiChecking : apiLoop === "ok" ? labels.apiOk : labels.apiFail}
        </span>
      </div>
      <h2 className="text-lg font-medium text-white">{labels.title}</h2>
      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <div className="space-y-2">
          <label className="block text-xs text-zinc-500">{labels.tenantName}</label>
          <input
            className="w-full rounded border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-100"
            value={tenantName}
            onChange={(e) => setTenantName(e.target.value)}
          />
          <button
            type="button"
            className="rounded bg-amber-600 px-3 py-2 text-sm font-medium text-black hover:bg-amber-500"
            onClick={() => onTenant().catch((e) => pushLog(String(e)))}
          >
            {labels.createTenant}
          </button>
          <p className="font-mono text-xs text-zinc-500">{tenantId || "—"}</p>
        </div>
        <div className="space-y-2">
          <label className="block text-xs text-zinc-500">{labels.agentName}</label>
          <input
            className="w-full rounded border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-100"
            value={agentName}
            onChange={(e) => setAgentName(e.target.value)}
          />
          <label className="block text-xs text-zinc-500">{labels.role}</label>
          <input
            className="w-full rounded border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-100"
            value={role}
            onChange={(e) => setRole(e.target.value)}
          />
          <label className="block text-xs text-zinc-500">{labels.prompt}</label>
          <textarea
            className="w-full rounded border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-100"
            rows={3}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
          />
          <button
            type="button"
            className="rounded bg-emerald-700 px-3 py-2 text-sm font-medium text-white hover:bg-emerald-600"
            onClick={() => onAgent().catch((e) => pushLog(String(e)))}
          >
            {labels.createAgent}
          </button>
          <p className="font-mono text-xs text-zinc-500">{agentId || "—"}</p>
        </div>
        <div className="space-y-2">
          <label className="block text-xs text-zinc-500">{labels.taskType}</label>
          <input
            className="w-full rounded border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-100"
            value={taskType}
            onChange={(e) => setTaskType(e.target.value)}
          />
          <button
            type="button"
            className="rounded bg-sky-700 px-3 py-2 text-sm font-medium text-white hover:bg-sky-600"
            onClick={() => onTask().catch((e) => pushLog(String(e)))}
          >
            {labels.createTask}
          </button>
          <button
            type="button"
            className="rounded border border-zinc-600 px-3 py-2 text-sm text-zinc-200 hover:bg-zinc-800"
            onClick={() => onEnqueue().catch((e) => pushLog(String(e)))}
          >
            {labels.enqueue}
          </button>
          <p className="font-mono text-xs text-zinc-500">{taskId || "—"}</p>
        </div>
        <div className="space-y-2">
          <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">{labels.llmTitle}</p>
          <textarea
            className="w-full rounded border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-100"
            rows={2}
            value={llmMessage}
            onChange={(e) => setLlmMessage(e.target.value)}
          />
          <button
            type="button"
            className="rounded bg-violet-700 px-3 py-2 text-sm font-medium text-white hover:bg-violet-600"
            onClick={() => onLlm().catch((e) => pushLog(String(e)))}
          >
            {labels.llmSend}
          </button>
        </div>
      </div>
      <div className="mt-6">
        <p className="text-xs text-zinc-500">{labels.log}</p>
        <pre className="mt-2 max-h-48 overflow-auto rounded border border-zinc-800 bg-black/40 p-3 font-mono text-xs text-zinc-300">
          {log.join("\n") || "—"}
        </pre>
      </div>
    </div>
  );
}
