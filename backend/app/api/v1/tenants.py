from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.domain import Tenant

router = APIRouter(prefix="/tenants", tags=["tenants"])


class TenantCreate(BaseModel):
    name: str
    industry_plugin: str = "payment_fintech"
    plan: str = "starter"


class TenantRead(BaseModel):
    id: UUID
    name: str
    industry_plugin: str
    plan: str

    model_config = {"from_attributes": True}


@router.get("", response_model=list[TenantRead])
async def list_tenants(db: AsyncSession = Depends(get_db)) -> list[Tenant]:
    res = await db.execute(select(Tenant).order_by(Tenant.created_at.desc()))
    return list(res.scalars().all())


@router.post("", response_model=TenantRead)
async def create_tenant(body: TenantCreate, db: AsyncSession = Depends(get_db)) -> Tenant:
    t = Tenant(name=body.name, industry_plugin=body.industry_plugin, plan=body.plan)
    db.add(t)
    await db.commit()
    await db.refresh(t)
    return t
