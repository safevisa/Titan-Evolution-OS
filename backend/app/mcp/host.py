"""
Titan MCP Host — stdio subprocess bridge for official/community MCP servers.

Complements (does not replace) app.integrations.execute_capability.
Agents receive MCP tools prefixed with ``mcp__`` via agent_tool_runner.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)


def mcp_server_configs() -> dict[str, dict[str, Any]]:
    """Build registry from current settings (env-backed)."""
    sync_db = settings.sync_database_url or settings.database_url or ""
    return {
        "brave_search": {
            "command": ["npx", "-y", "@modelcontextprotocol/server-brave-search"],
            "env": {"BRAVE_API_KEY": settings.brave_api_key or ""},
            "description": "Web search via Brave Search API",
            "roles": ["hunter", "researcher", "outreach", "delivery", "manager"],
            "priority": 1,
        },
        "fetch": {
            "command": ["uvx", "mcp-server-fetch"],
            "description": "Fetch web pages as markdown",
            "roles": ["hunter", "researcher"],
            "priority": 2,
        },
        "memory": {
            "command": ["npx", "-y", "@modelcontextprotocol/server-memory"],
            "description": "Persistent knowledge graph memory",
            "roles": ["hunter", "researcher", "outreach", "delivery", "manager"],
            "priority": 1,
        },
        "sequential_thinking": {
            "command": ["npx", "-y", "@modelcontextprotocol/server-sequential-thinking"],
            "description": "Multi-step reasoning scaffold",
            "roles": ["manager", "researcher"],
            "priority": 2,
        },
        "slack": {
            "command": ["npx", "-y", "@modelcontextprotocol/server-slack"],
            "env": {
                "SLACK_BOT_TOKEN": settings.slack_bot_token or "",
                "SLACK_TEAM_ID": settings.slack_team_id or "",
            },
            "description": "Slack messaging",
            "roles": ["outreach", "delivery", "operations"],
            "priority": 2,
        },
        "resend": {
            "command": ["npx", "-y", "mcp-server-resend"],
            "env": {"RESEND_API_KEY": settings.resend_api_key or ""},
            "description": "Transactional email via Resend",
            "roles": ["outreach", "delivery"],
            "priority": 1,
        },
        "postgres": {
            "command": ["npx", "-y", "@modelcontextprotocol/server-postgres", sync_db],
            "description": "Read-only Postgres queries",
            "roles": ["manager", "delivery"],
            "priority": 3,
        },
        "github": {
            "command": ["npx", "-y", "@modelcontextprotocol/server-github"],
            "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": settings.github_token or ""},
            "description": "GitHub repos, issues, code search",
            "roles": ["researcher", "delivery"],
            "priority": 3,
        },
        "apollo": {
            "command": ["uvx", "apollo-mcp"],
            "env": {"APOLLO_API_KEY": settings.apollo_api_key or ""},
            "description": "Apollo.io people and company search",
            "roles": ["hunter"],
            "priority": 1,
        },
        "notion": {
            "command": ["uvx", "mcp-notion"],
            "env": {"NOTION_API_KEY": settings.notion_api_key or ""},
            "description": "Notion pages and databases",
            "roles": ["delivery", "researcher", "manager"],
            "priority": 2,
        },
    }


def servers_to_autostart() -> list[str]:
    """Only start servers with required credentials (plus always-on local tools)."""
    ids: list[str] = ["memory", "sequential_thinking", "fetch"]
    if settings.brave_api_key:
        ids.append("brave_search")
    if settings.resend_api_key:
        ids.append("resend")
    if settings.slack_bot_token:
        ids.append("slack")
    if settings.apollo_api_key:
        ids.append("apollo")
    if settings.notion_api_key:
        ids.append("notion")
    if settings.github_token:
        ids.append("github")
    if settings.sync_database_url or settings.database_url:
        ids.append("postgres")
    return ids


@dataclass
class MCPTool:
    name: str
    description: str
    input_schema: dict[str, Any]
    server_id: str


@dataclass
class MCPServer:
    server_id: str
    config: dict[str, Any]
    process: asyncio.subprocess.Process | None = None
    tools: list[MCPTool] = field(default_factory=list)
    ready: bool = False
    _request_id: int = 0

    def next_id(self) -> int:
        self._request_id += 1
        return self._request_id


class TitanMCPHost:
    def __init__(self) -> None:
        self._servers: dict[str, MCPServer] = {}
        self._tool_index: dict[str, MCPServer] = {}
        self._started = False

    @property
    def is_started(self) -> bool:
        return self._started

    def ready_server_count(self) -> int:
        return sum(1 for s in self._servers.values() if s.ready)

    async def start(self, server_ids: list[str] | None = None) -> None:
        if self._started and self.ready_server_count() > 0:
            return
        configs = mcp_server_configs()
        ids = server_ids or servers_to_autostart()
        tasks = [self._start_server(sid, configs) for sid in ids if sid in configs]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        started = sum(1 for r in results if r is True)
        self._started = True
        logger.info("[MCP Host] %s/%s servers ready", started, len(ids))

    async def stop(self) -> None:
        for srv in self._servers.values():
            if srv.process and srv.process.returncode is None:
                srv.process.terminate()
                try:
                    await asyncio.wait_for(srv.process.wait(), timeout=5)
                except asyncio.TimeoutError:
                    srv.process.kill()
        self._servers.clear()
        self._tool_index.clear()
        self._started = False
        logger.info("[MCP Host] stopped")

    async def list_tools_for_role(self, role: str) -> list[dict[str, Any]]:
        tools: list[dict[str, Any]] = []
        for srv in self._servers.values():
            if not srv.ready:
                continue
            if role not in srv.config.get("roles", []):
                continue
            for tool in srv.tools:
                tools.append(
                    {
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": tool.input_schema,
                        },
                    }
                )
        return tools

    async def call_tool(self, tool_name: str, arguments: dict[str, Any], *, timeout: float = 45.0) -> dict[str, Any]:
        server = self._tool_index.get(tool_name)
        if not server or not server.ready or not server.process:
            return {
                "content": [{"type": "text", "text": f"Tool '{tool_name}' unavailable"}],
                "isError": True,
            }
        req_id = server.next_id()
        request = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
        }
        try:
            resp = await asyncio.wait_for(self._send_request(server, request), timeout=timeout)
            return resp.get("result", {"content": [], "isError": False})
        except asyncio.TimeoutError:
            return {
                "content": [{"type": "text", "text": f"Timeout calling {tool_name}"}],
                "isError": True,
            }
        except Exception as exc:
            return {
                "content": [{"type": "text", "text": str(exc)}],
                "isError": True,
            }

    async def _start_server(self, server_id: str, configs: dict[str, dict[str, Any]]) -> bool:
        config = configs[server_id]
        srv = MCPServer(server_id=server_id, config=config)
        self._servers[server_id] = srv
        cmd = config.get("command")
        if not cmd or not cmd[-1]:
            logger.warning("[MCP] %s: missing command or connection string", server_id)
            return False
        env = {**os.environ, **config.get("env", {})}
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
            srv.process = proc
        except FileNotFoundError:
            logger.warning("[MCP] %s: binary not found (%s)", server_id, cmd[0])
            return False

        init_req = {
            "jsonrpc": "2.0",
            "id": srv.next_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "clientInfo": {"name": "titan-evolution-os", "version": "1.0.0"},
            },
        }
        try:
            await asyncio.wait_for(self._send_request(srv, init_req), timeout=15)
        except Exception as exc:
            logger.warning("[MCP] %s: init failed: %s", server_id, exc)
            return False

        list_req = {
            "jsonrpc": "2.0",
            "id": srv.next_id(),
            "method": "tools/list",
            "params": {},
        }
        try:
            resp = await asyncio.wait_for(self._send_request(srv, list_req), timeout=15)
            for t in resp.get("result", {}).get("tools", []):
                tool = MCPTool(
                    name=t["name"],
                    description=t.get("description", ""),
                    input_schema=t.get("inputSchema", {"type": "object", "properties": {}}),
                    server_id=server_id,
                )
                srv.tools.append(tool)
                self._tool_index[t["name"]] = srv
            srv.ready = True
            logger.info("[MCP] %s: %s tools", server_id, len(srv.tools))
            return True
        except Exception as exc:
            logger.warning("[MCP] %s: tools/list failed: %s", server_id, exc)
            return False

    async def _send_request(self, srv: MCPServer, request: dict[str, Any]) -> dict[str, Any]:
        assert srv.process and srv.process.stdin and srv.process.stdout
        line = json.dumps(request) + "\n"
        srv.process.stdin.write(line.encode())
        await srv.process.stdin.drain()
        while True:
            raw = await srv.process.stdout.readline()
            if not raw:
                raise ConnectionError(f"MCP server {srv.server_id} closed stdout")
            try:
                msg = json.loads(raw.decode().strip())
                if msg.get("id") == request["id"]:
                    return msg
            except json.JSONDecodeError:
                continue


_host: TitanMCPHost | None = None


def get_mcp_host() -> TitanMCPHost:
    global _host
    if _host is None:
        _host = TitanMCPHost()
    return _host
