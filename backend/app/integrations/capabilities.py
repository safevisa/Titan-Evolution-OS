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
