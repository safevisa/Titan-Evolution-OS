"""Agent-S3 loop wrapper (gui-agents) with stub mode for integration without GPU."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from app.settings import get_settings


@dataclass
class LoopResult:
    status: str
    step_count: int = 0
    artifact: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


def _stub_loop(instruction: str, max_steps: int) -> LoopResult:
    """Deterministic demo path when AGENT_S_MODE=stub (no gui-agents / grounding)."""
    steps = min(max(1, max_steps), 3)
    log: list[dict[str, Any]] = []
    for i in range(1, steps + 1):
        time.sleep(0.4)
        log.append(
            {
                "step": i,
                "action": "stub_wait",
                "detail": f"Simulated Agent-S step {i}/{steps}",
            }
        )
    return LoopResult(
        status="success",
        step_count=steps,
        artifact={
            "step_log": log,
            "mode": "stub",
            "agent": "Agent-S3",
            "note": (
                "Stub run completed. Set AGENT_S_MODE=live, install gui-agents, "
                "and configure COMPUTER_USE_GROUND_URL for real GUI automation."
            ),
            "instruction_preview": instruction[:240],
        },
    )


def _live_loop(instruction: str, max_steps: int) -> LoopResult:
    """Run AgentS3 + OSWorldACI per https://github.com/simular-ai/Agent-S."""
    settings = get_settings()
    if not settings.openai_api_key:
        return LoopResult(
            status="failed",
            error="missing_openai_api_key",
            artifact={"mode": "live"},
        )
    if not settings.ground_url:
        return LoopResult(
            status="failed",
            error="missing_computer_use_ground_url",
            artifact={"mode": "live"},
        )

    try:
        from gui_agents.s3.agents.agent_s import AgentS3
        from gui_agents.s3.agents.grounding import OSWorldACI
    except ImportError:
        return LoopResult(
            status="failed",
            error="gui_agents_not_installed",
            artifact={
                "mode": "live",
                "hint": "pip install gui-agents in the computer-use-runner image",
            },
        )

    import pyautogui

    engine_params = {
        "engine_type": "openai",
        "model": "gpt-4o",
        "api_key": settings.openai_api_key,
    }
    grounding_agent = OSWorldACI(
        platform=settings.platform,
        engine_params=engine_params,
        ground_url=settings.ground_url,
        ground_model=settings.ground_model,
        grounding_width=settings.ground_width,
        grounding_height=settings.ground_height,
    )
    agent = AgentS3(
        engine_params,
        grounding_agent,
        platform=settings.platform,
        enable_local_env=settings.enable_local_env,
    )

    obs: dict[str, Any] = {}
    traj: list[dict[str, Any]] = []
    steps = min(max(1, max_steps), settings.max_steps_hard)
    log: list[dict[str, Any]] = []

    for step in range(1, steps + 1):
        screenshot = pyautogui.screenshot()
        obs["screenshot"] = screenshot
        info, action = agent.predict(instruction=instruction, observation=obs)
        log.append({"step": step, "info": str(info)[:500], "action": str(action)[:500]})
        traj.append({"step": step, "action": action})
        if action and len(action) > 0:
            try:
                exec(action[0])
            except Exception as exc:
                log[-1]["exec_error"] = str(exc)[:300]
        if info and str(info).lower().find("done") >= 0:
            break

    return LoopResult(
        status="success",
        step_count=len(log),
        artifact={
            "step_log": log,
            "mode": "live",
            "agent": "AgentS3",
            "trajectory_steps": len(traj),
        },
    )


def run_agent_loop(
    *,
    instruction: str,
    max_steps: int,
    cancelled: callable[[], bool] | None = None,
) -> LoopResult:
    if cancelled and cancelled():
        return LoopResult(status="cancelled", error="cancelled_before_start")

    settings = get_settings()
    capped = min(max(1, max_steps), settings.max_steps_hard)
    if settings.agent_s_mode == "live":
        return _live_loop(instruction, capped)
    return _stub_loop(instruction, capped)
