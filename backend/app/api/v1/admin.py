"""Platform admin operations — protected by TITAN_ADMIN_API_KEY (header X-Titan-Admin-Key)."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.domain import Tenant
from app.services.enterprise_roster_sync import sync_tenant_enterprise_roster

router = APIRouter(prefix="/admin", tags=["admin"])


def _require_admin_key(x_titan_admin_key: Optional[str]) -> None:
    expected = (settings.titan_admin_api_key or "").strip()
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="TITAN_ADMIN_API_KEY is not set on the API server",
        )
    if not x_titan_admin_key or x_titan_admin_key.strip() != expected:
        raise HTTPException(status_code=403, detail="Invalid or missing X-Titan-Admin-Key")


@router.post("/sync-all-enterprise-rosters")
async def sync_all_enterprise_rosters(
    db: AsyncSession = Depends(get_db),
    x_titan_admin_key: Optional[str] = Header(default=None, alias="X-Titan-Admin-Key"),
) -> dict:
    """Run enterprise roster sync for every tenant (agents + skills)."""
    _require_admin_key(x_titan_admin_key)
    res = await db.execute(select(Tenant).order_by(Tenant.created_at.desc()))
    tenants = list(res.scalars().all())
    results: list[dict] = []
    for t in tenants:
        row = await sync_tenant_enterprise_roster(db, t.id)
        results.append(
            {
                "tenant_id": str(t.id),
                "tenant_name": t.name,
                "industry_plugin": t.industry_plugin,
                **row,
            }
        )
    ok_n = sum(1 for r in results if r.get("ok"))
    return {
        "tenants_processed": len(tenants),
        "tenants_ok": ok_n,
        "tenants_failed": len(tenants) - ok_n,
        "results": results,
    }


@router.get("/tenants-overview")
async def tenants_overview(
    db: AsyncSession = Depends(get_db),
    x_titan_admin_key: Optional[str] = Header(default=None, alias="X-Titan-Admin-Key"),
) -> list[dict]:
    """Lightweight tenant list for admin dashboards."""
    _require_admin_key(x_titan_admin_key)
    res = await db.execute(select(Tenant).order_by(Tenant.created_at.desc()))
    return [
        {
            "id": str(t.id),
            "name": t.name,
            "plan": t.plan,
            "industry_plugin": t.industry_plugin,
        }
        for t in res.scalars().all()
    ]
