"""Celery tasks — real agent execution with status tracking and performance logging."""
from __future__ import annotations

import asyncio
import time
import uuid
from datetime import datetime, timezone

from app.workers.celery_app import celery_app


@celery_app.task(name="titan.ping")
def ping() -> str:
    return "pong"


@celery_app.task(name="titan.enqueue_agent_task", bind=True, max_retries=2)
def enqueue_agent_task(self, task_id: str) -> dict:
    """Load agent from DB, run it, write back result + performance log."""
    return asyncio.get_event_loop().run_until_complete(_run_task(task_id))


async def _run_task(task_id: str) -> dict:
    from app.agents.hunter_agent import HunterAgent
    from app.agents.outreach_agent import OutreachAgent
    from app.agents.researcher_agent import ResearcherAgent
    from app.agents.delivery_agent import DeliveryAgent
    from app.agents.manager_agent import ManagerAgent
    from app.agents.base_agent import TaskStub
    from app.core.database import AsyncSessionLocal
    from app.memory.long_term import save_memory
    from app.memory.short_term import cache_agent_perf, save_context
    from app.memory.closure_assessment_sync import (
        build_performance_log_extra,
        upsert_gap_closure_skill_ledger,
    )
    from app.memory.skill_manager import maybe_create_skill
    from app.models.domain import Agent, PerformanceLog, Task

    _ROLE_MAP = {
        "hunter": HunterAgent,
        "outreach": OutreachAgent,
        "researcher": ResearcherAgent,
        "delivery": DeliveryAgent,
        "manager": ManagerAgent,
    }

    async with AsyncSessionLocal() as db:
        task: Task | None = await db.get(Task, uuid.UUID(task_id))
        if task is None:
            return {"error": "task not found"}

        agent: Agent | None = await db.get(Agent, task.agent_id)
        if agent is None:
            task.status = "failed"
            task.output = {"error": "agent not found"}
            await db.commit()
            return {"error": "agent not found"}

        from app.workers.pipeline_followup import MANAGER_SKILL_CLOSURE, maybe_schedule_skill_gap_closure

        task.status = "running"
        await db.commit()

        AgentClass = _ROLE_MAP.get(agent.role)

        start = time.time()
        success = False
        result_output: dict = {}
        token_used = 0
        error_msg: str | None = None
        closure_task_to_enqueue: str | None = None

        try:
            if task.task_type == "goal_pipeline":
                from app.workers.goal_pipeline import run_goal_pipeline

                result_output, token_used, success, error_msg = await run_goal_pipeline(
                    db=db, task=task, coordinator_agent=agent
                )
                if not success and error_msg:
                    result_output = {**result_output, "error": error_msg}
                elif success and isinstance(result_output, dict):
                    cid = await maybe_schedule_skill_gap_closure(
                        db,
                        parent_task=task,
                        pipeline_output=result_output,
                        coordinator=agent,
                    )
                    if cid:
                        closure_task_to_enqueue = cid
                        result_output = {
                            **result_output,
                            "skill_gap_followup": {
                                "closure_task_id": cid,
                                "status": "queued",
                            },
                        }
            elif task.task_type == MANAGER_SKILL_CLOSURE:
                from app.workers.skill_gap_closure import run_skill_gap_closure

                result_output, token_used, success, error_msg = await run_skill_gap_closure(
                    db=db, task=task, manager=agent
                )
                if not success and error_msg:
                    result_output = {**result_output, "error": error_msg}
            elif task.task_type == "parallel_team":
                from app.workers.parallel_team import run_parallel_team

                result_output, token_used, success, error_msg = await run_parallel_team(
                    db=db, task=task, coordinator=agent
                )
                if not success and error_msg:
                    result_output = {**result_output, "error": error_msg}
            else:
                if AgentClass is not None:
                    runner = AgentClass(
                        agent_id=str(agent.id),
                        tenant_id=str(agent.tenant_id),
                        current_prompt=agent.current_prompt,
                    )
                else:
                    from app.agents.generic_role_agent import GenericRoleAgent

                    runner = GenericRoleAgent(
                        agent_id=str(agent.id),
                        tenant_id=str(agent.tenant_id),
                        current_prompt=agent.current_prompt,
                        role_key=agent.role,
                    )
                stub = TaskStub(id=task_id, type=task.task_type, input=task.input)
                result = await runner.run(stub)
                result_output = result.output
                token_used = result.token_used
                success = True
        except Exception as exc:
            error_msg = str(exc)
            result_output = {"error": error_msg}

        elapsed_ms = int((time.time() - start) * 1000)

        task.status = "done" if success else "failed"
        task.output = result_output
        task.token_used = token_used
        task.duration_ms = elapsed_ms
        task.completed_at = datetime.now(tz=timezone.utc)

        out_dict: dict = result_output if isinstance(result_output, dict) else {}
        perf_extra = build_performance_log_extra(
            task=task,
            agent=agent,
            task_type=task.task_type,
            result_output=out_dict,
            success=success,
        )
        if success and task.task_type == MANAGER_SKILL_CLOSURE:
            await upsert_gap_closure_skill_ledger(
                db,
                tenant_id=task.tenant_id,
                manager_agent=agent,
                task=task,
                result_output=out_dict,
                success=success,
            )

        perf = PerformanceLog(
            tenant_id=task.tenant_id,
            agent_id=task.agent_id,
            task_id=task.id,
            success_flag=success,
            token_cost=token_used,
            latency_ms=elapsed_ms,
            auto_eval_reason=error_msg,
            extra=perf_extra,
        )
        db.add(perf)
        await db.commit()

        if closure_task_to_enqueue:
            enqueue_agent_task.delay(closure_task_to_enqueue)

        if success and task.task_type == MANAGER_SKILL_CLOSURE:
            rows = result_output.get("child_tasks_spawned") if isinstance(result_output, dict) else None
            if isinstance(rows, list):
                for row in rows:
                    if isinstance(row, dict) and row.get("task_id"):
                        enqueue_agent_task.delay(str(row["task_id"]))

        # ── Quota + Billing ───────────────────────────────────────────────────
        from app.models.domain import Tenant as _Tenant
        from sqlalchemy import func as _func, select as _select
        from app.models.domain import Agent as _Agent

        tenant_obj = await db.get(_Tenant, task.tenant_id)
        plan = tenant_obj.plan if tenant_obj else "starter"

        if token_used:
            from app.core.quota import check_and_consume
            await check_and_consume(str(task.tenant_id), plan, token_used)

        if success:
            from app.services.billing import record_task_usage
            agent_count_q = await db.execute(
                _select(_func.count()).select_from(_Agent)
                .where(_Agent.tenant_id == task.tenant_id)
                .where(_Agent.status == "active")
            )
            agent_count = agent_count_q.scalar_one() or 0
            await record_task_usage(db, task.tenant_id, plan, token_used, agent_count)
        # ─────────────────────────────────────────────────────────────────────

        # ── Memory layer ──────────────────────────────────────────────────────
        # Save working context (Redis, TTL 24h)
        await save_context(task_id, {"type": task.task_type, "input": task.input, "output": result_output})

        # Save episodic memory (Qdrant)
        summary = _summarise(task.task_type, task.input, result_output, success)
        await save_memory(
            tenant_id=str(task.tenant_id),
            agent_id=str(task.agent_id),
            task_id=task_id,
            task_type=task.task_type,
            summary=summary,
            success_flag=success,
            quality_score=None,  # human feedback updates this later
            tags=[task.task_type, agent.role],
        )

        # Cache score for evolution trigger
        auto_score = 0.8 if success else 0.2
        await cache_agent_perf(str(task.agent_id), auto_score)

        # Skill distillation (only on high-quality success; score set after human feedback)
        if success and task.task_type != MANAGER_SKILL_CLOSURE:
            await maybe_create_skill(
                db=db,
                tenant_id=task.tenant_id,
                agent_id=task.agent_id,
                agent_role=agent.role,
                task_type=task.task_type,
                task_input=task.input,
                task_output=result_output,
                quality_score=auto_score,
            )
        # ─────────────────────────────────────────────────────────────────────

        return {"task_id": task_id, "status": task.status, "duration_ms": elapsed_ms}


def _summarise(task_type: str, inp: dict, out: dict, success: bool) -> str:
    """Build a short text summary of the task for embedding."""
    inp_str = str(inp)[:200]
    out_str = str(out)[:300]
    return f"[{task_type}] success={success} | input={inp_str} | output={out_str}"
