"""MCP tool bridge naming and config helpers."""
from __future__ import annotations

from app.mcp.host import mcp_server_configs, servers_to_autostart
from app.mcp.tool_bridge import MCP_TOOL_PREFIX, is_mcp_tool_name, resolve_mcp_tool_name


def test_mcp_tool_prefix() -> None:
    assert is_mcp_tool_name("mcp__brave_web_search")
    assert not is_mcp_tool_name("apollo_search")


def test_resolve_mcp_tool_name() -> None:
    name_map = {"mcp__fetch": "fetch"}
    assert resolve_mcp_tool_name("mcp__fetch", name_map) == "fetch"
    assert resolve_mcp_tool_name("mcp__unknown", {}) == "unknown"


def test_servers_to_autostart_always_includes_memory() -> None:
    ids = servers_to_autostart()
    assert "memory" in ids
    assert "fetch" in ids


def test_mcp_server_configs_has_brave_when_key_set(monkeypatch) -> None:
    monkeypatch.setattr("app.mcp.host.settings.brave_api_key", "test-key")
    cfg = mcp_server_configs()
    assert "brave_search" in cfg
    assert cfg["brave_search"]["env"]["BRAVE_API_KEY"] == "test-key"
