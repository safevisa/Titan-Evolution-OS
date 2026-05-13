from fastapi import APIRouter

router = APIRouter(prefix="/crm", tags=["crm"])


@router.get("/contacts")
async def list_contacts_placeholder() -> dict:
    return {"items": []}
