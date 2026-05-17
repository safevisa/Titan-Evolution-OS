"""WebSocket live task logs for the tasks console."""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

ws_router = APIRouter()

_connections: dict[str, set[WebSocket]] = defaultdict(set)


def _ts() -> str:
    return datetime.now(tz=timezone.utc).strftime("%H:%M:%S")


async def broadcast_task_log(task_id: str, payload: dict) -> None:
    clients = _connections.get(task_id)
    if not clients:
        return
    body = {**payload, "ts": payload.get("ts") or _ts()}
    message = json.dumps(body, ensure_ascii=False)
    dead: set[WebSocket] = set()
    for ws in clients:
        try:
            await ws.send_text(message)
        except Exception:
            dead.add(ws)
    if dead:
        _connections[task_id] -= dead


@ws_router.websocket("/ws/tasks/{task_id}")
async def task_log_ws(websocket: WebSocket, task_id: str) -> None:
    await websocket.accept()
    _connections[task_id].add(websocket)
    await websocket.send_text(
        json.dumps(
            {
                "ts": _ts(),
                "level": "info",
                "message": f"Connected to task {task_id[:8]}…",
                "agent": "system",
            }
        )
    )
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        _connections[task_id].discard(websocket)
