"""Parse capability references like `telegram_send_message@v1` and legacy aliases."""
from __future__ import annotations

from dataclasses import dataclass

from app.integrations.capabilities import ToolCapability

# Short ids accepted in workflows / packs → canonical catalog id.
CAPABILITY_ID_ALIASES: dict[str, str] = {
    "telegram_send": "telegram_send_message",
    "apollo_search": "apollo_search",
    "resend_email": "resend_email",
}


@dataclass(frozen=True)
class ResolvedCapabilityRef:
    capability: ToolCapability
    canonical_id: str
    version: str
    ref: str


def parse_capability_ref(raw: str) -> tuple[str, str | None]:
    """Return (base_id, version_or_none)."""
    s = (raw or "").strip()
    if "@" in s:
        base, ver = s.split("@", 1)
        return base.strip(), ver.strip() or None
    return s, None


def resolve_capability_ref(
    raw: str,
    *,
    index: dict[str, ToolCapability],
) -> ResolvedCapabilityRef | None:
    base, ver = parse_capability_ref(raw)
    canonical = CAPABILITY_ID_ALIASES.get(base, base)
    if ver:
        key = f"{canonical}@{ver}"
        cap = index.get(key) or index.get(canonical)
        if cap is None:
            return None
        if cap.version != ver:
            return None
        return ResolvedCapabilityRef(
            capability=cap,
            canonical_id=canonical,
            version=ver,
            ref=f"{canonical}@{ver}",
        )
    cap = index.get(canonical)
    if cap is None:
        return None
    return ResolvedCapabilityRef(
        capability=cap,
        canonical_id=canonical,
        version=cap.version,
        ref=f"{canonical}@{cap.version}" if cap.version else canonical,
    )
