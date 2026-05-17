from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    from app.core.config import settings
    from app.mcp.host import get_mcp_host, servers_to_autostart

    if settings.mcp_autostart:
        host = get_mcp_host()
        await host.start(servers_to_autostart())
    yield
    if settings.mcp_autostart:
        await get_mcp_host().stop()


_DESCRIPTION = """
## Titan Evolution OS — API Reference

Self-evolving digital workforce operating system. Create tenants, deploy AI agents,
run tasks, and let the system automatically improve agent prompts over time.

### Quick start
1. `POST /api/v1/tenants` — create a tenant (set `auto_provision=true` for instant agents)
2. `GET /api/v1/tenants` — list tenants and copy the tenant UUID
3. `POST /api/v1/tasks/smart` — LLM infers task type + workflow; then enqueue (goal_pipeline runs the DAG with multiple agents)
4. `POST /api/v1/tenants/{tenant_id}/sync-enterprise-roster` — add missing roles from the 54-role catalog + skills
5. `GET /api/v1/agents/enterprise-catalog` — read-only list of built-in roles and skill tags
6. `GET /api/v1/tasks/workflow-templates?tenant_id=` — list DAG templates for that tenant’s industry plugin
7. `POST /api/v1/tasks/{id}/enqueue` — run the task via Celery
8. `POST /api/v1/tasks/{id}/feedback` — rate the result (0–1 quality score)
9. `GET /api/v1/evolution/status` — view KPI scores and trigger evolution
10. `POST /api/v1/admin/sync-all-enterprise-rosters` — bulk roster sync (requires `X-Titan-Admin-Key` = `TITAN_ADMIN_API_KEY` on the API server)
11. `GET /api/v1/admin/tenants-overview` — tenant list for operators (same header)
12. `GET /api/v1/integrations/capabilities?tenant_id=` — external tool catalog + tenant grant / server readiness flags
13. `PATCH /api/v1/integrations/tenants/{tenant_id}/grants` — set `enabled_capability_ids` (stubs need explicit grant; live tools need env keys)
14. `POST /api/v1/integrations/tenants/{tenant_id}/connections/webhook` — save Discord/Slack/Feishu/WeChat Work webhook (encrypted); requires `TITAN_INTEGRATIONS_FERNET_KEY`
15. `GET /api/v1/integrations/tenants/{tenant_id}/connections` — list connected providers (no secrets)
16. `GET /api/v1/integrations/oauth/slack/start?tenant_id=` — Slack OAuth (needs `TITAN_API_PUBLIC_BASE_URL` + Slack app credentials)
17. `GET /api/v1/integrations/oauth/twitter/start?tenant_id=` — X OAuth 2 PKCE
18. `GET /api/v1/integrations/oauth/linkedin/start?tenant_id=` — LinkedIn OAuth
19. `POST /api/v1/integrations/tenants/{tenant_id}/connections/credential` — Telegram / WhatsApp Cloud / 微信公众号凭证（加密）
20. `GET /api/v1/integrations/oauth/facebook/start?tenant_id=` — Facebook Page + 可选 Instagram 商业号
21. `GET /api/v1/integrations/oauth/weibo/start?tenant_id=` — 新浪微博 OAuth
22. `GET /api/v1/integrations/oauth/reddit/start?tenant_id=` — Reddit OAuth
23. `GET /api/v1/integrations/oauth/google-youtube/start?tenant_id=` — YouTube Data（发评论等）

### Authentication
Currently open — JWT auth planned for Phase 5 production release.

### Rate limits
Enforced per tenant plan via Redis (tokens/min). Quota: starter 20K, growth 100K, enterprise 500K.
"""

app = FastAPI(
    title="Titan Evolution OS",
    version="1.0.0",
    description=_DESCRIPTION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://www.tokenply.world",
        "https://tokenply.world",
        "http://www.tokenply.world",
        "http://tokenply.world",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix="/api/v1")

from app.websocket import ws_router  # noqa: E402

app.include_router(ws_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
