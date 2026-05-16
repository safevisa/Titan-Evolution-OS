"""HTTP client for computer-use-runner (M03/M07c)."""
from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings


def runner_configured() -> bool:
    return bool(settings.computer_use_runner_url and settings.computer_use_runner_token)


async def create_run(
    *,
    instruction: str,
    max_steps: int = 30,
) -> dict[str, Any]:
    base = (settings.computer_use_runner_url or "").rstrip("/")
    token = settings.computer_use_runner_token or ""
    async with httpx.AsyncClient(timeout=httpx.Timeout(5.0, read=600.0)) as client:
        resp = await client.post(
            f"{base}/v1/runs",
            headers={"X-Runner-Token": token},
            json={
                "instruction": instruction,
                "max_steps": max(1, min(max_steps, 50)),
            },
        )
        resp.raise_for_status()
        return resp.json()


async def get_run(run_id: str) -> dict[str, Any]:
    base = (settings.computer_use_runner_url or "").rstrip("/")
    token = settings.computer_use_runner_token or ""
    async with httpx.AsyncClient(timeout=httpx.Timeout(5.0, read=60.0)) as client:
        resp = await client.get(
            f"{base}/v1/runs/{run_id}",
            headers={"X-Runner-Token": token},
        )
        resp.raise_for_status()
        return resp.json()


async def cancel_run(run_id: str) -> dict[str, Any]:
    base = (settings.computer_use_runner_url or "").rstrip("/")
    token = settings.computer_use_runner_token or ""
    async with httpx.AsyncClient(timeout=httpx.Timeout(5.0, read=30.0)) as client:
        resp = await client.post(
            f"{base}/v1/runs/{run_id}/cancel",
            headers={"X-Runner-Token": token},
        )
        resp.raise_for_status()
        return resp.json()
