from fastapi import APIRouter

from app.api.v1 import agents, analytics, crm, evolution, llm, memory, tasks, tenants

api_router = APIRouter()
api_router.include_router(tenants.router)
api_router.include_router(agents.router)
api_router.include_router(tasks.router)
api_router.include_router(llm.router)
api_router.include_router(evolution.router)
api_router.include_router(memory.router)
api_router.include_router(crm.router)
api_router.include_router(analytics.router)
