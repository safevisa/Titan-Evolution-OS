"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { apiUrl } from "@/lib/api-origin";
import { useAuth } from "@/hooks/useAuth";

export type TaskListLabels = {
  title: string;
  subtitle?: string;
  quickLaunch?: string;
  taskTypeLabel?: string;
  goalLabel?: string;
  goalPlaceholder?: string;
  assignLabel?: string;
  launchButton?: string;
  launching?: string;
  executionLog?: string;
  liveBadge?: string;
  emptyLog?: string;
  taskHistory?: string;
  collaborativeHint?: string;
  taskTypeLabels?: Record<string, string>;
  statusFilter: string;
  all: string;
  refresh: string;
  empty: string;
  type: string;
  status: string;
  duration: string;
  tokens: string;
  enqueue: string;
  feedback: string;
  feedbackPlaceholder: string;
  submitFeedback: string;
  output: string;
  close: string;
  noManagerAgent?: string;
  workflowLabel?: string;
  workflowStepsSuffix?: string;
  workflowRolesHint?: string;
  workflowNameLabel?: string;
  workflowNamePlaceholder?: string;
  workflowNameHint?: string;
};

const C = {
  bg: "#07090f", surface: "#0d1017", surfaceHigh: "#13171f",
  border: "rgba(255,255,255,0.06)", text: "#e8eaf0", textMid: "#8892a4",
  textDim: "#3d4557", accent: "#5b6ef5", green: "#2dd4a0",
  amber: "#f5a524", red: "#f25f5c", purple: "#a78bfa",
};

type AgentRow = { id: string; name: string; role: string };
type TaskRow = {
  id: string; type: string; status: string; token_used: number;
  duration_ms: number | null; output: Record<string, unknown> | null; created_at: string;
};

const TASK_TYPES = [
  "goal_pipeline",
  "lead_search",
  "icp_search",
  "partner_discovery",
  "company_research",
  "market_research",
  "competitive_intel",
  "tech_stack_research",
  "email_write",
  "trial_invite",
  "follow_up_email",
  "deal_summary",
  "exec_one_pager",
  "sprint_plan",
  "risk_assessment",
];
const STATUS_ICON: Record<string, string> = { done: "✅", running: "⏳", failed: "❌", pending: "⏸" };
const STATUS_COLOR: Record<string, string> = { done: C.green, running: C.accent, failed: C.red, pending: C.amber };

type WorkflowTemplateRow = { index: number; name: string; node_count: number; roles: string[] };

export function TaskListConsole({ labels }: { labels: TaskListLabels }) {
  const { tenantId } = useAuth();
  const [statusFilter, setStatusFilter] = useState("all");
  const [tasks, setTasks] = useState<TaskRow[]>([]);
  const [agents, setAgents] = useState<AgentRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [enqueueing, setEnqueueing] = useState<string | null>(null);
  const [feedbackTask, setFeedbackTask] = useState<string | null>(null);
  const [feedbackScore, setFeedbackScore] = useState("");
  const [submittingFeedback, setSubmittingFeedback] = useState(false);
  const [outputTask, setOutputTask] = useState<TaskRow | null>(null);

  // Launch panel state
  const [taskType, setTaskType] = useState("goal_pipeline");
  const [goal, setGoal] = useState("");
  const [selectedAgent, setSelectedAgent] = useState("");
  const [launching, setLaunching] = useState(false);
  const [liveLogs, setLiveLogs] = useState<{ time: string; icon: string; msg: string; color: string }[]>([]);
  const [workflows, setWorkflows] = useState<WorkflowTemplateRow[]>([]);
  const [workflowIndex, setWorkflowIndex] = useState(0);
  const [workflowNameOverride, setWorkflowNameOverride] = useState("");
  const logRef = useRef<HTMLDivElement>(null);

  const loadTasks = useCallback(async () => {
    if (!tenantId) return;
    setLoading(true);
    const params = new URLSearchParams({ tenant_id: tenantId });
    if (statusFilter !== "all") params.set("status", statusFilter);
    try {
      const res = await fetch(apiUrl(`/api/v1/tasks?${params}`));
      if (res.ok) setTasks(await res.json());
    } finally { setLoading(false); }
  }, [tenantId, statusFilter]);

  const loadAgents = useCallback(async () => {
    if (!tenantId) return;
    const res = await fetch(apiUrl(`/api/v1/analytics/agents?tenant_id=${tenantId}`));
    if (res.ok) {
      const data: AgentRow[] = await res.json();
      setAgents(data);
      setSelectedAgent(prev => prev || (data.length > 0 ? data[0].id : ""));
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tenantId]);

  const assignableAgents = useMemo(
    () => (taskType === "goal_pipeline" ? agents.filter(a => a.role === "manager") : agents),
    [taskType, agents],
  );

  useEffect(() => {
    if (taskType !== "goal_pipeline") return;
    if (assignableAgents.length === 0) {
      setSelectedAgent("");
      return;
    }
    const cur = agents.find(a => a.id === selectedAgent);
    if (!cur || cur.role !== "manager") {
      setSelectedAgent(assignableAgents[0].id);
    }
  }, [taskType, assignableAgents, agents, selectedAgent]);

  const loadWorkflows = useCallback(async () => {
    if (!tenantId) return;
    const res = await fetch(apiUrl(`/api/v1/tasks/workflow-templates?tenant_id=${tenantId}`));
    if (res.ok) {
      const data: WorkflowTemplateRow[] = await res.json();
      setWorkflows(data);
      setWorkflowIndex(0);
    }
  }, [tenantId]);

  useEffect(() => { loadTasks(); }, [loadTasks]);
  useEffect(() => { loadAgents(); }, [loadAgents]);
  useEffect(() => {
    if (taskType === "goal_pipeline") void loadWorkflows();
  }, [taskType, loadWorkflows]);

  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [liveLogs]);

  // Poll running tasks
  useEffect(() => {
    const hasRunning = tasks.some(t => t.status === "running");
    if (!hasRunning) return;
    const id = setInterval(loadTasks, 5000);
    return () => clearInterval(id);
  }, [tasks, loadTasks]);

  const taskTypeLabel = (t: string) => labels.taskTypeLabels?.[t] ?? t.replace(/_/g, " ");

  const addLog = (icon: string, msg: string, color = C.textMid) => {
    const time = new Date().toLocaleTimeString("en", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
    setLiveLogs(prev => [...prev, { time, icon, msg, color }]);
  };

  const launchTask = async () => {
    if (!tenantId || !selectedAgent || !goal.trim()) return;
    setLaunching(true);
    setLiveLogs([]);
    addLog("🚀", `Creating ${taskTypeLabel(taskType)}…`, C.accent);
    try {
      const agent = agents.find(a => a.id === selectedAgent);
      const input: Record<string, unknown> = { goal: goal.trim(), criteria: goal.trim() };
      if (taskType === "goal_pipeline") {
        const wn = workflowNameOverride.trim();
        if (wn) {
          input.workflow_name = wn;
        } else {
          input.workflow_index = workflowIndex;
        }
      }
      const createRes = await fetch(apiUrl("/api/v1/tasks"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tenant_id: tenantId, agent_id: selectedAgent, task_type: taskType, input }),
      });
      if (!createRes.ok) {
        const errText = await createRes.text();
        addLog("❌", `Failed to create task: ${createRes.status} ${errText.slice(0, 200)}`, C.red);
        setLaunching(false);
        return;
      }
      const task: TaskRow = await createRes.json();
      addLog("✅", `Task created (ID: ${task.id.slice(0, 8)}…)`, C.green);
      addLog("⚡", `Memory layer: retrieving relevant past experiences…`, C.purple);

      const enqRes = await fetch(apiUrl(`/api/v1/tasks/${task.id}/enqueue`), { method: "POST" });
      if (!enqRes.ok) { addLog("❌", `Failed to enqueue: ${enqRes.status}`, C.red); setLaunching(false); return; }
      addLog("⏳", `${agent?.name ?? "Agent"} is now running…`, C.amber);

      // Poll for completion
      let attempts = 0;
      const poll = setInterval(async () => {
        attempts++;
        const tRes = await fetch(apiUrl(`/api/v1/tasks/${task.id}`));
        if (!tRes.ok) return;
        const updated: TaskRow = await tRes.json();
        if (updated.status === "done") {
          clearInterval(poll);
          addLog("✅", `Task completed! Duration: ${updated.duration_ms}ms · Tokens: ${updated.token_used}`, C.green);
          setLiveLogs(prev => [...prev, { time: new Date().toLocaleTimeString("en", { hour: "2-digit", minute: "2-digit", second: "2-digit" }), icon: "🧠", msg: "Memory saved — this experience will improve future tasks", color: C.purple }]);
          setGoal(""); setLaunching(false);
          await loadTasks();
        } else if (updated.status === "failed") {
          clearInterval(poll);
          addLog("❌", `Task failed. ${JSON.stringify(updated.output ?? {}).slice(0, 80)}`, C.red);
          setLaunching(false);
          await loadTasks();
        } else if (attempts > 60) {
          clearInterval(poll); setLaunching(false);
        }
      }, 3000);
    } catch (e) {
      addLog("❌", String(e), C.red);
      setLaunching(false);
    }
  };

  const enqueue = async (taskId: string) => {
    setEnqueueing(taskId);
    try {
      await fetch(apiUrl(`/api/v1/tasks/${taskId}/enqueue`), { method: "POST" });
      await loadTasks();
    } finally { setEnqueueing(null); }
  };

  const submitFeedback = async () => {
    if (!feedbackTask) return;
    const score = parseFloat(feedbackScore);
    if (isNaN(score) || score < 0 || score > 1) return;
    setSubmittingFeedback(true);
    try {
      await fetch(apiUrl(`/api/v1/tasks/${feedbackTask}/feedback`), {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ quality_score: score }),
      });
      setFeedbackTask(null); setFeedbackScore("");
    } finally { setSubmittingFeedback(false); }
  };

  return (
    <div>
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, color: C.text, marginBottom: 4 }}>{labels.title}</h1>
        <p style={{ fontSize: 14, color: C.textMid }}>{labels.subtitle ?? "Launch tasks · Watch execution live"}</p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, marginBottom: 24 }}>
        {/* Launch panel */}
        <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 14, padding: 24 }}>
          <h3 style={{ fontSize: 15, fontWeight: 600, color: C.text, marginBottom: 20 }}>{labels.quickLaunch ?? "⚡ Quick launch"}</h3>
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <div>
              <label style={{ fontSize: 12, color: C.textMid, display: "block", marginBottom: 6 }}>{labels.taskTypeLabel ?? labels.type}</label>
              <select value={taskType} onChange={e => setTaskType(e.target.value)} style={{ width: "100%", padding: "10px 14px", background: C.surfaceHigh, border: `1px solid ${C.border}`, borderRadius: 9, color: C.text, fontSize: 13 }}>
                {TASK_TYPES.map(t => <option key={t} value={t}>{taskTypeLabel(t)}</option>)}
              </select>
              {taskType === "goal_pipeline" && labels.collaborativeHint && (
                <p style={{ fontSize: 11, color: C.textDim, marginTop: 6, lineHeight: 1.45 }}>{labels.collaborativeHint}</p>
              )}
            </div>
            {taskType === "goal_pipeline" && workflows.length > 0 && (
              <div>
                <label style={{ fontSize: 12, color: C.textMid, display: "block", marginBottom: 6 }}>{labels.workflowLabel ?? "Workflow template"}</label>
                <select
                  title={labels.workflowLabel ?? "Workflow template"}
                  value={workflowIndex}
                  onChange={e => setWorkflowIndex(Number(e.target.value))}
                  style={{ width: "100%", padding: "10px 14px", background: C.surfaceHigh, border: `1px solid ${C.border}`, borderRadius: 9, color: C.text, fontSize: 13 }}
                >
                  {workflows.map(w => (
                    <option key={w.index} value={w.index}>
                      {w.name} · {w.node_count} {labels.workflowStepsSuffix ?? "steps"}
                      {w.roles.length ? ` · ${w.roles.slice(0, 5).join(", ")}${w.roles.length > 5 ? "…" : ""}` : ""}
                    </option>
                  ))}
                </select>
                {labels.workflowRolesHint && (
                  <p style={{ fontSize: 11, color: C.textDim, marginTop: 6, lineHeight: 1.45 }}>{labels.workflowRolesHint}</p>
                )}
              </div>
            )}
            {taskType === "goal_pipeline" && (
              <div>
                <label style={{ fontSize: 12, color: C.textMid, display: "block", marginBottom: 6 }}>{labels.workflowNameLabel ?? "Workflow name (optional)"}</label>
                <input
                  value={workflowNameOverride}
                  onChange={e => setWorkflowNameOverride(e.target.value)}
                  placeholder={labels.workflowNamePlaceholder ?? "Substring match on template name; overrides index"}
                  title={labels.workflowNamePlaceholder ?? ""}
                  style={{ width: "100%", padding: "11px 14px", background: C.surfaceHigh, border: `1px solid ${C.border}`, borderRadius: 9, color: C.text, fontSize: 13, outline: "none" }}
                  onFocus={e => { e.target.style.borderColor = C.accent; }}
                  onBlur={e => { e.target.style.borderColor = C.border; }}
                />
                {labels.workflowNameHint && (
                  <p style={{ fontSize: 11, color: C.textDim, marginTop: 6, lineHeight: 1.45 }}>{labels.workflowNameHint}</p>
                )}
              </div>
            )}
            <div>
              <label style={{ fontSize: 12, color: C.textMid, display: "block", marginBottom: 6 }}>{labels.goalLabel ?? "Goal"}</label>
              <input value={goal} onChange={e => setGoal(e.target.value)} placeholder={labels.goalPlaceholder ?? "e.g. Find 50 fintech companies in MENA…"} style={{ width: "100%", padding: "11px 14px", background: C.surfaceHigh, border: `1px solid ${C.border}`, borderRadius: 9, color: C.text, fontSize: 13, outline: "none" }} onFocus={e => e.target.style.borderColor = C.accent} onBlur={e => e.target.style.borderColor = C.border} />
            </div>
            <div>
              <label style={{ fontSize: 12, color: C.textMid, display: "block", marginBottom: 6 }}>{labels.assignLabel ?? "Assign to"}</label>
              <select value={selectedAgent} onChange={e => setSelectedAgent(e.target.value)} style={{ width: "100%", padding: "10px 14px", background: C.surfaceHigh, border: `1px solid ${C.border}`, borderRadius: 9, color: C.text, fontSize: 13 }}>
                {assignableAgents.length === 0
                  ? <option value="">{taskType === "goal_pipeline" ? (labels.noManagerAgent ?? "No manager agent — reprovision tenant or pick another task type") : "No agents — create one first"}</option>
                  : assignableAgents.map(a => <option key={a.id} value={a.id}>{a.name} ({a.role})</option>)}
              </select>
            </div>
            <button onClick={launchTask} disabled={launching || !goal.trim() || !selectedAgent} style={{ width: "100%", padding: "13px", borderRadius: 9, border: "none", cursor: "pointer", fontWeight: 600, fontSize: 14, background: launching ? C.surfaceHigh : C.accent, color: launching ? C.textMid : "#fff", transition: "all 0.18s" }}>
              {launching ? (labels.launching ?? "⏳ Running…") : (labels.launchButton ?? "🚀 Launch Task")}
            </button>
          </div>
        </div>

        {/* Live log */}
        <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 14, padding: 24, display: "flex", flexDirection: "column" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
            <h3 style={{ fontSize: 15, fontWeight: 600, color: C.text }}>{labels.executionLog ?? "Execution log"}</h3>
            {launching && <span style={{ fontSize: 11, padding: "3px 9px", borderRadius: 20, background: `${C.green}18`, color: C.green, border: `1px solid ${C.green}35` }}>{labels.liveBadge ?? "● Live"}</span>}
          </div>
          <div ref={logRef} style={{ flex: 1, minHeight: 220, maxHeight: 280, overflowY: "auto" }}>
            {liveLogs.length === 0 ? (
              <div style={{ color: C.textDim, fontSize: 13, textAlign: "center", marginTop: 56 }}>
                {labels.emptyLog ?? "Launch a task to see real-time logs here…"}
              </div>
            ) : liveLogs.map((l, i) => (
              <div key={i} style={{ display: "flex", gap: 10, padding: "7px 0", borderBottom: `1px solid ${C.border}` }}>
                <span style={{ fontSize: 10, color: C.textDim, flexShrink: 0, fontVariantNumeric: "tabular-nums", marginTop: 2 }}>{l.time}</span>
                <span style={{ fontSize: 13, flexShrink: 0 }}>{l.icon}</span>
                <span style={{ fontSize: 12, color: l.color, lineHeight: 1.5 }}>{l.msg}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Task history */}
      <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 14, padding: 24 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 18 }}>
          <h3 style={{ fontSize: 15, fontWeight: 600, color: C.text }}>{labels.taskHistory ?? "Task history"}</h3>
          <div style={{ display: "flex", gap: 10 }}>
            <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} style={{ padding: "7px 12px", background: C.surfaceHigh, border: `1px solid ${C.border}`, borderRadius: 8, color: C.text, fontSize: 12 }}>
              {["all", "pending", "running", "done", "failed"].map(s => <option key={s} value={s}>{s === "all" ? labels.all : s}</option>)}
            </select>
            <button onClick={loadTasks} disabled={loading} style={{ padding: "7px 14px", borderRadius: 8, border: `1px solid ${C.border}`, background: C.surfaceHigh, color: C.textMid, fontSize: 12, cursor: "pointer" }}>
              {loading ? "…" : labels.refresh}
            </button>
          </div>
        </div>

        {tasks.length === 0 ? (
          <p style={{ fontSize: 13, color: C.textDim, textAlign: "center", padding: "20px 0" }}>No tasks yet &mdash; launch one above.</p>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ borderBottom: `1px solid ${C.border}` }}>
                {["Task type", "Time", "Agent", "Tokens", "Duration", "Status", "Actions"].map(h => (
                  <th key={h} style={{ padding: "8px 12px", fontSize: 11, color: C.textDim, textAlign: "left", letterSpacing: "0.08em", textTransform: "uppercase" }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {tasks.map(t => {
                return (
                  <tr key={t.id} style={{ borderBottom: `1px solid ${C.border}` }}>
                    <td style={{ padding: "12px", fontSize: 13, color: C.text }}>{taskTypeLabel(t.type)}</td>
                    <td style={{ padding: "12px", fontSize: 12, color: C.textDim }}>{new Date(t.created_at).toLocaleTimeString("en", { hour: "2-digit", minute: "2-digit" })}</td>
                    <td style={{ padding: "12px", fontSize: 12, color: C.textMid }}>—</td>
                    <td style={{ padding: "12px", fontSize: 12, color: C.textMid }}>{t.token_used}</td>
                    <td style={{ padding: "12px", fontSize: 12, color: C.textDim }}>{t.duration_ms != null ? `${t.duration_ms}ms` : "—"}</td>
                    <td style={{ padding: "12px" }}>
                      <span style={{ fontSize: 11, padding: "3px 9px", borderRadius: 20, background: `${STATUS_COLOR[t.status] ?? C.textDim}18`, color: STATUS_COLOR[t.status] ?? C.textDim, border: `1px solid ${STATUS_COLOR[t.status] ?? C.textDim}35` }}>
                        {STATUS_ICON[t.status]} {t.status}
                      </span>
                    </td>
                    <td style={{ padding: "12px" }}>
                      <div style={{ display: "flex", gap: 6 }}>
                        {t.output && (
                          <button onClick={() => setOutputTask(t)} style={{ padding: "4px 10px", borderRadius: 6, border: `1px solid ${C.border}`, background: C.surfaceHigh, color: C.textMid, fontSize: 11, cursor: "pointer" }}>
                            View
                          </button>
                        )}
                        {(t.status === "pending" || t.status === "failed") && (
                          <button onClick={() => enqueue(t.id)} disabled={enqueueing === t.id} style={{ padding: "4px 10px", borderRadius: 6, border: "none", background: C.accent, color: "#fff", fontSize: 11, cursor: "pointer", fontWeight: 600 }}>
                            {enqueueing === t.id ? "…" : "Run"}
                          </button>
                        )}
                        {t.status === "done" && (
                          <button onClick={() => { setFeedbackTask(t.id); setFeedbackScore(""); }} style={{ padding: "4px 10px", borderRadius: 6, border: "none", background: C.green, color: "#07150e", fontSize: 11, cursor: "pointer", fontWeight: 600 }}>
                            Rate
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* Feedback modal */}
      {feedbackTask && (
        <div style={{ position: "fixed", inset: 0, zIndex: 50, display: "flex", alignItems: "center", justifyContent: "center", background: "rgba(0,0,0,0.7)" }}>
          <div style={{ width: 320, background: C.surface, border: `1px solid ${C.border}`, borderRadius: 14, padding: 24 }}>
            <p style={{ fontSize: 14, fontWeight: 600, color: C.text, marginBottom: 14 }}>{labels.feedback}</p>
            <input type="number" min="0" max="1" step="0.05" value={feedbackScore} onChange={e => setFeedbackScore(e.target.value)} placeholder={labels.feedbackPlaceholder} style={{ width: "100%", padding: "11px 14px", background: C.surfaceHigh, border: `1px solid ${C.border}`, borderRadius: 9, color: C.text, fontSize: 14, outline: "none" }} />
            <div style={{ marginTop: 14, display: "flex", justifyContent: "flex-end", gap: 10 }}>
              <button onClick={() => setFeedbackTask(null)} style={{ padding: "8px 14px", borderRadius: 8, border: `1px solid ${C.border}`, background: "transparent", color: C.textMid, fontSize: 12, cursor: "pointer" }}>{labels.close}</button>
              <button onClick={submitFeedback} disabled={submittingFeedback} style={{ padding: "8px 14px", borderRadius: 8, border: "none", background: C.green, color: "#07150e", fontSize: 12, fontWeight: 600, cursor: "pointer" }}>
                {submittingFeedback ? "…" : labels.submitFeedback}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Output modal */}
      {outputTask && (
        <div style={{ position: "fixed", inset: 0, zIndex: 50, display: "flex", alignItems: "center", justifyContent: "center", background: "rgba(0,0,0,0.7)", padding: 16 }}>
          <div style={{ maxHeight: "70vh", width: "100%", maxWidth: 640, display: "flex", flexDirection: "column", background: C.surface, border: `1px solid ${C.border}`, borderRadius: 14 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "16px 20px", borderBottom: `1px solid ${C.border}` }}>
              <p style={{ fontSize: 14, fontWeight: 600, color: C.text }}>{outputTask.type} output</p>
              <button onClick={() => setOutputTask(null)} style={{ padding: "6px 12px", borderRadius: 8, border: `1px solid ${C.border}`, background: "transparent", color: C.textMid, fontSize: 12, cursor: "pointer" }}>{labels.close}</button>
            </div>
            <div style={{ flex: 1, overflowY: "auto", padding: 20 }}>
              <pre style={{ whiteSpace: "pre-wrap", fontFamily: "monospace", fontSize: 11, color: C.textMid, lineHeight: 1.6 }}>
                {JSON.stringify(outputTask.output, null, 2)}
              </pre>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
