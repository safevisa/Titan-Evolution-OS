"""Map workflow DAG nodes (role + task_type) to catalog capability ids."""
from __future__ import annotations

from typing import Any

# (role, task_type) -> canonical capability id (grants / execute_capability).
ROLE_TASK_CAPABILITY: dict[tuple[str, str], str] = {
    ("hunter", "lead_search"): "apollo_search",
    ("hunter", "icp_search"): "apollo_search",
    ("outreach", "email_write"): "resend_email",
    ("outreach", "trial_invite"): "resend_email",
    ("outreach", "follow_up_email"): "resend_email",
}


def capability_id_for_node(role: str | None, task_type: str | None) -> str | None:
    if not role or not task_type:
        return None
    return ROLE_TASK_CAPABILITY.get((role.strip(), task_type.strip()))


def enrich_workflow_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Ensure each node has capability_id when a mapping exists."""
    out: list[dict[str, Any]] = []
    for raw in nodes:
        node = dict(raw)
        if not node.get("capability_id"):
            cap = capability_id_for_node(
                str(node.get("role") or ""),
                str(node.get("task_type") or ""),
            )
            if cap:
                node["capability_id"] = cap
        out.append(node)
    return out


def enrich_dag_config(dag_config: dict[str, Any]) -> dict[str, Any]:
    dag = dict(dag_config or {})
    nodes = dag.get("nodes")
    if isinstance(nodes, list):
        dag["nodes"] = enrich_workflow_nodes([n for n in nodes if isinstance(n, dict)])
    return dag
