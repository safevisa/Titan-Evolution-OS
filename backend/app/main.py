from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    yield


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


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
