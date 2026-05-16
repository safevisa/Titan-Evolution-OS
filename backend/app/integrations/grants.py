from __future__ import annotations

from typing import Any

from app.core.config import settings
from app.integrations.capabilities import ToolCapability

INTEGRATION_GRANTS_KEY = "integration_grants"


def _grants_block(tenant_config: dict[str, Any] | None) -> dict[str, Any]:
    if not tenant_config:
        return {}
    raw = tenant_config.get(INTEGRATION_GRANTS_KEY)
    return raw if isinstance(raw, dict) else {}


def enabled_capability_ids_explicit(tenant_config: dict[str, Any] | None) -> list[str] | None:
    """If tenant set an explicit allow-list, return it; otherwise None (policy: live+env default)."""
    block = _grants_block(tenant_config)
    ids = block.get("enabled_capability_ids")
    if not isinstance(ids, list):
        return None
    out = [str(x).strip() for x in ids if str(x).strip()]
    return out


def server_env_ready(cap: ToolCapability) -> bool:
    if not cap.env_keys:
        return False
    return all(getattr(settings, k, None) for k in cap.env_keys)


def oauth_server_env_ready(cap: ToolCapability) -> bool | None:
    if not cap.oauth_server_env_keys:
        return None
    return all(getattr(settings, k, None) for k in cap.oauth_server_env_keys)


def tenant_allows_capability(tenant_config: dict[str, Any] | None, cap: ToolCapability) -> bool:
    """Whether tenant policy allows this capability id (not yet checking server credentials)."""
    explicit = enabled_capability_ids_explicit(tenant_config)
    if explicit is not None:
        return cap.id in explicit
    return True


def has_user_connection(cap: ToolCapability, connection_providers: frozenset[str]) -> bool:
    if not cap.connection_provider_any:
        return False
    return bool(connection_providers & frozenset(cap.connection_provider_any))


def can_execute_capability(
    tenant_config: dict[str, Any] | None,
    cap: ToolCapability,
    *,
    connection_providers: frozenset[str] = frozenset(),
) -> tuple[bool, str]:
    """Whether invoke_capability may run now."""
    if not tenant_allows_capability(tenant_config, cap):
        return False, "capability_not_enabled_for_tenant"

    if cap.status == "stub":
        explicit = enabled_capability_ids_explicit(tenant_config)
        if explicit is None or cap.id not in explicit:
            return False, "stub_requires_explicit_grant"
        return False, "stub_not_implemented"

    if cap.id.startswith("computer_use_"):
        from app.computer_use.orchestrator import computer_use_enabled

        if not computer_use_enabled(tenant_config):
            return False, "computer_use_disabled"
        if cap.env_keys and not server_env_ready(cap):
            return False, "missing_server_credentials"
        return True, "ok"

    if cap.connection_provider_any:
        if not has_user_connection(cap, connection_providers):
            return False, "missing_user_connection"
        return True, "ok"

    if cap.env_keys:
        if not server_env_ready(cap):
            return False, "missing_server_credentials"
        return True, "ok"

    if cap.auth_mode == "none" and not cap.connection_provider_any and not cap.env_keys:
        return True, "ok"

    return False, "capability_misconfigured"
