from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ToolCapability:
    """One external integration surface (social, chat, media, code, etc.)."""

    id: str
    category: str
    display_name: str
    description: str
    auth_mode: str  # none | api_key | oauth2 | user_token
    status: str  # live | stub
    env_keys: tuple[str, ...] = field(default_factory=tuple)
    roles_hint: tuple[str, ...] = field(default_factory=tuple)
    # Tenant must have at least one of these integration_connections.provider values.
    connection_provider_any: tuple[str, ...] = field(default_factory=tuple)
    # Optional: all must be set on the API server to expose OAuth "connect" links.
    oauth_server_env_keys: tuple[str, ...] = field(default_factory=tuple)
    # Semantic version for replay / audit (e.g. telegram_send_message@v1).
    version: str = "v1"
    # Per-tenant invocations per minute (None = use category default).
    quota_per_minute: int | None = None
    # Estimated USD per successful invocation for metering rollup.
    bill_unit_usd: float = 0.0
