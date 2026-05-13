from fastapi import APIRouter

router = APIRouter(prefix="/evolution", tags=["evolution"])


@router.get("/status")
async def evolution_status() -> dict:
    return {"phase": "skeleton", "active_ab_tests": 0}
