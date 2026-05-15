"""Normalize capability params: control keys off the wire + redacted audit snapshots."""
from __future__ import annotations

import copy
import re
from typing import Any

CONTROL_KEYS = frozenset({"_idempotency_key", "_correlation_id", "_actor"})
_SENSITIVE_SUBSTR = re.compile(
    r"(token|secret|password|credential|authorization|webhook|bearer)",
    re.I,
)


def split_control_params(params: dict[str, Any] | None) -> tuple[dict[str, Any], str | None, str | None, str | None]:
    """Return (clean_params, idempotency_key, correlation_id, actor)."""
    raw = dict(params or {})
    key = raw.pop("_idempotency_key", None)
    corr = raw.pop("_correlation_id", None)
    actor = raw.pop("_actor", None)
    idem = str(key).strip()[:160] if key is not None and str(key).strip() else None
    corr_s = str(corr).strip()[:128] if corr is not None and str(corr).strip() else None
    actor_s = str(actor).strip()[:256] if actor is not None and str(actor).strip() else None
    return raw, idem, corr_s, actor_s


def redact_params_snapshot(params: dict[str, Any], *, max_str: int = 240) -> dict[str, Any]:
    """Shallow copy safe for audit logs: no secrets, bounded size."""
    out: dict[str, Any] = {}
    for k, v in list(params.items())[:80]:
        if k in CONTROL_KEYS:
            continue
        lk = str(k).lower()
        if _SENSITIVE_SUBSTR.search(lk):
            out[k] = "[redacted]"
            continue
        if isinstance(v, str):
            s = v[:max_str] + ("…" if len(v) > max_str else "")
            out[k] = s
        elif isinstance(v, (int, float, bool)) or v is None:
            out[k] = v
        elif isinstance(v, dict):
            out[k] = redact_params_snapshot(v, max_str=max(40, max_str // 2))
        elif isinstance(v, list):
            out[k] = f"[list:{len(v)}]"
        else:
            out[k] = str(type(v).__name__)
    return out


def summarize_capability_result(result: dict[str, Any], *, max_depth_keys: int = 32) -> dict[str, Any]:
    """Small JSON-safe snapshot for idempotency / audit (no large payloads)."""
    if not isinstance(result, dict):
        return {"type": type(result).__name__}
    snap: dict[str, Any] = {}
    for i, (k, v) in enumerate(result.items()):
        if i >= max_depth_keys:
            snap["_truncated"] = True
            break
        if k in ("data", "raw") and isinstance(v, dict):
            snap[k] = {str(sk): type(sv).__name__ for sk, sv in list(v.items())[:12]}
        elif k == "data" and isinstance(v, list):
            snap[k] = f"[list:{len(v)}]"
        elif isinstance(v, (str, int, float, bool)) or v is None:
            snap[k] = (str(v)[:120] + "…") if isinstance(v, str) and len(str(v)) > 120 else v
        elif isinstance(v, dict):
            snap[k] = summarize_capability_result(v, max_depth_keys=8)
        else:
            snap[k] = type(v).__name__
    return snap


def shallow_copy_params(params: dict[str, Any] | None) -> dict[str, Any]:
    return copy.deepcopy(params) if params else {}
