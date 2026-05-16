"""Computer-use-runner — isolated Agent-S HTTP API (TEO-DUAL M03)."""
from __future__ import annotations

import threading
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from app.agent_loop import run_agent_loop
from app.sandbox import acquire_run_lock, open_sandbox
from app.settings import get_settings

app = FastAPI(title="Titan Computer Use Runner", version="1.0.0")

_store: dict[str, dict[str, Any]] = {}
_cancel_flags: dict[str, threading.Event] = {}


class CreateRunBody(BaseModel):
    instruction: str = Field(..., min_length=1, max_length=8000)
    max_steps: int = Field(default=30, ge=1, le=50)
    width: int | None = None
    height: int | None = None
    enable_local_env: bool | None = None


def _auth(token: str | None) -> None:
    expected = get_settings().runner_token
    if not expected or token != expected:
        raise HTTPException(status_code=401, detail="invalid_runner_token")


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _execute_run(run_id: str) -> None:
    row = _store.get(run_id)
    if row is None:
        return
    cancel_ev = _cancel_flags.setdefault(run_id, threading.Event())

    def cancelled() -> bool:
        return cancel_ev.is_set()

    lock = acquire_run_lock()
    with lock:
        if cancelled():
            row["status"] = "cancelled"
            row["finished_at"] = _now_iso()
            return
        row["status"] = "running"
        sandbox = open_sandbox()
        try:
            sandbox.start()
            result = run_agent_loop(
                instruction=str(row["instruction"]),
                max_steps=int(row["max_steps"]),
                cancelled=cancelled,
            )
        except Exception as exc:
            row["status"] = "failed"
            row["error"] = str(exc)[:800]
            row["finished_at"] = _now_iso()
            return
        finally:
            sandbox.stop()

    if cancelled():
        row["status"] = "cancelled"
    else:
        row["status"] = result.status
        row["step_count"] = result.step_count
        row["artifact"] = result.artifact
        row["error"] = result.error
    row["finished_at"] = _now_iso()


@app.get("/health")
def health() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "agent_s_mode": settings.agent_s_mode,
    }


@app.post("/v1/runs")
def create_run(
    body: CreateRunBody,
    x_runner_token: str | None = Header(default=None, alias="X-Runner-Token"),
) -> dict[str, Any]:
    _auth(x_runner_token)
    run_id = str(uuid.uuid4())
    _store[run_id] = {
        "run_id": run_id,
        "instruction": body.instruction.strip(),
        "max_steps": body.max_steps,
        "status": "queued",
        "step_count": 0,
        "artifact": {},
        "error": None,
        "created_at": _now_iso(),
        "finished_at": None,
    }
    _cancel_flags[run_id] = threading.Event()
    threading.Thread(target=_execute_run, args=(run_id,), daemon=True).start()
    return {"run_id": run_id, "status": "queued"}


@app.get("/v1/runs/{run_id}")
def get_run(
    run_id: str,
    x_runner_token: str | None = Header(default=None, alias="X-Runner-Token"),
) -> dict[str, Any]:
    _auth(x_runner_token)
    row = _store.get(run_id)
    if row is None:
        raise HTTPException(status_code=404, detail="run_not_found")
    return {
        "run_id": run_id,
        "status": row.get("status"),
        "step_count": row.get("step_count", 0),
        "artifact": row.get("artifact") or {},
        "error": row.get("error"),
    }


@app.post("/v1/runs/{run_id}/cancel")
def cancel_run(
    run_id: str,
    x_runner_token: str | None = Header(default=None, alias="X-Runner-Token"),
) -> dict[str, str]:
    _auth(x_runner_token)
    row = _store.get(run_id)
    if row is None:
        raise HTTPException(status_code=404, detail="run_not_found")
    ev = _cancel_flags.setdefault(run_id, threading.Event())
    ev.set()
    if row.get("status") in ("queued", "running"):
        row["status"] = "cancelled"
        row["finished_at"] = _now_iso()
    return {"status": str(row.get("status") or "cancelled")}
