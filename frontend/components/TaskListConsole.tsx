"use client";

import { useCallback, useEffect, useRef, useState } from "react";
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
  smartLaunchHint?: string;
  smartLaunchProgress?: string;
  smartLaunchButton?: string;
  advancedManual?: string;
  noAgentsHint?: string;
  resolvedRouting?: string;
  /** Smart launch: optional primary executor (empty = auto). */
  smartPrimaryAgentLabel?: string;
  smartPrimaryAgentAuto?: string;
  /** Task history table headers */
  historyColTaskType?: string;
  historyColTime?: string;
  historyColAgent?: string;
  historyColTokens?: string;
  historyColDuration?: string;
  historyColStatus?: string;
  historyColActions?: string;
  historyEmpty?: string;
  historyAgentDash?: string;
  outputTitleTemplate?: string;
  viewOutput?: string;
  syncRosterButton?: string;
  syncRosterRunning?: string;
  syncRosterDone?: string;
  pipelineStageDone?: string;
  pipelineStageSkipped?: string;
  pipelineSummaryHeader?: string;
  pipelineStagesTitle?: string;
  pipelineGoal?: string;
  pipelineWorkflow?: string;
  pipelineLeadsPreview?: string;
  pipelineRawToggle?: string;
  pipelineManagerHint?: string;
  /** Shown when backend queued a manager_skill_closure after skipped pipeline stages. Use {id} for closure task id. */
  pipelineSkillGapFollowup?: string;
  outputQualityHint?: string;
};

const C = {
  bg: "#07090f", surface: "#0d1017", surfaceHigh: "#13171f",
  border: "rgba(255,255,255,0.06)", text: "#e8eaf0", textMid: "#8892a4",
  textDim: "#3d4557", accent: "#5b6ef5", green: "#2dd4a0",
  amber: "#f5a524", red: "#f25f5c", purple: "#a78bfa",
};

type AgentRow = { id: string; name: string; role: string };
type TaskRow = {
  id: string;
  agent_id: string;
  type: string;
  status: string;
  token_used: number;
  duration_ms: number | null;
  output: Record<string, unknown> | null;
  created_at: string;
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

function isPipelineOutput(out: Record<string, unknown> | null | undefined): out is Record<string, unknown> & { stages: unknown[] } {
  return !!out && out.collaborative === true && Array.isArray(out.stages);
}

function appendPipelineCompletionLogs(
  out: Record<string, unknown> | null,
  addLog: (icon: string, msg: string, color?: string) => void,
  labels: TaskListLabels,
) {
  if (!isPipelineOutput(out)) return;
  const stages = out.stages as Array<Record<string, unknown>>;
  addLog("📊", labels.pipelineSummaryHeader ?? "Pipeline summary", C.accent);
  for (const s of stages) {
    if (s.skipped === true) {
      const role = String(s.role ?? "?");
      const reason = String(s.reason ?? "unknown");
      const line = (labels.pipelineStageSkipped ?? "{role} · skipped: {reason}")
        .replace("{role}", role)
        .replace("{reason}", reason);
      addLog("⏭️", line, C.amber);
      continue;
    }
    const role = String(s.role ?? "?");
    const taskType = String(s.task_type ?? "");
    const agent = String(s.agent_name ?? "");
    const tokens = s.tokens != null ? String(s.tokens) : "0";
    const line = (labels.pipelineStageDone ?? "{role} · {taskType} — {agent} ({tokens} tokens)")
      .replace("{role}", role)
      .replace("{taskType}", taskType)
      .replace("{agent}", agent)
      .replace("{tokens}", tokens);
    addLog("🤝", line, C.textMid);
  }
  if (stages.some((x) => x.skipped === true) && labels.pipelineManagerHint) {
    addLog("🧭", labels.pipelineManagerHint, C.amber);
  }
  const sku = out.skill_gap_followup;
  if (sku && typeof sku === "object" && !Array.isArray(sku) && labels.pipelineSkillGapFollowup) {
    const cid = String((sku as Record<string, unknown>).closure_task_id ?? "");
    if (cid) {
      addLog("🧩", labels.pipelineSkillGapFollowup.replace("{id}", cid), C.purple);
    }
  }
  if (labels.outputQualityHint) {
    addLog("💡", labels.outputQualityHint, C.textDim);
  }
}

function GoalPipelineOutputBody({
  output,
  labels,
  showRaw,
  onToggleRaw,
}: {
  output: Record<string, unknown> & { stages: unknown[] };
  labels: TaskListLabels;
  showRaw: boolean;
  onToggleRaw: () => void;
}) {
  const goal = String(output.goal ?? "");
  const wf = String(output.workflow ?? "");
  const stages = (output.stages as Array<Record<string, unknown>>) ?? [];

  const firstLead = (() => {
    const L = output.leads;
    if (L && typeof L === "object" && !Array.isArray(L)) {
      const leads = (L as { leads?: unknown }).leads;
      if (Array.isArray(leads) && leads[0] && typeof leads[0] === "object") {
        return leads[0] as Record<string, unknown>;
      }
    }
    if (Array.isArray(L) && L[0] && typeof L[0] === "object") return L[0] as Record<string, unknown>;
    return null;
  })();

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      {(goal || wf) && (
        <div style={{ padding: 12, borderRadius: 10, background: C.surfaceHigh, border: `1px solid ${C.border}` }}>
          {goal ? (
            <p style={{ margin: "0 0 6px", fontSize: 12, color: C.textDim }}>
              {labels.pipelineGoal ?? "Goal"}
            </p>
          ) : null}
          {goal ? <p style={{ margin: 0, fontSize: 13, color: C.text, lineHeight: 1.5 }}>{goal}</p> : null}
          {wf ? (
            <p style={{ margin: goal ? "10px 0 0" : 0, fontSize: 12, color: C.textDim }}>
              {labels.pipelineWorkflow ?? "Workflow"}: <span style={{ color: C.textMid }}>{wf}</span>
            </p>
          ) : null}
        </div>
      )}

      <div>
        <p style={{ margin: "0 0 8px", fontSize: 12, fontWeight: 600, color: C.text }}>
          {labels.pipelineStagesTitle ?? "Collaboration stages"}
        </p>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
          <thead>
            <tr style={{ borderBottom: `1px solid ${C.border}`, color: C.textDim, textAlign: "left" }}>
              <th style={{ padding: "6px 8px" }}>Role</th>
              <th style={{ padding: "6px 8px" }}>Step</th>
              <th style={{ padding: "6px 8px" }}>Agent</th>
              <th style={{ padding: "6px 8px", textAlign: "right" }}>Tokens</th>
            </tr>
          </thead>
          <tbody>
            {stages.map((s, i) => {
              const skipped = s.skipped === true;
              return (
                <tr key={i} style={{ borderBottom: `1px solid ${C.border}`, color: skipped ? C.amber : C.textMid }}>
                  <td style={{ padding: "8px", fontWeight: 600, color: C.text }}>{String(s.role ?? "—")}</td>
                  <td style={{ padding: "8px" }}>
                    {skipped ? (
                      <span style={{ color: C.amber }}>skipped ({String(s.reason ?? "")})</span>
                    ) : (
                      String(s.task_type ?? "—")
                    )}
                  </td>
                  <td style={{ padding: "8px" }}>{skipped ? "—" : String(s.agent_name ?? "—")}</td>
                  <td style={{ padding: "8px", textAlign: "right" }}>{skipped ? "—" : String(s.tokens ?? 0)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {(() => {
        const fu = output.skill_gap_followup;
        if (!fu || typeof fu !== "object" || Array.isArray(fu)) return null;
        const id = String((fu as Record<string, unknown>).closure_task_id ?? "");
        if (!id || !labels.pipelineSkillGapFollowup) return null;
        return (
          <div
            style={{
              padding: 10,
              borderRadius: 8,
              border: `1px solid ${C.border}`,
              background: "rgba(167,139,250,0.08)",
            }}
          >
            <p style={{ margin: 0, fontSize: 12, color: C.purple, lineHeight: 1.5 }}>
              {labels.pipelineSkillGapFollowup.replace("{id}", id)}
            </p>
          </div>
        );
      })()}

      {firstLead && (
        <div style={{ padding: 12, borderRadius: 10, border: `1px solid ${C.border}`, background: "rgba(91,110,245,0.06)" }}>
          <p style={{ margin: "0 0 6px", fontSize: 12, color: C.textDim }}>{labels.pipelineLeadsPreview ?? "Lead preview"}</p>
          <p style={{ margin: 0, fontSize: 13, color: C.text }}>
            {String(firstLead.contact_name ?? firstLead.name ?? "")}{" "}
            {firstLead.email ? <span style={{ color: C.accent }}>· {String(firstLead.email)}</span> : null}
          </p>
          {(firstLead.company_name ?? firstLead.company) ? (
            <p style={{ margin: "6px 0 0", fontSize: 12, color: C.textMid }}>
              {String(firstLead.company_name ?? firstLead.company)}
              {firstLead.score != null || firstLead["得分"] != null ? (
                <span style={{ marginLeft: 8 }}>· score {String(firstLead.score ?? firstLead["得分"])}</span>
              ) : null}
            </p>
          ) : null}
        </div>
      )}

      <button
        type="button"
        onClick={onToggleRaw}
        style={{ alignSelf: "flex-start", padding: "6px 12px", borderRadius: 8, border: `1px solid ${C.border}`, background: "transparent", color: C.accent, fontSize: 12, cursor: "pointer" }}
      >
        {showRaw ? "↑ " : ""}{labels.pipelineRawToggle ?? "Raw JSON"}
      </button>
      {showRaw ? (
        <pre style={{ whiteSpace: "pre-wrap", fontFamily: "monospace", fontSize: 11, color: C.textMid, lineHeight: 1.6, margin: 0 }}>
          {JSON.stringify(output, null, 2)}
        </pre>
      ) : null}
    </div>
  );
}

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
  const [showOutputRaw, setShowOutputRaw] = useState(false);

  // Launch panel state
  const [taskType, setTaskType] = useState("goal_pipeline");
  const [goal, setGoal] = useState("");
  const [selectedAgent, setSelectedAgent] = useState("");
  const [launching, setLaunching] = useState(false);
  const [smartExecutorId, setSmartExecutorId] = useState("");
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

  useEffect(() => {
    if (agents.length === 0) {
      setSelectedAgent("");
      return;
    }
    if (!selectedAgent || !agents.some(a => a.id === selectedAgent)) {
      setSelectedAgent(agents[0].id);
    }
  }, [agents, selectedAgent]);

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
    if (tenantId) void loadWorkflows();
  }, [tenantId, loadWorkflows]);

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

  const agentDisplayName = useCallback(
    (agentId: string | undefined) => {
      if (!agentId) return labels.historyAgentDash ?? "—";
      const a = agents.find(x => x.id === agentId);
      if (a) return `${a.name} (${a.role})`;
      return `${agentId.slice(0, 8)}…`;
    },
    [agents, labels.historyAgentDash],
  );

  const addLog = (icon: string, msg: string, color = C.textMid) => {
    const time = new Date().toLocaleTimeString("en", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
    setLiveLogs(prev => [...prev, { time, icon, msg, color }]);
  };

  const afterTaskCreated = async (task: TaskRow, runnerLabel: string) => {
    addLog("✅", `Task created (ID: ${task.id.slice(0, 8)}…)`, C.green);
    addLog("⚡", `Memory layer: retrieving relevant past experiences…`, C.purple);
    const enqRes = await fetch(apiUrl(`/api/v1/tasks/${task.id}/enqueue`), { method: "POST" });
    if (!enqRes.ok) {
      addLog("❌", `Failed to enqueue: ${enqRes.status}`, C.red);
      setLaunching(false);
      return;
    }
    addLog("⏳", `${runnerLabel} is now running…`, C.amber);
    let attempts = 0;
    const poll = setInterval(async () => {
      attempts++;
      const tRes = await fetch(apiUrl(`/api/v1/tasks/${task.id}`));
      if (!tRes.ok) return;
      const updated: TaskRow = await tRes.json();
      if (updated.status === "done") {
        clearInterval(poll);
        addLog("✅", `Task completed! Duration: ${updated.duration_ms}ms · Tokens: ${updated.token_used}`, C.green);
        appendPipelineCompletionLogs(updated.output, addLog, labels);
        setLiveLogs(prev => [...prev, { time: new Date().toLocaleTimeString("en", { hour: "2-digit", minute: "2-digit", second: "2-digit" }), icon: "🧠", msg: "Memory saved — this experience will improve future tasks", color: C.purple }]);
        setGoal("");
        setLaunching(false);
        await loadTasks();
      } else if (updated.status === "failed") {
        clearInterval(poll);
        addLog("❌", `Task failed. ${JSON.stringify(updated.output ?? {}).slice(0, 80)}`, C.red);
        setLaunching(false);
        await loadTasks();
      } else if (attempts > 60) {
        clearInterval(poll);
        setLaunching(false);
      }
    }, 3000);
  };

  const syncEnterpriseRoster = async () => {
    if (!tenantId) return;
    addLog("📦", labels.syncRosterRunning ?? "Syncing enterprise roster (54 roles + skills)…", C.accent);
    try {
      const res = await fetch(apiUrl(`/api/v1/tenants/${tenantId}/sync-enterprise-roster`), { method: "POST" });
      const j = await res.json().catch(() => ({}));
      if (!res.ok) {
        addLog("❌", `${res.status} ${JSON.stringify(j).slice(0, 200)}`, C.red);
        return;
      }
      const msg = labels.syncRosterDone
        ? labels.syncRosterDone
            .replace("{a}", String(j.agents_added ?? 0))
            .replace("{r}", String(j.agents_reactivated ?? 0))
            .replace("{s}", String(j.skills_added ?? 0))
        : `Roster sync: +${j.agents_added ?? 0} agents, reactivated ${j.agents_reactivated ?? 0}, +${j.skills_added ?? 0} skills`;
      addLog("✅", msg, C.green);
      await loadAgents();
    } catch (e) {
      addLog("❌", String(e), C.red);
    }
  };

  const launchSmartTask = async () => {
    if (!tenantId || !goal.trim()) return;
    setLaunching(true);
    setLiveLogs([]);
    addLog("🧭", labels.smartLaunchProgress ?? "Resolving task type and agent from your description…", C.accent);
    try {
      const wn = workflowNameOverride.trim();
      const body: Record<string, unknown> = { tenant_id: tenantId, goal: goal.trim() };
      if (wn) body.workflow_name = wn;
      else if (workflows.length > 0) body.workflow_index = workflowIndex;
      if (smartExecutorId) body.agent_id = smartExecutorId;

      const createRes = await fetch(apiUrl("/api/v1/tasks/smart"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!createRes.ok) {
        const errText = await createRes.text();
        addLog("❌", `${createRes.status} ${errText.slice(0, 220)}`, C.red);
        setLaunching(false);
        return;
      }
      const data: {
        task: TaskRow;
        resolved: {
          task_type: string;
          agent_name: string;
          agent_role: string;
          plan_reasoning?: string | null;
          workflow_template?: string | null;
          workflow_index?: number | null;
        };
      } = await createRes.json();
      const r = data.resolved;
      if (r.plan_reasoning) {
        addLog("🧠", r.plan_reasoning, C.textMid);
      }
      if (r.workflow_template) {
        const wfLine = r.workflow_index != null && r.workflow_index >= 0
          ? `${r.workflow_template} (#${r.workflow_index})`
          : r.workflow_template;
        addLog("📋", wfLine, C.textMid);
      }
      const line = labels.resolvedRouting
        ? labels.resolvedRouting
            .replace("{type}", taskTypeLabel(r.task_type))
            .replace("{name}", r.agent_name)
            .replace("{role}", r.agent_role)
        : `Matched: ${taskTypeLabel(r.task_type)} · ${r.agent_name} (${r.agent_role})`;
      addLog("✨", line, C.purple);
      await afterTaskCreated(data.task, r.agent_name);
    } catch (e) {
      addLog("❌", String(e), C.red);
      setLaunching(false);
    }
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
      await afterTaskCreated(task, agent?.name ?? "Agent");
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
            {labels.smartLaunchHint && (
              <p style={{ fontSize: 12, color: C.textMid, lineHeight: 1.5, margin: 0 }}>{labels.smartLaunchHint}</p>
            )}
            <div>
              <label style={{ fontSize: 12, color: C.textMid, display: "block", marginBottom: 6 }}>{labels.goalLabel ?? "Goal"}</label>
              <input value={goal} onChange={e => setGoal(e.target.value)} placeholder={labels.goalPlaceholder ?? "e.g. Find 50 fintech companies in MENA…"} style={{ width: "100%", padding: "11px 14px", background: C.surfaceHigh, border: `1px solid ${C.border}`, borderRadius: 9, color: C.text, fontSize: 13, outline: "none" }} onFocus={e => { e.target.style.borderColor = C.accent; }} onBlur={e => { e.target.style.borderColor = C.border; }} />
            </div>
            {agents.length > 0 && (
              <div>
                <label style={{ fontSize: 12, color: C.textMid, display: "block", marginBottom: 6 }}>{labels.smartPrimaryAgentLabel ?? "Primary executor (optional)"}</label>
                <select
                  title={labels.smartPrimaryAgentLabel ?? ""}
                  value={smartExecutorId}
                  onChange={e => setSmartExecutorId(e.target.value)}
                  style={{ width: "100%", padding: "10px 14px", background: C.surfaceHigh, border: `1px solid ${C.border}`, borderRadius: 9, color: C.text, fontSize: 13 }}
                >
                  <option value="">{labels.smartPrimaryAgentAuto ?? "Auto — system picks best match"}</option>
                  {agents.map(a => (
                    <option key={a.id} value={a.id}>{a.name} ({a.role})</option>
                  ))}
                </select>
              </div>
            )}
            <button type="button" onClick={launchSmartTask} disabled={launching || !goal.trim() || agents.length === 0} style={{ width: "100%", padding: "13px", borderRadius: 9, border: "none", cursor: agents.length === 0 ? "not-allowed" : "pointer", fontWeight: 600, fontSize: 14, background: launching || agents.length === 0 ? C.surfaceHigh : C.accent, color: launching || agents.length === 0 ? C.textMid : "#fff", transition: "all 0.18s" }}>
              {launching ? (labels.launching ?? "⏳ Running…") : (labels.smartLaunchButton ?? "🧭 Smart launch")}
            </button>
            {tenantId && (
              <button type="button" onClick={syncEnterpriseRoster} disabled={launching} style={{ width: "100%", padding: "8px", borderRadius: 8, border: `1px solid ${C.border}`, background: "transparent", color: C.textMid, fontSize: 11, cursor: launching ? "not-allowed" : "pointer" }}>
                {labels.syncRosterButton ?? "Sync full roster (54 roles + skills)"}
              </button>
            )}
            {agents.length === 0 && labels.noAgentsHint && (
              <p style={{ fontSize: 11, color: C.amber, margin: 0, lineHeight: 1.45 }}>{labels.noAgentsHint}</p>
            )}

            <details style={{ borderTop: `1px solid ${C.border}`, paddingTop: 14 }}>
              <summary style={{ cursor: "pointer", fontSize: 12, color: C.accent, fontWeight: 500 }}>{labels.advancedManual ?? "Advanced — manual task type & assignee"}</summary>
              <div style={{ display: "flex", flexDirection: "column", gap: 14, marginTop: 14 }}>
                <div>
                  <label style={{ fontSize: 12, color: C.textMid, display: "block", marginBottom: 6 }}>{labels.taskTypeLabel ?? labels.type}</label>
                  <select title={labels.taskTypeLabel ?? labels.type} value={taskType} onChange={e => setTaskType(e.target.value)} style={{ width: "100%", padding: "10px 14px", background: C.surfaceHigh, border: `1px solid ${C.border}`, borderRadius: 9, color: C.text, fontSize: 13 }}>
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
                  <label style={{ fontSize: 12, color: C.textMid, display: "block", marginBottom: 6 }}>{labels.assignLabel ?? "Assign to"}</label>
                  <select title={labels.assignLabel ?? "Assign to"} value={selectedAgent} onChange={e => setSelectedAgent(e.target.value)} style={{ width: "100%", padding: "10px 14px", background: C.surfaceHigh, border: `1px solid ${C.border}`, borderRadius: 9, color: C.text, fontSize: 13 }}>
                    {agents.length === 0
                      ? <option value="">{labels.noAgentsHint ?? "No agents — create one first"}</option>
                      : agents.map(a => <option key={a.id} value={a.id}>{a.name} ({a.role})</option>)}
                  </select>
                </div>
                <button type="button" onClick={launchTask} disabled={launching || !goal.trim() || !selectedAgent} style={{ width: "100%", padding: "13px", borderRadius: 9, border: `1px solid ${C.border}`, cursor: "pointer", fontWeight: 600, fontSize: 14, background: C.surfaceHigh, color: C.text, transition: "all 0.18s" }}>
                  {launching ? (labels.launching ?? "⏳ Running…") : (labels.launchButton ?? "🚀 Manual launch")}
                </button>
              </div>
            </details>
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
          <p style={{ fontSize: 13, color: C.textDim, textAlign: "center", padding: "20px 0" }}>{labels.historyEmpty ?? labels.empty ?? "No tasks yet."}</p>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ borderBottom: `1px solid ${C.border}` }}>
                {[
                  labels.historyColTaskType ?? "Task type",
                  labels.historyColTime ?? "Time",
                  labels.historyColAgent ?? "Agent",
                  labels.historyColTokens ?? "Tokens",
                  labels.historyColDuration ?? "Duration",
                  labels.historyColStatus ?? "Status",
                  labels.historyColActions ?? "Actions",
                ].map(h => (
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
                    <td style={{ padding: "12px", fontSize: 12, color: C.textMid }}>{agentDisplayName(t.agent_id)}</td>
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
                          <button onClick={() => { setShowOutputRaw(false); setOutputTask(t); }} style={{ padding: "4px 10px", borderRadius: 6, border: `1px solid ${C.border}`, background: C.surfaceHigh, color: C.textMid, fontSize: 11, cursor: "pointer" }}>
                            {labels.viewOutput ?? "View"}
                          </button>
                        )}
                        {(t.status === "pending" || t.status === "failed") && (
                          <button onClick={() => enqueue(t.id)} disabled={enqueueing === t.id} style={{ padding: "4px 10px", borderRadius: 6, border: "none", background: C.accent, color: "#fff", fontSize: 11, cursor: "pointer", fontWeight: 600 }}>
                            {enqueueing === t.id ? "…" : labels.enqueue}
                          </button>
                        )}
                        {t.status === "done" && (
                          <button onClick={() => { setFeedbackTask(t.id); setFeedbackScore(""); }} style={{ padding: "4px 10px", borderRadius: 6, border: "none", background: C.green, color: "#07150e", fontSize: 11, cursor: "pointer", fontWeight: 600 }}>
                            {labels.feedback}
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
          <div style={{ maxHeight: "85vh", width: "100%", maxWidth: isPipelineOutput(outputTask.output) ? 720 : 640, display: "flex", flexDirection: "column", background: C.surface, border: `1px solid ${C.border}`, borderRadius: 14 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "16px 20px", borderBottom: `1px solid ${C.border}` }}>
              <p style={{ fontSize: 14, fontWeight: 600, color: C.text }}>{(labels.outputTitleTemplate ?? "{type} output").replace("{type}", taskTypeLabel(outputTask.type))}</p>
              <button onClick={() => { setOutputTask(null); setShowOutputRaw(false); }} style={{ padding: "6px 12px", borderRadius: 8, border: `1px solid ${C.border}`, background: "transparent", color: C.textMid, fontSize: 12, cursor: "pointer" }}>{labels.close}</button>
            </div>
            <div style={{ flex: 1, overflowY: "auto", padding: 20 }}>
              {isPipelineOutput(outputTask.output) ? (
                <GoalPipelineOutputBody
                  output={outputTask.output}
                  labels={labels}
                  showRaw={showOutputRaw}
                  onToggleRaw={() => setShowOutputRaw((v) => !v)}
                />
              ) : (
                <pre style={{ whiteSpace: "pre-wrap", fontFamily: "monospace", fontSize: 11, color: C.textMid, lineHeight: 1.6 }}>
                  {JSON.stringify(outputTask.output, null, 2)}
                </pre>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
