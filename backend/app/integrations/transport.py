"""Stateless HTTP transport for third-party APIs: timeouts, retries (5xx), circuit breaker."""
from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx

_DEFAULT_TIMEOUT = 25.0
_MAX_RETRIES = 2
_RETRY_STATUSES = frozenset({500, 502, 503, 504, 429})
_CB_FAILURE_THRESHOLD = 5
_CB_OPEN_SECONDS = 45.0

_lock = asyncio.Lock()
_circuit: dict[str, dict[str, float | int]] = {}


def _cb_get(provider: str) -> dict[str, float | int]:
    return _circuit.setdefault(
        provider,
        {"failures": 0, "open_until": 0.0},
    )


async def _cb_before(provider: str) -> None:
    async with _lock:
        st = _cb_get(provider)
        if time.time() < float(st["open_until"]):
            raise httpx.HTTPError(f"circuit_open:{provider}")


async def _cb_success(provider: str) -> None:
    async with _lock:
        st = _cb_get(provider)
        st["failures"] = 0
        st["open_until"] = 0.0


async def _cb_failure(provider: str) -> None:
    async with _lock:
        st = _cb_get(provider)
        st["failures"] = int(st["failures"]) + 1
        if int(st["failures"]) >= _CB_FAILURE_THRESHOLD:
            st["open_until"] = time.time() + _CB_OPEN_SECONDS


def _should_retry(status: int) -> bool:
    return status in _RETRY_STATUSES


async def integration_request(
    method: str,
    url: str,
    *,
    provider: str,
    timeout: float = _DEFAULT_TIMEOUT,
    retries: int = _MAX_RETRIES,
    **kwargs: Any,
) -> httpx.Response:
    """
    Execute HTTP call for integrations. Retries on 5xx/429; does not retry 4xx.
    Raises httpx.HTTPError when circuit is open or all attempts fail.
    """
    await _cb_before(provider)
    last_exc: Exception | None = None
    attempts = max(1, retries + 1)
    for attempt in range(attempts):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.request(method.upper(), url, **kwargs)
            if _should_retry(resp.status_code) and attempt < attempts - 1:
                await asyncio.sleep(0.4 * (attempt + 1))
                continue
            if resp.status_code >= 500:
                await _cb_failure(provider)
            else:
                await _cb_success(provider)
            return resp
        except httpx.HTTPError as e:
            last_exc = e
            if attempt < attempts - 1:
                await asyncio.sleep(0.4 * (attempt + 1))
                continue
            await _cb_failure(provider)
            raise
    if last_exc:
        raise last_exc
    raise httpx.HTTPError("integration_request_failed")
